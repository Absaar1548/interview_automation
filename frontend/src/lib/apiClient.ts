import { ApiError } from "@/types/api";

class ApiClient {
    private baseURL: string;
    private interviewId: string | null = null;

    constructor(baseURL: string) {
        this.baseURL = baseURL;
    }

    setInterviewId(id: string): void {
        this.interviewId = id;
    }

    clearInterviewId(): void {
        this.interviewId = null;
    }

    private log(message: string): void {
        if (process.env.NODE_ENV === "development") {
            console.debug(`[ApiClient] ${message}`);
        }
    }

    private getAuthToken(): string | null {
        // We can access localStorage directly since this runs on client
        if (typeof window !== 'undefined') {
            try {
                const storage = localStorage.getItem('auth-storage');
                if (storage) {
                    const parsed = JSON.parse(storage);
                    return parsed.state?.token || null;
                }
            } catch (error) {
                console.error("Failed to parse auth token from storage", error);
            }
        }
        return null;
    }

    async get<T>(path: string, requireInterviewId: boolean = false): Promise<T> {
        this.log(`REQUEST: GET ${path}`);

        const headers: Record<string, string> = {
            "Content-Type": "application/json",
        };

        const token = this.getAuthToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        if (requireInterviewId) {
            if (!this.interviewId) {
                const error: ApiError = {
                    error_code: "MISSING_INTERVIEW_ID",
                    message: "Interview ID is required but not set",
                    current_state: null,
                };
                this.log(`ERROR: GET ${path} - MISSING_INTERVIEW_ID`);
                throw error;
            }
            headers["X-Interview-Id"] = this.interviewId;
        }

        const response = await fetch(`${this.baseURL}${path}`, {
            method: "GET",
            headers,
        });

        const text = await response.text();
        // ... rest is same
        const data = text ? JSON.parse(text) : null;

        this.log(`RESPONSE: GET ${path} - ${response.status}`);

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                // Optional: Trigger logout if we had a global store reference or event
                // For now just throw, UI should handle redirect
            }

            if (data && typeof data === "object" && "error_code" in data && "message" in data) {
                this.log(`ERROR: GET ${path} - ${data.error_code}`);
                throw data as ApiError;
            }
            const error: ApiError = {
                error_code: "HTTP_ERROR",
                message: `Request failed with status ${response.status}`,
                current_state: null,
            };
            this.log(`ERROR: GET ${path} - HTTP_ERROR`);
            throw error;
        }

        return data as T;
    }

    async post<T, B>(path: string, body: B, requireInterviewId: boolean = false, isFormData: boolean = false): Promise<T> {
        this.log(`REQUEST: POST ${path}`);

        const headers: Record<string, string> = {};

        if (!isFormData) {
            headers["Content-Type"] = "application/json";
        }

        const token = this.getAuthToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        if (requireInterviewId) {
            if (!this.interviewId) {
                const error: ApiError = {
                    error_code: "MISSING_INTERVIEW_ID",
                    message: "Interview ID is required but not set",
                    current_state: null,
                };
                this.log(`ERROR: POST ${path} - MISSING_INTERVIEW_ID`);
                throw error;
            }
            headers["X-Interview-Id"] = this.interviewId;
        }

        const response = await fetch(`${this.baseURL}${path}`, {
            method: "POST",
            headers,
            body: isFormData ? (body as any) : JSON.stringify(body),
        });

        const text = await response.text();
        const data = text ? JSON.parse(text) : null;

        this.log(`RESPONSE: POST ${path} - ${response.status}`);

        if (!response.ok) {
            if (data && typeof data === "object" && "error_code" in data && "message" in data) {
                this.log(`ERROR: POST ${path} - ${data.error_code}`);
                throw data as ApiError;
            }
            const error: ApiError = {
                error_code: "HTTP_ERROR",
                message: `Request failed with status ${response.status}`,
                current_state: null,
            };
            this.log(`ERROR: POST ${path} - HTTP_ERROR`);
            throw error;
        }

        return data as T;
    }
}

export const apiClient = new ApiClient(process.env.NEXT_PUBLIC_API_BASE_URL!);
