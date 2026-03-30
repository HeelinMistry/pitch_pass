const API_BASE = "http://localhost:8000/api/v1";

export async function apiRequest(endpoint, method = "GET", body = null) {
    const token = localStorage.getItem('pitchpass_token');

    const headers = {
        'Content-Type': 'application/json',
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        method,
        headers,
        credentials: 'include',
    };

    if (body) {
        config.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);

        // Auto-handle expired sessions
        if (response.status === 401) {
            localStorage.removeItem('pitchpass_token');
            const currentPath = encodeURIComponent(window.location.pathname + window.location.search);
            window.location.href = `login.html?redirect=${currentPath}`;
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}