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

export default function HRDashboardPage() {
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
            router.push('/login');
            return;
        }

        const parsedUser = JSON.parse(storedUser);
        if (parsedUser.role !== 'hr') {
            // Redirect non-HR users
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
        router.push('/login');
    };

    if (loading && !user) return <div className="min-h-screen bg-gray-900 flex items-center justify-center text-white">Loading...</div>;

    return (
        <div className="min-h-screen w-full bg-gray-900 text-gray-100 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white">HR Dashboard</h1>
                        <p className="text-gray-400">Overview of interview process and candidates</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <span className="text-sm text-gray-400">Welcome, {user?.username}</span>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
                        >
                            Logout
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-900/50 border border-red-800 text-red-200 p-4 rounded-lg mb-8">
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
                <div className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden shadow-xl">
                    <div className="p-6 border-b border-gray-700">
                        <h2 className="text-xl font-semibold text-white">Recent Interviews</h2>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="bg-gray-750 text-gray-400 uppercase text-xs">
                                <tr>
                                    <th className="px-6 py-4 font-medium">Candidate Token</th>
                                    <th className="px-6 py-4 font-medium">Interview ID</th>
                                    <th className="px-6 py-4 font-medium">Date</th>
                                    <th className="px-6 py-4 font-medium">Status</th>
                                    <th className="px-6 py-4 font-medium text-center">Trust Score</th>
                                    <th className="px-6 py-4 font-medium text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-700">
                                {interviews.length === 0 ? (
                                    <tr>
                                        <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                                            No interviews found.
                                        </td>
                                    </tr>
                                ) : (
                                    interviews.map((interview) => (
                                        <tr key={interview.interview_id} className="hover:bg-gray-700/50 transition-colors">
                                            <td className="px-6 py-4 font-medium text-white">{interview.candidate_token}</td>
                                            <td className="px-6 py-4 text-gray-400 text-sm font-mono">{interview.interview_id.substring(0, 8)}...</td>
                                            <td className="px-6 py-4 text-gray-400">
                                                {new Date(interview.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4">
                                                <StatusBadge status={interview.state} />
                                            </td>
                                            <td className="px-6 py-4 text-center">
                                                <div className="flex items-center justify-center gap-2">
                                                    <span className={`font-bold ${interview.cheat_score > 50 ? 'text-red-400' : 'text-green-400'}`}>
                                                        {Math.max(0, 100 - interview.cheat_score)}%
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
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
    const colorClasses = {
        blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
        green: "bg-green-500/10 text-green-400 border-green-500/20",
        yellow: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
        red: "bg-red-500/10 text-red-400 border-red-500/20",
    };

    // Fallback if color is not found
    const activeClass = colorClasses[color as keyof typeof colorClasses] || colorClasses.blue;

    return (
        <div className={`rounded-xl p-6 border ${activeClass}`}>
            <h3 className="text-sm font-medium opacity-80 mb-1">{title}</h3>
            <p className="text-3xl font-bold">{value}</p>
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    let classes = "bg-gray-700 text-gray-300";
    if (status === 'COMPLETED') classes = "bg-green-900/30 text-green-400 border border-green-800";
    else if (status === 'IN_PROGRESS') classes = "bg-blue-900/30 text-blue-400 border border-blue-800";
    else if (status === 'TERMINATED') classes = "bg-red-900/30 text-red-400 border border-red-800";
    else if (status === 'CREATED' || status === 'READY') classes = "bg-yellow-900/30 text-yellow-400 border border-yellow-800";

    return (
        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${classes}`}>
            {status}
        </span>
    );
}
