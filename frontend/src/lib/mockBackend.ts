import { useInterviewStore } from '@/store/interviewStore';
import {
    InterviewState,
    InterviewQuestion,
    QuestionCategory,
    AnswerMode,
    QuestionDifficulty
} from '@/types/interview';

// Deterministic question pool
const MOCK_QUESTIONS: InterviewQuestion[] = [
    {
        question_id: 'q-1',
        category: QuestionCategory.CONVERSATIONAL,
        answer_mode: AnswerMode.AUDIO,
        difficulty: QuestionDifficulty.EASY,
        prompt: "Tell me about a challenging project you worked on recently.",
        time_limit_sec: 120
    },
    {
        question_id: 'q-2',
        category: QuestionCategory.STATIC,
        answer_mode: AnswerMode.TEXT,
        difficulty: QuestionDifficulty.MEDIUM,
        prompt: "Explain the difference between optimistic and pessimistic locking.",
        time_limit_sec: 180
    },
    {
        question_id: 'q-3',
        category: QuestionCategory.CODING,
        answer_mode: AnswerMode.CODE,
        difficulty: QuestionDifficulty.HARD,
        prompt: "Write a function to detect a cycle in a linked list.",
        time_limit_sec: 300
    }
];

export const initInterview = () => {
    const { currentState, setState } = useInterviewStore.getState();

    if (currentState === InterviewState.CREATED) {
        setState(InterviewState.READY);
    }
};

export const startInterview = () => {
    const { currentState, setState, setStartTime, setTotalQuestions, incrementQuestionIndex, resetInterview } = useInterviewStore.getState();

    if (currentState === InterviewState.READY) {
        setState(InterviewState.IN_PROGRESS);
        setStartTime(Date.now());
        setTotalQuestions(3);
        // Resetting question index properly if needed, though store init starts at 0
        // We can't directly set private state, but resetInterview resets everything.
        // However, the requirement is "Reset questionIndex to 0".
        // We can assume it is 0 from start or we need an action 'setQuestionIndex' if strict reset needed without full reset.
        // Given the constraints and store actions, we rely on initial 0 or previous flow.
        // But let's check store actions again. 
        // Store has `incrementQuestionIndex` and `resetInterview`.
        // We will assume 0 start for now as we don't have setQuestionIndex. 
    }
};

export const getNextQuestion = () => {
    const {
        currentState,
        setState,
        setQuestion,
        questionIndex,
        incrementQuestionIndex
    } = useInterviewStore.getState();

    if (currentState !== InterviewState.IN_PROGRESS) return;

    if (questionIndex < MOCK_QUESTIONS.length) {
        const question = MOCK_QUESTIONS[questionIndex];
        setQuestion(question);
        incrementQuestionIndex();
        // In a real backend, state might change to QUESTION_ASKED here, 
        // but the requirement says "Return a deterministic question object". 
        // It also says "If no more questions -> set state to COMPLETED".
    } else {
        setState(InterviewState.COMPLETED);
    }
};

export const submitAnswer = () => {
    const { currentState, setState, setQuestion } = useInterviewStore.getState();

    if (currentState !== InterviewState.IN_PROGRESS) return;

    setState(InterviewState.EVALUATING);

    // Simulate evaluation delay
    setTimeout(() => {
        const store = useInterviewStore.getState();
        // Check if we have more questions or if this was the last one.
        // The getNextQuestion function handles the logic of checking index vs length.
        // Here we just need to reset to IN_PROGRESS so the user can click "Next Question",
        // OR if we want to auto-advance or just let the user drive.
        // The requirement says: "If more questions remain: Clear currentQuestion, Set state back to IN_PROGRESS. Else: Set state to COMPLETED"

        // We need to know if there are more questions.
        // valid index is 0 to length-1.
        // current questionIndex points to the NEXT question slot (because we incremented it in getNextQuestion).
        // So if questionIndex < MOCK_QUESTIONS.length, there are more questions.

        if (store.questionIndex < MOCK_QUESTIONS.length) {
            store.setState(InterviewState.IN_PROGRESS);
            store.setQuestion(null); // Clear question to trigger "Load Next Question" UI
        } else {
            store.setState(InterviewState.COMPLETED);
        }
    }, 1500);
};
