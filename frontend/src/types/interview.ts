/**
 * Interview State Machine (Authoritative)
 * Derived from: docs/architecture/interview_state_machine.md
 */
export enum InterviewState {
    CREATED = 'CREATED',
    RESUME_PARSED = 'RESUME_PARSED',
    READY = 'READY',
    IN_PROGRESS = 'IN_PROGRESS',
    QUESTION_ASKED = 'QUESTION_ASKED',
    ANSWER_SUBMITTED = 'ANSWER_SUBMITTED',
    EVALUATING = 'EVALUATING',
    COMPLETED = 'COMPLETED',
    TERMINATED = 'TERMINATED',
}

/**
 * Question Categories
 * Derived from: docs/architecture/api_contracts.md
 */
export enum QuestionCategory {
    CONVERSATIONAL = 'CONVERSATIONAL',
    STATIC = 'STATIC',
    CODING = 'CODING',
}

/**
 * Answer Modes
 * Derived from: docs/architecture/api_contracts.md
 */
export enum AnswerMode {
    TEXT = 'TEXT',
    AUDIO = 'AUDIO',
    CODE = 'CODE',
}

/**
 * Question Difficulty
 * Derived from: docs/architecture/api_contracts.md
 */
export enum QuestionDifficulty {
    EASY = 'EASY',
    MEDIUM = 'MEDIUM',
    HARD = 'HARD',
}

/**
 * Interview Question Interface
 * Derived from: docs/architecture/api_contracts.md (Section 3.1)
 */
export interface InterviewQuestion {
    question_id: string; // uuid
    category: QuestionCategory;
    answer_mode: AnswerMode;
    difficulty: QuestionDifficulty;
    prompt: string;
    time_limit_sec: number;
}
