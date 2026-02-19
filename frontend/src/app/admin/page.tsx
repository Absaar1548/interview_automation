'use client';

/* eslint-disable @typescript-eslint/no-unused-vars */
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/lib/authService';
import { dashboardService } from '@/lib/dashboardService';
import { CandidateResponse } from '@/types/api';

interface DashboardStats {
    total_interviews: number;
    completed: number;
    pending: number;
    flagged: number;
}

export default function AdminDashboardPage() {
    const router = useRouter();
    const { user, isAuthenticated, logout } = useAuthStore();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [candidates, setCandidates] = useState<CandidateResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Registration modal state
    const [showRegisterModal, setShowRegisterModal] = useState(false);
    const [registerLoading, setRegisterLoading] = useState(false);
    const [registerError, setRegisterError] = useState('');
    const [registerSuccess, setRegisterSuccess] = useState('');

    // New Form State excluding password
    const [candidateName, setCandidateName] = useState('');
    const [email, setEmail] = useState('');
    const [jobDescription, setJobDescription] = useState('');
    const [resumeFile, setResumeFile] = useState<File | null>(null);

    useEffect(() => {
        if (!isAuthenticated || !user) {
            router.push('/login/admin');
            return;
        }

        if (user.role !== 'admin' && user.role !== 'hr') {
            router.push(user.role === 'candidate' ? '/candidate' : '/login/admin');
            return;
        }

        fetchData();
    }, [isAuthenticated, user, router]);

    const fetchData = async () => {
        try {
            // Fetch stats (mocked for now or existing) and now Candidates list
            const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

            // Parallel fetch
            const [statsRes, candidatesData] = await Promise.all([
                fetch(`${baseUrl}/api/v1/dashboard/stats`).then(res => res.ok ? res.json() : { total_interviews: 0, completed: 0, pending: 0, flagged: 0 }),
                dashboardService.getCandidates()
            ]);

            setStats(statsRes);
            setCandidates(candidatesData);

        } catch (err: any) {
            console.error("Fetch error:", err);
            setError(err.message || 'An error occurred while fetching dashboard data');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        router.push('/login/admin');
    };

    const handleRegisterCandidate = async (e: React.FormEvent) => {
        e.preventDefault();
        setRegisterError('');
        setRegisterSuccess('');

        // Validation
        if (!candidateName || !email || !jobDescription || !resumeFile) {
            setRegisterError('All fields (Name, Email, JD, Resume) are required');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            setRegisterError('Please enter a valid email address');
            return;
        }

        setRegisterLoading(true);

        try {
            const formData = new FormData();
            formData.append('candidate_name', candidateName);
            formData.append('candidate_email', email);
            formData.append('job_description', jobDescription);
            formData.append('resume', resumeFile);

            await authService.registerCandidateWithResume(formData);

            setRegisterSuccess(`Candidate "${candidateName}" registered successfully! Password sent via email.`);

            // Reset form
            setCandidateName('');
            setEmail('');
            setJobDescription('');
            setResumeFile(null);

            // Refresh list
            fetchData();

            setTimeout(() => {
                setShowRegisterModal(false);
                setRegisterSuccess('');
            }, 3000);
        } catch (err: any) {
            let message = 'Registration failed. Please try again.';
            if (err.message) {
                message = err.message;
            }
            setRegisterError(message);
        } finally {
            setRegisterLoading(false);
        }
    };

    const handleToggleLogin = async (candidateId: string) => {
        if (!confirm("Are you sure you want to toggle login access for this candidate?")) return;

        try {
            const response = await dashboardService.toggleCandidateLogin(candidateId);
            // Update local state
            setCandidates(prev => prev.map(c =>
                c.id === candidateId ? { ...c, login_disabled: response.login_disabled } : c
            ));
        } catch (err: any) {
            alert(err.message || "Failed to toggle login status");
        }
    };

    const openRegisterModal = () => {
        setShowRegisterModal(true);
        setRegisterError('');
        setRegisterSuccess('');
        setCandidateName('');
        setEmail('');
        setJobDescription('');
        setResumeFile(null);
    };

    if (loading && !user) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                            <p className="text-sm text-gray-600 mt-1">Welcome, {user?.username}</p>
                        </div>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={openRegisterModal}
                                className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2 shadow-sm"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                                </svg>
                                Register Candidate
                            </button>
                            <button
                                onClick={handleLogout}
                                className="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {error && (
                    <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
                        {error}
                    </div>
                )}

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <h3 className="text-sm font-medium text-gray-600 mb-1">Total Interviews</h3>
                        <p className="text-3xl font-bold text-gray-900">{stats?.total_interviews || 0}</p>
                    </div>
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <h3 className="text-sm font-medium text-gray-600 mb-1">Completed</h3>
                        <p className="text-3xl font-bold text-green-600">{stats?.completed || 0}</p>
                    </div>
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <h3 className="text-sm font-medium text-gray-600 mb-1">Pending Review</h3>
                        <p className="text-3xl font-bold text-yellow-600">{stats?.pending || 0}</p>
                    </div>
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <h3 className="text-sm font-medium text-gray-600 mb-1">Registered Candidates</h3>
                        <p className="text-3xl font-bold text-blue-600">{candidates.length}</p>
                    </div>
                </div>

                {/* Candidates Table */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                        <h2 className="text-lg font-semibold text-gray-900">Registered Candidates</h2>
                        <button onClick={fetchData} className="text-sm text-blue-600 hover:text-blue-800">Refresh List</button>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name / Username</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Login Access</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Joined</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {candidates.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                                            No candidates found.
                                        </td>
                                    </tr>
                                ) : (
                                    candidates.map((candidate) => (
                                        <tr key={candidate.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {candidate.username}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {candidate.email}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${candidate.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                                    {candidate.is_active ? 'Active' : 'Inactive'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${!candidate.login_disabled ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}>
                                                    {!candidate.login_disabled ? 'Enabled' : 'Disabled'}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {new Date(candidate.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                                                <button
                                                    onClick={() => handleToggleLogin(candidate.id)}
                                                    className={`font-medium mr-4 ${candidate.login_disabled ? 'text-green-600 hover:text-green-800' : 'text-orange-600 hover:text-orange-800'}`}
                                                >
                                                    {candidate.login_disabled ? 'Enable Login' : 'Disable Login'}
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>

            {/* Registration Modal */}
            {showRegisterModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg w-full max-w-md p-6 shadow-xl max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-gray-900">Register New Candidate</h2>
                            <button
                                onClick={() => setShowRegisterModal(false)}
                                className="text-gray-400 hover:text-gray-600"
                                disabled={registerLoading}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>

                        {registerSuccess && (
                            <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                                </svg>
                                {registerSuccess}
                            </div>
                        )}

                        {registerError && (
                            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                                </svg>
                                {registerError}
                            </div>
                        )}

                        <form onSubmit={handleRegisterCandidate} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Candidate Name</label>
                                <input
                                    type="text"
                                    value={candidateName}
                                    onChange={(e) => setCandidateName(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="Full Name"
                                    required
                                    disabled={registerLoading}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="Enter email address"
                                    required
                                    disabled={registerLoading}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Job Description</label>
                                <textarea
                                    value={jobDescription}
                                    onChange={(e) => setJobDescription(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="Paste Job Description here..."
                                    rows={3}
                                    required
                                    disabled={registerLoading}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Resume (PDF/Doc)</label>
                                <input
                                    type="file"
                                    onChange={(e) => setResumeFile(e.target.files ? e.target.files[0] : null)}
                                    className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                                    accept=".pdf,.doc,.docx"
                                    required
                                    disabled={registerLoading}
                                />
                                {resumeFile && (
                                    <p className="mt-1 text-xs text-green-600">Selected: {resumeFile.name}</p>
                                )}
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setShowRegisterModal(false)}
                                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                                    disabled={registerLoading}
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={registerLoading}
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                >
                                    {registerLoading ? (
                                        <>
                                            <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            Processing...
                                        </>
                                    ) : (
                                        'Register Candidate'
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

// Helper badge component
function StatusBadge({ status }: { status: string }) {
    let classes = "px-2.5 py-0.5 rounded-full text-xs font-semibold";
    if (status === 'COMPLETED') classes += " bg-green-100 text-green-800";
    else if (status === 'IN_PROGRESS') classes += " bg-blue-100 text-blue-800";
    else if (status === 'TERMINATED') classes += " bg-red-100 text-red-800";
    else classes += " bg-gray-100 text-gray-800";
    return <span className={classes}>{status}</span>;
}
