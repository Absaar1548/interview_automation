"""
Question Generator Service
--------------------------
Generates interview questions: first 5-6 from question bank, then conversational questions
using Azure OpenAI GPT-4o based on parsed resume and JD.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.sql.models.question import Question, DifficultyEnum, CategoryEnum
from app.db.sql.models.coding_problem import CodingProblem
from app.services.resume_jd_parser import resume_jd_parser
from app.services.azure_openai_service import azure_openai_service

logger = logging.getLogger(__name__)


class QuestionGeneratorService:
    """Service to generate interview questions from resume and JD."""
    
    # Directory where resumes are stored
    RESUME_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "resumes")

    @staticmethod
    def _normalize_problem_solving_type(coding_config: Optional[Dict[str, Any]]) -> str:
        cfg = coding_config or {}
        raw = (
            cfg.get("problem_solving_type")
            or cfg.get("problem_type")
            or cfg.get("type")
            or "coding"
        )
        raw_s = str(raw).strip().lower()
        if raw_s in ("analytical", "analytical_question", "analytical_questions", "non_coding", "non-coding"):
            return "analytical"
        return "coding"
    
    @staticmethod
    async def generate_curated_questions(
        session: AsyncSession,
        template_id: str,
        candidate_id: str,
        resume_id: Optional[str] = None,
        resume_text: Optional[str] = None,
        job_description: Optional[str] = None,
        resume_json: Optional[Dict[str, Any]] = None,
        jd_json: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """
        Generate curated questions: first 5-6 from question bank, then conversational questions.
        
        Args:
            session: Database session
            template_id: UUID string of the interview template
            candidate_id: UUID string of the candidate
            resume_id: Resume identifier (used as fallback to find resume file)
            resume_text: Parsed resume text from database (preferred)
            job_description: Job description text
            resume_json: Pre-parsed structured resume data
            jd_json: Pre-parsed structured job description data
            
        Returns:
            dict conforming to CuratedQuestionsPayload schema
        """
        try:
            all_questions = []
            
            # Step 0: Get template to read config for number of questions
            import uuid as uuid_module
            from app.db.sql.models.interview_template import InterviewTemplate
            template_stmt = select(InterviewTemplate).where(InterviewTemplate.id == uuid_module.UUID(template_id))
            template_result = await session.execute(template_stmt)
            template = template_result.scalar_one_or_none()
            
            # Get number of technical questions and source from template config
            num_technical_questions = 6  # Default
            question_source = "ai_generated" # Default
            if template:
                technical_config = template.technical_config or {}
                if isinstance(technical_config, dict):
                    question_source = technical_config.get("question_source", "ai_generated")
                    # Count total questions from difficulty distribution (only easy, medium, hard)
                    difficulty_keys = ["easy", "medium", "hard"]
                    num_technical_questions = sum(v for k, v in technical_config.items() if k.lower() in difficulty_keys and isinstance(v, int))
                    
                    if num_technical_questions == 0:
                        num_technical_questions = technical_config.get("total_questions", 6)
                # Fallback to settings if technical_config not available
                elif template.settings and isinstance(template.settings, dict):
                    difficulty_dist = template.settings.get("difficulty_distribution", {})
                    if difficulty_dist:
                        num_technical_questions = sum(v for v in difficulty_dist.values() if isinstance(v, int))
            
            logger.info(f"Template Configuration - Technical questions: {num_technical_questions}, Source: {question_source}")
            
            # Step 1: Prepare resume and JD data
            logger.debug("Step 1: Preparing resume and JD data...")
            if resume_json:
                resume_data = resume_json.copy() if isinstance(resume_json, dict) else {}
                if resume_text and 'text' not in resume_data:
                    resume_data['text'] = resume_text
                logger.debug("Using provided resume_json")
            elif resume_text:
                # If we have resume text but no parsed JSON, parse it now with LLM
                logger.debug("Parsing resume text with LLM...")
                from app.services.resume_parser import parse_resume_with_llm
                resume_data = parse_resume_with_llm(resume_text)
                if not isinstance(resume_data, dict):
                    resume_data = {}
                resume_data['text'] = resume_text
                logger.debug("Resume parsed with LLM")
            else:
                logger.debug("Parsing resume from file...")
                resume_data = QuestionGeneratorService._parse_resume(resume_id)
                if not isinstance(resume_data, dict):
                    resume_data = {}
                logger.debug("Resume parsed from file")
            
            # Ensure resume_data is a dict with required keys
            if not isinstance(resume_data, dict):
                logger.warning("resume_data is not a dict, initializing empty dict")
                resume_data = {}
            
            # Ensure required keys exist
            if 'skills' not in resume_data:
                resume_data['skills'] = []
            if 'projects' not in resume_data:
                resume_data['projects'] = []
            if 'experience' not in resume_data:
                resume_data['experience'] = []
            
            # Ensure skills are extracted from all sources in resume (projects, experience)
            # Handle cases where skills might be None, empty, or in wrong format
            try:
                skills_list = resume_data.get('skills', [])
                if not isinstance(skills_list, list):
                    skills_list = []
                all_resume_skills = set(skills_list)
            except Exception as e:
                logger.warning(f"Error extracting skills from resume_data: {e}")
                all_resume_skills = set()
            
            # Add technologies from projects (handle both dict and string formats)
            try:
                projects_list = resume_data.get('projects', [])
                if not isinstance(projects_list, list):
                    projects_list = []
                for project in projects_list:
                    try:
                        if isinstance(project, dict):
                            project_techs = project.get('technologies', [])
                            if project_techs and isinstance(project_techs, list):
                                all_resume_skills.update(project_techs)
                        elif isinstance(project, str):
                            # If project is a string, skip technology extraction
                            logger.debug(f"Project is a string, skipping technology extraction: {project[:50]}")
                    except Exception as proj_error:
                        logger.warning(f"Error processing project item: {proj_error}")
                        continue
            except Exception as e:
                logger.warning(f"Error processing projects: {e}")
            
            # Add technologies from experience (handle both dict and string formats)
            try:
                experience_list = resume_data.get('experience', [])
                if not isinstance(experience_list, list):
                    experience_list = []
                for exp in experience_list:
                    try:
                        if isinstance(exp, dict):
                            exp_techs = exp.get('technologies', [])
                            if exp_techs and isinstance(exp_techs, list):
                                all_resume_skills.update(exp_techs)
                        elif isinstance(exp, str):
                            # If experience is a string, skip technology extraction
                            logger.debug(f"Experience item is a string, skipping technology extraction: {exp[:50]}")
                    except Exception as exp_error:
                        logger.warning(f"Error processing experience item: {exp_error}")
                        continue
            except Exception as e:
                logger.warning(f"Error processing experience: {e}")
            
            resume_data['skills'] = list(all_resume_skills)
            
            # Parse job description
            if jd_json:
                jd_data = jd_json
                logger.debug("Using provided jd_json")
            else:
                logger.debug("Parsing job description with LLM... ✅ Job description parsed with LLM")
            
            # Ensure JD has all skills from technologies field too
            jd_skills_set = set(jd_data.get('required_skills', []) + jd_data.get('technologies', []))
            jd_data['required_skills'] = list(jd_skills_set)
            
            # Extract role and skills for filtering question bank
            role_name = jd_data.get('job_title') or jd_data.get('role_name', '')
            
            # Combine skills from both resume and JD
            resume_skills = list(all_resume_skills)
            jd_skills = list(jd_skills_set)
            
            # Merge and deduplicate skills
            all_skills = list(set(resume_skills + jd_skills))
            logger.debug(f"[QuestionGenerator] Using skills for question selection: {all_skills}")
            logger.debug(f"[QuestionGenerator] Combined Skills: {all_skills}")
            
            # Step 2: Generate technical questions based on source
            logger.debug("GENERATING TECHNICAL QUESTIONS FOR INTERVIEW")
            
            technical_questions = []
            
            if question_source == "question_bank":
                logger.debug(f"📚 Fetching {num_technical_questions} questions from bank...")
                technical_questions = await QuestionGeneratorService._get_questions_from_bank(
                    session=session,
                    num_questions=num_technical_questions,
                    role_name=role_name,
                    required_skills=all_skills,
                    resume_skills=resume_skills,
                    jd_skills=jd_skills
                )
            
            # Only use LLM if source is AI_GENERATED, or if question_bank was requested but is literally empty
            if question_source == "ai_generated" or (question_source == "question_bank" and not technical_questions):
                logger.debug(f"🤖 Generating {num_technical_questions} technical questions using LLM...")
                # Check if Azure OpenAI is available
                from app.services.azure_openai_service import azure_openai_service
                if not azure_openai_service.async_client and not azure_openai_service.client:
                    logger.warning("Azure OpenAI client not initialized! Check configs in .env. Falling back to mock questions.")
                else:
                    logger.debug("Azure OpenAI client is initialized and ready")
                
                try:
                    technical_questions = await QuestionGeneratorService._generate_questions_with_llm(
                        num_questions=num_technical_questions,
                        skills=all_skills,
                        role_name=role_name,
                        resume_data=resume_data,
                        jd_data=jd_data
                    )
                    # Ensure LLM generated questions
                    if not technical_questions or len(technical_questions) == 0:
                        logger.warning("LLM generation returned empty, using mock questions")
                        technical_questions = QuestionGeneratorService._generate_mock_skill_based_questions(
                            num_questions=num_technical_questions,
                            skills=all_skills,
                            role_name=role_name
                        )
                    else:
                        logger.info(f"LLM successfully generated {len(technical_questions)} technical questions")
                except Exception as llm_error:
                    logger.error(f"LLM question generation failed: {llm_error}", exc_info=True)
                    logger.error(f"LLM generation failed: {llm_error}. Using mock questions instead.")
                    technical_questions = QuestionGeneratorService._generate_mock_skill_based_questions(
                        num_questions=num_technical_questions,
                        skills=all_skills,
                        role_name=role_name
                    )

            # If still no questions, use mock fallback
            if not technical_questions:
                logger.warning("LLM/Bank failed, using mock questions")
                technical_questions = QuestionGeneratorService._generate_mock_skill_based_questions(
                    num_questions=num_technical_questions,
                    skills=all_skills,
                    role_name=role_name
                )
            
            # Mark metadata
            for q in technical_questions:
                q['question_type'] = q.get('question_type', 'static')
                q['source'] = q.get('source', 'llm_generated' if question_source == "ai_generated" else "question_bank")
                q['evaluation_mode'] = q.get('evaluation_mode', 'text')
            
            # Ensure proper ordering
            for idx, q in enumerate(technical_questions, 1):
                q['order'] = idx
            all_questions.extend(technical_questions)
            
            logger.info(f"Generated {len(technical_questions)} technical questions")
            
            
            # CRITICAL CHECK: Ensure we have at least some questions before proceeding
            if len(all_questions) == 0:
                logger.error("❌ CRITICAL: No questions after LLM generation!")
                logger.error("No questions generated from LLM! Creating emergency questions...")
                emergency_questions = QuestionGeneratorService._generate_mock_skill_based_questions(
                    num_questions=num_technical_questions,
                    skills=all_skills,
                    role_name=role_name
                )
                for idx, q in enumerate(emergency_questions, 1):
                    q['order'] = idx
                    q['question_type'] = 'static'  # Schema expects 'static', 'conversational', or 'coding'
                    q['source'] = 'emergency_fallback'
                    q['evaluation_mode'] = q.get('evaluation_mode', 'text')  # Ensure evaluation_mode is set
                all_questions.extend(emergency_questions)
                logger.warning(f"Created {len(all_questions)} emergency questions")
            
            # NOTE: Conversational questions will be generated LIVE during interview
            # based on candidate responses. They are NOT generated at scheduling time.
            logger.debug("Conversational questions will be generated LIVE during interview based on candidate responses.")
            
            # Final sort by order to ensure correct sequence
            all_questions.sort(key=lambda x: x.get('order', 999))
            
            # CRITICAL: Ensure we have at least one question
            if not all_questions or len(all_questions) == 0:
                logger.error("❌ CRITICAL: No questions generated after all attempts!")
                logger.warning(f"Generated {len(all_questions)} emergency fallback questions")
            
            logger.info(f"TOTAL QUESTIONS GENERATED: {len(all_questions)}")
            
            # Final validation before returning
            if not all_questions or len(all_questions) == 0:
                logger.error("❌ CRITICAL: Still no questions after emergency fallback!")
                raise ValueError("Failed to generate any questions. All fallback mechanisms failed.")
            
            # Step 3: Build problem-solving section (coding or analytical)
            problem_solving_type = "coding"
            coding_problems_formatted = []
            analytical_questions_formatted = []
            if template and template.coding_config:
                problem_solving_type = QuestionGeneratorService._normalize_problem_solving_type(template.coding_config)
                if problem_solving_type == "coding":
                    from app.services.template_engine import template_engine
                    coding_items = await template_engine._generate_coding_questions(template, session)
                    for item in coding_items:
                        if item.coding_problem:
                            p = item.coding_problem
                            coding_problems_formatted.append({
                                "problem_id": str(p.id),
                                "title": p.title,
                                "difficulty": p.difficulty,
                                "description": p.description,
                                "starter_code": p.starter_code
                            })
                else:
                    count = int((template.coding_config or {}).get("count", 2) or 2)
                    analytical_questions = await QuestionGeneratorService._generate_analytical_questions_with_llm(
                        num_questions=max(1, count),
                        role_name=role_name or "Business Analyst",
                        resume_data=resume_data,
                        jd_data=jd_data,
                    )
                    for i, q in enumerate(analytical_questions, 1):
                        analytical_questions_formatted.append({
                            "question_id": q.get("question_id"),
                            "question_type": "static",
                            "order": i,
                            "prompt": q.get("prompt", ""),
                            "difficulty": q.get("difficulty", "medium"),
                            "time_limit_sec": q.get("time_limit_sec", 300),
                            "answer_mode": "audio",
                            "evaluation_mode": "audio",
                            "source": q.get("source", "llm_generated"),
                            "category": q.get("category", "ANALYTICAL"),
                            "focus": q.get("focus", "non-technical problem solving")
                        })
            
            return {
                "template_id": template_id,
                "generated_from": {
                    "resume_id": resume_id or candidate_id,
                    "jd_id": "jd_from_registration",
                },
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "generation_method": "question_bank_and_azure_openai_gpt4o",
                "technical_section": {"questions": all_questions},
                "coding_section": {
                    "problem_solving_type": problem_solving_type,
                    "problems": coding_problems_formatted,
                    "questions": analytical_questions_formatted,
                },
                "problem_solving_section": {
                    "problem_solving_type": problem_solving_type,
                    "problems": coding_problems_formatted,
                    "questions": analytical_questions_formatted,
                },
                "conversational_section": {"rounds": (template.conversational_config or {}).get("rounds", 0) if template else 0}
            }
        except Exception as e:
            logger.error(f"Error generating questions: {e}", exc_info=True)
            logger.error(f"ERROR in question generation: {e}. Using fallback questions...")
            # Fallback to mock questions - ensure it always returns questions
            fallback_result = await QuestionGeneratorService._generate_fallback_questions(session, template_id, candidate_id, resume_id)
            # Double-check fallback has questions
            if not fallback_result.get('questions') or len(fallback_result.get('questions', [])) == 0:
                logger.error("❌ CRITICAL: Fallback questions also empty!")
                # Last resort - create minimal questions
                fallback_result['questions'] = [
                    {
                        "question_id": "emergency_q_001",
                        "question_type": "conversational",
                        "order": 1,
                        "prompt": "Tell me about yourself and your technical background.",
                        "difficulty": "medium",
                        "time_limit_sec": 240,
                        "answer_mode": "text",
                        "evaluation_mode": "text",
                        "source": "emergency_fallback"
                    }
                ]
            return fallback_result
    
    @staticmethod
    async def _get_questions_from_bank(
        session: AsyncSession, 
        num_questions: int = 5,
        role_name: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
        resume_skills: Optional[List[str]] = None,
        jd_skills: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get questions from the question bank, filtered by role and technologies from both resume and JD."""
        try:
            import random
            from sqlalchemy import or_
            
            # Build query with filters
            # Note: We select Question directly - SQLAlchemy will handle missing columns gracefully
            # If question_type doesn't exist, it will be None/omitted
            stmt = select(Question).where(Question.is_active == True)
            
            # Comprehensive skill-to-category mapping
            skill_to_category = {
                # Python ecosystem
                'python': CategoryEnum.PYTHON,
                'django': CategoryEnum.PYTHON,
                'flask': CategoryEnum.PYTHON,
                'fastapi': CategoryEnum.PYTHON,
                'pandas': CategoryEnum.PYTHON,
                'numpy': CategoryEnum.PYTHON,
                
                # SQL/Database
                'sql': CategoryEnum.SQL,
                'postgresql': CategoryEnum.SQL,
                'mysql': CategoryEnum.SQL,
                'mongodb': CategoryEnum.SQL,
                'database': CategoryEnum.SQL,
                'db': CategoryEnum.SQL,
                
                # Machine Learning
                'machine learning': CategoryEnum.MACHINE_LEARNING,
                'ml': CategoryEnum.MACHINE_LEARNING,
                'deep learning': CategoryEnum.MACHINE_LEARNING,
                'tensorflow': CategoryEnum.MACHINE_LEARNING,
                'pytorch': CategoryEnum.MACHINE_LEARNING,
                'scikit-learn': CategoryEnum.MACHINE_LEARNING,
                'sklearn': CategoryEnum.MACHINE_LEARNING,
                'neural network': CategoryEnum.MACHINE_LEARNING,
                'ai': CategoryEnum.MACHINE_LEARNING,
                'artificial intelligence': CategoryEnum.MACHINE_LEARNING,
                
                # Data Structures & Algorithms
                'data structures': CategoryEnum.DATA_STRUCTURES,
                'algorithms': CategoryEnum.DATA_STRUCTURES,
                'dsa': CategoryEnum.DATA_STRUCTURES,
                'algorithm': CategoryEnum.DATA_STRUCTURES,
                
                # System Design
                'system design': CategoryEnum.SYSTEM_DESIGN,
                'distributed systems': CategoryEnum.SYSTEM_DESIGN,
                'microservices': CategoryEnum.SYSTEM_DESIGN,
                'architecture': CategoryEnum.SYSTEM_DESIGN,
                'scalability': CategoryEnum.SYSTEM_DESIGN,
                
                # Statistics
                'statistics': CategoryEnum.STATISTICS,
                'statistical': CategoryEnum.STATISTICS,
                'probability': CategoryEnum.STATISTICS,
            }
            
            matching_categories = []
            matching_tags = []
            
            # Process all skills (from both resume and JD)
            all_skills_to_check = list(set((required_skills or []) + (resume_skills or []) + (jd_skills or [])))
            
            logger.debug(f"[QuestionBank] Filtering questions by skills: {all_skills_to_check}")
            
            for skill in all_skills_to_check:
                if not skill:
                    continue
                skill_lower = skill.lower().strip()
                
                # Map skill to category
                for key, cat in skill_to_category.items():
                    if key in skill_lower:
                        if cat not in matching_categories:
                            matching_categories.append(cat)
                        break
                
                # Also add skill as a tag for matching
                matching_tags.append(skill_lower)
            
            # Filter by categories if we found matches
            category_condition = None
            if matching_categories:
                category_condition = Question.category.in_(matching_categories)
                logger.debug(f"[QuestionBank] Filtering by categories: {[c.value for c in matching_categories]}")
                logger.debug(f"[QuestionBank] Matching categories: {[c.value for c in matching_categories]}")
            
            # Also filter by tags if questions have tags
            tag_condition = None
            if matching_tags:
                # Check if any question tags match our skills
                # PostgreSQL JSONB contains operator
                tag_conditions = []
                for tag in matching_tags[:10]:  # Limit to avoid too many conditions
                    # Check if tags JSON array contains the skill
                    tag_conditions.append(
                        Question.tags.contains([tag])
                    )
                
                if tag_conditions:
                    tag_condition = or_(*tag_conditions)
                    logger.debug(f"[QuestionBank] Also filtering by tags: {matching_tags[:10]}")
                    logger.debug(f"[QuestionBank] Matching tags: {matching_tags[:10]}")
            
            # Combine category and tag filters with OR (question matches if it matches category OR tags)
            if category_condition and tag_condition:
                stmt = stmt.where(or_(category_condition, tag_condition))
            elif category_condition:
                stmt = stmt.where(category_condition)
            elif tag_condition:
                stmt = stmt.where(tag_condition)
            
            try:
                result = await session.execute(stmt)
                all_questions = result.scalars().all()
            except Exception as query_error:
                logger.error(f"Error executing question bank query: {query_error}", exc_info=True)
                logger.error("Error querying question bank. This might be due to missing question_type column. Trying alternative query without question_type...")
                # Try alternative query without question_type
                try:
                    from sqlalchemy import select as sql_select
                    alt_stmt = sql_select(
                        Question.id, Question.text, Question.category, 
                        Question.difficulty, Question.tags, Question.is_active
                    ).where(Question.is_active == True)
                    # Re-apply filters
                    if category_condition:
                        alt_stmt = alt_stmt.where(category_condition)
                    if tag_condition:
                        alt_stmt = alt_stmt.where(tag_condition)
                    alt_result = await session.execute(alt_stmt)
                    all_questions = alt_result.all()
                    logger.info(f"Alternative query succeeded, found {len(all_questions)} questions")
                except Exception as alt_error:
                    logger.error(f"Alternative query also failed: {alt_error}")
                    logger.error(f"Alternative query also failed: {alt_error}. Returning empty list - will use LLM fallback")
                    all_questions = []
            
            logger.info(f"Question Bank Search Results: Found {len(all_questions)} questions")
            
            # Fallback ladder: if no skill-specific questions found, fetch any active questions
            if not all_questions:
                logger.warning("[QuestionBank] No skill-specific questions found. Fetching any active questions as fallback.")
                logger.warning("No skill-specific questions found in bank. Fetching any active questions as fallback.")
                fallback_stmt = select(Question).where(Question.is_active == True)
                try:
                    res = await session.execute(fallback_stmt)
                    all_questions = res.scalars().all()
                except Exception as e:
                    logger.error(f"Fallback bank query failed: {e}")
                    all_questions = []

            # Randomly select questions
            if all_questions:
                selected_questions = random.sample(all_questions, min(num_questions, len(all_questions)))
                logger.info(f"Selected {len(selected_questions)} questions from bank for interview")
            else:
                selected_questions = []
                logger.error("Question bank is completely empty!")
            
            formatted_questions = []
            for i, q in enumerate(selected_questions, 1):
                # Handle both full Question objects and partial results
                import uuid as uuid_module
                try:
                    question_id = q.id if hasattr(q, 'id') else str(uuid_module.uuid4())
                    question_text = q.text if hasattr(q, 'text') else str(q)
                    question_category = q.category if hasattr(q, 'category') else CategoryEnum.PYTHON
                    question_difficulty = q.difficulty if hasattr(q, 'difficulty') else DifficultyEnum.MEDIUM
                except Exception as attr_error:
                    logger.error(f"Error accessing question attributes: {attr_error}")
                    # Skip this question if we can't access its attributes
                    continue
                # Randomly assign answer mode (voice or written) - 50/50 chance
                import random as rnd
                answer_mode_random = rnd.choice(["AUDIO", "TEXT"])
                
                # Override for coding questions - they should be written
                if question_category in [CategoryEnum.SQL, CategoryEnum.DATA_STRUCTURES]:
                    answer_mode = "CODE"
                else:
                    answer_mode = answer_mode_random
                
                # Time limits based on difficulty: easy 2min, medium 4min, hard 6min
                time_limits = {
                    DifficultyEnum.EASY: 120,  # 2 minutes
                    DifficultyEnum.MEDIUM: 240,  # 4 minutes
                    DifficultyEnum.HARD: 360  # 6 minutes
                }
                time_limit_sec = time_limits.get(question_difficulty, 240)
                
                # Use the safely extracted attributes
                formatted_questions.append({
                    "question_id": str(question_id),
                    "question_type": "static",
                    "order": i,
                    "prompt": question_text,
                    "difficulty": question_difficulty.value.lower() if hasattr(question_difficulty, 'value') else "medium",
                    "time_limit_sec": time_limit_sec,
                    "answer_mode": answer_mode.lower(),
                    "evaluation_mode": "text" if answer_mode == "TEXT" else ("code" if answer_mode == "CODE" else "audio"),
                    "source": "question_bank",
                    "category": question_category.value if hasattr(question_category, 'value') else "PYTHON"
                })
            
            return formatted_questions
        except Exception as e:
            logger.error(f"Error getting questions from bank: {e}")
            return []
    
    @staticmethod
    async def _generate_questions_with_llm(
        num_questions: int,
        skills: List[str],
        role_name: Optional[str] = None,
        resume_data: Optional[Dict[str, Any]] = None,
        jd_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate questions using LLM when question bank doesn't have matching questions.
        Questions are generated based on the provided skills, role, resume, and JD.
        """
        try:
            import random
            import uuid
            import asyncio
            from fastapi.concurrency import run_in_threadpool
            
            # Contextual logging
            # (Note: session_id is not passed here, but we can log important context)
            logger.info(f"🤖 [QuestionGenerator] Generating {num_questions} questions with LLM for skills: {skills}")
            
            if not azure_openai_service.async_client:
                logger.warning("Azure OpenAI async client not configured, using mock questions")
                return QuestionGeneratorService._generate_mock_skill_based_questions(num_questions, skills, role_name)
            
            # Build prompt for LLM question generation
            skills_text = ", ".join(skills[:30]) if skills else "general technical skills"
            role_text = role_name or "the role"
            
            # Get context from resume and JD if available
            resume_context = ""
            if resume_data:
                resume_skills = resume_data.get('skills', [])
                projects = resume_data.get('projects', [])
                if projects:
                    resume_context = f"\nCandidate has experience with: {', '.join(resume_skills[:10]) if resume_skills else 'various technologies'}\n"
                    resume_context += f"Projects: {', '.join([p.get('name', '') for p in projects[:3]])}"
            
            jd_context = ""
            if jd_data:
                jd_skills = jd_data.get('required_skills', []) or jd_data.get('technologies', [])
                jd_context = f"\nJob requires: {', '.join(jd_skills[:10]) if jd_skills else 'various skills'}"
            
            system_prompt = """You are an expert technical interviewer. Generate technical interview questions based on the provided skills and role.
Return ONLY a valid JSON array with this exact structure:
[
    {
        "question": "Question text here",
        "difficulty": "easy" or "medium" or "hard",
        "category": "PYTHON" or "SQL" or "MACHINE_LEARNING" or "DATA_STRUCTURES" or "SYSTEM_DESIGN" or "STATISTICS",
        "focus": "Brief description of what this question tests"
    }
]"""

            user_prompt = f"""Generate {num_questions} technical interview questions for {role_text}.

REQUIRED SKILLS:
{skills_text}
{resume_context}
{jd_context}

INSTRUCTIONS:
1. Generate questions that test knowledge of these specific skills: {skills_text}
2. Mix easy, medium, and hard difficulties as appropriate
3. Questions should be technical and relevant to the skills mentioned
4. Each question should focus on a specific skill or technology
5. Return exactly {num_questions} questions

Return ONLY the JSON array, no additional text or markdown."""

            logger.debug(f"Sending async request to Azure OpenAI (Prompt length: {len(user_prompt)} characters)")
            
            start_time = datetime.now()
            response_text = await asyncio.wait_for(
                azure_openai_service.chat_completion_json(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                ),
                timeout=60
            )
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ LLM generation completed in {duration:.2f}s")
            
            # Parse response - use threadpool for heavy JSON parsing
            import json
            import re
            logger.debug(f"Received response from Azure OpenAI (Length: {len(response_text)} characters)")
            
            # Use threadpool for parsing if needed
            def parse_json_safely(text):
                # Try to extract JSON array
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return None

            llm_questions = await run_in_threadpool(parse_json_safely, response_text)
            if llm_questions is None:
                # Try parsing as JSON object with questions key
                try:
                    parsed = json.loads(response_text)
                    if isinstance(parsed, dict) and "questions" in parsed:
                        llm_questions = parsed["questions"]
                    elif isinstance(parsed, list):
                        llm_questions = parsed
                    else:
                        raise ValueError("Unexpected response format")
                except:
                    logger.error(f"Failed to parse LLM response: {response_text}")
                    return QuestionGeneratorService._generate_mock_skill_based_questions(num_questions, skills, role_name)
            
            # Format questions to match question bank format
            formatted_questions = []
            logger.debug(f"Successfully parsed {len(llm_questions)} questions from LLM response")
            for i, q in enumerate(llm_questions[:num_questions], 1):
                # Map difficulty
                difficulty = q.get('difficulty', 'medium').lower()
                if difficulty not in ['easy', 'medium', 'hard']:
                    difficulty = 'medium'
                
                # Map category
                category_str = q.get('category', 'PYTHON').upper()
                try:
                    category = CategoryEnum[category_str]
                except KeyError:
                    category = CategoryEnum.PYTHON
                
                # Randomly assign answer mode
                answer_mode_random = random.choice(["AUDIO", "TEXT"])
                if category in [CategoryEnum.SQL, CategoryEnum.DATA_STRUCTURES]:
                    answer_mode = "CODE"
                else:
                    answer_mode = answer_mode_random
                
                # Time limits based on difficulty
                time_limits = {
                    'easy': 120,   # 2 minutes
                    'medium': 240, # 4 minutes
                    'hard': 360    # 6 minutes
                }
                time_limit_sec = time_limits.get(difficulty, 240)
                
                formatted_questions.append({
                    "question_id": str(uuid.uuid4()),  # Generate new UUID for LLM questions
                    "question_type": "static",
                    "order": i,
                    "prompt": q.get('question', ''),
                    "difficulty": difficulty,
                    "time_limit_sec": time_limit_sec,
                    "answer_mode": answer_mode.lower(),
                    "evaluation_mode": "text" if answer_mode == "TEXT" else ("code" if answer_mode == "CODE" else "audio"),
                    "source": "llm_generated",
                    "category": category.value,
                    "focus": q.get('focus', '')
                })
            
            logger.debug(f"[QuestionGenerator] Successfully generated {len(formatted_questions)} questions with LLM")
            logger.debug(f"Successfully generated {len(formatted_questions)} questions with LLM")
            
            return formatted_questions
            
        except Exception as e:
            logger.error(f"Error generating questions with LLM: {e}", exc_info=True)
            logger.error(f"ERROR generating with LLM: {e}")
            # Fallback to mock questions
            return QuestionGeneratorService._generate_mock_skill_based_questions(num_questions, skills, role_name)
    
    @staticmethod
    def _generate_mock_skill_based_questions(
        num_questions: int,
        skills: List[str],
        role_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate mock questions based on skills when LLM is not available."""
        import random
        import uuid
        
        skills_text = ", ".join(skills[:5]) if skills else "technical skills"
        
        mock_questions = [
            {
                "question_id": str(uuid.uuid4()),
                "question_type": "static",
                "order": i + 1,
                "prompt": f"Explain your experience with {skills_text}. What are the key concepts you've worked with?",
                "difficulty": "medium" if i < 2 else "hard",
                "time_limit_sec": 240 if i < 2 else 360,
                "answer_mode": random.choice(["audio", "text"]),
                "evaluation_mode": "text",
                "source": "mock_fallback",
                "category": "PYTHON",
                "focus": f"Tests knowledge of {skills_text}"
            }
            for i in range(num_questions)
        ]
        
        logger.warning(f"[QuestionGenerator] Using mock questions as fallback")
        logger.warning(f"[QuestionGenerator] WARNING: Using mock questions (LLM not available)")
        
        return mock_questions
    
    @staticmethod
    async def generate_live_conversational_question(
        resume_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        previous_questions: List[Dict[str, Any]],
        previous_answers: List[Dict[str, Any]],
        asked_question_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Generate a single conversational question LIVE during interview based on:
        - Previous questions asked
        - Previous answers given by candidate
        - Resume and JD data
        - Already asked question IDs to prevent duplicates
        
        Returns a single question dict.
        """
        import random
        import uuid
        import asyncio
        from fastapi.concurrency import run_in_threadpool
        
        logger.debug(f"💬 Generating LIVE conversational question...")
        logger.debug(f"   Previous questions: {len(previous_questions)}")
        logger.debug(f"   Previous answers: {len(previous_answers)}")
        logger.debug(f"   Already asked IDs: {len(asked_question_ids)}")
        
        # Build context from previous Q&A
        conversation_context = ""
        if previous_questions and previous_answers:
            conversation_context = "\n\nPREVIOUS CONVERSATION:\n"
            for i, (q, a) in enumerate(zip(previous_questions[-3:], previous_answers[-3:]), 1):  # Last 3 Q&A pairs
                q_text = q.get('prompt', q.get('question_text', 'N/A'))
                a_text = a.get('answer_text', a.get('answer', 'N/A'))[:500]  # Limit answer length
                conversation_context += f"Q{i}: {q_text}\nA{i}: {a_text}\n\n"
        
        # Get resume context - FOCUS ON PROJECTS
        resume_skills = resume_data.get('skills', [])
        projects = resume_data.get('projects', [])
        if not isinstance(projects, list):
            projects = []
        experience = resume_data.get('experience', [])
        
        # Build detailed project context (latest 2-3 projects only)
        project_context = ""
        selected_project_names: List[str] = []
        selected_projects: List[Dict[str, Any]] = []
        if projects:
            from datetime import datetime as _dt

            def _project_sort_key(p: Dict[str, Any]):
                if not isinstance(p, dict):
                    return _dt.min
                # Prefer explicit recency fields when available
                for k in ("end_date", "to", "completed_at", "updated_at", "year", "date"):
                    v = p.get(k)
                    if not v:
                        continue
                    s = str(v).strip()
                    # Handle current/ongoing projects as most recent
                    if s.lower() in ("present", "current", "ongoing", "now"):
                        return _dt.max
                    # Try common date formats first
                    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%m/%Y", "%Y"):
                        try:
                            return _dt.strptime(s, fmt)
                        except Exception:
                            pass
                # fallback: keep source order if no date exists
                return _dt.min

            # If dates are available, sort by recency; else rely on source ordering and take first 3
            dated_projects = [p for p in projects if isinstance(p, dict) and any(p.get(k) for k in ("end_date", "to", "completed_at", "updated_at", "year", "date"))]
            if dated_projects:
                projects_for_context = sorted(projects, key=_project_sort_key, reverse=True)[:3]
            else:
                projects_for_context = projects[:3]
            selected_projects = [p for p in projects_for_context if isinstance(p, dict)]

            project_context = "\n\nCANDIDATE PROJECTS (Focus on these for questions):\n"
            for i, project in enumerate(projects_for_context, 1):
                if isinstance(project, dict):
                    project_name = project.get('name', f'Project {i}')
                    selected_project_names.append(str(project_name).strip())
                    project_desc = project.get('description', '')
                    project_techs = project.get('technologies', [])
                    project_context += f"Project {i}: {project_name}\n"
                    project_context += f"  Description: {project_desc[:200]}\n"
                    if project_techs:
                        project_context += f"  Technologies: {', '.join(project_techs[:10])}\n"
                    project_context += "\n"

        # Per-project conversational flow:
        # 1) Ask project overview first
        # 2) Follow up using candidate's overview answer + resume/JD context
        if selected_project_names:
            prev_conv_prompts = [
                str(q.get("prompt", q.get("question_text", ""))).lower()
                for q in previous_questions
                if str(q.get("question_type", "")).lower() == "conversational"
            ]

            def _project_is_already_opened(project_name: str) -> bool:
                p = project_name.lower()
                return any(p in pq for pq in prev_conv_prompts)

            # Find first project that has not yet been opened in conversational round.
            unopened_project_name = None
            for pn in selected_project_names:
                if pn and not _project_is_already_opened(pn):
                    unopened_project_name = pn
                    break

            if unopened_project_name:
                overview_q = (
                    f"In your project '{unopened_project_name}', can you give a brief overview covering "
                    "the project goal, your role, and the key outcome?"
                )
                return {
                    "question_id": str(uuid.uuid4()),
                    "question_type": "conversational",
                    "order": len(previous_questions) + 1,
                    "prompt": overview_q,
                    "difficulty": "medium",
                    "time_limit_sec": 240,
                    "answer_mode": "audio",
                    "evaluation_mode": "contextual",
                    "source": "project_overview_seed",
                    "focus": "project overview and ownership",
                    "reasoning": "Start each project with an overview before deep follow-ups."
                }
        
        resume_context = f"Skills: {', '.join(resume_skills[:10])}\n"
        if projects:
            resume_context += f"Has {len(projects)} projects listed\n"
        
        # Get JD context
        jd_skills = jd_data.get('required_skills', []) or jd_data.get('technologies', [])
        jd_context = f"Job requires: {', '.join(jd_skills[:10])}\n"
        
        # Use Azure OpenAI to generate next question
        try:
            if azure_openai_service.async_client or azure_openai_service.client:
                system_prompt = """You are an expert interviewer conducting a live, resume-driven conversation.
Generate ONE conversational question grounded in the candidate's PROJECTS and prior answers.

Question objectives:
1) Explore the end-to-end FLOW of a project (context → goals → constraints → approach → stakeholders → risks → outcomes).
2) Dive into decision rationale, trade-offs, execution timeline, ownership, and impact.
3) Consider role transitions and cross-functional collaboration where applicable.
4) Keep it open-ended and natural, no coding tasks.
5) STRICTLY AVOID repetition: do not ask anything that is semantically similar to questions already asked (see AVOID_DUPLICATES).
6) Ask ONLY ONE question at a time. Do not combine multiple sub-questions in one prompt.
7) Keep each question focused to at most 3 concepts/aspects.
8) Prefer ONLY the latest 2-3 projects from the provided list; do not focus on old projects unless no recent projects are available.
9) The question MUST explicitly mention the project name it refers to (exact project name from context).

Return ONLY a valid JSON object:
{
  "question": "conversational question text (no numbering)",
  "difficulty": "medium" or "hard",
  "focus": "capability being tested (e.g., project flow, decision-making, stakeholder management)",
  "reasoning": "why this is relevant based on resume projects and the conversation so far"
}"""

                # Build duplication guard list
                avoid_list = ""
                if previous_questions:
                    avoid_list = "\\n".join([f"- {q.get('prompt', q.get('question_text',''))}" for q in previous_questions if (q.get('prompt') or q.get('question_text'))])

                # Choose project for follow-up: prefer latest project already opened in conversation.
                active_project_name = selected_project_names[0] if selected_project_names else ""
                for pn in reversed(selected_project_names):
                    if pn and any(pn.lower() in pq for pq in prev_conv_prompts):
                        active_project_name = pn
                        break

                # Latest answer context for better follow-up quality
                latest_answer_text = ""
                if previous_answers:
                    latest_answer = previous_answers[-1]
                    latest_answer_text = str(latest_answer.get("answer_text", latest_answer.get("answer", "")))[:900]

                user_prompt = f"""Generate the next conversational interview question.

CANDIDATE BACKGROUND:
{resume_context}
{project_context}

JOB REQUIREMENTS:
{jd_context}

{conversation_context}

INSTRUCTIONS:
1. PRIORITY: Focus on candidate PROJECTS and their end-to-end FLOW (goals, constraints, decisions, trade-offs, stakeholders, timelines, risks, metrics).
2. Prefer deeper follow-ups exploring decisions and impact rather than surface-level technology lists.
3. Difficulty should be medium or hard.
4. Keep it conversational and open-ended.
5. Make it relevant to the job requirements.
6. ABSOLUTE: Do NOT repeat or closely paraphrase any question below. If similar, choose a distinct angle.
7. Ask exactly ONE question sentence ending with a single question mark.
8. Limit scope to max 3 concepts in that question.
9. Ask from the most recent 2-3 projects shown in CANDIDATE PROJECTS.
10. Explicitly include the project name in the question text.

AVOID_DUPLICATES:
{avoid_list or "- (none)"} 

ACTIVE_PROJECT_FOR_THIS_TURN:
{active_project_name}

LATEST_CANDIDATE_OVERVIEW_OR_ANSWER_CONTEXT:
{latest_answer_text or "No prior answer context available."}

FLOW RULE (MANDATORY):
- For each project, first ask overview once.
- After overview is answered, ask follow-up questions for that SAME project using candidate's previous answer.
- Do not jump to another project in follow-up unless current project has been sufficiently explored.

Return ONLY the JSON object."""

                start_time = datetime.now()
                content = await asyncio.wait_for(
                    azure_openai_service.chat_completion_json(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.8,
                        max_tokens=500,
                        response_format={"type": "json_object"}
                    ),
                    timeout=60
                )
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"✅ Live conversational question generated in {duration:.2f}s")
                
                import json
                llm_response = await run_in_threadpool(json.loads, content)
                
                # Format the question
                question_text = llm_response.get('question', 'Tell me more about your experience.')
                # Safety guard: if model returns multiple questions, keep only the first one.
                if isinstance(question_text, str):
                    q_marks = question_text.count("?")
                    if q_marks > 1:
                        first_q = question_text.split("?")[0].strip()
                        question_text = f"{first_q}?"
                    # Remove accidental line-break bullets that imply multiple asks.
                    question_text = " ".join(question_text.splitlines()).strip()
                    # Ensure the question explicitly references a project name when available.
                    if selected_project_names:
                        lower_q = question_text.lower()
                        if not any(name.lower() in lower_q for name in selected_project_names if name):
                            project_name = selected_project_names[0]
                            question_text = f"In your project '{project_name}', {question_text[0].lower() + question_text[1:]}" if len(question_text) > 1 else f"In your project '{project_name}', can you explain your approach?"
                difficulty = llm_response.get('difficulty', 'medium').lower()
                if difficulty not in ['easy', 'medium', 'hard']:
                    difficulty = 'medium'
                
                # Time limits based on difficulty
                time_limits = {'easy': 120, 'medium': 240, 'hard': 360}
                time_limit_sec = time_limits.get(difficulty, 240)
                
                # Randomly assign answer mode
                answer_mode = random.choice(['audio', 'text']).lower()
                
                question = {
                    "question_id": str(uuid.uuid4()),
                    "question_type": "conversational",
                    "order": len(previous_questions) + 1,
                    "prompt": question_text,
                    "difficulty": difficulty,
                    "time_limit_sec": time_limit_sec,
                    "answer_mode": answer_mode,
                    "evaluation_mode": "contextual",
                    "source": "llm_live_generated",
                    "focus": llm_response.get('focus', 'Technical depth'),
                    "reasoning": llm_response.get('reasoning', '')
                }
                
                logger.debug(f"   ✅ Generated live question: {question_text[:80]}...")
                return question
                
        except Exception as e:
            logger.error(f"Error generating live conversational question: {e}", exc_info=True)
            logger.debug(f"   ❌ LLM generation failed: {e}")
            logger.debug(f"   Using fallback question...")
        
        # Fallback: Generate a generic follow-up question
        fallback_prompts = [
            "Can you elaborate on the technical challenges you faced in that project?",
            "What would you do differently if you had to approach that problem again?",
            "How did you ensure the quality and reliability of your solution?",
            "What technologies or tools did you consider but didn't use, and why?",
            "How would you scale this solution for a larger user base?",
        ]
        
        # Pick a prompt that hasn't been used
        used_prompts = [q.get('prompt', '') for q in previous_questions]
        available_prompts = [p for p in fallback_prompts if p not in used_prompts]
        prompt = available_prompts[0] if available_prompts else fallback_prompts[0]
        
        return {
            "question_id": str(uuid.uuid4()),
            "question_type": "conversational",
            "order": len(previous_questions) + 1,
            "prompt": prompt,
            "difficulty": "medium",
            "time_limit_sec": 240,
            "answer_mode": random.choice(['audio', 'text']).lower(),
            "evaluation_mode": "contextual",
            "source": "fallback_live"
        }
    
    @staticmethod
    async def _generate_conversational_with_drilldown(
        resume_data: Dict[str, Any],
        jd_data: Dict[str, Any],
        total_questions: int = 10
    ) -> List[Dict[str, Any]]:
        """DEPRECATED: Conversational questions are now generated live during interview."""
        # This method is kept for backward compatibility but should not be used
        logger.warning("_generate_conversational_with_drilldown is deprecated - use generate_live_conversational_question instead")
        return []
    
    @staticmethod
    def _parse_resume(resume_id: Optional[str]) -> Dict[str, Any]:
        """Parse resume file if available."""
        if not resume_id:
            return {
                'text': '',
                'projects': [],
                'skills': [],
                'experience': {},
                'education': {}
            }
        
        try:
            # Try to find resume file
            resume_path = os.path.join(QuestionGeneratorService.RESUME_UPLOAD_DIR, f"{resume_id}.pdf")
            
            if os.path.exists(resume_path):
                return resume_jd_parser.parse_resume_pdf(resume_path)
            else:
                logger.warning(f"Resume file not found: {resume_path}")
                return {
                    'text': '',
                    'projects': [],
                    'skills': [],
                    'experience': {},
                    'education': {}
                }
        except Exception as e:
            logger.error(f"Error parsing resume: {e}")
            return {
                'text': '',
                'projects': [],
                'skills': [],
                'experience': {},
                'education': {}
            }
    
    @staticmethod
    async def _generate_fallback_questions(
        session: AsyncSession,
        template_id: str,
        candidate_id: str,
        resume_id: Optional[str]
    ) -> dict:
        """Generate fallback mock questions if generation fails. ALWAYS returns at least 5 questions."""
        logger.warning("Using fallback mock questions - primary generation failed")
        logger.warning("Using FALLBACK mock questions - this means primary question generation failed")
        
        return {
            "template_id": template_id,
            "generated_from": {
                "resume_id": resume_id or candidate_id,
                "jd_id": "fallback",
            },
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generation_method": "fallback_mock",
            "technical_section": {
                "questions": [
                    {
                        "question_id": "conv_q_001",
                        "question_type": "technical",
                        "order": 1,
                        "prompt": "Tell me about a challenging project you worked on. What technologies did you use?",
                        "text": "Tell me about a challenging project you worked on. What technologies did you use?",
                        "difficulty": "medium",
                        "category": "GENERAL",
                        "time_limit_sec": 300
                    },
                    {
                        "question_id": "conv_q_002",
                        "question_type": "technical",
                        "order": 2,
                        "prompt": "Walk me through your approach to solving a complex technical problem.",
                        "text": "Walk me through your approach to solving a complex technical problem.",
                        "difficulty": "medium",
                        "category": "GENERAL",
                        "time_limit_sec": 300
                    }
                ]
            },
            "coding_section": {"problems": []},
            "conversational_section": {"rounds": 2}
        }

    @staticmethod
    async def _regenerate_single_question_with_llm(
        existing_question: Dict[str, Any],
        all_questions: List[Dict[str, Any]],
        comment: Optional[str],
        skills: List[str],
        role_name: Optional[str] = None,
        resume_data: Optional[Dict[str, Any]] = None,
        jd_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Regenerate a single technical question using LLM.
        Passes all current questions to prevent duplicates.
        """
        try:
            import json
            import re
            import uuid
            
            logger.info(f"[QuestionGenerator] Regenerating single question with comment: {comment}")
            
            if not azure_openai_service.async_client and not azure_openai_service.client:
                # Fallback to a mock question if no LLM
                return {
                    **existing_question,
                    "prompt": f"NEW: {existing_question.get('prompt')} (Regenerated due to: {comment})",
                    "question_id": str(uuid.uuid4())
                }

            # Build context
            current_questions_text = "\n".join([f"- {q.get('prompt')}" for q in all_questions])
            
            system_prompt = """You are an expert technical interviewer. Your task is to REGENERATE a single technical interview question.
You MUST ensure the new question is DIFFERENT from the ones already in the interview to avoid redundancy.
Return ONLY a valid JSON object with this exact structure:
{
    "question": "Question text here",
    "difficulty": "easy" or "medium" or "hard",
    "category": "PYTHON" or "SQL" or "MACHINE_LEARNING" or "DATA_STRUCTURES" or "SYSTEM_DESIGN" or "STATISTICS",
    "focus": "Brief description of what this question tests"
}"""

            user_prompt = f"""Regenerate this specific interview question:
"{existing_question.get('prompt')}"

USER'S INSTRUCTION/COMMENT FOR REGENERATION:
"{comment or 'Make it more specific and technically challenging'}"

CURRENT QUESTIONS IN THE INTERVIEW (AVOID DUPLICATING THESE):
{current_questions_text}

TARGET SKILLS:
{', '.join(skills[:20])}

ROLE: {role_name or 'Technical Candidate'}

Return ONLY the JSON object."""

            start_time = datetime.now()
            response = await asyncio.wait_for(
                azure_openai_service.async_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                ),
                timeout=60
            )
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Question regenerated in {duration:.2f}s")
            
            content = response.choices[0].message.content
            llm_q = await run_in_threadpool(json.loads, content)
            
            # Map values back to our schema
            difficulty = llm_q.get('difficulty', existing_question.get('difficulty', 'medium')).lower()
            category_str = llm_q.get('category', existing_question.get('category', 'PYTHON')).upper()
            
            try:
                category = CategoryEnum[category_str]
            except KeyError:
                category = CategoryEnum.PYTHON
                
            time_limits = {'easy': 120, 'medium': 240, 'hard': 360}
            
            return {
                "question_id": str(uuid.uuid4()),
                "question_type": "static",
                "order": existing_question.get("order", 1),
                "prompt": llm_q.get("question", ""),
                "difficulty": difficulty,
                "time_limit_sec": time_limits.get(difficulty, 240),
                "answer_mode": existing_question.get("answer_mode", "text"),
                "evaluation_mode": existing_question.get("evaluation_mode", "text"),
                "source": "llm_regenerated",
                "category": category.value,
                "focus": llm_q.get("focus", "")
            }
            
        except Exception as e:
            logger.error(f"Error regenerating single question with LLM: {e}")
            return {
                **existing_question,
                "prompt": f"FALLBACK: {existing_question.get('prompt')} (Regeneration failed)",
                "source": "regeneration_failed"
            }

    @staticmethod
    async def _generate_analytical_questions_with_llm(
        num_questions: int,
        role_name: Optional[str] = None,
        resume_data: Optional[Dict[str, Any]] = None,
        jd_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate non-technical analytical questions (puzzles, guesstimates, business reasoning)
        for roles like manager/business analyst.
        """
        try:
            import uuid
            import asyncio
            import json
            from fastapi.concurrency import run_in_threadpool

            if not azure_openai_service.async_client and not azure_openai_service.client:
                return QuestionGeneratorService._generate_mock_analytical_questions(num_questions, role_name)

            role_text = role_name or "Business Analyst / Manager"
            jd_focus = ""
            if jd_data and isinstance(jd_data, dict):
                reqs = jd_data.get("requirements", []) or []
                jd_focus = "\n".join(reqs[:5]) if isinstance(reqs, list) else ""

            system_prompt = """You are an expert interviewer for NON-TECHNICAL problem-solving roles.
Generate analytical interview questions ONLY (no coding, no technical implementation details).

Question styles should include:
- Business case scenarios
- Guesstimates / estimation questions
- Logic puzzles and structured reasoning
- Prioritization / decision-making scenarios
- Process improvement and trade-off analysis

Strict rules:
- DO NOT ask programming, system design, architecture, or tool/framework questions.
- Focus on thinking process, assumptions, structure, and communication.
- Return ONLY a valid JSON array.

JSON format:
[
  {
    "question": "Question text",
    "difficulty": "medium" or "hard",
    "category": "ANALYTICAL",
    "focus": "what capability this tests"
  }
]"""

            user_prompt = f"""Generate {num_questions} non-technical analytical interview questions for role: {role_text}.

Context (optional):
{jd_focus if jd_focus else "General business / operations context"}

Requirements:
1. Include a mix of puzzle, guesstimate, and business case reasoning.
2. Questions must assess structured thinking and problem-solving.
3. Return exactly {num_questions} questions.
4. Return JSON array only."""

            response_text = await asyncio.wait_for(
                azure_openai_service.chat_completion_json(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=1800,
                ),
                timeout=60,
            )

            def _parse(text: str):
                import re
                m = re.search(r'\[.*\]', text, re.DOTALL)
                if m:
                    return json.loads(m.group())
                parsed = json.loads(text)
                if isinstance(parsed, dict) and "questions" in parsed:
                    return parsed["questions"]
                return parsed if isinstance(parsed, list) else []

            llm_questions = await run_in_threadpool(_parse, response_text)
            if not llm_questions:
                return QuestionGeneratorService._generate_mock_analytical_questions(num_questions, role_name)

            time_limits = {"easy": 180, "medium": 300, "hard": 420}
            formatted = []
            for i, q in enumerate(llm_questions[:num_questions], 1):
                difficulty = str(q.get("difficulty", "medium")).lower()
                if difficulty not in ("easy", "medium", "hard"):
                    difficulty = "medium"
                formatted.append({
                    "question_id": str(uuid.uuid4()),
                    "question_type": "static",
                    "order": i,
                    "prompt": q.get("question", ""),
                    "difficulty": difficulty,
                    "time_limit_sec": time_limits.get(difficulty, 300),
                    "answer_mode": "text",
                    "evaluation_mode": "text",
                    "source": "llm_generated",
                    "category": "ANALYTICAL",
                    "focus": q.get("focus", "structured problem solving"),
                })
            return formatted
        except Exception as e:
            logger.error(f"Error generating analytical questions with LLM: {e}", exc_info=True)
            return QuestionGeneratorService._generate_mock_analytical_questions(num_questions, role_name)

    @staticmethod
    def _generate_mock_analytical_questions(
        num_questions: int,
        role_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        import uuid
        bank = [
            ("Estimate the number of daily rides in your city. Explain assumptions and approach.", "guesstimate"),
            ("A team misses deadlines repeatedly. How would you diagnose root causes and fix the process?", "process improvement"),
            ("You have 20% budget cut across 5 initiatives. How would you prioritize what to keep?", "prioritization"),
            ("A new store has low conversion despite good footfall. How would you investigate?", "business case"),
            ("How would you estimate market size for a new subscription service in your region?", "market sizing"),
        ]
        out = []
        for i in range(max(1, num_questions)):
            q, focus = bank[i % len(bank)]
            out.append({
                "question_id": str(uuid.uuid4()),
                "question_type": "static",
                "order": i + 1,
                "prompt": q,
                "difficulty": "medium" if i < 2 else "hard",
                "time_limit_sec": 300 if i < 2 else 420,
                "answer_mode": "audio",
                "evaluation_mode": "audio",
                "source": "mock_analytical_fallback",
                "category": "ANALYTICAL",
                "focus": focus,
            })
        return out

    @staticmethod
    async def _regenerate_analytical_question_with_llm(
        existing_question: Dict[str, Any],
        all_questions: List[Dict[str, Any]],
        comment: Optional[str],
        role_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            import uuid
            import json
            import asyncio
            from fastapi.concurrency import run_in_threadpool

            if not azure_openai_service.async_client and not azure_openai_service.client:
                return {
                    **existing_question,
                    "question_id": str(uuid.uuid4()),
                    "prompt": f"{existing_question.get('prompt', '')} (refined)",
                    "category": "ANALYTICAL",
                    "source": "mock_analytical_regen",
                }

            current_questions_text = "\n".join([f"- {q.get('prompt')}" for q in all_questions])
            system_prompt = """You regenerate ONE non-technical analytical interview question.
Must be different from existing questions.
No coding/tech stack/system design questions.
Return JSON object:
{"question":"...", "difficulty":"medium|hard", "category":"ANALYTICAL", "focus":"..."}"""
            user_prompt = f"""Regenerate this analytical question:
{existing_question.get('prompt')}

Comment: {comment or "Make it sharper and more realistic for business roles"}
Role: {role_name or "Business Analyst / Manager"}
Existing questions (avoid overlap):
{current_questions_text}
Return JSON only."""

            content = await asyncio.wait_for(
                azure_openai_service.chat_completion_json(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=800,
                    response_format={"type": "json_object"},
                ),
                timeout=60,
            )
            llm_q = await run_in_threadpool(json.loads, content)
            diff = str(llm_q.get("difficulty", existing_question.get("difficulty", "medium"))).lower()
            if diff not in ("easy", "medium", "hard"):
                diff = "medium"
            return {
                "question_id": str(uuid.uuid4()),
                "question_type": "static",
                "order": existing_question.get("order", 1),
                "prompt": llm_q.get("question", ""),
                "difficulty": diff,
                "time_limit_sec": 300 if diff == "medium" else 420,
                "answer_mode": "audio",
                "evaluation_mode": "audio",
                "source": "llm_analytical_regenerated",
                "category": "ANALYTICAL",
                "focus": llm_q.get("focus", "analytical reasoning"),
            }
        except Exception as e:
            logger.error(f"Error regenerating analytical question: {e}")
            return {
                **existing_question,
                "source": "analytical_regeneration_failed"
            }

    @staticmethod
    async def _get_single_replacement_question_from_bank(
        session: AsyncSession,
        exclude_ids: List[str],
        skills: List[str],
        difficulty: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single unique replacement question from the bank."""
        try:
            import random
            from sqlalchemy import or_
            import uuid as uuid_module
            
            # Use the same logic as _get_questions_from_bank but exclude existing IDs
            # and limit to 1
            stmt = select(Question).where(
                Question.is_active == True,
                Question.id.notin_([uuid_module.UUID(i) for i in exclude_ids if i and len(i) == 36])
            )
            
            # Try to match difficulty if possible
            # ... (omitting full skill mapping logic for brevity, reusing it if possible) ...
            # Actually, let's keep it simple for now or refactor _get_questions_from_bank to be more reusable.
            # For a single replacement, we can just call _get_questions_from_bank with num=1 and filter later,
            # but that's inefficient.
            
            # Let's reuse some of the filter logic
            result = await session.execute(stmt.limit(20)) # Get a small pool
            available = result.scalars().all()
            
            if not available:
                return None
                
            q = random.choice(available)
            
            # Format
            difficulty_val = q.difficulty.value.lower() if hasattr(q.difficulty, 'value') else "medium"
            time_limits = {'easy': 120, 'medium': 240, 'hard': 360}
            
            import random as rnd
            category_val = q.category.value if hasattr(q.category, 'value') else "PYTHON"
            if category_val in ["SQL", "DATA_STRUCTURES"]:
                answer_mode = "code"
            else:
                answer_mode = rnd.choice(["audio", "text"])

            return {
                "question_id": str(q.id),
                "question_type": "static",
                "order": 1, # Will be overridden by caller
                "prompt": q.text,
                "difficulty": difficulty_val,
                "time_limit_sec": time_limits.get(difficulty_val, 240),
                "answer_mode": answer_mode,
                "evaluation_mode": "text" if answer_mode == "text" else ("code" if answer_mode == "code" else "audio"),
                "source": "question_bank",
                "category": category_val
            }
        except Exception as e:
            logger.error(f"Error getting single replacement question from bank: {e}")
            return None

    @staticmethod
    async def _get_single_replacement_coding_problem_from_bank(
        session: AsyncSession,
        exclude_ids: List[str],
        difficulties: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single unique replacement coding problem from the bank."""
        try:
            import random
            import uuid as uuid_module
            
            valid_diffs = [d.upper() for d in difficulties if isinstance(d, str)]
            
            stmt = select(CodingProblem).where(
                CodingProblem.id.notin_([uuid_module.UUID(i) for i in exclude_ids if i and len(i) == 36])
            )
            
            if valid_diffs:
                stmt = stmt.where(func.upper(CodingProblem.difficulty).in_(valid_diffs))
            
            result = await session.execute(stmt.limit(10))
            available = result.scalars().all()
            
            if not available:
                return None
                
            p = random.choice(available)
            
            return {
                "problem_id": str(p.id),
                "title": p.title,
                "difficulty": p.difficulty,
                "description": p.description,
                "starter_code": p.starter_code
            }
        except Exception as e:
            logger.error(f"Error getting single replacement coding problem from bank: {e}")
            return None


question_generator_service = QuestionGeneratorService()
