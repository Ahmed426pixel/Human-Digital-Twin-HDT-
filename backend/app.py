from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from config import Config
from database import init_db, DatabaseManager
from api import api
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Register API blueprint
app.register_blueprint(api, url_prefix='/api')

# ============================================
# SERVE FRONTEND FILES
# ============================================

@app.route('/')
def index():
    """Serve the main HTML page"""
    try:
        return send_from_directory(FRONTEND_DIR, 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return jsonify({
            'error': 'Frontend not found',
            'frontend_dir': FRONTEND_DIR,
            'exists': os.path.exists(FRONTEND_DIR)
        }), 404

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    try:
        return send_from_directory(os.path.join(FRONTEND_DIR, 'css'), filename)
    except Exception as e:
        logger.warning(f"CSS file not found: {filename}")
        return jsonify({'error': f'CSS file not found: {filename}'}), 404

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    try:
        return send_from_directory(os.path.join(FRONTEND_DIR, 'js'), filename)
    except Exception as e:
        logger.warning(f"JS file not found: {filename}")
        return jsonify({'error': f'JS file not found: {filename}'}), 404

@app.route('/models/<path:filename>')
def serve_models(filename):
    """Serve 3D model files"""
    try:
        return send_from_directory(os.path.join(FRONTEND_DIR, 'models'), filename)
    except Exception as e:
        logger.warning(f"Model file not found: {filename}")
        return jsonify({'error': f'Model file not found: {filename}'}), 404

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/health')
def health():
    """Health check endpoint"""
    db_status = DatabaseManager.test_connection()
    
    return jsonify({
        'status': 'healthy' if db_status else 'unhealthy',
        'database': 'connected' if db_status else 'disconnected',
        'timestamp': datetime.now().isoformat()
    }), 200 if db_status else 503

# ============================================
# WEBSOCKET EVENTS (Real-time monitoring)
# ============================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('subscribe_session')
def handle_subscribe(data):
    """Subscribe to session updates"""
    session_id = data.get('session_id')
    logger.info(f'Client subscribed to session {session_id}')
    emit('subscription_confirmed', {'session_id': session_id})

@socketio.on('physiological_update')
def handle_physiological_update(data):
    """Receive real-time physiological data"""
    session_id = data.get('session_id')
    emit('physiological_data', data, broadcast=True)

@socketio.on('activity_update')
def handle_activity_update(data):
    """Receive real-time activity data"""
    session_id = data.get('session_id')
    emit('activity_data', data, broadcast=True)

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal server error: {error}')
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f'Unhandled exception: {error}')
    return jsonify({'error': str(error)}), 500

# ============================================
# APPLICATION STARTUP
# ============================================

def initialize_app():
    """Initialize application"""
    print("\n" + "="*60)
    print("🚀 INDUSTRY-LEVEL HUMAN DIGITAL TWIN - BACKEND")
    print("="*60 + "\n")
    
    # Show directory structure
    print(f"📁 Backend directory:  {BACKEND_DIR}")
    print(f"📁 Frontend directory: {FRONTEND_DIR}")
    
    # Check if frontend exists
    if os.path.exists(FRONTEND_DIR):
        print("✓ Frontend directory found")
        
        # Check for key files
        index_path = os.path.join(FRONTEND_DIR, 'index.html')
        if os.path.exists(index_path):
            print("✓ index.html found")
        else:
            print("⚠️  WARNING: index.html not found!")
            
        css_path = os.path.join(FRONTEND_DIR, 'css')
        if os.path.exists(css_path):
            print(f"✓ CSS directory found")
            
        js_path = os.path.join(FRONTEND_DIR, 'js')
        if os.path.exists(js_path):
            print(f"✓ JS directory found")
    else:
        print("⚠️  WARNING: Frontend directory not found!")
        print(f"   Expected at: {FRONTEND_DIR}")
    
    print()
    
    # Validate configuration
    Config.validate()
    
    # Test database connection
    print("📊 Testing database connection...")
    if DatabaseManager.test_connection():
        print("✓ Database connected successfully\n")
    else:
        print("✗ Database connection failed!")
        print("   Please check your database configuration in .env\n")
        return False
    
    # Initialize database tables
    print("📊 Initializing database tables...")
    if init_db():
        print("✓ Database tables ready\n")
    else:
        print("✗ Database initialization failed\n")
        return False
    
    print("="*60)
    print("✅ BACKEND INITIALIZED SUCCESSFULLY")
    print("="*60)
    print(f"\n🌐 Server running on http://localhost:5000")
    print(f"📡 WebSocket available on ws://localhost:5000")
    print(f"🎨 Frontend UI: http://localhost:5000")
    print(f"\n📚 API Endpoints:")
    print(f"   Health Check: GET  http://localhost:5000/health")
    print(f"   Register:     POST http://localhost:5000/api/auth/register")
    print(f"   Login:        POST http://localhost:5000/api/auth/login")
    print(f"   Start Session:POST http://localhost:5000/api/sessions/start")
    print(f"\n💡 Press CTRL+C to stop the server\n")
    
    return True

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    if initialize_app():
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=Config.DEBUG,
            allow_unsafe_werkzeug=True
        )
    else:
        print("\n❌ Failed to start application")
        print("   Please fix the errors above and try again\n")