'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { useInterviewStore } from '@/store/interviewStore';
import {
    fetchActiveInterview,
    startInterview,
    ActiveInterviewResponse,
    SchedulingApiError,
} from '@/lib/api/interviews';
import { verificationService, VerificationStatus } from '@/lib/verificationService';

// ─── Status badge ─────────────────────────────────────────────────────────────

const STATUS_STYLES: Record<string, string> = {
    scheduled: 'bg-blue-100 text-blue-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-gray-100 text-gray-600',
};
const STATUS_LABELS: Record<string, string> = {
    scheduled: 'Scheduled',
    in_progress: 'In Progress',
    completed: 'Completed',
    cancelled: 'Cancelled',
};

// ─── Main page ────────────────────────────────────────────────────────────────

export default function CandidatePage() {
    const router = useRouter();
    const { user, isAuthenticated, logout } = useAuthStore();
    const initializeInterview = useInterviewStore((s) => s.initialize);

    const [interview, setInterview] = useState<ActiveInterviewResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [startLoading, setStartLoading] = useState(false);
    const [error, setError] = useState('');

    // Verification (face + voice) for interview monitoring
    const [verificationStatus, setVerificationStatus] = useState<VerificationStatus | null>(null);
    const [verificationError, setVerificationError] = useState('');
    const videoRef = useRef<HTMLVideoElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const [cameraActive, setCameraActive] = useState(false);
    const [videoReady, setVideoReady] = useState(false);
    const [capturedPhoto, setCapturedPhoto] = useState<Blob | null>(null);
    const [faceLoading, setFaceLoading] = useState(false);
    const [voiceRecording, setVoiceRecording] = useState(false);
    const [voiceChunks, setVoiceChunks] = useState<Blob[]>([]);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const [voiceLoading, setVoiceLoading] = useState(false);

    /** Read JWT from localStorage—same key used by authStore & API helpers. */
    const getJwt = (): string => {
        try {
            const raw = localStorage.getItem('auth-storage');
            return JSON.parse(raw ?? '{}')?.state?.token ?? '';
        } catch {
            return '';
        }
    };

    // ─── Auth guard + data fetch ────────────────────────────────────────────
    const fetchData = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const data = await fetchActiveInterview();
            setInterview(data);
        } catch (err: any) {
            const apiErr = err as SchedulingApiError;
            if (apiErr.status === 401 || apiErr.status === 403) {
                logout();
                router.push('/login/candidate');
                return;
            }
            setError('Failed to load interview details. Please try again.');
        } finally {
            setLoading(false);
        }
    }, [logout, router]);

    useEffect(() => {
        if (!isAuthenticated || !user) {
            router.push('/login/candidate');
            return;
        }
        if (user.role !== 'candidate') {
            router.push(user.role === 'admin' ? '/admin' : '/login/candidate');
            return;
        }
        fetchData();
    }, [isAuthenticated, user, router, fetchData]);

    // ─── Verification status ─────────────────────────────────────────────────
    const loadVerificationStatus = useCallback(async () => {
        try {
            const status = await verificationService.getVerificationStatus();
            setVerificationStatus(status);
        } catch {
            setVerificationStatus({ face_enrolled: false, voice_enrolled: false, face_updated_at: null, voice_updated_at: null });
        }
    }, []);
    useEffect(() => {
        if (isAuthenticated && user?.role === 'candidate') loadVerificationStatus();
    }, [isAuthenticated, user?.role, loadVerificationStatus]);

    // ─── Face: start/stop camera, capture, upload ────────────────────────────
    const startCamera = useCallback(async () => {
        setVerificationError('');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
            });
            streamRef.current = stream;
            setCapturedPhoto(null);
            setCameraActive(true);
        } catch (e) {
            setVerificationError('Could not access camera. Please allow camera permission.');
        }
    }, []);

    // Attach stream to video once the video element is mounted (cameraActive true)
    useEffect(() => {
        if (!cameraActive || !streamRef.current || !videoRef.current) return;
        const video = videoRef.current;
        const stream = streamRef.current;
        video.srcObject = stream;
        setVideoReady(false);
        const onCanPlay = () => setVideoReady(true);
        video.addEventListener('canplay', onCanPlay, { once: true });
        video.play().catch(() => {});
        return () => video.removeEventListener('canplay', onCanPlay);
    }, [cameraActive]);
    const stopCamera = useCallback(() => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((t) => t.stop());
            streamRef.current = null;
        }
        if (videoRef.current) videoRef.current.srcObject = null;
        setCameraActive(false);
        setVideoReady(false);
        setCapturedPhoto(null);
    }, []);
    const capturePhoto = useCallback(() => {
        const video = videoRef.current;
        if (!video || !streamRef.current) return;
        let w = video.videoWidth;
        let h = video.videoHeight;
        if (!w || !h) {
            w = 640;
            h = 480;
        }
        const canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        ctx.drawImage(video, 0, 0, w, h);
        canvas.toBlob(
            (blob) => {
                if (blob) setCapturedPhoto(blob);
            },
            'image/jpeg',
            0.9
        );
    }, []);
    const submitFace = useCallback(async () => {
        if (!capturedPhoto) return;
        setFaceLoading(true);
        setVerificationError('');
        try {
            await verificationService.uploadFace(capturedPhoto, 'photo.jpg');
            await loadVerificationStatus();
            stopCamera();
        } catch (e: unknown) {
            setVerificationError((e as { message?: string })?.message || 'Failed to upload photo.');
        } finally {
            setFaceLoading(false);
        }
    }, [capturedPhoto, loadVerificationStatus, stopCamera]);
    useEffect(() => {
        return () => {
            if (streamRef.current) {
                streamRef.current.getTracks().forEach((t) => t.stop());
            }
        };
    }, []);

    // ─── Voice: record and upload ─────────────────────────────────────────────
    const startVoiceRecording = useCallback(async () => {
        setVerificationError('');
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream);
            const chunks: Blob[] = [];
            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunks.push(e.data);
            };
            recorder.onstop = () => {
                stream.getTracks().forEach((t) => t.stop());
                setVoiceChunks(chunks);
            };
            recorder.start(200);
            mediaRecorderRef.current = recorder;
            setVoiceRecording(true);
            setVoiceChunks([]);
        } catch (e) {
            setVerificationError('Could not access microphone. Please allow microphone permission.');
        }
    }, []);
    const stopVoiceRecording = useCallback(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
        }
        setVoiceRecording(false);
    }, []);
    const submitVoice = useCallback(async () => {
        if (voiceChunks.length === 0) return;
        setVoiceLoading(true);
        setVerificationError('');
        try {
            const blob = new Blob(voiceChunks, { type: 'audio/webm' });
            await verificationService.uploadVoice(blob, 'recording.webm');
            await loadVerificationStatus();
            setVoiceChunks([]);
        } catch (e: unknown) {
            setVerificationError((e as { message?: string })?.message || 'Failed to upload voice.');
        } finally {
            setVoiceLoading(false);
        }
    }, [voiceChunks, loadVerificationStatus]);

    // ─── Start / Rejoin interview ────────────────────────────────────────────
    const handleStart = async () => {
        if (!interview) return;
        setStartLoading(true);
        setError('');
        try {
            let sessionId: string;

            if (interview.status === 'in_progress' && interview.session_id) {
                sessionId = interview.session_id; // rejoin existing session
            } else {
                const result = await startInterview(interview.interview_id);
                sessionId = result.session_id;
            }

            // Seed the interviewStore so /interview page has what it needs:
            //   interviewId  → session_id (used as the WS room identifier)
            //   candidateToken → JWT (used for WS auth)
            const jwt = getJwt();
            initializeInterview(sessionId, jwt);

            router.push('/interview');
        } catch (err: any) {
            const apiErr = err as SchedulingApiError;
            if (apiErr.status === 401 || apiErr.status === 403) {
                logout();
                router.push('/login/candidate');
                return;
            }
            setError(apiErr.detail || 'Failed to start interview. Please try again.');
        } finally {
            setStartLoading(false);
        }
    };

    const handleLogout = () => { logout(); router.push('/login/candidate'); };

    // ─── Render ───────────────────────────────────────────────────────────────

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
                    <p className="text-gray-600">Loading your dashboard…</p>
                </div>
            </div>
        );
    }

    if (!user) return null;

    const ivStatus = interview?.status;
    const isInProgress = ivStatus === 'in_progress';
    const statusKey = ivStatus ?? '';

    // Format scheduled_at in local timezone
    const scheduledDisplay = interview?.scheduled_at
        ? new Date(interview.scheduled_at).toLocaleString(undefined, {
            dateStyle: 'full',
            timeStyle: 'short',
        })
        : null;

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white shadow-sm border-b border-gray-200">
                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">Candidate Dashboard</h1>
                            <p className="text-sm text-gray-600 mt-0.5">Welcome, {user.username}</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium text-sm"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            {/* Main */}
            <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
                {error && (
                    <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
                )}
                {verificationError && (
                    <div className="p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-sm">{verificationError}</div>
                )}

                {/* Verification setup — face & voice for interview monitoring */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-100">
                        <h2 className="text-base font-semibold text-gray-900">Verification Setup</h2>
                        <p className="text-xs text-gray-500 mt-0.5">
                            Upload your live photo and voice. These will be used for face and audio verification during the interview.
                        </p>
                    </div>
                    <div className="p-6 grid gap-6 sm:grid-cols-2">
                        {/* Face */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2">
                                <h3 className="text-sm font-medium text-gray-700">Face (live camera)</h3>
                                {verificationStatus?.face_enrolled && (
                                    <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded">Enrolled</span>
                                )}
                            </div>
                            {!cameraActive && !capturedPhoto ? (
                                <button
                                    type="button"
                                    onClick={startCamera}
                                    className="w-full py-2.5 px-4 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                                >
                                    Start camera
                                </button>
                            ) : (
                                <div className="space-y-2">
                                    {cameraActive && (
                                        <div className="relative w-full rounded-lg bg-gray-900 aspect-video overflow-hidden">
                                            <video
                                                ref={videoRef}
                                                autoPlay
                                                playsInline
                                                muted
                                                className="w-full h-full object-cover"
                                                style={{ transform: 'scaleX(1)' }}
                                            />
                                            {!videoReady && (
                                                <div className="absolute inset-0 flex items-center justify-center bg-gray-900 text-gray-400 text-sm">
                                                    Loading camera…
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    {capturedPhoto && (
                                        <p className="text-xs text-gray-500">Photo captured. Submit or capture again.</p>
                                    )}
                                    <div className="flex flex-wrap gap-2">
                                        {cameraActive && (
                                            <>
                                                <button
                                                    type="button"
                                                    onClick={capturePhoto}
                                                    disabled={!videoReady}
                                                    className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                                >
                                                    Capture photo
                                                </button>
                                                <button type="button" onClick={stopCamera} className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
                                                    Cancel
                                                </button>
                                            </>
                                        )}
                                        {capturedPhoto && (
                                            <button
                                                type="button"
                                                onClick={submitFace}
                                                disabled={faceLoading}
                                                className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                                            >
                                                {faceLoading ? 'Uploading…' : 'Submit photo'}
                                            </button>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                        {/* Voice */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2">
                                <h3 className="text-sm font-medium text-gray-700">Voice (live recording)</h3>
                                {verificationStatus?.voice_enrolled && (
                                    <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded">Enrolled</span>
                                )}
                            </div>
                            {!voiceRecording && voiceChunks.length === 0 ? (
                                <button
                                    type="button"
                                    onClick={startVoiceRecording}
                                    className="w-full py-2.5 px-4 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                                >
                                    Start recording
                                </button>
                            ) : (
                                <div className="space-y-2">
                                    {voiceRecording && (
                                        <p className="text-sm text-gray-600 flex items-center gap-2">
                                            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" /> Recording… Speak for a few seconds, then stop.
                                        </p>
                                    )}
                                    <div className="flex flex-wrap gap-2">
                                        {voiceRecording ? (
                                            <button type="button" onClick={stopVoiceRecording} className="px-3 py-1.5 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700">
                                                Stop recording
                                            </button>
                                        ) : voiceChunks.length > 0 ? (
                                            <>
                                                <button
                                                    type="button"
                                                    onClick={submitVoice}
                                                    disabled={voiceLoading}
                                                    className="px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                                                >
                                                    {voiceLoading ? 'Uploading…' : 'Submit voice'}
                                                </button>
                                                <button type="button" onClick={() => setVoiceChunks([])} className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50">
                                                    Record again
                                                </button>
                                            </>
                                        ) : null}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Interview card */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-100">
                        <h2 className="text-base font-semibold text-gray-900">Your Interview</h2>
                    </div>

                    {interview ? (
                        <div className="p-6 space-y-5">
                            {/* Status row */}
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-500">Status</span>
                                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${STATUS_STYLES[statusKey] ?? 'bg-gray-100 text-gray-600'}`}>
                                    {STATUS_LABELS[statusKey] ?? statusKey}
                                </span>
                            </div>

                            {/* Scheduled At */}
                            {scheduledDisplay && (
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-gray-500">
                                        {isInProgress ? 'Started' : 'Scheduled For'}
                                    </span>
                                    <span className="text-sm text-gray-900 font-medium">{scheduledDisplay}</span>
                                </div>
                            )}

                            {/* Interview ID */}
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-500">Interview ID</span>
                                <span className="text-xs font-mono text-gray-400">{interview.interview_id}</span>
                            </div>

                            {/* can_start gate */}
                            {interview.can_start ? (
                                <button
                                    onClick={handleStart}
                                    disabled={startLoading}
                                    className="w-full py-3 px-6 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {startLoading ? (
                                        <>
                                            <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                            </svg>
                                            {isInProgress ? 'Rejoining…' : 'Starting…'}
                                        </>
                                    ) : (
                                        <>
                                            {isInProgress ? 'Rejoin Interview' : 'Start Interview'}
                                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                                            </svg>
                                        </>
                                    )}
                                </button>
                            ) : (
                                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 flex items-start gap-2">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 flex-shrink-0 mt-0.5">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5c0 .414.336.75.75.75h4a.75.75 0 000-1.5h-3.25V5z" clipRule="evenodd" />
                                    </svg>
                                    <span>
                                        Your interview is scheduled for <strong>{scheduledDisplay}</strong>. The Start button will unlock at that time.
                                    </span>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="p-6 space-y-4">
                            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-between">
                                <div>
                                    <p className="font-medium text-gray-700 text-sm">No Active Interview</p>
                                    <p className="text-xs text-gray-400 mt-0.5">Contact HR if you believe this is an error.</p>
                                </div>
                                <div className="w-3 h-3 bg-gray-300 rounded-full" />
                            </div>
                            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-sm flex items-start gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 flex-shrink-0 mt-0.5">
                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                </svg>
                                Waiting for interview assignment by your recruiter…
                            </div>
                        </div>
                    )}
                </div>

                {/* Guidelines */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg flex-shrink-0">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                            </svg>
                        </div>
                        <div>
                            <h3 className="text-sm font-semibold text-gray-900 mb-2">Interview Guidelines</h3>
                            <ul className="text-sm text-gray-600 space-y-1.5">
                                {[
                                    'Ensure a stable internet connection.',
                                    'Find a quiet environment with good lighting.',
                                    'Camera and microphone must be ready and working.',
                                    'Once started, complete the session without interruption.',
                                ].map(tip => (
                                    <li key={tip} className="flex items-start gap-2">
                                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                                        <span>{tip}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
