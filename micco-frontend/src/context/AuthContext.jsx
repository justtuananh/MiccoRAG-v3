import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '') + '/api';
const SKIP_AUTH = import.meta.env.VITE_SKIP_AUTH === 'true';

const MOCK_USER = {
    id: 1,
    name: 'Admin (Dev)',
    email: 'admin@micco.vn',
    role: 'Admin',
    department_id: null,
    department_name: null,
    avatar: null,
};

export function AuthProvider({ children }) {
    const [user, setUser] = useState(SKIP_AUTH ? MOCK_USER : null);
    const [token, setToken] = useState(SKIP_AUTH ? 'dev-skip' : localStorage.getItem('docvault_token'));
    const [isAuthenticated, setIsAuthenticated] = useState(SKIP_AUTH);
    const [loading, setLoading] = useState(!SKIP_AUTH);

    // Auto-login on mount if token exists (skipped in dev bypass mode)
    useEffect(() => {
        if (SKIP_AUTH) return;
        if (token) {
            fetchUser(token);
        } else {
            setLoading(false);
        }
    }, []);

    const fetchUser = async (accessToken) => {
        try {
            const res = await fetch(`${API_BASE}/auth/me`, {
                headers: { Authorization: `Bearer ${accessToken}` },
            });
            if (res.ok) {
                const data = await res.json();
                setUser(data);
                setIsAuthenticated(true);
            } else {
                // Token expired or invalid
                localStorage.removeItem('docvault_token');
                setToken(null);
                setUser(null);
                setIsAuthenticated(false);
            }
        } catch (err) {
            console.error('Auth check failed:', err);
        } finally {
            setLoading(false);
        }
    };

    const login = async (email, password) => {
        try {
            const res = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Đăng nhập thất bại');
            }

            const data = await res.json();
            localStorage.setItem('docvault_token', data.access_token);
            setToken(data.access_token);
            await fetchUser(data.access_token);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.message };
        }
    };

    const register = async (name, email, password, department_id = null) => {
        try {
            const payload = { name, email, password };
            if (department_id) payload.department_id = department_id;
            const res = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                let msg = 'Đăng ký thất bại';
                try {
                    const err = await res.json();
                    msg = err.detail || err.message || msg;
                } catch {
                    // Not JSON — use default
                }
                throw new Error(msg);
            }

            const data = await res.json();
            localStorage.setItem('docvault_token', data.access_token);
            setToken(data.access_token);
            await fetchUser(data.access_token);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.message };
        }
    };

    const logout = () => {
        localStorage.removeItem('docvault_token');
        setToken(null);
        setUser(null);
        setIsAuthenticated(false);
    };

    // Helper for authenticated API calls
    const authFetch = async (url, options = {}) => {
        const currentToken = SKIP_AUTH ? 'dev-skip' : localStorage.getItem('docvault_token');
        const headers = {
            ...options.headers,
            Authorization: `Bearer ${currentToken}`,
        };
        const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
        const fullUrl = baseUrl && url.startsWith('/api') ? baseUrl + url : url;
        return fetch(fullUrl, { ...options, headers });
    };

    return (
        <AuthContext.Provider value={{
            user, isAuthenticated, loading, token,
            login, register, logout, authFetch
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
