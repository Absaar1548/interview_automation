'use client';

import InterviewShell from '@/components/interview/InterviewShell';
import {
    initInterview,
    startInterview,
    getNextQuestion,
    submitAnswer
} from '@/lib/mockBackend';

export default function InterviewPage() {
    return (
        <div className="flex min-h-screen flex-col items-center justify-center p-24">
            <InterviewShell
                onInit={initInterview}
                onStart={startInterview}
                onNextQuestion={getNextQuestion}
                onSubmitAnswer={submitAnswer}
            />
        </div>
    );
}
