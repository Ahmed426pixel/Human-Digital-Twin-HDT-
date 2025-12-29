// API Client for HDT Backend
// Use relative URL to work from same origin
const API_BASE_URL = '/api';
const WS_BASE_URL = window.location.origin;

class APIClient {
    constructor() {
        this.token = localStorage.getItem('hdt_token');
        this.socket = null;
    }

    // Helper method for making requests
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Authentication
    async register(username, email, password, fullName = '') {
        const data = await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                username,
                email,
                password,
                full_name: fullName
            })
        });
        return data;
    }

    async login(username, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        if (data.token) {
            this.token = data.token;
            localStorage.setItem('hdt_token', data.token);
        }
        
        return data;
    }

    logout() {
        this.token = null;
        localStorage.removeItem('hdt_token');
        if (this.socket) {
            this.socket.disconnect();
        }
    }

    async getCurrentUser() {
        return await this.request('/auth/me');
    }

    // HDT Profiles
    async getProfiles() {
        return await this.request('/hdt/profiles');
    }

    async createProfile(roleType, displayName = null) {
        return await this.request('/hdt/profiles', {
            method: 'POST',
            body: JSON.stringify({
                role_type: roleType,
                display_name: displayName
            })
        });
    }

    async getRoles() {
        return await this.request('/hdt/roles');
    }

    // Session Management
    async startSession(profileId) {
        return await this.request('/sessions/start', {
            method: 'POST',
            body: JSON.stringify({ profile_id: profileId })
        });
    }

    async endSession(sessionId) {
        return await this.request(`/sessions/${sessionId}/end`, {
            method: 'POST'
        });
    }

    async getSessions() {
        return await this.request('/sessions');
    }

    // Monitoring
    async submitPhysiologicalData(sessionId, data) {
        return await this.request('/monitoring/physiological', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                ...data
            })
        });
    }

    async submitWorkActivity(sessionId, data) {
        return await this.request('/monitoring/work-activity', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                ...data
            })
        });
    }

    async getCurrentState(sessionId) {
        return await this.request(`/monitoring/current-state/${sessionId}`);
    }

    // AI Tasks
    async createTask(sessionId, profileId, command, taskType = 'general', context = null) {
        return await this.request('/tasks', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                profile_id: profileId,
                command,
                task_type: taskType,
                context
            })
        });
    }

    async getTasks(sessionId = null) {
        const query = sessionId ? `?session_id=${sessionId}` : '';
        return await this.request(`/tasks${query}`);
    }

    // Chat
    async sendChatMessage(sessionId, message) {
        return await this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                message
            })
        });
    }

    async getChatHistory(sessionId) {
        return await this.request(`/chat/history/${sessionId}`);
    }

    // WebSocket Connection
    connectWebSocket() {
        this.socket = io(WS_BASE_URL, {
            transports: ['websocket', 'polling']
        });

        this.socket.on('connect', () => {
            console.log('✓ WebSocket connected');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('✗ WebSocket disconnected');
            this.updateConnectionStatus(false);
        });

        this.socket.on('connection_response', (data) => {
            console.log('Connection response:', data);
        });

        return this.socket;
    }

    subscribeToSession(sessionId) {
        if (this.socket) {
            this.socket.emit('subscribe_session', { session_id: sessionId });
        }
    }

    sendPhysiologicalUpdate(data) {
        if (this.socket) {
            this.socket.emit('physiological_update', data);
        }
    }

    sendActivityUpdate(data) {
        if (this.socket) {
            this.socket.emit('activity_update', data);
        }
    }

    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        if (!statusEl) return;
        
        const dot = statusEl.querySelector('.status-dot');
        const text = statusEl.querySelector('.status-text');
        
        if (connected) {
            dot.classList.add('connected');
            text.textContent = 'Connected';
        } else {
            dot.classList.remove('connected');
            text.textContent = 'Disconnected';
        }
    }
}

// Create global API client instance
const api = new APIClient();