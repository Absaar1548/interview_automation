import type {
    InterviewState,
    QuestionResponse,
    EvaluationSubmitRequest,
    EvaluationSubmitResponse,
    SummaryResponse,
    ProctoringEventRequest,
    ProctoringEventResponse,
    CodeTemplateResponse,
    ConversationPromptResponse,
    ApiError,
} from "../types/api";

const BASE_PATH = "/api/v1";

async function request<T>(
    endpoint: string,
    options: {
        method: "GET" | "POST";
        interviewId?: string;
        body?: unknown;
    }
): Promise<T> {
    const headers: Record<string, string> = {};

    if (options.interviewId) {
        headers["X-Interview-Id"] = options.interviewId;
    }

    if (options.body) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(`${BASE_PATH}${endpoint}`, {
        method: options.method,
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined,
    });

    if (!response.ok) {
        try {
            const error: ApiError = await response.json();
            throw error;
        } catch {
            throw {
                error_code: "HTTP_ERROR",
                message: `Request failed with status ${response.status}`,
            } as ApiError;
        }
    }

    try {
        return await response.json();
    } catch {
        throw {
            error_code: "INVALID_JSON",
            message: "Server returned invalid JSON",
        } as ApiError;
    }
}

export async function startSession(
    interviewId: string
): Promise<{ state: InterviewState; first_question_ready: boolean }> {
    return request("/session/start", {
        method: "POST",
        interviewId,
    });
}

export async function getNextQuestion(
    interviewId: string
): Promise<QuestionResponse> {
    return request("/questions/next", {
        method: "GET",
        interviewId,
    });
}

export async function submitEvaluation(
    interviewId: string,
    payload: EvaluationSubmitRequest
): Promise<EvaluationSubmitResponse> {
    return request("/evaluation/submit", {
        method: "POST",
        interviewId,
        body: payload,
    });
}

export async function getSummary(
    interviewId: string
): Promise<SummaryResponse> {
    return request("/summary", {
        method: "GET",
        interviewId,
    });
}

export async function sendProctoringEvent(
    interviewId: string,
    payload: ProctoringEventRequest
): Promise<ProctoringEventResponse> {
    return request("/proctoring/event", {
        method: "POST",
        interviewId,
        body: payload,
    });
}

export async function getCodeTemplate(
    interviewId: string,
    questionId: string
): Promise<CodeTemplateResponse> {
    return request(`/code/template/${questionId}`, {
        method: "GET",
        interviewId,
    });
}

export async function getConversationPrompt(
    interviewId: string
): Promise<ConversationPromptResponse> {
    return request("/conversation/prompt", {
        method: "GET",
        interviewId,
    });
}
