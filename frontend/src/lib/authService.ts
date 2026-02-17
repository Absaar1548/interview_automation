import { apiClient } from "./apiClient";
import { AuthRequest, TokenResponse, RegisterResponse } from "@/types/api";

export const authService = {
    loginAdmin: async (credentials: AuthRequest): Promise<TokenResponse> => {
        return apiClient.post<TokenResponse, AuthRequest>("/api/v1/auth/login/admin", credentials);
    },

    loginCandidate: async (credentials: AuthRequest): Promise<TokenResponse> => {
        return apiClient.post<TokenResponse, AuthRequest>("/api/v1/auth/login/candidate", credentials);
    },

    register: async (credentials: AuthRequest): Promise<RegisterResponse> => {
        return apiClient.post<RegisterResponse, AuthRequest>("/api/v1/auth/register", credentials);
    },

    logout: () => {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user");
    }
};
