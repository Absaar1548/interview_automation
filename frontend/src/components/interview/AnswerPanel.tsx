import { useState, useEffect } from 'react';
import { AnswerMode, InterviewQuestion } from '@/types/interview';

interface AnswerPanelProps {
    question: InterviewQuestion | null;
    onSubmit: () => void;
}

export default function AnswerPanel({ question, onSubmit }: AnswerPanelProps) {
    const [recording, setRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [transcript, setTranscript] = useState<string | null>(null);

    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (recording) {
            interval = setInterval(() => {
                setRecordingTime((prev) => prev + 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [recording]);

    // Reset state when question changes
    useEffect(() => {
        setRecording(false);
        setRecordingTime(0);
        setTranscript(null);
    }, [question?.question_id]);

    if (!question) return null;

    const mode = question.answer_mode;

    const handleStartRecording = () => {
        setRecording(true);
        setTranscript(null);
    };

    const handleStopRecording = () => {
        setRecording(false);
        setTranscript("This is a simulated transcription of the candidate's response.");
    };

    return (
        <div className="w-full max-w-2xl mt-4">
            <div className="border p-6 rounded-lg bg-white dark:bg-gray-800 shadow-sm">
                <h3 className="text-lg font-semibold mb-4">Your Answer ({mode})</h3>

                {mode === AnswerMode.TEXT && (
                    <>
                        <textarea
                            className="w-full h-32 p-3 border rounded mb-4 bg-gray-50 dark:bg-gray-700 dark:border-gray-600"
                            placeholder="Type your answer here..."
                        />
                        <button
                            onClick={onSubmit}
                            className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium"
                        >
                            Submit Answer
                        </button>
                    </>
                )}

                {mode === AnswerMode.CODE && (
                    <>
                        <textarea
                            className="w-full h-64 p-3 border rounded mb-4 font-mono bg-gray-900 text-green-400"
                            placeholder="// Write your code here..."
                        />
                        <button
                            onClick={onSubmit}
                            className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium"
                        >
                            Submit Answer
                        </button>
                    </>
                )}

                {mode === AnswerMode.AUDIO && (
                    <div className="flex flex-col items-center">
                        {!recording && !transcript && (
                            <div className="flex items-center justify-center h-32 w-full border-2 border-dashed rounded mb-4 bg-gray-50 dark:bg-gray-700">
                                <button
                                    onClick={handleStartRecording}
                                    className="px-6 py-3 bg-red-500 text-white rounded-full hover:bg-red-600 transition"
                                >
                                    Start Recording
                                </button>
                            </div>
                        )}

                        {recording && (
                            <div className="flex flex-col items-center justify-center h-32 w-full border-2 border-red-200 rounded mb-4 bg-red-50 dark:bg-red-900/20">
                                <div className="text-2xl font-mono mb-4 text-red-600">{recordingTime}s</div>
                                <button
                                    onClick={handleStopRecording}
                                    className="px-6 py-3 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition"
                                >
                                    Stop Recording
                                </button>
                                <p className="mt-2 text-sm text-gray-500 animate-pulse">Recording...</p>
                            </div>
                        )}

                        {transcript && (
                            <div className="w-full">
                                <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded mb-4 italic text-gray-700 dark:text-gray-300">
                                    "{transcript}"
                                </div>
                                <button
                                    onClick={onSubmit}
                                    className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-medium"
                                >
                                    Submit Answer
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
