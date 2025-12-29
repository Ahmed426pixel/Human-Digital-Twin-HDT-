// Main Application Entry Point
console.log('🚀 HDT Application Starting...');

// Global state
window.sceneManager = null;
window.appState = {
    initialized: false,
    user: null,
    session: null,
    profile: null
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    console.log('✓ DOM loaded');
    
    try {
        // Initialize UI controller
        uiController.init();
        console.log('✓ UI Controller initialized');

        // Check if user is already logged in
        if (api.token) {
            try {
                uiController.showLoading('Loading your Digital Twin...');
                const userData = await api.getCurrentUser();
                uiController.currentUser = userData.user;
                
                // Connect WebSocket
                api.connectWebSocket();
                
                // Show main content
                uiController.showMainContent();
                
                // Initialize 3D scene
                initializeScene();
                
                uiController.hideLoading();
                
            } catch (error) {
                console.error('Auto-login failed:', error);
                api.logout();
                uiController.hideLoading();
            }
        } else {
            // Show auth panel
            uiController.hideLoading();
        }

        // Setup WebSocket listeners
        setupWebSocketListeners();

        window.appState.initialized = true;
        console.log('✅ Application initialized successfully');

    } catch (error) {
        console.error('❌ Initialization error:', error);
        alert('Failed to initialize application: ' + error.message);
    }
});

// Initialize 3D Scene
function initializeScene() {
    try {
        if (!window.sceneManager) {
            window.sceneManager = new SceneManager('threejs-container');
            console.log('✓ 3D Scene initialized');
        }
    } catch (error) {
        console.error('✗ Scene initialization error:', error);
        // Show error message to user
        const container = document.getElementById('threejs-container');
        container.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; color: #ff6b6b;">
                <div style="text-align: center;">
                    <h3>⚠️ 3D Visualization Error</h3>
                    <p>Failed to initialize 3D scene.</p>
                    <p style="font-size: 0.875rem; color: #a0a0a0;">${error.message}</p>
                </div>
            </div>
        `;
    }
}

// Setup WebSocket Event Listeners
function setupWebSocketListeners() {
    if (!api.socket) return;

    // Listen for physiological data updates
    api.socket.on('physiological_data', (data) => {
        console.log('Received physiological update:', data);
        
        if (window.sceneManager && data.session_id === uiController.currentSession?.session_id) {
            uiController.updateMonitoringUI(data);
        }
    });

    // Listen for activity updates
    api.socket.on('activity_data', (data) => {
        console.log('Received activity update:', data);
    });

    // Handle connection errors
    api.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
    });

    // Handle reconnection
    api.socket.on('reconnect', (attemptNumber) => {
        console.log(`✓ Reconnected after ${attemptNumber} attempts`);
    });
}

// Global error handler
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    // End session if active
    if (uiController.currentSession) {
        navigator.sendBeacon(
            `${API_BASE_URL}/sessions/${uiController.currentSession.session_id}/end`,
            JSON.stringify({})
        );
    }

    // Disconnect WebSocket
    if (api.socket) {
        api.socket.disconnect();
    }

    // Dispose 3D scene
    if (window.sceneManager) {
        window.sceneManager.dispose();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to send chat message
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const chatInput = document.getElementById('chat-input');
        if (document.activeElement === chatInput) {
            uiController.sendChatMessage();
        }
    }

    // Escape to close modals (if any)
    if (e.key === 'Escape') {
        // Handle escape key
    }
});

// Utility functions
window.HDT = {
    // Get current application state
    getState: () => window.appState,
    
    // Send custom command to AI
    sendCommand: async (command, taskType = 'general') => {
        if (!uiController.currentSession) {
            throw new Error('No active session');
        }
        
        const result = await api.createTask(
            uiController.currentSession.session_id,
            uiController.currentProfile.profile_id,
            command,
            taskType
        );
        
        return result;
    },
    
    // Update avatar state manually
    updateAvatar: (stateData) => {
        if (window.sceneManager) {
            window.sceneManager.updateAvatarState(stateData);
        }
    },
    
    // Get session statistics
    getSessionStats: async () => {
        if (!uiController.currentSession) {
            return null;
        }
        
        const tasks = await api.getTasks(uiController.currentSession.session_id);
        const state = await api.getCurrentState(uiController.currentSession.session_id);
        
        return {
            session: uiController.currentSession,
            tasks: tasks.tasks,
            currentState: state
        };
    }
};

console.log('💡 HDT utilities available via window.HDT');
console.log('   Example: HDT.sendCommand("Create a Python hello world")');