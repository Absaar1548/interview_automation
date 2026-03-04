import { create } from "zustand";
import {
    CodingProblem,
    TestCaseResult,
    fetchCodingProblem,
    runCode,
    submitCode,
} from "@/lib/api/codingApi";

// Number of random problems each candidate gets
export const TOTAL_PROBLEMS = 2;

export type SupportedLanguage = "python3" | "javascript" | "java" | "cpp";

interface CodingStore {
    // Problem state
    problem: CodingProblem | null;
    isLoadingProblem: boolean;
    solvedProblemIds: string[];
    questionNumber: number;
    allProblemsComplete: boolean;

    // Editor state
    language: SupportedLanguage;
    code: Record<string, string>;

    // Execution state
    isRunning: boolean;
    isSubmitting: boolean;
    isSubmitted: boolean;
    results: TestCaseResult[] | null;
    resultSummary: { passed: number; total: number } | null;
    submissionStatus: string | null;
    error: string | null;

    // Timer state
    timerActive: boolean;

    // Actions
    loadProblem: (problemId?: string) => Promise<void>;
    loadNextProblem: () => Promise<void>;
    setLanguage: (lang: SupportedLanguage) => void;
    setCode: (code: string) => void;
    runCurrentCode: () => Promise<void>;
    submitCurrentCode: (interviewId?: string, candidateId?: string) => Promise<void>;
    stopTimer: () => void;
    reset: () => void;
}

export const LANGUAGE_LABELS: Record<SupportedLanguage, string> = {
    python3: "Python 3",
    javascript: "JavaScript",
    java: "Java",
    cpp: "C++",
};

export const MONACO_LANGUAGE_MAP: Record<SupportedLanguage, string> = {
    python3: "python",
    javascript: "javascript",
    java: "java",
    cpp: "cpp",
};

export const useCodingStore = create<CodingStore>((set, get) => ({
    problem: null,
    isLoadingProblem: false,
    solvedProblemIds: [],
    questionNumber: 1,
    allProblemsComplete: false,
    language: "python3",
    code: {},
    isRunning: false,
    isSubmitting: false,
    isSubmitted: false,
    results: null,
    resultSummary: null,
    submissionStatus: null,
    error: null,
    timerActive: true,

    loadProblem: async (problemId?: string) => {
        set({ isLoadingProblem: true, error: null });
        try {
            const { solvedProblemIds } = get();
            const problem = await fetchCodingProblem(problemId, solvedProblemIds);
            set({
                problem,
                isLoadingProblem: false,
                code: { ...problem.starter_code },
                language: "python3",
                timerActive: true,
                isSubmitted: false,
                results: null,
                resultSummary: null,
                submissionStatus: null,
                allProblemsComplete: false,
            });
        } catch (err: any) {
            if (err.message === "No coding problems found") {
                set({ isLoadingProblem: false, allProblemsComplete: true });
            } else {
                set({ error: err.message, isLoadingProblem: false });
            }
        }
    },

    loadNextProblem: async () => {
        const { problem, solvedProblemIds, questionNumber } = get();
        const newSolvedIds = problem
            ? [...solvedProblemIds, problem.id]
            : solvedProblemIds;

        // If we've already done TOTAL_PROBLEMS, we're done
        if (newSolvedIds.length >= TOTAL_PROBLEMS) {
            set({ solvedProblemIds: newSolvedIds, allProblemsComplete: true });
            return;
        }

        set({
            solvedProblemIds: newSolvedIds,
            questionNumber: questionNumber + 1,
            isSubmitted: false,
            results: null,
            resultSummary: null,
            submissionStatus: null,
            error: null,
            isLoadingProblem: true,
        });

        try {
            const nextProblem = await fetchCodingProblem(undefined, newSolvedIds);
            set({
                problem: nextProblem,
                isLoadingProblem: false,
                code: { ...nextProblem.starter_code },
                language: "python3",
                timerActive: true,
                allProblemsComplete: false,
            });
        } catch (err: any) {
            if (err.message === "No coding problems found") {
                set({ isLoadingProblem: false, allProblemsComplete: true });
            } else {
                set({ error: err.message, isLoadingProblem: false });
            }
        }
    },

    setLanguage: (lang: SupportedLanguage) => {
        const { problem, code } = get();
        if (!code[lang] && problem?.starter_code[lang]) {
            set({
                language: lang,
                code: { ...code, [lang]: problem.starter_code[lang] },
            });
        } else {
            set({ language: lang });
        }
    },

    setCode: (newCode: string) => {
        const { language, code } = get();
        set({ code: { ...code, [language]: newCode } });
    },

    runCurrentCode: async () => {
        const { problem, language, code } = get();
        if (!problem) return;
        set({ isRunning: true, error: null, results: null, resultSummary: null });
        try {
            const response = await runCode({
                problem_id: problem.id,
                language,
                source_code: code[language] || "",
            });
            set({
                isRunning: false,
                results: response.results,
                resultSummary: { passed: response.passed, total: response.total },
            });
        } catch (err: any) {
            set({ isRunning: false, error: err.message });
        }
    },

    submitCurrentCode: async (interviewId?: string, candidateId?: string) => {
        const { problem, language, code } = get();
        if (!problem) return;
        set({ isSubmitting: true, error: null, results: null, resultSummary: null });
        try {
            const response = await submitCode({
                problem_id: problem.id,
                language,
                source_code: code[language] || "",
                interview_id: interviewId,
                candidate_id: candidateId,
            });
            set({
                isSubmitting: false,
                isSubmitted: true,
                results: response.results,
                resultSummary: { passed: response.passed, total: response.total },
                submissionStatus: response.status,
                timerActive: false,
            });
        } catch (err: any) {
            set({ isSubmitting: false, error: err.message });
        }
    },

    stopTimer: () => set({ timerActive: false }),

    reset: () =>
        set({
            problem: null,
            isLoadingProblem: false,
            solvedProblemIds: [],
            questionNumber: 1,
            allProblemsComplete: false,
            language: "python3",
            code: {},
            isRunning: false,
            isSubmitting: false,
            isSubmitted: false,
            results: null,
            resultSummary: null,
            submissionStatus: null,
            error: null,
            timerActive: true,
        }),
}));
