import { create } from "zustand";
import type {
    InterviewState,
    QuestionResponse,
    EvaluationSubmitRequest,
    ProctoringEventRequest,
    ApiError,
} from "../types/api";
import { InterviewService } from "../lib/interviewService";

interface InterviewStoreState {
    interviewId: string | null;
    candidateToken: string | null;

    state: InterviewState | null;
    currentQuestion: QuestionResponse | null;

    timeRemaining: number | null;
    isSubmitting: boolean;
    wsConnected: boolean;

    terminationReason: string | null;

    service: InterviewService | null;
    timerId: number | null;

    initialize: (interviewId: string, candidateToken: string) => void;
    startInterview: () => Promise<void>;
    fetchNextQuestion: () => Promise<void>;
    submitAnswer: (payload: EvaluationSubmitRequest) => Promise<void>;
    reportProctoringEvent: (payload: ProctoringEventRequest) => Promise<void>;
    handleWsConnected: (state: InterviewState) => void;
    handleWsDisconnected: () => void;
    handleTermination: (reason: string) => void;
    startTimer: (seconds: number) => void;
    stopTimer: () => void;
}

export const useInterviewStore = create<InterviewStoreState>((set, get) => ({
    interviewId: null,
    candidateToken: null,

    state: null,
    currentQuestion: null,

    timeRemaining: null,
    isSubmitting: false,
    wsConnected: false,

    terminationReason: null,

    service: null,
    timerId: null,

    initialize: (interviewId: string, candidateToken: string) => {
        const { service: existingService } = get();
        if (existingService) return;

        const service = new InterviewService(interviewId, candidateToken, {
            onWsConnected: (state) => get().handleWsConnected(state),
            onWsDisconnected: () => get().handleWsDisconnected(),
            onTerminate: (reason) => get().handleTermination(reason),
        });

        service.connectWebSocket();

        set({
            interviewId,
            candidateToken,
            service,
        });
    },

    startInterview: async () => {
        const { service, fetchNextQuestion } = get();
        if (!service) return;

        try {
            const response = await service.startSession();
            set({ state: response.state });

            if (response.state === "IN_PROGRESS") {
                await fetchNextQuestion();
            }
        } catch (error) {
            const apiError = error as ApiError;
            if (apiError.current_state) {
                set({ state: apiError.current_state });
            }
        }
    },

    fetchNextQuestion: async () => {
        const { service, startTimer } = get();
        if (!service) return;

        try {
            const question = await service.fetchNextQuestion();
            set({
                currentQuestion: question,
                state: "QUESTION_ASKED",
            });
            startTimer(question.time_limit_sec);
        } catch (error) {
            const apiError = error as ApiError;
            if (apiError.current_state) {
                set({ state: apiError.current_state });
            }
        }
    },

    submitAnswer: async (payload: EvaluationSubmitRequest) => {
        const { isSubmitting, service, stopTimer, fetchNextQuestion } = get();
        if (isSubmitting || !service) return;

        stopTimer();
        set({ isSubmitting: true });

        try {
            const response = await service.submitAnswer(payload);
            set({ state: response.state });

            if (response.state === "IN_PROGRESS") {
                await fetchNextQuestion();
            } else if (response.state === "COMPLETED") {
                stopTimer();
                service.disconnectWebSocket();
            }
        } catch (error) {
            const apiError = error as ApiError;
            if (apiError.current_state) {
                set({ state: apiError.current_state });
            }
        } finally {
            set({ isSubmitting: false });
        }
    },

    reportProctoringEvent: async (payload: ProctoringEventRequest) => {
        const { service } = get();
        if (!service) return;

        try {
            const response = await service.sendProctoringEvent(payload);
            if (response.action === "TERMINATE") {
                const { stopTimer } = get();
                stopTimer();
                set({
                    state: "TERMINATED",
                    terminationReason: "Backend termination",
                });
                service.disconnectWebSocket();
            }
        } catch (error) {
            const apiError = error as ApiError;
            if (apiError.current_state) {
                set({ state: apiError.current_state });
            }
        }
    },

    handleWsConnected: (state: InterviewState) => {
        set({ wsConnected: true });
        const currentState = get().state;
        if (currentState !== state) {
            set({ state });
        }
    },

    handleWsDisconnected: () => {
        set({ wsConnected: false });
    },

    handleTermination: (reason: string) => {
        const { stopTimer, service } = get();
        stopTimer();
        set({
            state: "TERMINATED",
            terminationReason: reason,
        });
        service?.disconnectWebSocket();
    },

    startTimer: (seconds: number) => {
        const { stopTimer, submitAnswer } = get();
        stopTimer();

        set({ timeRemaining: seconds });

        const timerId = window.setInterval(() => {
            const { timeRemaining, currentQuestion } = get();
            if (timeRemaining === null) return;

            if (timeRemaining <= 1) {
                stopTimer();
                if (currentQuestion) {
                    submitAnswer({
                        question_id: currentQuestion.question_id,
                        answer_type: currentQuestion.answer_mode,
                        answer_payload: "",
                    });
                }
            } else {
                set({ timeRemaining: timeRemaining - 1 });
            }
        }, 1000);

        set({ timerId });
    },

    stopTimer: () => {
        const { timerId } = get();
        if (timerId !== null) {
            clearInterval(timerId);
            set({ timerId: null, timeRemaining: null });
        }
    },
}));
