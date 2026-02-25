import { apiClient } from "./apiClient";
import { AuthRequest, TokenResponse, CandidateRegistrationRequest, CandidateRegistration } from "@/types/api";

export const authService = {
    loginAdmin: async (credentials: AuthRequest): Promise<TokenResponse> => {
        return apiClient.post<TokenResponse, AuthRequest>("/api/v1/auth/login/admin", credentials);
    },

    loginCandidate: async (credentials: AuthRequest): Promise<TokenResponse> => {
        return apiClient.post<TokenResponse, AuthRequest>("/api/v1/auth/login/candidate", credentials);
    },

    registerCandidateByAdmin: async (request: CandidateRegistrationRequest): Promise<TokenResponse> => {
        // ... (Keep existing implementation for backward compatibility if needed, or deprecate)
        // For now, I will modify this to use the new route or create a new method.
        // The instruction was to "Add registerCandidateWithResume".
        // Let's add the new method.
        const payload: CandidateRegistration = {
            username: request.username,
            email: request.email,
            password: request.password,
            role: "candidate",
            profile: {
                skills: [],
                experience_years: 0,
                first_name: "",
                last_name: "",
                phone: ""
            }
        };
        return apiClient.post<TokenResponse, CandidateRegistration>("/api/v1/auth/register/candidate", payload);
    },

    registerCandidateWithResume: async (formData: FormData): Promise<import("@/types/api").CandidateResponse> => {
        // Last argument true -> isFormData
        return apiClient.post<import("@/types/api").CandidateResponse, FormData>(
            "/api/v1/auth/admin/register-candidate",
            formData,
            false,
            true
        );
    },

    logout: () => {
        if (typeof window !== 'undefined') {
            localStorage.removeItem("auth-storage");
        }
    }
};
