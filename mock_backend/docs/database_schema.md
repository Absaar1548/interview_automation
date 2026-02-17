# Database Schema Documentation

## Collections Overview

This document describes the MongoDB collections used in the AI Interview Automation system.

---

## 1. users

Stores user information for both admins and candidates.

```json
{
  "_id": ObjectId,
  "username": "absaar",
  "email": "absaar@example.com",
  "hashed_password": "bcrypt_hash",
  "role": "admin" | "candidate",
  "is_active": true,
  "profile": {
    // For candidates:
    "first_name": "Absaar",
    "last_name": "Ali",
    "phone": "+91xxxxxx",
    "resume_id": ObjectId,  // references resumes._id
    "experience_years": 3,
    "skills": ["Python", "ML", "NLP"]
    
    // For admins:
    "first_name": "HR",
    "last_name": "Manager",
    "department": "Data Science Hiring",
    "designation": "Lead Recruiter"
  },
  "created_at": datetime,
  "updated_at": datetime,
  "last_login": datetime
}
```

**Indexes:**
- `username` (unique)
- `email` (unique)
- `role`

---

## 2. resumes

Stores candidate resume information and parsed data.

```json
{
  "_id": ObjectId,
  "candidate_id": ObjectId,  // references users._id
  "file_url": "s3_url_or_local_path",
  "parsed_text": "...",
  "parsed_structured": {
    "education": [],
    "experience": [],
    "skills": []
  },
  "uploaded_at": datetime
}
```

**Indexes:**
- `candidate_id`

---

## 3. questions

Question bank for interviews.

```json
{
  "_id": ObjectId,
  "title": "Explain overfitting",
  "description": "Detailed question text",
  "difficulty": "easy" | "medium" | "hard",
  "category": "machine_learning",
  "tags": ["ML", "theory"],
  "expected_answer_keywords": ["bias", "variance"],
  "created_by": ObjectId,  // references users._id (admin)
  "is_active": true,
  "created_at": datetime
}
```

**Indexes:**
- `category`
- `difficulty`
- `is_active`
- `tags`

---

## 4. interview_templates

Predefined interview templates with question sets.

```json
{
  "_id": ObjectId,
  "name": "ML Fresher Round 1",
  "description": "Basic ML screening",
  "created_by": ObjectId,  // references users._id (admin)
  "questions": [
    {
      "question_id": ObjectId,  // references questions._id
      "order": 1,
      "time_limit_sec": 120
    }
  ],
  "total_duration_sec": 1800,
  "is_active": true,
  "created_at": datetime
}
```

**Indexes:**
- `is_active`
- `created_by`

---

## 5. interviews

Interview instances assigned to candidates.

```json
{
  "_id": ObjectId,
  "candidate_id": ObjectId,  // references users._id
  "template_id": ObjectId,  // references interview_templates._id
  "assigned_by": ObjectId,  // references users._id (admin)
  "status": "scheduled" | "in_progress" | "completed" | "cancelled",
  "scheduled_at": datetime,
  "started_at": datetime,
  "completed_at": datetime,
  "overall_score": null,
  "feedback": null,
  "created_at": datetime
}
```

**Indexes:**
- `candidate_id`
- `status`
- `scheduled_at`

---

## 6. interview_sessions

Active session tracking for proctoring and monitoring.

```json
{
  "_id": ObjectId,
  "interview_id": ObjectId,  // references interviews._id
  "candidate_id": ObjectId,  // references users._id
  "started_at": datetime,
  "ended_at": datetime,
  "termination_reason": "timeout" | "manual_exit" | "network_issue",
  "proctoring_flags": [],
  "browser_metadata": {},
  "ip_address": "",
  "status": "active" | "terminated" | "completed"
}
```

**Indexes:**
- `interview_id`
- `status`

---

## 7. responses

Candidate answers to interview questions.

```json
{
  "_id": ObjectId,
  "session_id": ObjectId,  // references interview_sessions._id
  "question_id": ObjectId,  // references questions._id
  "answer_text": "...",
  "video_url": "optional",
  "audio_url": "optional",
  "submitted_at": datetime,
  "ai_score": null,
  "ai_feedback": null,
  "manual_score": null,
  "final_score": null
}
```

**Indexes:**
- `session_id`
- `question_id`

---

## 8. ai_evaluations

AI model evaluation metadata and results.

```json
{
  "_id": ObjectId,
  "response_id": ObjectId,  // references responses._id
  "model_used": "gpt-4",
  "prompt_version": "v1.2",
  "raw_prompt": "...",
  "raw_response": "...",
  "confidence_score": 0.87,
  "evaluated_at": datetime
}
```

**Indexes:**
- `response_id`
- `model_used`

---

## Relationships

```
users (admin) ──┬─> questions (created_by)
                ├─> interview_templates (created_by)
                └─> interviews (assigned_by)

users (candidate) ──┬─> resumes (candidate_id)
                    ├─> interviews (candidate_id)
                    └─> interview_sessions (candidate_id)

questions ──> interview_templates.questions (question_id)

interview_templates ──> interviews (template_id)

interviews ──> interview_sessions (interview_id)

interview_sessions ──> responses (session_id)

questions ──> responses (question_id)

responses ──> ai_evaluations (response_id)
```
