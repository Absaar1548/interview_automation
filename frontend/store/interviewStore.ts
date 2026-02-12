import { create } from "zustand";
import { interviewService } from "@/lib/interviewService";
import {
    InterviewState,
    QuestionResponse,
    EvaluationSubmitRequest,
    ProctoringEventRequest,
} from "@/types/api";

interface InterviewStore {
    interviewId: string | null;
    candidateToken: string | null;
    state: InterviewState | null;
    currentQuestion: QuestionResponse | null;
    terminationReason: string | null;
    isSubmitting: boolean;
    isConnected: boolean;
    error: string | null;

    initialize: (interviewId: string, candidateToken: string) => void;
    startInterview: () => Promise<void>;
    fetchNextQuestion: () => Promise<void>;
    submitAnswer: (payload: EvaluationSubmitRequest) => Promise<void>;
    sendProctoringEvent: (event: ProctoringEventRequest) => Promise<void>;
    terminate: () => void;
}

export const useInterviewStore = create<InterviewStore>((set, get) => ({
    interviewId: null,
    candidateToken: null,
    state: null,
    currentQuestion: null,
    terminationReason: null,
    isSubmitting: false,
    isConnected: false,
    error: null,

    initialize: (interviewId: string, candidateToken: string) => {
        set({ interviewId, candidateToken, error: null });
        interviewService.initialize({
            interviewId,
            candidateToken,
            onConnected: () => {
                set({ isConnected: true });
            },
            onTerminated: (reason: string) => {
                set({ state: "TERMINATED", terminationReason: reason, isConnected: false, currentQuestion: null });
            },
            onError: (error: unknown) => {
                const errorMessage = error instanceof Error ? error.message : "Unknown error";
                set({ error: errorMessage, isConnected: false });
            },
        });
    },

    startInterview: async () => {
        set({ error: null });
        try {
            const state = await interviewService.startInterview();
            set({ state });
            if (state === "IN_PROGRESS") {
                await get().fetchNextQuestion();
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "Failed to start interview";
            set({ error: errorMessage });
        }
    },

    fetchNextQuestion: async () => {
        if (get().state !== "IN_PROGRESS") return;
        set({ error: null });
        try {
            const question = await interviewService.fetchNextQuestion();
            set({ currentQuestion: question, state: "QUESTION_ASKED" });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "Failed to fetch question";
            set({ error: errorMessage });
        }
    },

    submitAnswer: async (payload: EvaluationSubmitRequest) => {
        set({ isSubmitting: true, error: null });
        try {
            const state = await interviewService.submitAnswer(payload);
            set({ state });

            if (state === "IN_PROGRESS") {
                await get().fetchNextQuestion();
            } else if (state === "COMPLETED") {
                set({ currentQuestion: null });
            }
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : "Failed to submit answer";
            set({ error: errorMessage });
        } finally {
            set({ isSubmitting: false });
        }
    },

    sendProctoringEvent: async (event: ProctoringEventRequest) => {
        try {
            await interviewService.sendProctoringEvent(event);
        } catch (error) {
            // Silently log or handle if critical, but specs say no console logs.
            // Keeping error state consistent if meaningful.
            const errorMessage = error instanceof Error ? error.message : "Failed to send proctoring event";
            set({ error: errorMessage });
        }
    },

    terminate: () => {
        interviewService.terminate();
        set({
            interviewId: null,
            candidateToken: null,
            state: null,
            currentQuestion: null,
            terminationReason: null,
            isSubmitting: false,
            isConnected: false,
            error: null,
        });
    },
}));
