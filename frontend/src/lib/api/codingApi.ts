/**
 * codingApi.ts — API helpers for the coding challenge feature
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function getToken(): string | null {
    if (typeof window === "undefined") return null;
    try {
        const raw = localStorage.getItem("auth-storage");
        if (!raw) return null;
        return JSON.parse(raw)?.state?.token ?? null;
    } catch {
        return null;
    }
}

function authHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
    };
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return headers;
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface TestCaseExample {
    input: string;
    expected_output: string;
    order: number;
}

export interface CodingProblem {
    id: string;
    title: string;
    description: string;
    difficulty: string;
    time_limit_sec: number;
    starter_code: Record<string, string>;
    examples: TestCaseExample[];
}

export interface TestCaseResult {
    test_case_id: string;
    input: string;
    expected_output: string;
    actual_output: string;
    passed: boolean;
    error: string | null;
}

export interface RunCodeResponse {
    passed: number;
    total: number;
    results: TestCaseResult[];
}

export interface SubmitCodeResponse {
    submission_id: string;
    status: string;
    passed: number;
    total: number;
    results: TestCaseResult[];
}

// ─── API Calls ────────────────────────────────────────────────────────────────

export async function fetchCodingProblem(
    problemId?: string,
    excludeIds?: string[]
): Promise<CodingProblem> {
    const params = new URLSearchParams();
    if (problemId) params.set("problem_id", problemId);
    if (excludeIds && excludeIds.length > 0) params.set("exclude_ids", excludeIds.join(","));
    const qs = params.toString();
    const url = `${BASE_URL}/api/v1/coding/problem${qs ? `?${qs}` : ""}`;

    const res = await fetch(url, { headers: authHeaders() });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to fetch problem");
    }
    return res.json();
}

export async function runCode(data: {
    problem_id: string;
    language: string;
    source_code: string;
}): Promise<RunCodeResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/coding/run`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to run code");
    }
    return res.json();
}

export async function submitCode(data: {
    problem_id: string;
    language: string;
    source_code: string;
    interview_id?: string;
    candidate_id?: string;
}): Promise<SubmitCodeResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/coding/submit`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to submit code");
    }
    return res.json();
}
