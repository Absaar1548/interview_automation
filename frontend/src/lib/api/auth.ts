const API_URL = 'http://localhost:8000/api/v1/auth';

export interface AuthResponse {
    access_token?: string;
    token_type?: string;
    username: string;
    role?: string;
    message?: string;
}

export const registerUser = async (username: string, password: string): Promise<AuthResponse> => {
    const response = await fetch(`${API_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Registration failed');
    }

    return response.json();
};

export const loginUser = async (username: string, password: string): Promise<AuthResponse> => {
    const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
    }

    return response.json();
};
