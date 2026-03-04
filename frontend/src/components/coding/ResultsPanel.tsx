"use client";

import { TestCaseResult } from "@/lib/api/codingApi";

interface ResultsPanelProps {
    results: TestCaseResult[] | null;
    summary: { passed: number; total: number } | null;
    isRunning: boolean;
    isSubmitting: boolean;
    error: string | null;
    submissionStatus: string | null;
}

export default function ResultsPanel({
    results,
    summary,
    isRunning,
    isSubmitting,
    error,
    submissionStatus,
}: ResultsPanelProps) {
    if (isRunning || isSubmitting) {
        return (
            <div className="p-4 bg-[#181825] flex items-center gap-3">
                <div className="animate-spin h-4 w-4 border-2 border-blue-400 border-t-transparent rounded-full" />
                <span className="text-gray-400 text-sm">
                    {isSubmitting ? "Submitting..." : "Running test cases..."}
                </span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 bg-[#181825]">
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-red-400 text-sm">
                    ⚠ {error}
                </div>
            </div>
        );
    }

    if (!results || !summary) {
        return (
            <div className="p-4 bg-[#181825] text-gray-500 text-sm">
                Run your code to see results here.
            </div>
        );
    }

    const allPassed = summary.passed === summary.total;

    return (
        <div className="p-4 bg-[#181825] overflow-y-auto">
            {/* Summary */}
            <div className="flex items-center gap-3 mb-3">
                <div
                    className={`px-3 py-1 rounded-full text-xs font-bold ${allPassed
                            ? "bg-emerald-500/20 text-emerald-400"
                            : "bg-red-500/20 text-red-400"
                        }`}
                >
                    {allPassed ? "ALL PASSED" : "FAILED"}
                </div>
                <span className="text-gray-400 text-sm">
                    {summary.passed}/{summary.total} test cases passed
                </span>
                {submissionStatus && (
                    <span
                        className={`ml-auto text-xs font-bold px-2 py-1 rounded ${submissionStatus === "passed"
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-red-500/20 text-red-400"
                            }`}
                    >
                        Submission: {submissionStatus.toUpperCase()}
                    </span>
                )}
            </div>

            {/* Individual results */}
            <div className="space-y-2">
                {results.map((r, i) => (
                    <div
                        key={r.test_case_id}
                        className={`border rounded-lg p-3 ${r.passed
                                ? "border-emerald-500/30 bg-emerald-500/5"
                                : "border-red-500/30 bg-red-500/5"
                            }`}
                    >
                        <div className="flex items-center gap-2 mb-2">
                            <span
                                className={`text-xs font-bold ${r.passed ? "text-emerald-400" : "text-red-400"
                                    }`}
                            >
                                {r.passed ? "✓" : "✗"} Test Case {i + 1}
                            </span>
                        </div>
                        <div className="grid grid-cols-1 gap-1.5 text-xs font-mono">
                            <div>
                                <span className="text-gray-500">Input: </span>
                                <span className="text-gray-300 whitespace-pre-wrap">
                                    {r.input}
                                </span>
                            </div>
                            <div>
                                <span className="text-gray-500">Expected: </span>
                                <span className="text-sky-300 whitespace-pre-wrap">
                                    {r.expected_output}
                                </span>
                            </div>
                            <div>
                                <span className="text-gray-500">Actual: </span>
                                <span
                                    className={`whitespace-pre-wrap ${r.passed ? "text-emerald-300" : "text-red-300"
                                        }`}
                                >
                                    {r.actual_output || "(no output)"}
                                </span>
                            </div>
                            {r.error && (
                                <div>
                                    <span className="text-gray-500">Error: </span>
                                    <span className="text-red-400 whitespace-pre-wrap">
                                        {r.error}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
