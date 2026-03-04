import { create } from "zustand";
import {
    TechnicalQuestion,
    fetchTechnicalQuestion,
    submitTechnicalAnswer,
} from "@/lib/api/technicalApi";

export const TOTAL_TECHNICAL_QUESTIONS = 2;

interface TechnicalStore {
    question: TechnicalQuestion | null;
    isLoadingQuestion: boolean;
    answeredQuestionIds: string[];
    questionNumber: number;
    allComplete: boolean;

    answerText: string;
    isSubmitting: boolean;
    isSubmitted: boolean;
    error: string | null;

    timerActive: boolean;

    loadQuestion: (questionId?: string) => Promise<void>;
    loadNextQuestion: () => Promise<void>;
    setAnswerText: (text: string) => void;
    submitAnswer: (interviewId?: string, candidateId?: string) => Promise<void>;
    stopTimer: () => void;
    reset: () => void;
}

export const useTechnicalStore = create<TechnicalStore>((set, get) => ({
    question: null,
    isLoadingQuestion: false,
    answeredQuestionIds: [],
    questionNumber: 1,
    allComplete: false,

    answerText: "",
    isSubmitting: false,
    isSubmitted: false,
    error: null,

    timerActive: true,

    loadQuestion: async (questionId?: string) => {
        set({ isLoadingQuestion: true, error: null });
        try {
            const { answeredQuestionIds } = get();
            const question = await fetchTechnicalQuestion(questionId, answeredQuestionIds);
            set({
                question,
                isLoadingQuestion: false,
                answerText: "",
                timerActive: true,
                isSubmitted: false,
                allComplete: false,
            });
        } catch (err: any) {
            if (err.message === "No technical questions found") {
                set({ isLoadingQuestion: false, allComplete: true });
            } else {
                set({ error: err.message, isLoadingQuestion: false });
            }
        }
    },

    loadNextQuestion: async () => {
        const { question, answeredQuestionIds, questionNumber } = get();
        const newAnsweredIds = question
            ? [...answeredQuestionIds, question.id]
            : answeredQuestionIds;

        if (newAnsweredIds.length >= TOTAL_TECHNICAL_QUESTIONS) {
            set({ answeredQuestionIds: newAnsweredIds, allComplete: true });
            return;
        }

        set({
            answeredQuestionIds: newAnsweredIds,
            questionNumber: questionNumber + 1,
            isSubmitted: false,
            answerText: "",
            error: null,
            isLoadingQuestion: true,
        });

        try {
            const nextQ = await fetchTechnicalQuestion(undefined, newAnsweredIds);
            set({
                question: nextQ,
                isLoadingQuestion: false,
                timerActive: true,
                allComplete: false,
            });
        } catch (err: any) {
            if (err.message === "No technical questions found") {
                set({ isLoadingQuestion: false, allComplete: true });
            } else {
                set({ error: err.message, isLoadingQuestion: false });
            }
        }
    },

    setAnswerText: (text: string) => set({ answerText: text }),

    submitAnswer: async (interviewId?: string, candidateId?: string) => {
        const { question, answerText } = get();
        if (!question) return;
        set({ isSubmitting: true, error: null });
        try {
            await submitTechnicalAnswer({
                question_id: question.id,
                answer_text: answerText || "(No answer provided)",
                interview_id: interviewId,
                candidate_id: candidateId,
            });
            set({
                isSubmitting: false,
                isSubmitted: true,
                timerActive: false,
            });
        } catch (err: any) {
            set({ isSubmitting: false, error: err.message });
        }
    },

    stopTimer: () => set({ timerActive: false }),

    reset: () =>
        set({
            question: null,
            isLoadingQuestion: false,
            answeredQuestionIds: [],
            questionNumber: 1,
            allComplete: false,
            answerText: "",
            isSubmitting: false,
            isSubmitted: false,
            error: null,
            timerActive: true,
        }),
}));
