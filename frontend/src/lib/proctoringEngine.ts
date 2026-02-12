import { mediaWebSocket } from "./mediaWebSocket";

class ProctoringEngine {
    private stream: MediaStream | null = null;
    private recorder: MediaRecorder | null = null;
    private isRunning: boolean = false;

    async start(): Promise<void> {
        if (this.isRunning) {
            return;
        }

        if (!window.MediaRecorder) {
            throw new Error("MediaRecorder not supported");
        }

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: 640,
                    height: 480,
                    frameRate: 15,
                },
                audio: true,
            });
        } catch (error) {
            throw error;
        }

        try {
            this.recorder = new MediaRecorder(this.stream);
        } catch (error) {
            if (this.stream) {
                this.stream.getTracks().forEach((track) => track.stop());
                this.stream = null;
            }
            throw error;
        }

        this.recorder.ondataavailable = async (event) => {
            if (event.data.size > 0) {
                const arrayBuffer = await event.data.arrayBuffer();
                if (!this.isRunning) return;
                mediaWebSocket.send(arrayBuffer);
            }
        };

        this.recorder.onerror = () => {
            this.stop();
        };

        mediaWebSocket.connect({
            onOpen: () => {
                this.isRunning = true;
                if (this.recorder) {
                    this.recorder.start(1000);
                }
            },
            onError: () => { },
            onClose: () => { },
        });
    }

    stop(): void {
        if (!this.isRunning) {
            return;
        }

        if (this.recorder) {
            this.recorder.stop();
            this.recorder = null;
        }

        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }

        mediaWebSocket.disconnect();
        this.isRunning = false;
    }
}

export const proctoringEngine = new ProctoringEngine();
