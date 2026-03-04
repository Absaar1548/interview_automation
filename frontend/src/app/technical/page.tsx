"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useTechnicalStore, TOTAL_TECHNICAL_QUESTIONS } from "@/store/technicalStore";

const CATEGORY_LABELS: Record<string, string> = {
    data_science: "Data Science",
    ai_ml: "AI / ML",
    deep_learning: "Deep Learning",
    nlp: "NLP",
    statistics: "Statistics",
};

const DIFFICULTY_STYLES: Record<string, string> = {
    easy: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    medium: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    hard: "bg-red-500/20 text-red-400 border-red-500/30",
};

export default function TechnicalPage() {
    const router = useRouter();

    const question = useTechnicalStore((s) => s.question);
    const isLoadingQuestion = useTechnicalStore((s) => s.isLoadingQuestion);
    const answerText = useTechnicalStore((s) => s.answerText);
    const isSubmitting = useTechnicalStore((s) => s.isSubmitting);
    const isSubmitted = useTechnicalStore((s) => s.isSubmitted);
    const error = useTechnicalStore((s) => s.error);
    const timerActive = useTechnicalStore((s) => s.timerActive);
    const questionNumber = useTechnicalStore((s) => s.questionNumber);
    const allComplete = useTechnicalStore((s) => s.allComplete);
    const loadQuestion = useTechnicalStore((s) => s.loadQuestion);
    const loadNextQuestion = useTechnicalStore((s) => s.loadNextQuestion);
    const setAnswerText = useTechnicalStore((s) => s.setAnswerText);
    const submitAnswer = useTechnicalStore((s) => s.submitAnswer);

    // Timer
    const [timeLeft, setTimeLeft] = useState(600);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const hasAutoSubmitted = useRef(false);

    useEffect(() => {
        loadQuestion();
    }, [loadQuestion]);

    useEffect(() => {
        if (question) {
            setTimeLeft(question.time_limit_sec);
            hasAutoSubmitted.current = false;
        }
    }, [question]);

    const handleAutoSubmit = useCallback(() => {
        if (!hasAutoSubmitted.current && !isSubmitted) {
            hasAutoSubmitted.current = true;
            submitAnswer();
        }
    }, [isSubmitted, submitAnswer]);

    useEffect(() => {
        if (!timerActive || isSubmitted) {
            if (timerRef.current) clearInterval(timerRef.current);
            return;
        }
        timerRef.current = setInterval(() => {
            setTimeLeft((prev) => {
                if (prev <= 1) {
                    if (timerRef.current) clearInterval(timerRef.current);
                    handleAutoSubmit();
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [timerActive, isSubmitted, handleAutoSubmit]);

    useEffect(() => {
        if (isSubmitted && timerRef.current) clearInterval(timerRef.current);
    }, [isSubmitted]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    };

    const isTimeCritical = timeLeft <= 30;
    const isTimeWarning = timeLeft <= 90 && !isTimeCritical;

    // Complete interview when all questions are done
    const [interviewEnded, setInterviewEnded] = useState(false);

    useEffect(() => {
        if (!allComplete || interviewEnded) return;

        const finalize = async () => {
            try {
                // Get candidate_id from auth storage
                let candidateId: string | undefined;
                try {
                    const raw = localStorage.getItem("auth-storage");
                    if (raw) {
                        const parsed = JSON.parse(raw);
                        candidateId = parsed?.state?.user?.id;
                    }
                } catch { }

                // Call the backend to mark interview as completed + disable login
                const { completeInterview } = await import("@/lib/api/technicalApi");
                await completeInterview(candidateId);
            } catch (err) {
                console.error("Failed to complete interview:", err);
            }

            // Clear auth storage to log out
            localStorage.removeItem("auth-storage");
            setInterviewEnded(true);
        };

        finalize();
    }, [allComplete, interviewEnded]);

    // Final completion screen
    if (allComplete) {
        return (
            <div className="min-h-screen bg-[#1e1e2e] flex items-center justify-center">
                <div className="text-center max-w-lg px-6">
                    <div className="text-6xl mb-6">🎉</div>
                    <h1 className="text-3xl font-bold text-white mb-3">
                        Interview Complete!
                    </h1>
                    <p className="text-gray-400 mb-4 text-lg">
                        You have successfully completed all coding challenges and technical questions.
                    </p>
                    <p className="text-gray-500 mb-8 text-sm">
                        Thank you for your time. The interview results will be reviewed by the admin.
                        You will no longer be able to log in to this account.
                    </p>
                    <div className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600/20 border border-emerald-500/30 rounded-lg text-emerald-400 text-sm font-medium">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                            <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                        </svg>
                        All responses submitted
                    </div>
                </div>
            </div>
        );
    }

    if (isLoadingQuestion || !question) {
        return (
            <div className="min-h-screen bg-[#1e1e2e] flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin h-10 w-10 border-3 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
                    <p className="text-gray-400 text-sm">Loading question...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen flex flex-col bg-[#11111b] overflow-hidden">
            {/* Top Bar */}
            <header className="flex items-center justify-between px-4 py-2 bg-[#181825] border-b border-[#313244] shrink-0">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-purple-400">
                            <path d="M11.25 4.533A9.707 9.707 0 006 3a9.735 9.735 0 00-3.25.555.75.75 0 00-.5.707v14.25a.75.75 0 001 .707A8.237 8.237 0 016 18.75c1.995 0 3.823.707 5.25 1.886V4.533zM12.75 20.636A8.214 8.214 0 0118 18.75c.966 0 1.89.166 2.75.47a.75.75 0 001-.708V4.262a.75.75 0 00-.5-.707A9.735 9.735 0 0018 3a9.707 9.707 0 00-5.25 1.533v16.103z" />
                        </svg>
                        <span className="text-white font-semibold text-sm">Technical Question</span>
                    </div>
                    <span className="text-gray-600 text-sm">|</span>
                    <span className="text-gray-400 text-sm">
                        Q{questionNumber} of {TOTAL_TECHNICAL_QUESTIONS}: {question.title}
                    </span>
                </div>

                {/* Timer */}
                <div className="flex items-center gap-4">
                    <div
                        className={`flex items-center gap-2 px-4 py-1.5 rounded-lg border font-mono text-sm font-bold transition-all ${isTimeCritical
                            ? "bg-red-500/20 border-red-500/50 text-red-400 animate-pulse"
                            : isTimeWarning
                                ? "bg-amber-500/15 border-amber-500/40 text-amber-400"
                                : "bg-[#313244] border-[#45475a] text-gray-300"
                            }`}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5c0 .414.336.75.75.75h4a.75.75 0 000-1.5h-3.25V5z" clipRule="evenodd" />
                        </svg>
                        {formatTime(timeLeft)}
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <div className="flex-1 flex min-h-0">
                {/* Left: Question */}
                <div className="w-[40%] border-r border-[#313244] overflow-y-auto bg-[#1e1e2e] p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <h1 className="text-xl font-bold text-white">{question.title}</h1>
                        <span
                            className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border capitalize ${DIFFICULTY_STYLES[question.difficulty] || DIFFICULTY_STYLES.medium
                                }`}
                        >
                            {question.difficulty}
                        </span>
                    </div>
                    <div className="inline-block px-2.5 py-0.5 text-xs font-medium rounded bg-purple-500/20 text-purple-400 border border-purple-500/30 mb-4">
                        {CATEGORY_LABELS[question.category] || question.category}
                    </div>

                    <div className="prose prose-invert prose-sm max-w-none">
                        {question.description.split("\n").map((line, i) => {
                            if (line.startsWith("## "))
                                return <h2 key={i} className="text-lg font-bold text-white mt-4 mb-2">{line.replace("## ", "")}</h2>;
                            if (line.startsWith("- "))
                                return <li key={i} className="text-gray-400 ml-4 list-disc text-sm">{line.replace("- ", "")}</li>;
                            if (line.startsWith("**") && line.endsWith("**"))
                                return <p key={i} className="text-amber-400 text-sm font-semibold mt-3">{line.replace(/\*\*/g, "")}</p>;
                            if (line.trim() === "") return <div key={i} className="h-2" />;
                            return <p key={i} className="text-gray-400 text-sm leading-relaxed">{line}</p>;
                        })}
                    </div>
                </div>

                {/* Right: Text Editor */}
                <div className="w-[60%] flex flex-col min-h-0">
                    {/* Editor Label */}
                    <div className="px-4 py-2 bg-[#181825] border-b border-[#313244]">
                        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                            Your Answer
                        </span>
                    </div>

                    {/* Text Area */}
                    <div className="flex-1 min-h-0 p-4 bg-[#1e1e2e]">
                        <textarea
                            value={answerText}
                            onChange={(e) => setAnswerText(e.target.value)}
                            readOnly={isSubmitted}
                            placeholder="Type your answer here... Be detailed and well-structured in your response."
                            className="w-full h-full bg-[#11111b] text-gray-200 text-sm font-mono leading-relaxed rounded-lg border border-[#313244] p-4 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/50 placeholder-gray-600 disabled:opacity-60"
                        />
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="px-4 py-2 bg-[#181825]">
                            <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-2 text-red-400 text-sm">
                                ⚠ {error}
                            </div>
                        </div>
                    )}

                    {/* Bottom Action Bar */}
                    <div className="flex items-center justify-between px-4 py-3 bg-[#181825] border-t border-[#313244] shrink-0">
                        <div className="text-xs text-gray-500">
                            {isSubmitted && (
                                <span className="text-emerald-400 font-medium">✓ Answer submitted successfully</span>
                            )}
                            {!isSubmitted && answerText.length > 0 && (
                                <span className="text-gray-500">{answerText.length} characters</span>
                            )}
                        </div>
                        <div className="flex items-center gap-3">
                            {isSubmitted ? (
                                <button
                                    onClick={() => loadNextQuestion()}
                                    className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-500 transition-all flex items-center gap-2 shadow-lg shadow-blue-600/20"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                                        <path fillRule="evenodd" d="M2 10a.75.75 0 01.75-.75h12.59l-2.1-1.95a.75.75 0 111.02-1.1l3.5 3.25a.75.75 0 010 1.1l-3.5 3.25a.75.75 0 11-1.02-1.1l2.1-1.95H2.75A.75.75 0 012 10z" clipRule="evenodd" />
                                    </svg>
                                    Next Question
                                </button>
                            ) : (
                                <button
                                    onClick={() => submitAnswer()}
                                    disabled={isSubmitting || answerText.trim().length === 0}
                                    className="px-5 py-2 bg-purple-600 text-white rounded-lg text-sm font-semibold hover:bg-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg shadow-purple-600/20"
                                >
                                    {isSubmitting ? (
                                        <>
                                            <div className="animate-spin h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full" />
                                            Submitting...
                                        </>
                                    ) : (
                                        <>
                                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                                                <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.896 28.896 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z" />
                                            </svg>
                                            Submit Answer
                                        </>
                                    )}
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
