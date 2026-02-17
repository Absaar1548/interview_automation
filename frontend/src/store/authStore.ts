import { create } from "zustand";
import { persist } from "zustand/middleware";
import { authService } from "@/lib/authService";
import { AuthRequest } from "@/types/api";

interface User {
    username: string;
    role: string;
}

interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;

    login: (credentials: AuthRequest) => Promise<void>;
    register: (credentials: AuthRequest) => Promise<void>;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,

            login: async (credentials) => {
                set({ isLoading: true, error: null });
                try {
                    const response = await authService.login(credentials);
                    set({
                        user: { username: response.username, role: response.role },
                        token: response.access_token,
                        isAuthenticated: true,
                        isLoading: false,
                    });
                } catch (error) {
                    const message = error instanceof Error ? error.message : "Login failed";
                    set({ error: message, isLoading: false });
                    throw error;
                }
            },

            register: async (credentials) => {
                set({ isLoading: true, error: null });
                try {
                    await authService.register(credentials);
                    set({ isLoading: false });
                } catch (error) {
                    const message = error instanceof Error ? error.message : "Registration failed";
                    set({ error: message, isLoading: false });
                    throw error;
                }
            },

            logout: () => {
                authService.logout();
                set({ user: null, token: null, isAuthenticated: false });
            },
        }),
        {
            name: "auth-storage",
            partialize: (state) => ({ user: state.user, token: state.token, isAuthenticated: state.isAuthenticated }),
        }
    )
);
