import { apiClient } from "./apiClient";
import { controlWebSocket } from "./controlWebSocket";
import { proctoringEngine } from "./proctoringEngine";
import {
    InterviewState,
    QuestionResponse,
    EvaluationSubmitRequest,
    ProctoringEventRequest,
    EvaluationSubmitResponse,
    ProctoringEventResponse,
} from "@/types/api";

class InterviewService {
    private interviewId: string | null = null;
    private candidateToken: string | null = null;

    initialize(params: {
        interviewId: string;
        candidateToken: string;
        onConnected: () => void;
        onTerminated: (reason: string) => void;
        onError: (error: unknown) => void;
    }): void {
        this.interviewId = params.interviewId;
        this.candidateToken = params.candidateToken;

        apiClient.setInterviewId(this.interviewId);

        controlWebSocket.disconnect();
        controlWebSocket.connect({
            interviewId: this.interviewId,
            candidateToken: this.candidateToken,
            onOpen: () => {
                params.onConnected();
            },
            onTerminate: (reason: string) => {
                proctoringEngine.stop();
                params.onTerminated(reason);
            },
            onError: (error: Event) => {
                const err = error instanceof Error ? error : new Error("WebSocket connection error");
                params.onError(err);
            },
            onClose: (event: CloseEvent) => {
                console.log(`[InterviewService] WebSocket Closed: ${event.code} - ${event.reason}`);
                proctoringEngine.stop();
                if (event.code === 1008) {
                    // Invalid session/token -> Terminate/Error
                    const error = new Error(`Session invalid or expired: ${event.reason}`);
                    params.onError(error);
                }
            },
        });
    }

    async startInterview(): Promise<InterviewState> {
        const response = await apiClient.post<{ state: InterviewState }, {}>(
            "/api/v1/session/start",
            {},
            true
        );

        if (response.state === "IN_PROGRESS") {
            try {
                await proctoringEngine.start();
            } catch (error) {
                controlWebSocket.disconnect();
                throw error;
            }
        }

        return response.state;
    }

    async fetchNextQuestion(): Promise<QuestionResponse> {
        return apiClient.get<QuestionResponse>("/api/v1/question/next", true);
    }

    async submitAnswer(payload: EvaluationSubmitRequest): Promise<InterviewState> {
        const response = await apiClient.post<EvaluationSubmitResponse, EvaluationSubmitRequest>(
            "/api/v1/submit/submit",
            payload,
            true
        );

        if (response.state === "COMPLETED") {
            proctoringEngine.stop();
        }

        return response.state;
    }

    async sendProctoringEvent(event: ProctoringEventRequest): Promise<void> {
        await apiClient.post<ProctoringEventResponse, ProctoringEventRequest>(
            "/api/v1/proctoring/event",
            event,
            true
        );
    }

    terminate(): void {
        proctoringEngine.stop();
        controlWebSocket.disconnect();
        apiClient.clearInterviewId();
        this.interviewId = null;
        this.candidateToken = null;
    }
}

export const interviewService = new InterviewService();
