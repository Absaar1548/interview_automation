'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function CandidatePage() {
    const router = useRouter();
    const [user, setUser] = useState<{ username: string; role: string } | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [hasActiveSession, setHasActiveSession] = useState(false);

    useEffect(() => {
        // Check if user is logged in
        const storedUser = localStorage.getItem('user');
        if (!storedUser) {
            router.push('/login');
            return;
        }

        const userData = JSON.parse(storedUser);
        setUser(userData);

        // Check if there's an active interview session
        const interviewId = localStorage.getItem('interview_id');
        setHasActiveSession(!!interviewId);
    }, [router]);

    const handleStartInterview = async () => {
        setError('');
        setLoading(true);

        try {
            const response = await fetch('http://localhost:8000/api/v1/dev/bootstrap', {
                method: 'GET',
            });

            if (!response.ok) {
                throw new Error('Failed to create interview session');
            }

            const data = await response.json();

            // Store interview details
            localStorage.setItem('interview_id', data.interview_id);
            localStorage.setItem('candidate_token', data.candidate_token);

            // Navigate to interview page
            router.push('/interview');
        } catch (err: any) {
            setError(err.message || 'Failed to start interview');
        } finally {
            setLoading(false);
        }
    };

    const handleResumeInterview = () => {
        router.push('/interview');
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('interview_id');
        localStorage.removeItem('candidate_token');
        router.push('/login');
    };

    if (!user) {
        return null; // Will redirect to login
    }

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-gray-900 p-4">
            <div className="w-full max-w-2xl bg-gray-800 border border-gray-700 rounded-2xl shadow-xl overflow-hidden">
                <div className="p-8">
                    {/* Header */}
                    <div className="flex justify-between items-start mb-8">
                        <div>
                            <h1 className="text-3xl font-bold text-white mb-2">Candidate Dashboard</h1>
                            <p className="text-gray-400">Welcome, {user.username}!</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
                        >
                            Logout
                        </button>
                    </div>

                    {/* Interview Status Card */}
                    <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6 mb-6">
                        <h2 className="text-xl font-semibold text-white mb-4">Interview Status</h2>

                        {hasActiveSession ? (
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-gray-300 mb-1">You have an active interview session</p>
                                        <p className="text-sm text-gray-500">Resume your interview to continue</p>
                                    </div>
                                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                                </div>
                                <button
                                    onClick={handleResumeInterview}
                                    className="w-full py-3 px-4 bg-green-600 text-white rounded-lg font-bold shadow-lg hover:bg-green-700 transition-all duration-200 transform hover:-translate-y-0.5"
                                >
                                    Resume Interview
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-gray-300 mb-1">No active interview session</p>
                                        <p className="text-sm text-gray-500">Start a new interview when you're ready</p>
                                    </div>
                                    <div className="w-3 h-3 bg-gray-600 rounded-full"></div>
                                </div>
                                <button
                                    onClick={handleStartInterview}
                                    disabled={loading}
                                    className={`w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-bold shadow-lg hover:bg-blue-700 transition-all duration-200 transform hover:-translate-y-0.5 ${loading ? 'opacity-70 cursor-not-allowed' : ''
                                        }`}
                                >
                                    {loading ? (
                                        <div className="flex items-center justify-center">
                                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                            </svg>
                                            Creating Session...
                                        </div>
                                    ) : (
                                        'Start New Interview'
                                    )}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Error Display */}
                    {error && (
                        <div className="p-3 rounded-lg bg-red-900/50 border border-red-800 text-red-200 text-sm text-center">
                            {error}
                        </div>
                    )}

                    {/* Info Section */}
                    <div className="bg-blue-900/20 border border-blue-800/30 rounded-lg p-4 mt-6">
                        <div className="flex items-start">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 text-blue-400 mt-0.5 mr-3 flex-shrink-0">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                            </svg>
                            <div>
                                <h3 className="text-sm font-semibold text-blue-300 mb-1">Interview Guidelines</h3>
                                <ul className="text-sm text-blue-200/80 space-y-1">
                                    <li>• Ensure you have a stable internet connection</li>
                                    <li>• Find a quiet environment with good lighting</li>
                                    <li>• Have your camera and microphone ready</li>
                                    <li>• You can pause and resume your interview anytime</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
