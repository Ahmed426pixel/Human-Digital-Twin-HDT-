// UI Controller for HDT Frontend - WITH TYPING ANIMATION
class UIController {
    constructor() {
        this.currentUser = null;
        this.currentProfile = null;
        this.currentSession = null;
        this.sessionTimer = null;
        this.sessionStartTime = null;
    }

    // Initialize UI
    init() {
        this.setupAuthListeners();
        this.setupProfileListeners();
        this.setupSessionListeners();
        this.setupChatListeners();
    }

    // Auth Listeners
    setupAuthListeners() {
        // Show register form
        document.getElementById('show-register').addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('register-form').style.display = 'block';
            document.getElementById('auth-title').textContent = 'Create Your Account';
        });

        // Show login form
        document.getElementById('show-login').addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('register-form').style.display = 'none';
            document.getElementById('login-form').style.display = 'block';
            document.getElementById('auth-title').textContent = 'Login to Your Digital Twin';
        });

        // Register submit
        document.getElementById('register-submit').addEventListener('click', async () => {
            await this.handleRegister();
        });

        // Login submit
        document.getElementById('login-submit').addEventListener('click', async () => {
            await this.handleLogin();
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.handleLogout();
        });

        // Enter key for login
        document.getElementById('login-password').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleLogin();
            }
        });

        // Enter key for register
        document.getElementById('register-password').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleRegister();
            }
        });
    }

    async handleRegister() {
        const username = document.getElementById('register-username').value.trim();
        const email = document.getElementById('register-email').value.trim();
        const fullname = document.getElementById('register-fullname').value.trim();
        const password = document.getElementById('register-password').value;

        if (!username || !email || !password) {
            this.showError('Please fill in all required fields');
            return;
        }

        try {
            this.showLoading('Creating account...');
            await api.register(username, email, password, fullname);
            
            // Auto login with the SAME credentials
            const data = await api.login(username, password);
            this.currentUser = data.user;
            
            // Connect WebSocket
            api.connectWebSocket();
            
            this.hideLoading();
            this.showMainContent();
            
            // Initialize 3D scene
            if (typeof initializeScene === 'function') {
                initializeScene();
            }
            
        } catch (error) {
            this.hideLoading();
            this.showError(error.message);
        }
    }

    async handleLogin() {
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;

        if (!username || !password) {
            this.showError('Please enter username and password');
            return;
        }

        try {
            this.showLoading('Logging in...');
            const data = await api.login(username, password);
            this.currentUser = data.user;
            
            // Connect WebSocket
            api.connectWebSocket();
            
            this.hideLoading();
            this.showMainContent();
            
            // Initialize 3D scene
            if (typeof initializeScene === 'function') {
                initializeScene();
            }
            
        } catch (error) {
            this.hideLoading();
            this.showError(error.message);
        }
    }

    handleLogout() {
        if (this.currentSession) {
            api.endSession(this.currentSession.session_id);
            this.stopSessionTimer();
        }
        
        api.logout();
        this.currentUser = null;
        this.currentProfile = null;
        this.currentSession = null;
        
        location.reload();
    }

    showError(message) {
        const errorEl = document.getElementById('auth-error');
        errorEl.textContent = message;
        errorEl.style.display = 'block';
        
        setTimeout(() => {
            errorEl.style.display = 'none';
        }, 5000);
    }

    showMainContent() {
        document.getElementById('auth-panel').style.display = 'none';
        document.getElementById('main-content').style.display = 'grid';
        document.getElementById('user-info').textContent = `👤 ${this.currentUser.username}`;
    }

    // Profile Listeners
    setupProfileListeners() {
        const profileBtns = document.querySelectorAll('.profile-btn');
        
        profileBtns.forEach(btn => {
            btn.addEventListener('click', async () => {
                const roleType = btn.dataset.role;
                await this.selectProfile(roleType);
            });
        });
    }

    async selectProfile(roleType) {
        try {
            // Remove active class from all buttons
            document.querySelectorAll('.profile-btn').forEach(b => {
                b.classList.remove('active');
            });

            // Add active class to selected button
            event.target.closest('.profile-btn').classList.add('active');

            // Check if profile exists, if not create it
            const profilesData = await api.getProfiles();
            let profile = profilesData.profiles.find(p => p.role_type === roleType);

            if (!profile) {
                const created = await api.createProfile(roleType);
                profile = created.profile;
            }

            this.currentProfile = profile;
            console.log('✓ Profile selected:', profile.role_type);

            // Load 3D model for this role
            if (window.sceneManager) {
                await window.sceneManager.loadRole(roleType);
            }

            // Enable session start button
            document.getElementById('start-session-btn').disabled = false;

        } catch (error) {
            console.error('Profile selection error:', error);
            alert('Failed to select profile: ' + error.message);
        }
    }

    // Session Listeners
    setupSessionListeners() {
        document.getElementById('start-session-btn').addEventListener('click', async () => {
            await this.startSession();
        });

        document.getElementById('end-session-btn').addEventListener('click', async () => {
            await this.endSession();
        });
    }

    async startSession() {
        if (!this.currentProfile) {
            alert('Please select a role first');
            return;
        }

        try {
            const data = await api.startSession(this.currentProfile.profile_id);
            this.currentSession = data.session;
            
            // Subscribe to real-time updates
            api.subscribeToSession(this.currentSession.session_id);

            // Update UI
            document.getElementById('start-session-btn').style.display = 'none';
            document.getElementById('end-session-btn').style.display = 'block';
            document.getElementById('session-info').style.display = 'block';

            // Start session timer
            this.startSessionTimer();

            // Start simulated monitoring
            this.startMonitoring();

            console.log('✓ Session started:', this.currentSession.session_id);

        } catch (error) {
            console.error('Session start error:', error);
            alert('Failed to start session: ' + error.message);
        }
    }

    async endSession() {
        if (!this.currentSession) return;

        try {
            await api.endSession(this.currentSession.session_id);
            
            // Stop monitoring
            this.stopMonitoring();
            this.stopSessionTimer();

            // Update UI
            document.getElementById('start-session-btn').style.display = 'block';
            document.getElementById('end-session-btn').style.display = 'none';
            document.getElementById('session-info').style.display = 'none';

            this.currentSession = null;
            console.log('✓ Session ended');

        } catch (error) {
            console.error('Session end error:', error);
            alert('Failed to end session: ' + error.message);
        }
    }

    startSessionTimer() {
        this.sessionStartTime = Date.now();
        this.sessionTimer = setInterval(() => {
            const elapsed = Date.now() - this.sessionStartTime;
            const hours = Math.floor(elapsed / 3600000);
            const minutes = Math.floor((elapsed % 3600000) / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            const timeStr = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            document.getElementById('session-duration').textContent = timeStr;
        }, 1000);
    }

    stopSessionTimer() {
        if (this.sessionTimer) {
            clearInterval(this.sessionTimer);
            this.sessionTimer = null;
        }
    }

    // Monitoring (simulated for demo)
    startMonitoring() {
        this.monitoringInterval = setInterval(() => {
            const data = this.generateSimulatedData();
            this.updateMonitoringUI(data);
            
            // Send to backend
            api.submitPhysiologicalData(this.currentSession.session_id, data);
        }, 2000);
    }

    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }
    }

    generateSimulatedData() {
        // Generate realistic fluctuating values
        return {
            heart_rate: 60 + Math.floor(Math.random() * 30),
            stress_level: 20 + Math.random() * 40,
            cognitive_load: 30 + Math.random() * 50,
            fatigue_score: 10 + Math.random() * 30,
            posture_score: 70 + Math.random() * 20
        };
    }

    updateMonitoringUI(data) {
        // Update stress bar
        this.updateMetric('stress', data.stress_level);
        
        // Update cognitive load bar
        this.updateMetric('cognitive', data.cognitive_load);
        
        // Update fatigue bar
        this.updateMetric('fatigue', data.fatigue_score);

        // Update avatar state
        if (window.sceneManager) {
            window.sceneManager.updateAvatarState(data);
        }

        // Update avatar status badge
        const badge = document.getElementById('avatar-state');
        if (data.stress_level < 30) {
            badge.textContent = 'Optimal';
            badge.className = 'state-badge state-optimal';
        } else if (data.stress_level < 60) {
            badge.textContent = 'Moderate';
            badge.className = 'state-badge state-moderate';
        } else {
            badge.textContent = 'Critical';
            badge.className = 'state-badge state-critical';
        }
    }

    updateMetric(name, value) {
        const bar = document.getElementById(`${name}-bar`);
        const valueEl = document.getElementById(`${name}-value`);
        
        bar.style.width = `${value}%`;
        valueEl.textContent = `${Math.round(value)}%`;

        // Update color based on value
        bar.className = 'metric-fill';
        if (value < 30) {
            // Green - optimal
        } else if (value < 60) {
            bar.classList.add('warning');
        } else {
            bar.classList.add('danger');
        }
    }

    // Chat Listeners
    setupChatListeners() {
        document.getElementById('send-chat-btn').addEventListener('click', () => {
            this.sendChatMessage();
        });

        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendChatMessage();
            }
        });
    }

    async sendChatMessage() {
        if (!this.currentSession) {
            alert('Please start a session first');
            return;
        }

        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) return;

        // Add user message to chat
        this.addChatMessage('user', message);
        input.value = '';

        // Check if message is code-related
        const isCodeRelated = this.isCodeRelatedMessage(message);

        try {
            // Start typing animation for code-related tasks
            if (isCodeRelated && window.sceneManager) {
                window.sceneManager.startTypingAnimation();
            }

            // Send to AI
            const response = await api.sendChatMessage(this.currentSession.session_id, message);

            // Stop typing animation
            if (isCodeRelated && window.sceneManager) {
                // Keep typing for a bit longer to make it feel realistic
                setTimeout(() => {
                    window.sceneManager.stopTypingAnimation();
                }, 2000);
            }

            // Add AI response
            this.addChatMessage('assistant', response.response);

            // Update task list
            await this.updateTaskList();

        } catch (error) {
            console.error('Chat error:', error);
            if (window.sceneManager) {
                window.sceneManager.stopTypingAnimation();
            }
            this.addChatMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        }
    }

    isCodeRelatedMessage(message) {
        // Check if the message contains code-related keywords
        const codeKeywords = [
            'code', 'write', 'create', 'build', 'develop', 'implement',
            'function', 'class', 'algorithm', 'program', 'script',
            'python', 'javascript', 'java', 'c++', 'html', 'css',
            'debug', 'fix', 'error', 'bug', 'api', 'database',
            'generate', 'make', 'design', 'coding', 'software'
        ];
        
        const lowerMessage = message.toLowerCase();
        return codeKeywords.some(keyword => lowerMessage.includes(keyword));
    }

    addChatMessage(role, text) {
        const container = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;
        
        // Parse code blocks
        const formattedText = this.formatMessageText(text);
        messageDiv.innerHTML = formattedText;
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
    }

    formatMessageText(text) {
        // Simple code block formatting
        return text
            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
            .replace(/\n/g, '<br>');
    }

    async updateTaskList() {
        try {
            const data = await api.getTasks(this.currentSession.session_id);
            const taskList = document.getElementById('task-list');
            
            taskList.innerHTML = '';
            
            if (data.tasks.length === 0) {
                taskList.innerHTML = '<p class="empty-state">No tasks yet</p>';
                return;
            }

            data.tasks.slice(0, 5).forEach(task => {
                const taskDiv = document.createElement('div');
                taskDiv.className = `task-item ${task.task_status}`;
                taskDiv.innerHTML = `
                    <div class="task-type">${task.task_type}</div>
                    <div class="task-command">${this.truncateText(task.command_text, 50)}</div>
                    <div class="task-time">${this.formatTime(task.created_at)}</div>
                `;
                taskList.appendChild(taskDiv);
            });

            // Update task count
            const completed = data.tasks.filter(t => t.task_status === 'completed').length;
            document.getElementById('tasks-completed').textContent = completed;

        } catch (error) {
            console.error('Failed to update task list:', error);
        }
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    formatTime(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        
        return date.toLocaleDateString();
    }

    showLoading(message) {
        const screen = document.getElementById('loading-screen');
        const status = document.getElementById('loading-status');
        status.textContent = message;
        screen.style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading-screen').style.display = 'none';
        document.getElementById('app').style.display = 'flex';
    }
}

// Create global UI controller
const uiController = new UIController();