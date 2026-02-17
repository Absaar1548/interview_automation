"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useInterviewStore } from "@/store/interviewStore";
import { dashboardService, InterviewSummary } from "@/lib/dashboardService";

export default function CandidatePage() {
    const router = useRouter();
    const { user, isAuthenticated, logout } = useAuthStore();
    const initializeInterview = useInterviewStore((s) => s.initialize);

    // State to hold the fetched interview (if any)
    const [interview, setInterview] = useState<InterviewSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // 1. Authentication Check & Data Fetching
    useEffect(() => {
        if (!isAuthenticated) {
            router.push("/login/candidate");
            return;
        }

        const fetchDashboardData = async () => {
            setLoading(true);
            try {
                const interviews = await dashboardService.getInterviews(user?.username);
                if (interviews.length > 0) {
                    setInterview(interviews[0]);
                }
            } catch (err: any) {
                console.error("Dashboard fetch error:", err);
                setError("Failed to load interview details. Please try again later.");
            } finally {
                setLoading(false);
            }
        };

        if (user?.username) {
            fetchDashboardData();
        }
    }, [isAuthenticated, user, router]);

    // 2. Action Handlers
    const handleStartOrResumeInterview = () => {
        if (!interview) return;

        // Initialize the interview store
        initializeInterview(interview.interview_id, interview.candidate_token);

        // Navigate to the interview runtime
        router.push("/interview");
    };

    const handleDebugCreate = async () => {
        if (!user) return;
        setLoading(true);
        try {
            await dashboardService.createSession(user.username);
            // Refresh dashboard
            const interviews = await dashboardService.getInterviews(user.username);
            if (interviews.length > 0) {
                setInterview(interviews[0]);
            }
        } catch (err: any) {
            console.error("Debug create error:", err);
            setError(err.message || "Failed to create debug session. You might have an active one.");
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        router.push("/login/candidate");
    };

    // 3. Render Loading State
    // 3. Render Loading State
    if (loading) {
        return (
            <div className="min-h-screen w-full flex items-center justify-center text-gray-600">
                <div className="flex flex-col items-center">
                    <svg className="animate-spin h-8 w-8 text-blue-500 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p className="text-gray-600">Loading your dashboard...</p>
                </div>
            </div>
        );
    }

    if (!user) return null; // Should have redirected

    const hasActiveSession = !!interview;

    return (
        <div className="min-h-screen w-full flex items-center justify-center p-4 relative">
            {/* Background elements for glass effect */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
                <div className="absolute bottom-[-10%] right-[20%] w-[40%] h-[40%] bg-pink-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>
            </div>

            <div className="w-full max-w-2xl glass-card rounded-2xl shadow-xl overflow-hidden relative z-10 transition-all duration-300 hover:shadow-2xl">
                <div className="p-8">
                    {/* Header */}
                    <div className="flex justify-between items-start mb-8 border-b border-gray-100 pb-6">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800 mb-2">Candidate Dashboard</h1>
                            <p className="text-gray-600 font-medium">Welcome, {user.username}!</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-white/50 hover:bg-white text-gray-700 border border-gray-200 rounded-xl transition-all shadow-sm font-medium hover:shadow-md"
                        >
                            Logout
                        </button>
                    </div>

                    {/* Interview Status Card */}
                    <div className="bg-white/60 backdrop-blur-md border border-white/40 rounded-2xl p-6 mb-8 shadow-sm">
                        <h2 className="text-xl font-bold text-gray-800 mb-4">Interview Status</h2>

                        {hasActiveSession ? (
                            <div className="space-y-6">
                                <div className="flex items-center justify-between p-4 glass-card border border-white/20 rounded-xl">
                                    <div>
                                        <p className="text-gray-800 font-semibold mb-1">
                                            {interview.state === "COMPLETED"
                                                ? "Interview Completed"
                                                : "You have an active interview session"}
                                        </p>
                                        <p className="text-sm text-gray-500">
                                            {interview.state === "COMPLETED"
                                                ? "Thank you for your participation."
                                                : `Status: ${interview.state}`}
                                        </p>
                                        {interview.state !== "COMPLETED" && (
                                            <p className="text-xs text-mono text-gray-400 mt-1">ID: {interview.interview_id}</p>
                                        )}
                                    </div>
                                    <div className={`w-4 h-4 rounded-full shadow-sm ring-2 ring-offset-2 ${interview.state === "COMPLETED" ? "bg-gray-400 ring-gray-200" : "bg-green-500 ring-green-100 animate-pulse"}`}></div>
                                </div>

                                {interview.state !== "COMPLETED" && (
                                    <button
                                        onClick={handleStartOrResumeInterview}
                                        className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-bold shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 transition-all duration-300 transform hover:-translate-y-0.5 active:scale-[0.98] flex items-center justify-center gap-2"
                                    >
                                        {interview.state === "CREATED" || interview.state === "READY"
                                            ? "Start Interview"
                                            : "Resume Interview"}
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                                        </svg>
                                    </button>
                                )}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div className="flex items-center justify-between p-4 glass-card border border-white/20 rounded-xl">
                                    <div>
                                        <p className="text-gray-600 font-medium mb-1">No active interview session</p>
                                        <p className="text-sm text-gray-400">Contact HR if you believe this is an error.</p>
                                    </div>
                                    <div className="w-3 h-3 bg-gray-300 rounded-full"></div>
                                </div>
                                {/* No button to start manual interview since we auto-schedule */}
                                <div className="p-4 bg-yellow-50/80 border border-yellow-100 rounded-xl text-yellow-700 text-sm flex items-center gap-2">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 flex-shrink-0 text-yellow-500">
                                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                    </svg>
                                    Waiting for interview assignment...
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Error Display */}
                    {error && (
                        <div className="p-4 rounded-xl bg-red-50/80 border border-red-100 text-red-700 text-sm text-center mb-6 shadow-sm backdrop-blur-sm">
                            {error}
                        </div>
                    )}

                    {/* Info Section */}
                    <div className="glass-card border border-white/20 rounded-xl p-5 mt-6">
                        <div className="flex items-start">
                            <div className="p-2 bg-blue-50/50 text-blue-600 rounded-lg mr-3 flex-shrink-0 backdrop-blur-sm">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                                </svg>
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-gray-700 mb-1">Interview Guidelines</h3>
                                <ul className="text-sm text-gray-600 space-y-1.5 mt-2">
                                    <li className="flex items-center gap-2">
                                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                                        Ensure you have a stable internet connection
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                                        Find a quiet environment with good lighting
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                                        Have your camera and microphone ready
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                                        You can pause and resume your interview anytime
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Debug Section */}
                <div className="p-4 bg-gray-50/50 border-t border-gray-100 text-center">
                    <button
                        onClick={handleDebugCreate}
                        className="text-xs text-gray-400 hover:text-gray-600 font-medium transition-colors"
                    >
                        [Debug] Create New Interview Session
                    </button>
                </div>
            </div>
        </div>
    );
}
