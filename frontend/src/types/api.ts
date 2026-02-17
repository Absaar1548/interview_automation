export type InterviewState =
    | "CREATED"
    | "RESUME_PARSED"
    | "READY"
    | "IN_PROGRESS"
    | "QUESTION_ASKED"
    | "ANSWER_SUBMITTED"
    | "EVALUATING"
    | "COMPLETED"
    | "TERMINATED";

export type QuestionCategory = "CONVERSATIONAL" | "STATIC" | "CODING";

export type AnswerMode = "AUDIO" | "CODE";

export type Difficulty = "EASY" | "MEDIUM" | "HARD";

export type Recommendation = "PROCEED" | "REJECT" | "REVIEW";

export type FraudRisk = "LOW" | "MEDIUM" | "HIGH";

export type EventType = "TAB_SWITCH" | "MULTI_FACE" | "VOICE_MISMATCH";

export type ProctoringAction = "FLAG" | "TERMINATE" | "IGNORE";

export interface QuestionResponse {
    question_id: string;
    category: QuestionCategory;
    answer_mode: AnswerMode;
    difficulty: Difficulty;
    prompt: string;
    time_limit_sec: number;
}

export interface EvaluationSubmitRequest {
    question_id: string;
    answer_type: AnswerMode;
    answer_payload: string;
}

export interface EvaluationSubmitResponse {
    state: InterviewState;
}

export interface SummaryResponse {
    final_score: number;
    recommendation: Recommendation;
    fraud_risk: FraudRisk;
    strengths: string[];
    gaps: string[];
    notes: string;
}

export interface ProctoringEventRequest {
    event_type: EventType;
    confidence: number;
}

export interface ProctoringEventResponse {
    action: ProctoringAction;
}

export interface CodeTemplateResponse {
    language: string;
    starter_code: string;
}

export interface ConversationPromptResponse {
    prompt: string;
    followup_allowed: boolean;
}

export interface ApiError {
    error_code: string;
    message: string;
    current_state?: InterviewState | null;
}

export interface AuthRequest {
    username: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    username: string;
    role: string;
}

export interface RegisterResponse {
    username: string;
    message: string;
}
