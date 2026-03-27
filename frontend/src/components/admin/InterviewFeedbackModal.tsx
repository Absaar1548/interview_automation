'use client';

import { useEffect, useState } from 'react';
import { fetchInterviewFeedback, CandidateFeedbackData, SchedulingApiError } from '@/lib/api/interviews';

interface InterviewFeedbackModalProps {
    interviewId: string;
    candidateName: string;
    onClose: () => void;
    onAuthError: () => void;
}

export default function InterviewFeedbackModal({
    interviewId,
    candidateName,
    onClose,
    onAuthError,
}: InterviewFeedbackModalProps) {
    const [feedback, setFeedback] = useState<CandidateFeedbackData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            setError('');
            try {
                const data = await fetchInterviewFeedback(interviewId);
                setFeedback(data);
            } catch (err: any) {
                const apiErr = err as SchedulingApiError;
                if (apiErr.status === 401 || apiErr.status === 403) {
                    onAuthError();
                    return;
                }
                setError(apiErr.detail || 'Failed to load feedback');
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [interviewId, onAuthError]);

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto"
            onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
        >
            <div className="bg-white rounded-xl w-full max-w-3xl shadow-2xl max-h-[90vh] flex flex-col my-8">
                <div className="bg-gradient-to-r from-indigo-600 to-blue-600 px-6 py-5 flex-shrink-0">
                    <div className="flex justify-between items-center">
                        <div>
                            <h2 className="text-xl font-bold text-white">Candidate Feedback</h2>
                            <p className="text-indigo-100 text-sm mt-0.5">{candidateName}</p>
                        </div>
                        <button onClick={onClose} className="text-indigo-200 hover:text-white transition-colors p-1 rounded">✕</button>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6">
                    {loading ? (
                        <div className="flex items-center justify-center py-10">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                        </div>
                    ) : error ? (
                        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>
                    ) : feedback ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.entries(feedback).map(([k, v]) => (
                                <div key={k} className={k === 'ui_feedback' || k === 'recommendation' ? 'md:col-span-2' : ''}>
                                    <p className="text-[11px] font-bold uppercase tracking-wide text-gray-500 mb-1">{k.replace(/_/g, ' ')}</p>
                                    <div className="p-3 border rounded-lg bg-gray-50 text-sm text-gray-800 whitespace-pre-wrap">{String(v || '-')}</div>
                                </div>
                            ))}
                        </div>
                    ) : null}
                </div>

                <div className="border-t border-gray-200 px-6 py-4 flex justify-end flex-shrink-0">
                    <button onClick={onClose} className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-semibold hover:bg-gray-700">Close</button>
                </div>
            </div>
        </div>
    );
}

