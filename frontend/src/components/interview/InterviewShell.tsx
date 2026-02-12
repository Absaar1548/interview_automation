import { InterviewState } from '@/types/interview';
import { useInterviewStore } from '@/store/interviewStore';
import QuestionPanel from './QuestionPanel';
import AnswerPanel from './AnswerPanel';
import { useEffect } from 'react';
import { connect, disconnect } from '@/lib/websocketClient';
import Timer from './Timer';

interface InterviewShellProps {
    onInit: () => void;
    onStart: () => void;
    onNextQuestion: () => void;
    onSubmitAnswer: () => void;
}

export default function InterviewShell({
    onInit,
    onStart,
    onNextQuestion,
    onSubmitAnswer
}: InterviewShellProps) {
    const currentState = useInterviewStore((state) => state.currentState);
    const currentQuestion = useInterviewStore((state) => state.currentQuestion);
    const questionIndex = useInterviewStore((state) => state.questionIndex);
    const totalQuestions = useInterviewStore((state) => state.totalQuestions);
    const violations = useInterviewStore((state) => state.violations);

    useEffect(() => {
        if (currentState === InterviewState.IN_PROGRESS) {
            connect();
        } else if (currentState === InterviewState.COMPLETED || currentState === InterviewState.TERMINATED) {
            disconnect();
        }
    }, [currentState]);

    useEffect(() => {
        return () => disconnect();
    }, []);

    if (currentState === InterviewState.CREATED) {
        return (
            <div className="text-center">
                <h1 className="text-4xl font-bold mb-4">Interview Created</h1>
                <p className="text-xl mb-8">Your interview setup is being initialized.</p>
                <button
                    onClick={onInit}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                    Initialize Interview
                </button>
            </div>
        );
    }

    if (currentState === InterviewState.RESUME_PARSED) {
        return (
            <div className="text-center">
                <h1 className="text-4xl font-bold mb-4">Resume Parsed</h1>
                <p className="text-xl">We have processed your resume and are preparing the session.</p>
            </div>
        );
    }

    if (currentState === InterviewState.READY) {
        return (
            <div className="text-center">
                <h1 className="text-4xl font-bold mb-4">Ready to Start</h1>
                <p className="text-xl mb-8">Please ensure your camera and microphone are working.</p>
                <button
                    onClick={onStart}
                    className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                >
                    Start Interview
                </button>
            </div>
        );
    }

    if (currentState === InterviewState.IN_PROGRESS ||
        currentState === InterviewState.QUESTION_ASKED ||
        currentState === InterviewState.ANSWER_SUBMITTED ||
        currentState === InterviewState.EVALUATING) {
        return (
            <div className="flex flex-col items-center w-full max-w-4xl">
                <div className="w-full flex justify-between items-center mb-6 px-4">
                    <div className="flex flex-col text-left">
                        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
                            {currentState === InterviewState.EVALUATING ? "Evaluating..." : "In Progress"}
                        </h1>
                        {violations > 0 && (
                            <div className="text-red-500 font-bold text-sm">
                                Warnings: {violations}
                            </div>
                        )}
                    </div>
                    <div className="text-lg font-medium text-gray-600 dark:text-gray-400">
                        Question {questionIndex} of {totalQuestions}
                    </div>
                </div>

                {currentState === InterviewState.EVALUATING ? (
                    <div className="text-center py-12">
                        <h2 className="text-3xl font-bold mb-4 animate-pulse">Analyzing Response...</h2>
                        <p className="text-xl text-gray-500">Please wait while we evaluate your answer.</p>
                    </div>
                ) : (
                    !currentQuestion ? (
                        <div className="mt-8 text-center">
                            <p className="text-xl mb-8">Ready for the next question?</p>
                            <button
                                onClick={onNextQuestion}
                                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                            >
                                Load Next Question
                            </button>
                        </div>
                    ) : (
                        <>
                            <div className="w-full flex justify-end px-4 mb-2">
                                <Timer
                                    duration={currentQuestion.time_limit_sec}
                                    active={true}
                                    onExpire={onSubmitAnswer}
                                />
                            </div>
                            <QuestionPanel question={currentQuestion} />
                            <AnswerPanel question={currentQuestion} onSubmit={onSubmitAnswer} />
                        </>
                    )
                )}
            </div>
        );
    }

    if (currentState === InterviewState.COMPLETED) {
        return (
            <div className="text-center">
                <h1 className="text-4xl font-bold mb-4 text-green-600">Interview Completed</h1>
                <p className="text-xl">Thank you for completing the interview.</p>
            </div>
        );
    }

    if (currentState === InterviewState.TERMINATED) {
        return (
            <div className="text-center">
                <h1 className="text-4xl font-bold mb-4 text-red-600">Interview Terminated</h1>
                <p className="text-xl">The interview has been terminated due to a violation.</p>
            </div>
        );
    }

    return null;
}
