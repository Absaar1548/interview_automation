'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface DashboardStats {
    total_interviews: number;
    completed: number;
    pending: number;
    flagged: number;
}

interface InterviewSummary {
    interview_id: string;
    candidate_token: string;
    state: string;
    cheat_score: number;
    created_at: string;
}

export default function AdminDashboardPage() {
    const router = useRouter();
    const [user, setUser] = useState<{ username: string; role: string } | null>(null);
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [interviews, setInterviews] = useState<InterviewSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        // Check auth
        const storedUser = localStorage.getItem('user');
        if (!storedUser) {
            router.push('/login/admin');
            return;
        }

        const parsedUser = JSON.parse(storedUser);
        if (parsedUser.role !== 'admin' && parsedUser.role !== 'hr') {
            // Redirect non-Admin/HR users
            router.push(parsedUser.role === 'candidate' ? '/candidate' : '/login');
            return;
        }

        setUser(parsedUser);
        fetchData();
    }, [router]);

    const fetchData = async () => {
        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

            const [statsRes, interviewsRes] = await Promise.all([
                fetch(`${baseUrl}/api/v1/dashboard/stats`),
                fetch(`${baseUrl}/api/v1/dashboard/interviews`)
            ]);

            if (!statsRes.ok || !interviewsRes.ok) {
                throw new Error('Failed to fetch dashboard data');
            }

            const statsData = await statsRes.json();
            const interviewsData = await interviewsRes.json();

            setStats(statsData);
            setInterviews(interviewsData);
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('interview_id');
        router.push('/login/admin');
    };

    if (loading && !user) return <div className="min-h-screen flex items-center justify-center text-gray-600">Loading...</div>;

    return (
        <div className="min-h-screen w-full p-8 relative">
            {/* Background elements for glass effect - fixed position to stay behind scrollable content */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
                <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] bg-pink-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
            </div>

            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-center mb-8 glass-card p-6 rounded-2xl">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">Admin Dashboard</h1>
                        <p className="text-gray-600">Overview of interview process and candidates</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-sm font-medium text-gray-600">Welcome, {user?.username}</span>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-white/80 border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors shadow-sm font-medium"
                        >
                            Logout
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-50/80 backdrop-blur-sm border border-red-100 text-red-700 p-4 rounded-2xl mb-8 shadow-sm">
                        {error}
                    </div>
                )}

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <StatsCard title="Total Interviews" value={stats?.total_interviews || 0} color="blue" />
                    <StatsCard title="Completed" value={stats?.completed || 0} color="green" />
                    <StatsCard title="Pending Review" value={stats?.pending || 0} color="yellow" />
                    <StatsCard title="Flagged for Fraud" value={stats?.flagged || 0} color="red" />
                </div>

                {/* Interviews Table */}
                <div className="glass-card rounded-2xl overflow-hidden shadow-lg border border-white/20">
                    <div className="p-6 border-b border-gray-100 bg-white/40">
                        <h2 className="text-xl font-bold text-gray-800">Recent Interviews</h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-gray-50/50 text-gray-500 uppercase text-xs font-semibold">
                                <tr>
                                    <th className="px-6 py-4">Candidate Token</th>
                                    <th className="px-6 py-4">Interview ID</th>
                                    <th className="px-6 py-4">Date</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4 text-center">Trust Score</th>
                                    <th className="px-6 py-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {interviews.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                                            No interviews found.
                                        </td>
                                    </tr>
                                ) : (
                                    interviews.map((interview) => (
                                        <tr key={interview.interview_id} className="hover:bg-blue-50/30 transition-colors">
                                            <td className="px-6 py-4 font-medium text-gray-900">{interview.candidate_token}</td>
                                            <td className="px-6 py-4 text-gray-500 text-sm font-mono">{interview.interview_id.substring(0, 8)}...</td>
                                            <td className="px-6 py-4 text-gray-600">
                                                {new Date(interview.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4">
                                                <StatusBadge status={interview.state} />
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <div className="flex items-center justify-center gap-2">
                                                    <span className={`font-bold px-2 py-1 rounded-lg ${interview.cheat_score > 50 ? 'bg-red-100/50 text-red-600' : 'bg-green-100/50 text-green-600'}`}>
                                                        {Math.max(0, 100 - interview.cheat_score)}%
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button className="text-blue-600 hover:text-blue-800 text-sm font-semibold hover:underline">
                                                    View Report
                                                </button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}

function StatsCard({ title, value, color }: { title: string, value: number, color: string }) {
    return (
        <div className={`glass-card rounded-2xl p-6 border border-white/20 transition-transform hover:-translate-y-1`}>
            <h3 className="text-sm font-semibold opacity-70 mb-1 text-gray-600">{title}</h3>
            <p className="text-3xl font-bold text-gray-800">{value}</p>
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    let classes = "bg-gray-100/50 text-gray-600 border-gray-200";
    if (status === 'COMPLETED') classes = "bg-green-50/50 text-green-700 border border-green-100";
    else if (status === 'IN_PROGRESS') classes = "bg-blue-50/50 text-blue-700 border border-blue-100";
    else if (status === 'TERMINATED') classes = "bg-red-50/50 text-red-700 border border-red-100";
    else if (status === 'CREATED' || status === 'READY') classes = "bg-yellow-50/50 text-yellow-700 border border-yellow-100";

    return (
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold shadow-sm backdrop-blur-sm ${classes}`}>
            {status}
        </span>
    );
}
