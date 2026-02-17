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
            router.push("/login");
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
        router.push("/login");
    };

    // 3. Render Loading State
    if (loading) {
        return (
            <div className="min-h-screen w-full flex items-center justify-center bg-gray-900">
                <div className="flex flex-col items-center">
                    <svg className="animate-spin h-8 w-8 text-blue-500 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p className="text-gray-400">Loading your dashboard...</p>
                </div>
            </div>
        );
    }

    if (!user) return null; // Should have redirected

    const hasActiveSession = !!interview;

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
                                        <p className="text-gray-300 mb-1">
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
                                            <p className="text-xs text-mono text-gray-600 mt-1">ID: {interview.interview_id}</p>
                                        )}
                                    </div>
                                    <div className={`w-3 h-3 rounded-full ${interview.state === "COMPLETED" ? "bg-gray-500" : "bg-green-500 animate-pulse"}`}></div>
                                </div>

                                {interview.state !== "COMPLETED" && (
                                    <button
                                        onClick={handleStartOrResumeInterview}
                                        className="w-full py-3 px-4 bg-green-600 text-white rounded-lg font-bold shadow-lg hover:bg-green-700 transition-all duration-200 transform hover:-translate-y-0.5"
                                    >
                                        {interview.state === "CREATED" || interview.state === "READY"
                                            ? "Start Interview"
                                            : "Resume Interview"}
                                    </button>
                                )}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-gray-300 mb-1">No active interview session</p>
                                        <p className="text-sm text-gray-500">Contact HR if you believe this is an error.</p>
                                    </div>
                                    <div className="w-3 h-3 bg-gray-600 rounded-full"></div>
                                </div>
                                {/* No button to start manual interview since we auto-schedule */}
                                <div className="p-4 bg-yellow-900/20 border border-yellow-700/50 rounded text-yellow-200 text-sm">
                                    Waiting for interview assignment...
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Error Display */}
                    {error && (
                        <div className="p-3 rounded-lg bg-red-900/50 border border-red-800 text-red-200 text-sm text-center mb-6">
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

                {/* Debug Section */}
                <div className="mt-8 pt-8 border-t border-gray-700">
                    <button
                        onClick={handleDebugCreate}
                        className="text-xs text-gray-500 hover:text-gray-300 underline"
                    >
                        [Debug] Create New Interview Session
                    </button>
                </div>
            </div>
        </div>
    );
}
