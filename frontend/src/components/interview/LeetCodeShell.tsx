"use client";

import { useState, useEffect, useCallback } from "react";
import Editor from "@monaco-editor/react";
import ProblemList from "./ProblemList";
import ProblemDescription from "./ProblemDescription";
import TestCasesPanel from "./TestCasesPanel";
import LeetCodeTimer from "./LeetCodeTimer";

// ---------- Types ----------

interface ProblemListItem {
    id: string;
    title: string;
    difficulty: string;
}

interface TestCase {
    input: string;
    expected_output: string;
    is_hidden: boolean;
    points: number;
}

interface Problem {
    _id: string;
    title: string;
    difficulty: string;
    description: string;
    time_limit_sec: number;
    memory_limit_mb: number;
    test_cases: TestCase[];
    sample_code: Record<string, string>;
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

// ---------- Language options ----------

const LANGUAGES = [
    { id: "python", name: "Python 3", monacoId: "python" },
    { id: "javascript", name: "JavaScript", monacoId: "javascript" },
    { id: "java", name: "Java", monacoId: "java" },
    { id: "cpp", name: "C++", monacoId: "cpp" },
];

const DEFAULT_CODE: Record<string, string> = {
    python: "# Write your solution here\n",
    javascript:
        "// Write your solution here\nconst readline = require('readline');\nconst rl = readline.createInterface({ input: process.stdin });\nlet lines = [];\nrl.on('line', l => lines.push(l));\nrl.on('close', () => {\n    // your code\n});\n",
    java: "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        // your code\n    }\n}\n",
    cpp: "#include <bits/stdc++.h>\nusing namespace std;\nint main() {\n    // your code\n    return 0;\n}\n",
};

const API = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// ---------- Verdict Banner ----------
type Verdict = "accepted" | "wrong_answer" | "error" | null;

function VerdictBanner({
    verdict,
    detail,
    passedCount,
    totalCount,
    onClose,
}: {
    verdict: Verdict;
    detail: string;
    passedCount?: number;
    totalCount?: number;
    onClose: () => void;
}) {
    if (!verdict) return null;

    const config = {
        accepted: {
            bg: "bg-green-900/60 border-green-600/50",
            icon: "✅",
            title: "Accepted",
            textColor: "text-green-300",
        },
        wrong_answer: {
            bg: "bg-red-900/60 border-red-600/50",
            icon: "❌",
            title: "Wrong Answer",
            textColor: "text-red-300",
        },
        error: {
            bg: "bg-orange-900/60 border-orange-600/50",
            icon: "⚠️",
            title: "Runtime Error",
            textColor: "text-orange-300",
        },
    }[verdict];

    return (
        <div
            className={`absolute inset-x-0 top-0 z-30 mx-4 mt-2 rounded-xl border px-5 py-4 flex items-center justify-between shadow-2xl backdrop-blur-sm ${config.bg}`}
        >
            <div className="flex items-center gap-3">
                <span className="text-2xl">{config.icon}</span>
                <div>
                    <p className={`text-lg font-bold ${config.textColor}`}>
                        {config.title}
                    </p>
                    {passedCount !== undefined && totalCount !== undefined && (
                        <p className="text-sm text-gray-400">
                            {passedCount} / {totalCount} test cases passed
                        </p>
                    )}
                    {detail && (
                        <p className="text-xs text-gray-500 mt-0.5">{detail}</p>
                    )}
                </div>
            </div>
            <button
                onClick={onClose}
                className="text-gray-500 hover:text-gray-200 text-xl leading-none ml-4"
            >
                ×
            </button>
        </div>
    );
}

// ---------- Main Shell ----------

export default function LeetCodeShell() {
    const [problems, setProblems] = useState<ProblemListItem[]>([]);
    const [problemsLoading, setProblemsLoading] = useState(true);

    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [problem, setProblem] = useState<Problem | null>(null);
    const [problemLoading, setProblemLoading] = useState(false);

    const [language, setLanguage] = useState(LANGUAGES[0]);
    const [code, setCode] = useState(DEFAULT_CODE.python);

    const [activeTab, setActiveTab] = useState<"description" | "testcases">(
        "description"
    );

    const [runResults, setRunResults] = useState<TestRunSummary | null>(null);
    const [isRunning, setIsRunning] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [verdict, setVerdict] = useState<Verdict>(null);
    const [verdictDetail, setVerdictDetail] = useState("");
    const [verdictPass, setVerdictPass] = useState<number | undefined>();
    const [verdictTotal, setVerdictTotal] = useState<number | undefined>();

    const [timerKey, setTimerKey] = useState(0);
    const [sidebarOpen, setSidebarOpen] = useState(true);

    // Load problem list
    useEffect(() => {
        fetch(`${API}/api/v1/code/problems`)
            .then((r) => r.json())
            .then((data: ProblemListItem[]) => {
                setProblems(data);
                if (data.length > 0) setSelectedId(data[0].id);
            })
            .catch(() => { })
            .finally(() => setProblemsLoading(false));
    }, []);

    // Load selected problem
    useEffect(() => {
        if (!selectedId) return;
        setProblemLoading(true);
        setRunResults(null);
        setVerdict(null);
        setTimerKey((k) => k + 1);
        setActiveTab("description");

        fetch(`${API}/api/v1/code/problems/${selectedId}`)
            .then((r) => r.json())
            .then((data: Problem) => {
                setProblem(data);
                // Set sample code for current language
                const sample =
                    data.sample_code?.[language.id] ||
                    DEFAULT_CODE[language.id] ||
                    "";
                setCode(sample);
            })
            .catch(() => { })
            .finally(() => setProblemLoading(false));
    }, [selectedId]); // eslint-disable-line react-hooks/exhaustive-deps

    const handleLanguageChange = (langId: string) => {
        const lang = LANGUAGES.find((l) => l.id === langId);
        if (!lang) return;
        setLanguage(lang);
        const sample =
            problem?.sample_code?.[langId] || DEFAULT_CODE[langId] || "";
        setCode(sample);
    };

    const handleRun = useCallback(async () => {
        if (!problem || !code.trim()) return;
        setIsRunning(true);
        setRunResults(null);
        setActiveTab("testcases");

        try {
            const res = await fetch(`${API}/api/v1/code/test`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    problem_id: problem._id,
                    code,
                    language: language.id,
                }),
            });
            const data: TestRunSummary = await res.json();
            setRunResults(data);
        } catch {
            // silently fail
        } finally {
            setIsRunning(false);
        }
    }, [problem, code, language]);

    const handleSubmit = useCallback(async () => {
        if (!problem || !code.trim()) return;
        setIsSubmitting(true);
        setVerdict(null);

        try {
            const res = await fetch(`${API}/api/v1/code/submit`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    problem_id: problem._id,
                    code,
                    language: language.id,
                    user_id: "candidate",
                }),
            });
            const data = await res.json();

            const allPassed = data.passed_count === data.total_count;
            setVerdict(allPassed ? "accepted" : "wrong_answer");
            setVerdictDetail(
                allPassed
                    ? `Score: ${data.score} / ${data.total_points}`
                    : `${data.total_count - data.passed_count} test case(s) failed`
            );
            setVerdictPass(data.passed_count);
            setVerdictTotal(data.total_count);
        } catch {
            setVerdict("error");
            setVerdictDetail("Could not connect to server");
        } finally {
            setIsSubmitting(false);
        }
    }, [problem, code, language]);

    const visibleTestCases =
        problem?.test_cases?.filter((tc) => !tc.is_hidden) ?? [];

    return (
        <div className="h-screen w-screen flex flex-col bg-[#1a1a2e] text-white overflow-hidden">
            {/* ===== Top Nav Bar ===== */}
            <header className="shrink-0 flex items-center justify-between px-4 h-12 bg-[#16213e] border-b border-gray-700/60 shadow-lg z-10">
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setSidebarOpen((v) => !v)}
                        className="text-gray-400 hover:text-white p-1 rounded"
                        title="Toggle sidebar"
                    >
                        ☰
                    </button>
                    <span className="font-bold text-blue-400 text-lg tracking-tight">
                        CodeArena
                    </span>
                    {problem && (
                        <span className="hidden md:block text-gray-500 text-sm truncate max-w-xs">
                            / {problem.title}
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-4">
                    <LeetCodeTimer key={timerKey} />
                    <button
                        onClick={handleRun}
                        disabled={isRunning || isSubmitting || !problem}
                        className="px-4 py-1.5 rounded-md bg-gray-700 hover:bg-gray-600 text-sm font-medium text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                        {isRunning ? "Running…" : "▶ Run"}
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={isRunning || isSubmitting || !problem}
                        className="px-4 py-1.5 rounded-md bg-green-600 hover:bg-green-500 text-sm font-semibold text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                        {isSubmitting ? "Submitting…" : "Submit"}
                    </button>
                </div>
            </header>

            {/* ===== Three-pane Body ===== */}
            <div className="flex flex-1 overflow-hidden">
                {/* ── Left: Problem Sidebar ── */}
                <aside
                    className={`shrink-0 flex flex-col bg-[#16213e] border-r border-gray-700/60 transition-all duration-200 overflow-hidden ${sidebarOpen ? "w-60" : "w-0"
                        }`}
                >
                    <ProblemList
                        problems={problems}
                        selectedId={selectedId}
                        onSelect={(id) => setSelectedId(id)}
                        loading={problemsLoading}
                    />
                </aside>

                {/* ── Center: Description / Test Cases ── */}
                <section className="flex flex-col w-[38%] shrink-0 border-r border-gray-700/60 bg-[#1e1e2e] relative">
                    {/* Verdict banner */}
                    <VerdictBanner
                        verdict={verdict}
                        detail={verdictDetail}
                        passedCount={verdictPass}
                        totalCount={verdictTotal}
                        onClose={() => setVerdict(null)}
                    />

                    {/* Tab bar */}
                    <div className="shrink-0 flex border-b border-gray-700/60 bg-[#16213e]">
                        {(["description", "testcases"] as const).map((tab) => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                className={`px-4 py-2.5 text-xs font-medium uppercase tracking-wider transition-colors ${activeTab === tab
                                        ? "text-blue-400 border-b-2 border-blue-400"
                                        : "text-gray-500 hover:text-gray-300"
                                    }`}
                            >
                                {tab === "description" ? "Description" : "Test Cases"}
                                {tab === "testcases" &&
                                    runResults && (
                                        <span
                                            className={`ml-1.5 text-[10px] px-1.5 py-0.5 rounded-full font-bold ${runResults.passed_count ===
                                                    runResults.total_count
                                                    ? "bg-green-700 text-green-200"
                                                    : "bg-red-700 text-red-200"
                                                }`}
                                        >
                                            {runResults.passed_count}/
                                            {runResults.total_count}
                                        </span>
                                    )}
                            </button>
                        ))}
                    </div>

                    {/* Tab content */}
                    <div className="flex-1 overflow-hidden">
                        {problemLoading ? (
                            <div className="p-6 flex flex-col gap-3">
                                {[1, 2, 3, 4].map((i) => (
                                    <div
                                        key={i}
                                        className={`h-4 rounded bg-gray-700/50 animate-pulse ${i === 1 ? "w-2/3" : i === 4 ? "w-1/2" : "w-full"
                                            }`}
                                    />
                                ))}
                            </div>
                        ) : problem ? (
                            activeTab === "description" ? (
                                <ProblemDescription
                                    title={problem.title}
                                    difficulty={problem.difficulty}
                                    description={problem.description}
                                    timeLimitSec={problem.time_limit_sec}
                                    memoryLimitMb={problem.memory_limit_mb}
                                    testCases={visibleTestCases}
                                />
                            ) : (
                                <TestCasesPanel
                                    testCases={visibleTestCases}
                                    runResults={runResults}
                                    isRunning={isRunning}
                                />
                            )
                        ) : (
                            <div className="flex h-full items-center justify-center text-gray-600 text-sm">
                                Select a problem to get started
                            </div>
                        )}
                    </div>
                </section>

                {/* ── Right: Monaco Editor ── */}
                <section className="flex flex-col flex-1 bg-[#1e1e2e] overflow-hidden">
                    {/* Editor toolbar */}
                    <div className="shrink-0 flex items-center gap-3 px-3 py-2 bg-[#16213e] border-b border-gray-700/60">
                        <select
                            value={language.id}
                            onChange={(e) => handleLanguageChange(e.target.value)}
                            className="text-xs bg-gray-800 text-gray-200 border border-gray-600 rounded px-2 py-1.5 focus:outline-none focus:border-blue-500"
                        >
                            {LANGUAGES.map((l) => (
                                <option key={l.id} value={l.id}>
                                    {l.name}
                                </option>
                            ))}
                        </select>
                        <span className="text-gray-600 text-xs">
                            {code.split("\n").length} lines
                        </span>
                        <div className="ml-auto flex gap-2">
                            <button
                                onClick={() =>
                                    setCode(
                                        problem?.sample_code?.[language.id] ||
                                        DEFAULT_CODE[language.id] ||
                                        ""
                                    )
                                }
                                className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 rounded hover:bg-gray-800 transition-colors"
                                title="Reset to default"
                            >
                                ↺ Reset
                            </button>
                        </div>
                    </div>

                    {/* Monaco */}
                    <div className="flex-1 overflow-hidden">
                        <Editor
                            height="100%"
                            language={language.monacoId}
                            value={code}
                            onChange={(v) => setCode(v || "")}
                            theme="vs-dark"
                            options={{
                                minimap: { enabled: false },
                                fontSize: 14,
                                lineNumbers: "on",
                                scrollBeyondLastLine: false,
                                automaticLayout: true,
                                tabSize: 4,
                                wordWrap: "off",
                                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                                fontLigatures: true,
                                cursorBlinking: "smooth",
                                renderLineHighlight: "line",
                                scrollbar: {
                                    vertical: "auto",
                                    horizontal: "auto",
                                },
                                padding: { top: 12, bottom: 12 },
                            }}
                        />
                    </div>
                </section>
            </div>
        </div>
    );
}
