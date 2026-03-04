/**
 * technicalApi.ts — API helpers for technical (subjective) questions
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

export interface TechnicalQuestion {
    id: string;
    title: string;
    description: string;
    category: string;
    difficulty: string;
    time_limit_sec: number;
}

export interface AnswerResponse {
    answer_id: string;
    status: string;
}

// ─── API Calls ────────────────────────────────────────────────────────────────

export async function fetchTechnicalQuestion(
    questionId?: string,
    excludeIds?: string[]
): Promise<TechnicalQuestion> {
    const params = new URLSearchParams();
    if (questionId) params.set("question_id", questionId);
    if (excludeIds && excludeIds.length > 0) params.set("exclude_ids", excludeIds.join(","));
    const qs = params.toString();
    const url = `${BASE_URL}/api/v1/technical/question${qs ? `?${qs}` : ""}`;

    const res = await fetch(url, { headers: authHeaders() });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to fetch question");
    }
    return res.json();
}

export async function submitTechnicalAnswer(data: {
    question_id: string;
    answer_text: string;
    interview_id?: string;
    candidate_id?: string;
}): Promise<AnswerResponse> {
    const res = await fetch(`${BASE_URL}/api/v1/technical/answer`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to submit answer");
    }
    return res.json();
}

export async function completeInterview(candidateId?: string): Promise<{ status: string; message: string }> {
    const res = await fetch(`${BASE_URL}/api/v1/coding/complete-interview`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ candidate_id: candidateId || null }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to complete interview");
    }
    return res.json();
}

