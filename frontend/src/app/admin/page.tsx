'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/lib/authService';
import { dashboardService } from '@/lib/dashboardService';
import {
    cancelInterview,
    fetchInterviewSummary,
    InterviewSummaryItem,
    SchedulingApiError,
} from '@/lib/api/interviews';
import { CandidateResponse } from '@/types/api';
import ScheduleInterviewModal from '@/components/admin/ScheduleInterviewModal';
import CancelInterviewDialog from '@/components/admin/CancelInterviewDialog';
import { Toast, useToast } from '@/components/ui/Toast';

// ─── Types ────────────────────────────────────────────────────────────────────

interface DashboardStats {
    total_interviews: number;
    completed: number;
    pending: number;
    flagged: number;
}

interface CandidateRow extends CandidateResponse {
    summary: InterviewSummaryItem | null;
}

// ─── Status badge ─────────────────────────────────────────────────────────────

const STATUS_STYLES: Record<string, string> = {
    scheduled: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-gray-100 text-gray-600',
    none: 'bg-slate-100 text-slate-500',
};

const STATUS_LABELS: Record<string, string> = {
    scheduled: 'Scheduled',
    in_progress: 'In Progress',
    completed: 'Completed',
    cancelled: 'Cancelled',
    none: 'No Interview',
};

function InterviewStatusBadge({ status }: { status: string }) {
    const key = status in STATUS_STYLES ? status : 'none';
    return (
        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap ${STATUS_STYLES[key]}`}>
            {STATUS_LABELS[key]}
        </span>
    );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function AdminDashboardPage() {
    const router = useRouter();
    const { user, isAuthenticated, logout } = useAuthStore();
    const toast = useToast();

    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [candidates, setCandidates] = useState<CandidateRow[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // ── Register modal ────────────────────────────────────────────────────────
    const [showRegisterModal, setShowRegisterModal] = useState(false);
    const [registerLoading, setRegisterLoading] = useState(false);
    const [registerError, setRegisterError] = useState('');
    const [registerSuccess, setRegisterSuccess] = useState('');
    const [candidateName, setCandidateName] = useState('');
    const [email, setEmail] = useState('');
    const [jobDescription, setJobDescription] = useState('');
    const [resumeFile, setResumeFile] = useState<File | null>(null);

    // ── Schedule / Reschedule ─────────────────────────────────────────────────
    const [scheduleTarget, setScheduleTarget] = useState<CandidateRow | null>(null);
    const [scheduleMode, setScheduleMode] = useState<'schedule' | 'reschedule'>('schedule');

    // ── Cancel ────────────────────────────────────────────────────────────────
    const [cancelTarget, setCancelTarget] = useState<CandidateRow | null>(null);
    const [cancelLoading, setCancelLoading] = useState(false);

    // ─── Auth guard ───────────────────────────────────────────────────────────
    useEffect(() => {
        if (!isAuthenticated || !user) { router.push('/login/admin'); return; }
        if (user.role !== 'admin' && user.role !== 'hr') {
            router.push(user.role === 'candidate' ? '/candidate' : '/login/admin');
            return;
        }
        fetchData();
    }, [isAuthenticated, user, router]);

    // ─── Fetch all data + build merged rows ──────────────────────────────────
    const fetchData = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

            const [statsRes, candidatesData, summaryData] = await Promise.all([
                fetch(`${baseUrl}/api/v1/dashboard/stats`).then(r =>
                    r.ok ? r.json() : { total_interviews: 0, completed: 0, pending: 0, flagged: 0 }
                ),
                dashboardService.getCandidates(),
                fetchInterviewSummary().catch(() => [] as InterviewSummaryItem[]),
            ]);

            setStats(statsRes);

            // Build a map: candidate_id → most-relevant interview summary
            // Priority: scheduled > in_progress > completed > cancelled
            const PRIORITY: Record<string, number> = {
                scheduled: 4, in_progress: 3, completed: 2, cancelled: 1,
            };
            const summaryMap = new Map<string, InterviewSummaryItem>();
            for (const item of summaryData as InterviewSummaryItem[]) {
                const existing = summaryMap.get(item.candidate_id);
                if (!existing || (PRIORITY[item.status] ?? 0) > (PRIORITY[existing.status] ?? 0)) {
                    summaryMap.set(item.candidate_id, item);
                }
            }

            const rows: CandidateRow[] = candidatesData.map(c => ({
                ...c,
                summary: summaryMap.get(c.id) ?? null,
            }));
            setCandidates(rows);
        } catch (err: any) {
            setError(err.message || 'Failed to load dashboard data.');
        } finally {
            setLoading(false);
        }
    }, []);

    // ─── Handlers ─────────────────────────────────────────────────────────────

    const handleLogout = () => { logout(); router.push('/login/admin'); };
    const handleAuthError = () => { logout(); router.push('/login/admin'); };

    const handleToggleLogin = async (candidateId: string) => {
        if (!confirm('Toggle login access for this candidate?')) return;
        try {
            const response = await dashboardService.toggleCandidateLogin(candidateId);
            setCandidates(prev =>
                prev.map(c => c.id === candidateId ? { ...c, login_disabled: response.login_disabled } : c)
            );
            toast.success(response.login_disabled ? 'Login disabled.' : 'Login enabled.');
        } catch (err: any) {
            toast.error(err.message || 'Failed to toggle login status.');
        }
    };

    const onScheduleSuccess = () => {
        setScheduleTarget(null);
        toast.success(scheduleMode === 'schedule' ? 'Interview scheduled!' : 'Interview rescheduled!');
        fetchData();
    };

    const handleConfirmCancel = async () => {
        if (!cancelTarget?.summary) return;
        setCancelLoading(true);
        try {
            await cancelInterview(cancelTarget.summary.interview_id);
            toast.success('Interview cancelled.');
            setCancelTarget(null);
            fetchData();
        } catch (err: any) {
            const apiErr = err as SchedulingApiError;
            if (apiErr.status === 401 || apiErr.status === 403) { handleAuthError(); return; }
            toast.error(apiErr.detail || 'Failed to cancel interview.');
        } finally {
            setCancelLoading(false);
        }
    };

    const openRegisterModal = () => {
        setShowRegisterModal(true);
        setRegisterError(''); setRegisterSuccess('');
        setCandidateName(''); setEmail(''); setJobDescription(''); setResumeFile(null);
    };

    const handleRegisterCandidate = async (e: React.FormEvent) => {
        e.preventDefault();
        setRegisterError(''); setRegisterSuccess('');
        if (!candidateName || !email || !jobDescription || !resumeFile) {
            setRegisterError('All fields (Name, Email, JD, Resume) are required.'); return;
        }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            setRegisterError('Please enter a valid email address.'); return;
        }
        setRegisterLoading(true);
        try {
            const formData = new FormData();
            formData.append('candidate_name', candidateName);
            formData.append('candidate_email', email);
            formData.append('job_description', jobDescription);
            formData.append('resume', resumeFile);
            await authService.registerCandidateWithResume(formData);
            setRegisterSuccess(`"${candidateName}" registered! Password sent via email.`);
            fetchData();
            setTimeout(() => { setShowRegisterModal(false); setRegisterSuccess(''); }, 3000);
        } catch (err: any) {
            setRegisterError(err.message || 'Registration failed. Please try again.');
        } finally {
            setRegisterLoading(false);
        }
    };

    // ─── Render ───────────────────────────────────────────────────────────────

    if (loading && candidates.length === 0) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
                    <p className="text-gray-600">Loading dashboard…</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            <Toast toasts={toast.toasts} onDismiss={toast.dismiss} />

            {/* Header */}
            <header className="bg-white shadow-sm border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                            <p className="text-sm text-gray-600 mt-0.5">Welcome, {user?.username}</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={openRegisterModal}
                                className="px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2 shadow-sm text-sm"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                                </svg>
                                Register Candidate
                            </button>
                            <button onClick={handleLogout} className="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium text-sm">
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {error && (
                    <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
                )}

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    {[
                        { label: 'Total Interviews', value: stats?.total_interviews ?? 0, color: 'text-gray-900' },
                        { label: 'Completed', value: stats?.completed ?? 0, color: 'text-green-600' },
                        { label: 'Pending Review', value: stats?.pending ?? 0, color: 'text-yellow-600' },
                        { label: 'Candidates', value: candidates.length, color: 'text-blue-600' },
                    ].map(s => (
                        <div key={s.label} className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
                            <p className="text-xs font-medium text-gray-500 mb-1">{s.label}</p>
                            <p className={`text-3xl font-bold ${s.color}`}>{s.value}</p>
                        </div>
                    ))}
                </div>

                {/* Candidates table */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                        <h2 className="text-lg font-semibold text-gray-900">Registered Candidates</h2>
                        <button onClick={fetchData} disabled={loading} className="text-sm text-blue-600 hover:text-blue-800 font-medium disabled:opacity-50">
                            {loading ? 'Refreshing…' : '↻ Refresh'}
                        </button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50 text-xs uppercase tracking-wider text-gray-500">
                                <tr>
                                    <th className="px-6 py-3 text-left">Name</th>
                                    <th className="px-6 py-3 text-left">Email</th>
                                    <th className="px-6 py-3 text-left">Interview Status</th>
                                    <th className="px-6 py-3 text-left">Scheduled At</th>
                                    <th className="px-6 py-3 text-left">Login</th>
                                    <th className="px-6 py-3 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {candidates.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-10 text-center text-gray-400">No candidates found.</td>
                                    </tr>
                                ) : (
                                    candidates.map(candidate => {
                                        const s = candidate.summary;
                                        const ivStatus = s?.status ?? 'none';
                                        const canReschedule = ivStatus === 'scheduled';
                                        const canCancel = s && ivStatus !== 'completed' && ivStatus !== 'cancelled';
                                        const canSchedule = !s || ivStatus === 'cancelled' || ivStatus === 'completed';

                                        return (
                                            <tr key={candidate.id} className="hover:bg-gray-50 transition-colors">
                                                <td className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">{candidate.username}</td>
                                                <td className="px-6 py-4 text-gray-500 whitespace-nowrap">{candidate.email}</td>
                                                <td className="px-6 py-4"><InterviewStatusBadge status={ivStatus} /></td>
                                                <td className="px-6 py-4 text-gray-500 whitespace-nowrap">
                                                    {s?.scheduled_at ? new Date(s.scheduled_at).toLocaleString() : '—'}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${!candidate.login_disabled ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-600'}`}>
                                                        {!candidate.login_disabled ? 'Enabled' : 'Disabled'}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 text-right whitespace-nowrap">
                                                    <div className="flex items-center justify-end gap-2">
                                                        {canSchedule && (
                                                            <button
                                                                onClick={() => { setScheduleMode('schedule'); setScheduleTarget(candidate); }}
                                                                className="px-3 py-1.5 bg-blue-600 text-white rounded-md text-xs font-semibold hover:bg-blue-700 transition-colors"
                                                            >
                                                                Schedule
                                                            </button>
                                                        )}
                                                        {canReschedule && (
                                                            <button
                                                                onClick={() => { setScheduleMode('reschedule'); setScheduleTarget(candidate); }}
                                                                className="px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded-md text-xs font-semibold hover:bg-indigo-200 transition-colors"
                                                            >
                                                                Reschedule
                                                            </button>
                                                        )}
                                                        {canCancel && (
                                                            <button
                                                                onClick={() => setCancelTarget(candidate)}
                                                                className="px-3 py-1.5 bg-red-50 text-red-700 rounded-md text-xs font-semibold hover:bg-red-100 transition-colors"
                                                            >
                                                                Cancel
                                                            </button>
                                                        )}
                                                        <button
                                                            onClick={() => handleToggleLogin(candidate.id)}
                                                            className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${candidate.login_disabled ? 'bg-green-50 text-green-700 hover:bg-green-100' : 'bg-orange-50 text-orange-700 hover:bg-orange-100'}`}
                                                        >
                                                            {candidate.login_disabled ? 'Enable Login' : 'Disable Login'}
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>

            {/* Schedule / Reschedule Modal */}
            {scheduleTarget && (
                <ScheduleInterviewModal
                    mode={scheduleMode}
                    candidateId={scheduleTarget.id}
                    candidateName={scheduleTarget.username}
                    interviewId={scheduleTarget.summary?.interview_id}
                    existingScheduledAt={scheduleTarget.summary?.scheduled_at ?? undefined}
                    onClose={() => setScheduleTarget(null)}
                    onSuccess={onScheduleSuccess}
                    onAuthError={handleAuthError}
                />
            )}

            {/* Cancel Dialog */}
            {cancelTarget && (
                <CancelInterviewDialog
                    candidateName={cancelTarget.username}
                    onConfirm={handleConfirmCancel}
                    onCancel={() => setCancelTarget(null)}
                    loading={cancelLoading}
                />
            )}

            {/* Register Modal */}
            {showRegisterModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl w-full max-w-md p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-5">
                            <h2 className="text-xl font-bold text-gray-900">Register New Candidate</h2>
                            <button onClick={() => setShowRegisterModal(false)} disabled={registerLoading} className="text-gray-400 hover:text-gray-600">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        {registerSuccess && <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm">{registerSuccess}</div>}
                        {registerError && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{registerError}</div>}

                        <form onSubmit={handleRegisterCandidate} className="space-y-4">
                            {[
                                { label: 'Candidate Name', value: candidateName, setter: setCandidateName, placeholder: 'Full Name', type: 'text' },
                                { label: 'Email', value: email, setter: setEmail, placeholder: 'Email address', type: 'email' },
                            ].map(({ label, value, setter, placeholder, type }) => (
                                <div key={label}>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
                                    <input
                                        type={type} value={value} onChange={e => setter(e.target.value)}
                                        placeholder={placeholder} required disabled={registerLoading}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            ))}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Job Description</label>
                                <textarea
                                    value={jobDescription} onChange={e => setJobDescription(e.target.value)}
                                    rows={3} placeholder="Paste Job Description here…" required disabled={registerLoading}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Resume (PDF/Doc)</label>
                                <input
                                    type="file" accept=".pdf,.doc,.docx" required disabled={registerLoading}
                                    onChange={e => setResumeFile(e.target.files?.[0] ?? null)}
                                    className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                                />
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button type="button" onClick={() => setShowRegisterModal(false)} disabled={registerLoading} className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium transition-colors disabled:opacity-50">Cancel</button>
                                <button type="submit" disabled={registerLoading} className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-semibold transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
                                    {registerLoading ? (
                                        <><svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>Registering…</>
                                    ) : 'Register Candidate'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
