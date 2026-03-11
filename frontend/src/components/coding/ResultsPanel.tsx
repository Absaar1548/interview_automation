import React from "react"
import { TestCaseResult } from "@/lib/api/codingApi"

interface ResultsPanelProps {
    results: TestCaseResult[]
    summary: { passed: number; total: number } | null
    isRunning: boolean
    isSubmitting: boolean
    error: string | null
    submissionStatus: "passed" | "failed" | "error" | null
}

export default function ResultsPanel({
    results,
    summary,
    isRunning,
    isSubmitting,
    error,
    submissionStatus
}: ResultsPanelProps) {
    if (isRunning || isSubmitting) {
        return (
            <div className="flex flex-col items-center justify-center h-full bg-[#282828] rounded-lg border border-[#3e3e42] shadow-xl">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#2cbb5d] mb-4"></div>
                <p className="text-sm text-[#bfbfc1] font-medium">
                    {isSubmitting ? "Judging..." : "Running Tests..."}
                </p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="h-full p-6 bg-[#282828] border border-[#3e3e42] rounded-lg shadow-xl shrink-0">
                <h3 className="text-xl font-bold text-red-500 mb-4">Execution Error</h3>
                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded font-mono text-sm text-red-400 whitespace-pre-wrap">
                    {error}
                </div>
            </div>
        )
    }

    if (!results || results.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-center bg-[#282828] rounded-lg border border-[#3e3e42] shadow-xl text-[#7a7a7d] text-sm">
                <div className="flex flex-col items-center gap-3">
                    <svg className="w-10 h-10 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
                    <span>Run your code to see results here</span>
                </div>
            </div>
        )
    }

    const allPassed = summary && summary.passed === summary.total
    const isAccepted = submissionStatus === 'passed'

    return (
        <div className="flex flex-col h-full bg-[#282828] rounded-lg border border-[#3e3e42] overflow-hidden shadow-xl">
            <div className="px-5 py-3 flex items-center justify-between border-b border-[#3e3e42] bg-[#313131]">
                <div className="flex items-center gap-4">
                    <h3 className="text-sm font-semibold text-[#eff1f6]">Test Results</h3>
                    {summary && (
                        <span className="text-sm font-bold text-[#bfbfc1]">
                            {summary.passed} / {summary.total} Passed
                        </span>
                    )}
                </div>

                {submissionStatus && (
                    <span className={`text-xl font-bold tracking-tight ${isAccepted ? 'text-[#2cbb5d]' :
                        submissionStatus === 'failed' ? 'text-red-500' :
                            'text-yellow-500'
                        }`}>
                        {isAccepted ? 'Accepted' : submissionStatus === 'failed' ? 'Wrong Answer' : 'Error'}
                    </span>
                )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
                {!submissionStatus && summary && (
                    <h2 className={`text-2xl font-bold ${allPassed ? 'text-[#2cbb5d]' : 'text-red-500'}`}>
                        {allPassed ? 'Accepted' : 'Wrong Answer'}
                    </h2>
                )}

                <div className="space-y-4">
                    {results.map((res, idx) => (
                        <div key={idx} className="space-y-3">
                            <div className="flex items-center gap-3">
                                <span className={`px-2 py-1 rounded text-sm font-bold ${res.passed ? 'text-[#2cbb5d] bg-[#2cbb5d]/10' : 'text-red-500 bg-red-500/10'}`}>
                                    Case {idx + 1}: {res.passed ? 'Accepted' : 'Wrong Answer'}
                                </span>
                            </div>

                            <div className="space-y-3 bg-[#333] rounded-lg p-4 border border-[#3e3e42] text-sm font-mono text-[#eff1f6]">
                                <div>
                                    <p className="text-[#bfbfc1] mb-1 text-xs uppercase font-sans font-semibold tracking-wider">Input</p>
                                    <div className="bg-[#1e1e1e] p-2 rounded text-[#eff1f6] break-words">{res.input}</div>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-[#bfbfc1] mb-1 text-xs uppercase font-sans font-semibold tracking-wider">Output</p>
                                        <div className={`p-2 rounded break-words ${res.passed ? 'bg-[#1e1e1e]' : 'bg-red-500/10 text-red-200'}`}>{res.actual_output}</div>
                                    </div>
                                    {!res.passed && !res.error && (
                                        <div>
                                            <p className="text-[#bfbfc1] mb-1 text-xs uppercase font-sans font-semibold tracking-wider">Expected</p>
                                            <div className="bg-[#1e1e1e] p-2 rounded text-[#2cbb5d] break-words">{res.expected_output}</div>
                                        </div>
                                    )}
                                </div>

                                {res.error && (
                                    <div className="mt-2 p-3 bg-red-500/10 rounded border border-red-500/20">
                                        <p className="text-red-400 font-mono text-xs whitespace-pre-wrap">{res.error}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            <style jsx>{`
                .custom-scrollbar::-webkit-scrollbar {
                    width: 8px;
                }
                .custom-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb {
                    background: #5c5c60;
                    border-radius: 4px;
                }
                .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                    background: #7a7a7d;
                }
            `}</style>
        </div>
    )
}
