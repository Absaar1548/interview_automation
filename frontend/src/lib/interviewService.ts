import type {
    InterviewState,
    QuestionResponse,
    EvaluationSubmitRequest,
    EvaluationSubmitResponse,
    ProctoringEventRequest,
    ProctoringEventResponse,
} from "../types/api";
import {
    startSession,
    getNextQuestion,
    submitEvaluation,
    sendProctoringEvent,
} from "./apiClient";
import { InterviewWebSocket, WebSocketCallbacks } from "./websocketClient";

export class InterviewService {
    private interviewId: string;
    private candidateToken: string;
    private ws: InterviewWebSocket | null = null;
    private callbacks: {
        onWsConnected: (state: InterviewState) => void;
        onWsDisconnected: () => void;
        onTerminate: (reason: string) => void;
    };

    constructor(
        interviewId: string,
        candidateToken: string,
        callbacks: {
            onWsConnected: (state: InterviewState) => void;
            onWsDisconnected: () => void;
            onTerminate: (reason: string) => void;
        }
    ) {
        this.interviewId = interviewId;
        this.candidateToken = candidateToken;
        this.callbacks = callbacks;
    }

    async startSession(): Promise<{
        state: InterviewState;
        first_question_ready: boolean;
    }> {
        return startSession(this.interviewId);
    }

    async fetchNextQuestion(): Promise<QuestionResponse> {
        return getNextQuestion(this.interviewId);
    }

    async submitAnswer(
        payload: EvaluationSubmitRequest
    ): Promise<EvaluationSubmitResponse> {
        return submitEvaluation(this.interviewId, payload);
    }

    async sendProctoringEvent(
        payload: ProctoringEventRequest
    ): Promise<ProctoringEventResponse> {
        return sendProctoringEvent(this.interviewId, payload);
    }

    connectWebSocket(): void {
        if (this.ws) {
            return;
        }

        const wsCallbacks: WebSocketCallbacks = {
            onConnected: this.callbacks.onWsConnected,
            onDisconnected: this.callbacks.onWsDisconnected,
            onTerminate: this.callbacks.onTerminate,
        };

        this.ws = new InterviewWebSocket(wsCallbacks);
        this.ws.connect(this.interviewId, this.candidateToken);
    }

    disconnectWebSocket(): void {
        if (this.ws) {
            this.ws.disconnect();
            this.ws = null;
        }
    }
}
