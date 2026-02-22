"use client";

interface TestCase {
    input: string;
    expected_output: string;
    is_hidden: boolean;
}

interface TestCaseResult {
    test_case_index: number;
    passed: boolean;
    actual_output?: string;
    expected_output?: string;
    error?: string;
    execution_time_ms?: number;
    is_hidden: boolean;
}

interface TestRunSummary {
    results: TestCaseResult[];
    passed_count: number;
    total_count: number;
}

interface TestCasesPanelProps {
    testCases: TestCase[];
    runResults: TestRunSummary | null;
    isRunning: boolean;
}

export default function TestCasesPanel({
    testCases,
    runResults,
    isRunning,
}: TestCasesPanelProps) {
    const visibleCases = testCases.filter((tc) => !tc.is_hidden);

    return (
        <div className="flex flex-col h-full overflow-hidden">
            {/* Summary banner */}
            {runResults && (
                <div
                    className={`shrink-0 flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b border-gray-700 ${runResults.passed_count === runResults.total_count
                            ? "bg-green-900/30 text-green-400"
                            : "bg-red-900/30 text-red-400"
                        }`}
                >
                    {runResults.passed_count === runResults.total_count ? "✅" : "❌"}
                    {runResults.passed_count} / {runResults.total_count} test cases passed
                </div>
            )}

            {isRunning && (
                <div className="shrink-0 flex items-center gap-2 px-4 py-2 text-sm text-yellow-400 border-b border-gray-700 bg-yellow-900/20">
                    <span className="animate-spin">⚙</span> Running test cases...
                </div>
            )}

            {/* Test case list */}
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
                {visibleCases.map((tc, idx) => {
                    const result = runResults?.results.find(
                        (r) => r.test_case_index === idx
                    );

                    return (
                        <div
                            key={idx}
                            className={`rounded-lg border overflow-hidden ${result
                                    ? result.passed
                                        ? "border-green-500/40 bg-green-900/10"
                                        : "border-red-500/40 bg-red-900/10"
                                    : "border-gray-700 bg-gray-800/40"
                                }`}
                        >
                            {/* Header */}
                            <div className="flex items-center justify-between px-3 py-2 bg-gray-800/60 border-b border-gray-700">
                                <span className="text-xs font-semibold text-gray-300">
                                    Case {idx + 1}
                                </span>
                                {result && (
                                    <span
                                        className={`text-xs font-bold px-2 py-0.5 rounded ${result.passed
                                                ? "bg-green-700/50 text-green-300"
                                                : "bg-red-700/50 text-red-300"
                                            }`}
                                    >
                                        {result.passed ? "✅ Passed" : "❌ Failed"}
                                    </span>
                                )}
                                {result?.execution_time_ms && (
                                    <span className="text-xs text-gray-500">
                                        {result.execution_time_ms.toFixed(0)} ms
                                    </span>
                                )}
                            </div>

                            {/* Content */}
                            <div className="p-3 flex flex-col gap-2 text-xs font-mono">
                                <div>
                                    <p className="text-gray-500 mb-1 font-sans text-[11px] uppercase tracking-wider">
                                        Input
                                    </p>
                                    <pre className="bg-gray-900/60 rounded p-2 text-gray-200 whitespace-pre-wrap break-all">
                                        {tc.input}
                                    </pre>
                                </div>

                                <div>
                                    <p className="text-gray-500 mb-1 font-sans text-[11px] uppercase tracking-wider">
                                        Expected
                                    </p>
                                    <pre className="bg-gray-900/60 rounded p-2 text-green-300 whitespace-pre-wrap break-all">
                                        {tc.expected_output}
                                    </pre>
                                </div>

                                {result && !result.passed && (
                                    <div>
                                        <p className="text-gray-500 mb-1 font-sans text-[11px] uppercase tracking-wider">
                                            Your Output
                                        </p>
                                        <pre className="bg-gray-900/60 rounded p-2 text-red-300 whitespace-pre-wrap break-all">
                                            {result.error
                                                ? `Error: ${result.error}`
                                                : result.actual_output ?? "(no output)"}
                                        </pre>
                                    </div>
                                )}
                                {result && result.passed && (
                                    <div>
                                        <p className="text-gray-500 mb-1 font-sans text-[11px] uppercase tracking-wider">
                                            Your Output
                                        </p>
                                        <pre className="bg-gray-900/60 rounded p-2 text-green-300 whitespace-pre-wrap break-all">
                                            {result.actual_output ?? "(no output)"}
                                        </pre>
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}

                {visibleCases.length === 0 && (
                    <div className="text-center text-gray-500 text-sm py-8">
                        No visible test cases available.
                    </div>
                )}
            </div>
        </div>
    );
}
