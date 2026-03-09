'use client';

import { useState, useEffect } from 'react';
import { getInterviewQuestions, updateInterviewQuestions, InterviewQuestion, SchedulingApiError } from '@/lib/api/interviews';

interface InterviewQuestionsModalProps {
    interviewId: string;
    onClose: () => void;
    onSuccess: () => void;
    onAuthError: () => void;
}

export default function InterviewQuestionsModal({
    interviewId,
    onClose,
    onSuccess,
    onAuthError,
}: InterviewQuestionsModalProps) {
    const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [editingIdx, setEditingIdx] = useState<number | null>(null);
    const [editText, setEditText] = useState('');
    const [newQuestion, setNewQuestion] = useState({
        prompt: '',
        difficulty: 'medium' as 'easy' | 'medium' | 'hard',
        time_limit_sec: 240,
    });

    useEffect(() => {
        fetchQuestions();
    }, [interviewId]);

    const fetchQuestions = async () => {
        setLoading(true);
        setError('');
        try {
            const data = await getInterviewQuestions(interviewId);
            setQuestions(data.questions || []);
        } catch (err: any) {
            const apiErr = err as SchedulingApiError;
            if (apiErr.status === 401 || apiErr.status === 403) {
                onAuthError();
                return;
            }
            setError(apiErr.detail || 'Failed to load questions');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        if (questions.length === 0) {
            setError('Interview must contain at least one question');
            return;
        }

        setSaving(true);
        setError('');
        try {
            await updateInterviewQuestions(interviewId, questions);
            onSuccess();
            onClose();
        } catch (err: any) {
            const apiErr = err as SchedulingApiError;
            if (apiErr.status === 401 || apiErr.status === 403) {
                onAuthError();
                return;
            }
            setError(apiErr.detail || 'Failed to update questions');
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = (index: number) => {
        if (questions.length <= 1) {
            setError('Interview must contain at least one question');
            return;
        }
        const updated = questions.filter((_, i) => i !== index);
        // Reorder questions
        updated.forEach((q, i) => {
            q.order = i + 1;
        });
        setQuestions(updated);
        setEditingIdx(null);
    };

    const handleEdit = (index: number) => {
        setEditingIdx(index);
        setEditText(questions[index].prompt);
    };

    const handleSaveEdit = (index: number) => {
        const updated = [...questions];
        updated[index].prompt = editText;
        setQuestions(updated);
        setEditingIdx(null);
        setEditText('');
    };

    const handleCancelEdit = () => {
        setEditingIdx(null);
        setEditText('');
    };

    const handleAddQuestion = () => {
        if (!newQuestion.prompt.trim()) {
            setError('Please enter a question');
            return;
        }
        const question: InterviewQuestion = {
            question_id: `new_${Date.now()}`,
            question_type: 'static',
            order: questions.length + 1,
            prompt: newQuestion.prompt.trim(),
            difficulty: newQuestion.difficulty,
            time_limit_sec: newQuestion.time_limit_sec,
            evaluation_mode: 'text',
            source: 'manual',
        };
        setQuestions([...questions, question]);
        setNewQuestion({
            prompt: '',
            difficulty: 'medium',
            time_limit_sec: 240,
        });
        setError('');
    };

    return (
        <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={(e) => { if (e.target === e.currentTarget && !saving) onClose(); }}
        >
            <div className="bg-white rounded-xl w-full max-w-4xl shadow-2xl max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-5">
                    <div className="flex justify-between items-center">
                        <h2 className="text-xl font-bold text-white">
                            Manage Interview Questions
                        </h2>
                        <button
                            onClick={onClose}
                            disabled={saving}
                            className="text-blue-200 hover:text-white transition-colors p-1 rounded"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-6">
                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                            {error}
                        </div>
                    )}

                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {/* Existing Questions */}
                            <div>
                                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                                    Technical Questions ({questions.length})
                                </h3>
                                <div className="space-y-3">
                                    {questions.map((q, idx) => (
                                        <div
                                            key={q.question_id || idx}
                                            className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                                        >
                                            {editingIdx === idx ? (
                                                <div className="space-y-3">
                                                    <textarea
                                                        value={editText}
                                                        onChange={(e) => setEditText(e.target.value)}
                                                        className="w-full p-2 border border-gray-300 rounded text-sm"
                                                        rows={3}
                                                    />
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => handleSaveEdit(idx)}
                                                            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm font-semibold hover:bg-blue-700"
                                                        >
                                                            Save
                                                        </button>
                                                        <button
                                                            onClick={handleCancelEdit}
                                                            className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded text-sm font-semibold hover:bg-gray-300"
                                                        >
                                                            Cancel
                                                        </button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="flex justify-between items-start gap-4">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <span className="text-xs font-bold text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                                                Q{q.order} • {q.difficulty.toUpperCase()}
                                                            </span>
                                                        </div>
                                                        <p className="text-sm text-gray-800">{q.prompt}</p>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <button
                                                            onClick={() => handleEdit(idx)}
                                                            className="px-2 py-1 text-xs font-semibold text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded"
                                                        >
                                                            Edit
                                                        </button>
                                                        <button
                                                            onClick={() => handleDelete(idx)}
                                                            disabled={questions.length <= 1}
                                                            className="px-2 py-1 text-xs font-semibold text-red-600 hover:text-red-700 hover:bg-red-50 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                                        >
                                                            Delete
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Add New Question */}
                            <div className="border-t border-gray-200 pt-4">
                                <h3 className="text-sm font-semibold text-gray-700 mb-3">Add New Question</h3>
                                <div className="space-y-3">
                                    <textarea
                                        value={newQuestion.prompt}
                                        onChange={(e) => setNewQuestion({ ...newQuestion, prompt: e.target.value })}
                                        placeholder="Enter question text..."
                                        className="w-full p-3 border border-gray-300 rounded-lg text-sm"
                                        rows={3}
                                    />
                                    <div className="flex gap-4 items-center">
                                        <div>
                                            <label className="text-xs font-medium text-gray-600 mb-1 block">Difficulty</label>
                                            <select
                                                value={newQuestion.difficulty}
                                                onChange={(e) => setNewQuestion({ ...newQuestion, difficulty: e.target.value as 'easy' | 'medium' | 'hard' })}
                                                className="px-3 py-1.5 border border-gray-300 rounded text-sm"
                                            >
                                                <option value="easy">Easy</option>
                                                <option value="medium">Medium</option>
                                                <option value="hard">Hard</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-xs font-medium text-gray-600 mb-1 block">Time Limit (seconds)</label>
                                            <input
                                                type="number"
                                                value={newQuestion.time_limit_sec}
                                                onChange={(e) => setNewQuestion({ ...newQuestion, time_limit_sec: parseInt(e.target.value) || 240 })}
                                                className="px-3 py-1.5 border border-gray-300 rounded text-sm w-24"
                                                min="60"
                                                max="600"
                                            />
                                        </div>
                                        <button
                                            onClick={handleAddQuestion}
                                            className="px-4 py-2 bg-green-600 text-white rounded text-sm font-semibold hover:bg-green-700 mt-6"
                                        >
                                            Add Question
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        disabled={saving}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving || loading || questions.length === 0}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </div>
        </div>
    );
}
