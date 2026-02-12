interface ConnectParams {
    onOpen: () => void;
    onError: (error: Event) => void;
    onClose: () => void;
}

class MediaWebSocket {
    private ws: WebSocket | null = null;
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 3;
    private manualClose: boolean = false;
    private connectParams: ConnectParams | null = null;

    connect(params: ConnectParams): void {
        if (this.ws) {
            this.disconnect();
        }

        this.connectParams = params;
        this.reconnectAttempts = 0;
        this.manualClose = false;

        this.establishConnection();
    }

    private establishConnection(): void {
        if (!this.connectParams) {
            return;
        }

        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
        const wsUrl = baseUrl
            .replace(/^https:/, "wss:")
            .replace(/^http:/, "ws:");

        this.ws = new WebSocket(`${wsUrl}/api/v1/proctoring/media/ws`);

        this.ws.onopen = () => {
            this.connectParams?.onOpen();
        };

        this.ws.onerror = (error) => {
            this.connectParams?.onError(error);
        };

        this.ws.onclose = () => {
            if (!this.manualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                setTimeout(() => {
                    this.establishConnection();
                }, 1000);
            } else {
                this.connectParams?.onClose();
            }
        };
    }

    send(data: ArrayBuffer): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        }
    }

    disconnect(): void {
        this.manualClose = true;
        this.reconnectAttempts = 0;
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

export const mediaWebSocket = new MediaWebSocket();
