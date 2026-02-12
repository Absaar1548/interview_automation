"use client";

import { useState, useEffect } from "react";
import { useInterviewStore } from "@/store/interviewStore";
import QuestionPanel from "./QuestionPanel";
import AnswerPanel from "./AnswerPanel";
import Timer from "./Timer";

export default function InterviewShell() {
    const currentQuestion = useInterviewStore((s) => s.currentQuestion);
    const state = useInterviewStore((s) => s.state);
    const isSubmitting = useInterviewStore((s) => s.isSubmitting);
    const submitAnswer = useInterviewStore((s) => s.submitAnswer);

    const [answerPayload, setAnswerPayload] = useState("");

    useEffect(() => {
        setAnswerPayload("");
    }, [currentQuestion?.question_id]);

    if (state !== "QUESTION_ASKED" || !currentQuestion) {
        return null;
    }

    const handleSubmit = () => {
        if (isSubmitting) return;
        if (currentQuestion.answer_mode === "AUDIO" && !answerPayload) return;

        submitAnswer({
            question_id: currentQuestion.question_id,
            answer_type: currentQuestion.answer_mode,
            answer_payload: answerPayload.trim(),
        });
    };

    return (
        <div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto w-full">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold">Question</h2>
                <Timer durationSec={currentQuestion.time_limit_sec} onExpire={handleSubmit} />
            </div>

            <QuestionPanel question={currentQuestion} />

            <AnswerPanel
                mode={currentQuestion.answer_mode}
                value={answerPayload}
                onChange={setAnswerPayload}
                questionId={currentQuestion.question_id}
            />

            <button
                onClick={handleSubmit}
                disabled={
                    isSubmitting ||
                    (currentQuestion.answer_mode === "AUDIO" && !answerPayload)
                }
                className="mt-4 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 self-end"
            >
                {isSubmitting ? "Submitting..." : "Submit Answer"}
            </button>
        </div>
    );
}
