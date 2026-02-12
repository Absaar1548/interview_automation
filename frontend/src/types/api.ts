// TypeScript types mirroring backend contract from mock_backend_spec.md

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

export interface QuestionResponse {
    question_id: string;
    category: "CONVERSATIONAL" | "STATIC" | "CODING";
    answer_mode: "AUDIO" | "CODE";
    difficulty: "EASY" | "MEDIUM" | "HARD";
    prompt: string;
    time_limit_sec: number;
}

export interface EvaluationSubmitRequest {
    question_id: string;
    answer_type: "AUDIO" | "CODE";
    answer_payload: string;
}

export interface EvaluationSubmitResponse {
    state: InterviewState;
}

export interface SummaryResponse {
    final_score: number;
    recommendation: "PROCEED" | "REJECT" | "HOLD";
    fraud_risk: "LOW" | "MEDIUM" | "HIGH";
    strengths: string[];
    gaps: string[];
    notes: string;
}

export interface ProctoringEventRequest {
    event_type: "MULTI_FACE" | "VOICE_MISMATCH" | "TAB_SWITCH";
    confidence: number;
}

export interface ProctoringEventResponse {
    action: "FLAG" | "TERMINATE" | "IGNORE";
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
    current_state?: InterviewState;
}
