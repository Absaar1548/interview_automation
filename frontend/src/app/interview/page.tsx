"use client";

import { useEffect, useRef } from "react";
import { useInterviewStore } from "@/store/interviewStore";
import InterviewShell from "@/components/interview/InterviewShell";

export default function InterviewPage() {
    const interviewId = useInterviewStore((s) => s.interviewId);
    const candidateToken = useInterviewStore((s) => s.candidateToken);
    const state = useInterviewStore((s) => s.state);
    const terminationReason = useInterviewStore((s) => s.terminationReason);
    const isConnected = useInterviewStore((s) => s.isConnected);
    const error = useInterviewStore((s) => s.error);
    const startInterview = useInterviewStore((s) => s.startInterview);
    const initialize = useInterviewStore((s) => s.initialize);
    const hasStarted = useRef(false);
    const hasBootstrapped = useRef(false);

    useEffect(() => {
        if (!interviewId || !candidateToken) {
            // START DEV BOOTSTRAP - Remove in Production
            if (process.env.NODE_ENV === "development" && !hasBootstrapped.current) {
                hasBootstrapped.current = true;
                // Add /api/v1 because NEXT_PUBLIC_API_BASE_URL is localhost:8000
                fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/dev/bootstrap`)
                    .then((res) => res.json())
                    .then((data) => {
                        initialize(data.interview_id, data.candidate_token);
                    })
                    .catch((err) => console.error("Bootstrap failed", err));
            }
            // END DEV BOOTSTRAP
            return;
        }

        if (!isConnected) return;
        if (hasStarted.current) return;

        hasStarted.current = true;
        startInterview();
    }, [interviewId, candidateToken, isConnected, startInterview, initialize]);

    if (!interviewId || !candidateToken) {
        return (
            <div className="flex h-screen items-center justify-center text-red-500 font-bold">
                Interview session not initialized.
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-screen items-center justify-center text-red-600 font-bold">
                Error: {error}
            </div>
        );
    }

    if (state === null) {
        return (
            <div className="flex h-screen items-center justify-center text-gray-500">
                Initializing interview...
            </div>
        );
    }

    if (state === "TERMINATED") {
        return (
            <div className="flex flex-col h-screen items-center justify-center text-red-600">
                <h1 className="text-2xl font-bold mb-4">Interview Terminated</h1>
                {terminationReason && <p className="text-lg">{terminationReason}</p>}
            </div>
        );
    }

    if (state === "COMPLETED") {
        return (
            <div className="flex h-screen items-center justify-center text-green-600 text-2xl font-bold">
                Interview Completed
            </div>
        );
    }

    return <InterviewShell />;
}
