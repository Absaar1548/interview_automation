import { create } from 'zustand';
import { InterviewState, InterviewQuestion } from '@/types/interview';

interface InterviewStoreState {
    // State
    interviewId: string | null;
    currentState: InterviewState;
    currentQuestion: InterviewQuestion | null;
    questionIndex: number;
    totalQuestions: number;
    violations: number;
    startTime: number | null;

    // Actions
    setInterviewId: (id: string) => void;
    setState: (state: InterviewState) => void;
    setQuestion: (question: InterviewQuestion | null) => void;
    incrementQuestionIndex: () => void;
    setTotalQuestions: (count: number) => void;
    addViolation: () => void;
    setStartTime: (time: number) => void;
    resetInterview: () => void;
}

export const useInterviewStore = create<InterviewStoreState>((set) => ({
    // Initial State
    interviewId: null,
    currentState: InterviewState.CREATED,
    currentQuestion: null,
    questionIndex: 0,
    totalQuestions: 0,
    violations: 0,
    startTime: null,

    // Actions
    setInterviewId: (id) => set({ interviewId: id }),
    setState: (state) => set({ currentState: state }),
    setQuestion: (question) => set({ currentQuestion: question }),
    incrementQuestionIndex: () => set((state) => ({ questionIndex: state.questionIndex + 1 })),
    setTotalQuestions: (count) => set({ totalQuestions: count }),
    addViolation: () => set((state) => ({ violations: state.violations + 1 })),
    setStartTime: (time) => set({ startTime: time }),
    resetInterview: () => set({
        interviewId: null,
        currentState: InterviewState.CREATED,
        currentQuestion: null,
        questionIndex: 0,
        totalQuestions: 0,
        violations: 0,
        startTime: null,
    }),
}));
