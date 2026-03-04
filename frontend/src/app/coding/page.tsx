"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useCodingStore, TOTAL_PROBLEMS } from "@/store/codingStore";
import ProblemPanel from "@/components/coding/ProblemPanel";
import CodeEditorPanel from "@/components/coding/CodeEditorPanel";
import ResultsPanel from "@/components/coding/ResultsPanel";

export default function CodingPage() {
    const router = useRouter();

    const problem = useCodingStore((s) => s.problem);
    const isLoadingProblem = useCodingStore((s) => s.isLoadingProblem);
    const isRunning = useCodingStore((s) => s.isRunning);
    const isSubmitting = useCodingStore((s) => s.isSubmitting);
    const isSubmitted = useCodingStore((s) => s.isSubmitted);
    const results = useCodingStore((s) => s.results);
    const resultSummary = useCodingStore((s) => s.resultSummary);
    const submissionStatus = useCodingStore((s) => s.submissionStatus);
    const error = useCodingStore((s) => s.error);
    const timerActive = useCodingStore((s) => s.timerActive);
    const questionNumber = useCodingStore((s) => s.questionNumber);
    const allProblemsComplete = useCodingStore((s) => s.allProblemsComplete);
    const loadProblem = useCodingStore((s) => s.loadProblem);
    const loadNextProblem = useCodingStore((s) => s.loadNextProblem);
    const runCurrentCode = useCodingStore((s) => s.runCurrentCode);
    const submitCurrentCode = useCodingStore((s) => s.submitCurrentCode);

    // Timer state
    const [timeLeft, setTimeLeft] = useState(900);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const hasAutoSubmitted = useRef(false);

    // Load problem on mount
    useEffect(() => {
        loadProblem();
    }, [loadProblem]);

    // Update timer duration when problem loads
    useEffect(() => {
        if (problem) {
            setTimeLeft(problem.time_limit_sec);
            hasAutoSubmitted.current = false;
        }
    }, [problem]);

    // Auto-submit handler
    const handleAutoSubmit = useCallback(() => {
        if (!hasAutoSubmitted.current && !isSubmitted) {
            hasAutoSubmitted.current = true;
            submitCurrentCode();
        }
    }, [isSubmitted, submitCurrentCode]);

    // Timer countdown
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

    // Stop timer on submission
    useEffect(() => {
        if (isSubmitted && timerRef.current) {
            clearInterval(timerRef.current);
        }
    }, [isSubmitted]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    };

    const isTimeCritical = timeLeft <= 60;
    const isTimeWarning = timeLeft <= 180 && !isTimeCritical;

    // Show results panel
    const [showResults, setShowResults] = useState(false);
    useEffect(() => {
        if (results || error) setShowResults(true);
    }, [results, error]);

    // Reset showResults when new problem loads
    useEffect(() => {
        if (!isSubmitted && !results) setShowResults(false);
    }, [isSubmitted, results]);

    // Handle next question
    const handleNextQuestion = () => {
        setShowResults(false);
        loadNextProblem();
    };

    // All coding problems complete — redirect to technical questions
    if (allProblemsComplete) {
        return (
            <div className="min-h-screen bg-[#1e1e2e] flex items-center justify-center">
                <div className="text-center max-w-md">
                    <div className="text-5xl mb-6">✅</div>
                    <h1 className="text-2xl font-bold text-white mb-3">
                        Coding Challenges Complete!
                    </h1>
                    <p className="text-gray-400 mb-6">
                        Great work! Now let's move on to the technical questions.
                    </p>
                    <button
                        onClick={() => router.push("/technical")}
                        className="px-6 py-3 bg-purple-600 text-white rounded-lg font-semibold hover:bg-purple-500 transition-all flex items-center gap-2 mx-auto"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                            <path fillRule="evenodd" d="M2 10a.75.75 0 01.75-.75h12.59l-2.1-1.95a.75.75 0 111.02-1.1l3.5 3.25a.75.75 0 010 1.1l-3.5 3.25a.75.75 0 11-1.02-1.1l2.1-1.95H2.75A.75.75 0 012 10z" clipRule="evenodd" />
                        </svg>
                        Continue to Technical Questions
                    </button>
                </div>
            </div>
        );
    }

    if (isLoadingProblem || !problem) {
        return (
            <div className="min-h-screen bg-[#1e1e2e] flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin h-10 w-10 border-3 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
                    <p className="text-gray-400 text-sm">Loading coding challenge...</p>
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
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-blue-400">
                            <path fillRule="evenodd" d="M14.447 3.027a.75.75 0 01.527.92l-4.5 16.5a.75.75 0 01-1.448-.394l4.5-16.5a.75.75 0 01.921-.526zM16.72 6.22a.75.75 0 011.06 0l5.25 5.25a.75.75 0 010 1.06l-5.25 5.25a.75.75 0 11-1.06-1.06L21.44 12l-4.72-4.72a.75.75 0 010-1.06zm-9.44 0a.75.75 0 010 1.06L2.56 12l4.72 4.72a.75.75 0 11-1.06 1.06L.97 12.53a.75.75 0 010-1.06l5.25-5.25a.75.75 0 011.06 0z" clipRule="evenodd" />
                        </svg>
                        <span className="text-white font-semibold text-sm">Coding Challenge</span>
                    </div>
                    <span className="text-gray-600 text-sm">|</span>
                    <span className="text-gray-400 text-sm">
                        Q{questionNumber} of {TOTAL_PROBLEMS}: {problem.title}
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
                {/* Left: Problem Statement */}
                <div className="w-[40%] border-r border-[#313244] overflow-hidden">
                    <ProblemPanel
                        title={problem.title}
                        difficulty={problem.difficulty}
                        description={problem.description}
                        examples={problem.examples}
                    />
                </div>

                {/* Right: Editor + Results */}
                <div className="w-[60%] flex flex-col min-h-0">
                    {/* Code Editor */}
                    <div className={`${showResults ? "h-[55%]" : "flex-1"} min-h-0`}>
                        <CodeEditorPanel />
                    </div>

                    {/* Results Panel */}
                    {showResults && (
                        <div className="h-[45%] border-t border-[#313244] overflow-y-auto">
                            <div className="flex items-center justify-between px-4 py-2 bg-[#181825] border-b border-[#313244]">
                                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                    Test Results
                                </span>
                                <button
                                    onClick={() => setShowResults(false)}
                                    className="text-gray-500 hover:text-gray-300 text-xs"
                                >
                                    ✕ Close
                                </button>
                            </div>
                            <ResultsPanel
                                results={results}
                                summary={resultSummary}
                                isRunning={isRunning}
                                isSubmitting={isSubmitting}
                                error={error}
                                submissionStatus={submissionStatus}
                            />
                        </div>
                    )}

                    {/* Bottom Action Bar */}
                    <div className="flex items-center justify-between px-4 py-3 bg-[#181825] border-t border-[#313244] shrink-0">
                        <div className="text-xs text-gray-500">
                            {isSubmitted && (
                                <span className="text-emerald-400 font-medium">
                                    ✓ Code submitted successfully
                                </span>
                            )}
                        </div>
                        <div className="flex items-center gap-3">
                            {/* Run Button */}
                            <button
                                onClick={() => {
                                    setShowResults(true);
                                    runCurrentCode();
                                }}
                                disabled={isRunning || isSubmitting || isSubmitted}
                                className="px-5 py-2 bg-[#313244] text-gray-200 rounded-lg text-sm font-medium hover:bg-[#45475a] transition-all disabled:opacity-50 disabled:cursor-not-allowed border border-[#45475a] flex items-center gap-2"
                            >
                                {isRunning ? (
                                    <>
                                        <div className="animate-spin h-3.5 w-3.5 border-2 border-gray-400 border-t-transparent rounded-full" />
                                        Running...
                                    </>
                                ) : (
                                    <>
                                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 text-emerald-400">
                                            <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                                        </svg>
                                        Run
                                    </>
                                )}
                            </button>

                            {/* Submit / Next Question Button */}
                            {isSubmitted ? (
                                <button
                                    onClick={handleNextQuestion}
                                    className="px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-500 transition-all flex items-center gap-2 shadow-lg shadow-blue-600/20"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                                        <path fillRule="evenodd" d="M2 10a.75.75 0 01.75-.75h12.59l-2.1-1.95a.75.75 0 111.02-1.1l3.5 3.25a.75.75 0 010 1.1l-3.5 3.25a.75.75 0 11-1.02-1.1l2.1-1.95H2.75A.75.75 0 012 10z" clipRule="evenodd" />
                                    </svg>
                                    Next Question
                                </button>
                            ) : (
                                <button
                                    onClick={() => {
                                        setShowResults(true);
                                        submitCurrentCode();
                                    }}
                                    disabled={isSubmitting || isRunning}
                                    className="px-5 py-2 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shadow-lg shadow-emerald-600/20"
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
                                            Submit
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
