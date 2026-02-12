interface ConnectParams {
    questionId: string;
    onOpen: () => void;
    onPartialTranscript: (text: string) => void;
    onFinalTranscript: (text: string) => void;
    onAnswerReady: (transcriptId: string) => void;
    onError: (error: Event) => void;
    onClose: () => void;
}

class AnswerWebSocket {
    private ws: WebSocket | null = null;
    private questionId: string | null = null;

    connect(params: ConnectParams): void {
        const { questionId, onOpen, onPartialTranscript, onFinalTranscript, onAnswerReady, onError, onClose } = params;

        if (this.ws) {
            this.disconnect();
        }

        this.questionId = questionId;

        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
        const wsUrl = baseUrl
            .replace(/^https:/, "wss:")
            .replace(/^http:/, "ws:");

        this.ws = new WebSocket(`${wsUrl}/api/v1/answer/ws`);

        this.ws.onopen = () => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN && this.questionId) {
                this.ws.send(JSON.stringify({
                    type: "START_ANSWER",
                    question_id: this.questionId,
                }));
                onOpen();
            }
        };

        this.ws.onmessage = (event) => {
            if (!this.questionId) return;

            try {
                const message = JSON.parse(event.data);

                if (message.type === "TRANSCRIPT_PARTIAL") {
                    onPartialTranscript(message.text);
                } else if (message.type === "TRANSCRIPT_FINAL") {
                    onFinalTranscript(message.text);
                } else if (message.type === "ANSWER_READY") {
                    onAnswerReady(message.transcript_id);
                    this.disconnect();
                }
            } catch (error) {
                // Invalid JSON, ignore
            }
        };

        this.ws.onerror = (error) => {
            onError(error);
        };

        this.ws.onclose = () => {
            onClose();
        };
    }

    sendAudio(data: ArrayBuffer): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        }
    }

    endAnswer(): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: "END_ANSWER",
            }));
        }
    }

    disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.questionId = null;
    }
}

export const answerWebSocket = new AnswerWebSocket();
