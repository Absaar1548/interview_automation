"use client";

import { useState, useRef, useEffect } from "react";
import { answerWebSocket } from "@/lib/answerWebSocket";
import CodeEditor from "./CodeEditor";

interface AnswerPanelProps {
    mode: "AUDIO" | "CODE";
    value: string;
    onChange: (value: string) => void;
    questionId: string;
}

export default function AnswerPanel({
    mode,
    value,
    onChange,
    questionId,
}: AnswerPanelProps) {
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState("");
    const [finalTranscript, setFinalTranscript] = useState<string | null>(null);

    const mediaStreamRef = useRef<MediaStream | null>(null);
    const recorderRef = useRef<MediaRecorder | null>(null);

    const cleanup = () => {
        if (recorderRef.current && recorderRef.current.state !== "inactive") {
            recorderRef.current.stop();
        }
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach((track) => track.stop());
        }

        mediaStreamRef.current = null;
        recorderRef.current = null;

        answerWebSocket.disconnect();
        setIsRecording(false);
    };

    useEffect(() => {
        return () => {
            cleanup();
        };
    }, []);

    const startRecording = async () => {
        if (isRecording) return;

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;

            answerWebSocket.connect({
                questionId,
                onOpen: () => {
                    const recorder = new MediaRecorder(stream);
                    recorderRef.current = recorder;

                    recorder.ondataavailable = async (event) => {
                        if (event.data.size > 0) {
                            const arrayBuffer = await event.data.arrayBuffer();
                            answerWebSocket.sendAudio(arrayBuffer);
                        }
                    };

                    recorder.start(1000);
                    setIsRecording(true);
                    setTranscript("");
                    setFinalTranscript(null);
                },
                onPartialTranscript: (text) => {
                    setTranscript(text);
                },
                onFinalTranscript: (text) => {
                    setTranscript(text);
                },
                onAnswerReady: (transcriptId) => {
                    onChange(transcriptId);
                    setFinalTranscript(transcriptId);
                    cleanup();
                },
                onError: () => {
                    cleanup();
                },
                onClose: () => {
                    setIsRecording(false);
                },
            });
        } catch (error) {
            // Handle error silently or via UI state if needed, but no console logs as per req.
            cleanup();
        }
    };

    const stopRecording = () => {
        if (!isRecording) return;
        answerWebSocket.endAnswer();
        // Cleanup happens in onAnswerReady or onClose
    };

    if (mode === "CODE") {
        return (
            <CodeEditor
                value={value}
                onChange={onChange}
                questionId={questionId}
            />
        );
    }

    return (
        <div className="flex flex-col gap-4 border p-4 rounded bg-gray-50">
            <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-700">Audio Answer</span>
                <button
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`px-4 py-2 rounded text-white font-medium ${isRecording ? "bg-red-600 hover:bg-red-700" : "bg-blue-600 hover:bg-blue-700"
                        }`}
                >
                    {isRecording ? "Stop Recording" : "Start Recording"}
                </button>
            </div>

            <div className="bg-white p-4 rounded border min-h-[100px] text-gray-800">
                {finalTranscript ? (
                    <div className="text-green-600 font-medium">
                        Answer Finalized (ID: {finalTranscript})
                    </div>
                ) : (
                    <p>{transcript || "Waiting for speech..."}</p>
                )}
            </div>
        </div>
    );
}
