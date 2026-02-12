interface ConnectParams {
    interviewId: string;
    candidateToken: string;
    onOpen: () => void;
    onTerminate: (reason: string) => void;
    onError: (error: Event) => void;
    onClose: () => void;
}

class ControlWebSocket {
    private ws: WebSocket | null = null;
    private heartbeatIntervalId: ReturnType<typeof setInterval> | null = null;
    private heartbeatIntervalSec: number = 10;

    connect(params: ConnectParams): void {
        const { interviewId, candidateToken, onOpen, onTerminate, onError, onClose } = params;

        if (this.ws) {
            this.disconnect();
        }

        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
        const wsUrl = baseUrl
            .replace(/^https:/, "wss:")
            .replace(/^http:/, "ws:");

        this.ws = new WebSocket(`${wsUrl}/api/v1/proctoring/ws`);

        this.ws.onopen = () => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: "HANDSHAKE",
                    interview_id: interviewId,
                    candidate_token: candidateToken,
                }));
            }
        };

        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);

                if (message.type === "HANDSHAKE_ACK") {
                    this.heartbeatIntervalSec = message.heartbeat_interval_sec || 10;
                    this.startHeartbeat();
                    onOpen();
                } else if (message.type === "HEARTBEAT_ACK") {
                    // Do nothing
                } else if (message.type === "TERMINATE") {
                    this.stopHeartbeat();
                    const reason = message.payload?.reason || "Unknown reason";
                    onTerminate(reason);
                    this.ws?.close();
                }
            } catch (error) {
                // Invalid JSON, ignore
            }
        };

        this.ws.onerror = (error) => {
            onError(error);
        };

        this.ws.onclose = () => {
            this.stopHeartbeat();
            onClose();
        };
    }

    disconnect(): void {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    private startHeartbeat(): void {
        this.stopHeartbeat();
        this.heartbeatIntervalId = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: "HEARTBEAT" }));
            }
        }, this.heartbeatIntervalSec * 1000);
    }

    private stopHeartbeat(): void {
        if (this.heartbeatIntervalId) {
            clearInterval(this.heartbeatIntervalId);
            this.heartbeatIntervalId = null;
        }
    }
}

export const controlWebSocket = new ControlWebSocket();
