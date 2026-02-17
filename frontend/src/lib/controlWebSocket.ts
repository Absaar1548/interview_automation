interface ConnectParams {
    interviewId: string;
    candidateToken: string;
    onOpen: () => void;
    onTerminate: (reason: string) => void;
    onError: (error: Event) => void;
    onClose: (event: CloseEvent) => void;
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

        const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || "").replace(/\/$/, "");
        const wsUrl = baseUrl
            .replace(/^https:/, "wss:")
            .replace(/^http:/, "ws:");

        const fullUrl = `${wsUrl}/api/v1/proctoring/ws`;
        console.log(`[ControlWebSocket] Connecting to: ${fullUrl}`);
        this.ws = new WebSocket(fullUrl);

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

        this.ws.onclose = (event) => {
            this.stopHeartbeat();
            onClose(event);
        };
    }

    disconnect(): void {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.onclose = null; // Prevent triggering onClose during manual disconnect
            this.ws.onerror = null;
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
