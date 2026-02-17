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
        // Build the full payload as per backend API requirements
        // Explicitly set optional fields to null/undefined or empty arrays to satisfy strict backend validation
        const payload: CandidateRegistration = {
            username: request.username,
            email: request.email,
            password: request.password,
            role: "candidate",
            profile: {
                // We must provide at least one field or ensure the structure matches CandidateProfile
                // to avoid ambiguity with other profile types in the backend Union
                skills: [],
                experience_years: 0,
                first_name: "",
                last_name: "",
                phone: ""
            }
        };
        return apiClient.post<TokenResponse, CandidateRegistration>("/api/v1/auth/register/candidate", payload);
    },

    logout: () => {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user");
    }
};
