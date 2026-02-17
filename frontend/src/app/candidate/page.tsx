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

    const [interview, setInterview] = useState<InterviewSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!isAuthenticated || !user) {
            router.push("/login/candidate");
            return;
        }

        const fetchDashboardData = async () => {
            setLoading(true);
            try {
                const interviews = await dashboardService.getInterviews(user.username);
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

    const handleStartOrResumeInterview = () => {
        if (!interview) return;
        initializeInterview(interview.interview_id, interview.candidate_token);
        router.push("/interview");
    };

    const handleDebugCreate = async () => {
        if (!user) return;
        setLoading(true);
        try {
            await dashboardService.createSession(user.username);
            const interviews = await dashboardService.getInterviews(user.username);
            if (interviews.length > 0) {
                setInterview(interviews[0]);
            }
        } catch (err: any) {
            console.error("Debug create error:", err);
            setError(err.message || "Failed to create debug session.");
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        router.push("/login/candidate");
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading your dashboard...</p>
                </div>
            </div>
        );
    }

    if (!user) return null;

    const hasActiveSession = !!interview;

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b border-gray-200">
                <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Candidate Dashboard</h1>
                            <p className="text-sm text-gray-600 mt-1">Welcome, {user.username}</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {error && (
                    <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
                        {error}
                    </div>
                )}

                {/* Interview Status Card */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Interview Status</h2>

                    {hasActiveSession ? (
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                                <div>
                                    <p className="font-semibold text-gray-900 mb-1">
                                        {interview.state === "COMPLETED"
                                            ? "Interview Completed"
                                            : "Active Interview Session"}
                                    </p>
                                    <p className="text-sm text-gray-600">
                                        {interview.state === "COMPLETED"
                                            ? "Thank you for your participation."
                                            : `Status: ${interview.state}`}
                                    </p>
                                    {interview.state !== "COMPLETED" && (
                                        <p className="text-xs text-gray-400 mt-1 font-mono">
                                            ID: {interview.interview_id}
                                        </p>
                                    )}
                                </div>
                                <div className={`w-3 h-3 rounded-full ${interview.state === "COMPLETED" ? "bg-gray-400" : "bg-green-500 animate-pulse"}`}></div>
                            </div>

                            {interview.state !== "COMPLETED" && (
                                <button
                                    onClick={handleStartOrResumeInterview}
                                    className="w-full py-3 px-6 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-sm flex items-center justify-center gap-2"
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
                            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200">
                                <div>
                                    <p className="font-medium text-gray-700 mb-1">No Active Interview</p>
                                    <p className="text-sm text-gray-500">Contact HR if you believe this is an error.</p>
                                </div>
                                <div className="w-3 h-3 bg-gray-300 rounded-full"></div>
                            </div>
                            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 flex-shrink-0">
                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                </svg>
                                Waiting for interview assignment...
                            </div>
                        </div>
                    )}
                </div>

                {/* Guidelines Card */}
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                            </svg>
                        </div>
                        <div className="flex-1">
                            <h3 className="text-sm font-semibold text-gray-900 mb-2">Interview Guidelines</h3>
                            <ul className="text-sm text-gray-600 space-y-2">
                                <li className="flex items-start gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0"></span>
                                    <span>Ensure you have a stable internet connection</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0"></span>
                                    <span>Find a quiet environment with good lighting</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0"></span>
                                    <span>Have your camera and microphone ready</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0"></span>
                                    <span>You can pause and resume your interview anytime</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Debug Section */}
                <div className="mt-6 text-center">
                    <button
                        onClick={handleDebugCreate}
                        className="text-xs text-gray-400 hover:text-gray-600 font-medium transition-colors"
                    >
                        [Debug] Create New Interview Session
                    </button>
                </div>
            </main>
        </div>
    );
}
