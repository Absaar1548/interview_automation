'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useInterviewStore } from '@/store/interviewStore';

// â”€â”€â”€ Types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

interface SummaryData {
    final_score: number;
    recommendation: 'PROCEED' | 'REVIEW' | 'REJECT';
    fraud_risk: 'LOW' | 'MEDIUM' | 'HIGH';
    strengths: string[];
    gaps: string[];
    notes: string;
    completed_at: string | null;
}

// â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

const RECOMMENDATION_CONFIG = {
    PROCEED: { label: 'Proceed to Next Round', bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', dot: 'bg-emerald-500' },
    REVIEW: { label: 'Pending Review', bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', dot: 'bg-amber-500' },
    REJECT: { label: 'Not Selected', bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', dot: 'bg-red-500' },
};

const FRAUD_RISK_CONFIG = {
    LOW: { label: 'Low Risk', color: 'text-emerald-600' },
    MEDIUM: { label: 'Medium Risk', color: 'text-amber-600' },
    HIGH: { label: 'High Risk', color: 'text-red-600' },
};

function ScoreRing({ score }: { score: number }) {
    const pct = score / 100;
    const r = 52;
    const circ = 2 * Math.PI * r;
    const dash = circ * pct;
    const color = score >= 85 ? '#10b981' : score >= 70 ? '#f59e0b' : '#ef4444';

    return (
        <div className="relative flex items-center justify-center w-36 h-36">
            <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r={r} fill="none" stroke="#e5e7eb" strokeWidth="10" />
                <circle
                    cx="60" cy="60" r={r} fill="none"
                    stroke={color} strokeWidth="10"
                    strokeDasharray={`${dash} ${circ}`}
                    strokeLinecap="round"
                    style={{ transition: 'stroke-dasharray 1s ease' }}
                />
            </svg>
            <div className="text-center z-10">
                <p className="text-3xl font-extrabold text-gray-900">{score}</p>
                <p className="text-xs text-gray-400 font-medium">/ 100</p>
            </div>
        </div>
    );
}

// â”€â”€â”€ Main Page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export default function SummaryPage() {
    const router = useRouter();
    const { user, isAuthenticated, logout, _hasHydrated } = useAuthStore();
    const interviewId = useInterviewStore((s) => s.interviewId);
    const candidateToken = useInterviewStore((s) => s.candidateToken);
    const terminate = useInterviewStore((s) => s.terminate);

    const [summary, setSummary] = useState<SummaryData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    const fetchSummary = useCallback(async () => {
        if (!interviewId || !candidateToken) {
            // Nothing in store â€” redirect to candidate dashboard
            router.replace('/candidate');
            return;
        }

        const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        try {
            const res = await fetch(`${base}/api/v1/session/summary`, {
                headers: {
                    Authorization: `Bearer ${candidateToken}`,
                    'X-Interview-Id': interviewId,
                },
            });
            if (!res.ok) {
                const body = await res.json().catch(() => ({}));
                throw new Error(body.detail || `Error ${res.status}`);
            }
            const data: SummaryData = await res.json();
            setSummary(data);
        } catch (err: any) {
            setError(err.message || 'Failed to load summary.');
        } finally {
            setLoading(false);
        }
    }, [interviewId, candidateToken, router]);

    useEffect(() => {
        if (!_hasHydrated) return;  // wait for localStorage rehydration
        if (!isAuthenticated || !user) { router.push('/login/candidate'); return; }
        if (user.role !== 'candidate') { router.push('/candidate'); return; }
        fetchSummary();
    }, [_hasHydrated, isAuthenticated, user, router, fetchSummary]);

    const handleReturnToDashboard = () => {
        terminate(); // Clear interview store
        router.push('/candidate');
    };

    // â”€â”€â”€ Loading â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
                    <p className="text-gray-500 text-sm">Generating your resultsâ€¦</p>
                </div>
            </div>
        );
    }

    // â”€â”€â”€ Error â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if (error || !summary) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 gap-6">
                <div className="bg-white rounded-xl shadow-sm border border-red-200 p-8 max-w-md w-full text-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-red-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                    </svg>
                    <h2 className="text-lg font-semibold text-gray-800 mb-1">Could not load summary</h2>
                    <p className="text-sm text-gray-500 mb-5">{error || 'No summary data available.'}</p>
                    <button
                        onClick={handleReturnToDashboard}
                        className="px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors"
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    const rec = RECOMMENDATION_CONFIG[summary.recommendation] ?? RECOMMENDATION_CONFIG.REVIEW;
    const risk = FRAUD_RISK_CONFIG[summary.fraud_risk] ?? FRAUD_RISK_CONFIG.LOW;
    const completedDisplay = summary.completed_at
        ? new Date(summary.completed_at).toLocaleString(undefined, { dateStyle: 'full', timeStyle: 'short' })
        : null;

    // â”€â”€â”€ Render â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 shadow-sm">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-bold text-gray-900">Interview Complete</h1>
                        <p className="text-sm text-gray-500 mt-0.5">Your results are ready</p>
                    </div>
                    {completedDisplay && (
                        <span className="text-xs text-gray-400 hidden sm:block">{completedDisplay}</span>
                    )}
                </div>
            </header>

            <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">

                {/* Score + Recommendation Card */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex flex-col sm:flex-row items-center gap-8">
                        {/* Ring */}
                        <div className="flex-shrink-0 flex flex-col items-center gap-2">
                            <ScoreRing score={summary.final_score} />
                            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Overall Score</p>
                        </div>

                        {/* Details */}
                        <div className="flex-1 space-y-4 w-full">
                            {/* Recommendation badge */}
                            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-semibold ${rec.bg} ${rec.text} ${rec.border}`}>
                                <span className={`w-2 h-2 rounded-full ${rec.dot}`} />
                                {rec.label}
                            </div>

                            {/* Notes */}
                            <p className="text-sm text-gray-600 leading-relaxed">{summary.notes}</p>

                            {/* Integrity */}
                            <div className="flex items-center gap-2 text-sm">
                                <span className="text-gray-500">Integrity Check:</span>
                                <span className={`font-semibold ${risk.color}`}>{risk.label}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Strengths & Gaps */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Strengths */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                        <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2 mb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-emerald-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                            </svg>
                            Strengths
                        </h2>
                        <ul className="space-y-2">
                            {summary.strengths.map((s, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
                                    {s}
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Areas to Improve */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                        <h2 className="text-sm font-semibold text-gray-900 flex items-center gap-2 mb-3">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-amber-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                            </svg>
                            Areas to Improve
                        </h2>
                        <ul className="space-y-2">
                            {summary.gaps.map((g, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                                    {g}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* What happens next */}
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
                    <div className="flex items-start gap-3">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                        </svg>
                        <div>
                            <p className="text-sm font-semibold text-blue-800 mb-0.5">What happens next?</p>
                            <p className="text-sm text-blue-700">
                                Your recruiter will review your results and reach out with next steps. Thank you for completing your interview!
                            </p>
                        </div>
                    </div>
                </div>

                {/* CTA */}
                <div className="flex justify-center pb-4">
                    <button
                        onClick={handleReturnToDashboard}
                        className="flex items-center gap-2 px-8 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-sm"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
                        </svg>
                        Return to Dashboard
                    </button>
                </div>
            </main>
        </div>
    );
}
