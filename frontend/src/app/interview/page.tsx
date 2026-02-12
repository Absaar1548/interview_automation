'use client';

import { useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { useInterviewStore } from '@/store/interviewStore';

export default function InterviewPage() {
    const searchParams = useSearchParams();
    const interviewId = searchParams.get('interviewId');
    const candidateToken = searchParams.get('candidateToken');

    const state = useInterviewStore((store) => store.state);
    const terminationReason = useInterviewStore((store) => store.terminationReason);
    const initialize = useInterviewStore((store) => store.initialize);
    const startInterview = useInterviewStore((store) => store.startInterview);

    const hasInitialized = useRef(false);

    useEffect(() => {
        if (hasInitialized.current) return;

        if (interviewId && candidateToken) {
            hasInitialized.current = true;
            initialize(interviewId, candidateToken);
            startInterview();
        }
    }, [interviewId, candidateToken, initialize, startInterview]);

    if (!interviewId || !candidateToken) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-red-600">Error</h1>
                    <p className="mt-2">Missing interview ID or candidate token</p>
                </div>
            </div>
        );
    }

    if (state === 'COMPLETED') {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="text-center">
                    <h1 className="text-2xl font-bold">Interview Completed</h1>
                </div>
            </div>
        );
    }

    if (state === 'TERMINATED') {
        return (
            <div className="flex min-h-screen items-center justify-center">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-red-600">Interview Terminated</h1>
                    {terminationReason && (
                        <p className="mt-2 text-gray-600">Reason: {terminationReason}</p>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="flex min-h-screen items-center justify-center">
            <div className="text-center">
                <p>Loading interview...</p>
            </div>
        </div>
    );
}
