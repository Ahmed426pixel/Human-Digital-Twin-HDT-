from flask import Blueprint, request, jsonify
from database import Session
from models import User, HDTProfile, Session as WorkSession, PhysiologicalData, WorkActivity, AITask, AIInteraction
from ai_service import ai_service
from datetime import datetime, timedelta
import jwt
from config import Config
from functools import wraps
import logging

logger = logging.getLogger(__name__)
api = Blueprint('api', __name__)

# ============================================
# AUTHENTICATION DECORATOR
# ============================================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['user_id']
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@api.route('/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    db = Session()
    
    try:
        # Validate input
        if not all(k in data for k in ['username', 'email', 'password']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        if db.query(User).filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if db.query(User).filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create user
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data.get('full_name', '')
        )
        user.set_password(data['password'])
        
        db.add(user)
        db.commit()
        
        logger.info(f"✓ User registered: {user.username}")
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Registration error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.json
    db = Session()
    
    try:
        user = db.query(User).filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Update last login
        user.last_login = datetime.now()
        db.commit()
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.user_id,
            'exp': datetime.now() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
        }, Config.SECRET_KEY, algorithm='HS256')
        
        logger.info(f"✓ User logged in: {user.username}")
        return jsonify({
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Login error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user_id):
    """Get current user info"""
    db = Session()
    try:
        user = db.query(User).filter_by(user_id=current_user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
    finally:
        db.close()

# ============================================
# HDT PROFILE ENDPOINTS
# ============================================

@api.route('/hdt/profiles', methods=['GET'])
@token_required
def get_profiles(current_user_id):
    """Get all user profiles"""
    db = Session()
    try:
        profiles = db.query(HDTProfile).filter_by(user_id=current_user_id).all()
        return jsonify({
            'profiles': [p.to_dict() for p in profiles]
        }), 200
    finally:
        db.close()

@api.route('/hdt/profiles', methods=['POST'])
@token_required
def create_profile(current_user_id):
    """Create new HDT profile"""
    data = request.json
    db = Session()
    
    try:
        # Validate role type
        valid_roles = ['software_engineer', 'office_worker', 'factory_worker']
        if data.get('role_type') not in valid_roles:
            return jsonify({'error': 'Invalid role type'}), 400
        
        # Get capabilities for role
        capabilities = ai_service.get_role_capabilities(data['role_type'])
        
        profile = HDTProfile(
            user_id=current_user_id,
            role_type=data['role_type'],
            display_name=data.get('display_name', f"{data['role_type'].replace('_', ' ').title()}"),
            avatar_model_path=f"models/avatars/{data['role_type']}.fbx",
            capabilities=capabilities,
            preferences=data.get('preferences', {})
        )
        
        db.add(profile)
        db.commit()
        
        logger.info(f"✓ Profile created: {profile.role_type} for user {current_user_id}")
        return jsonify({
            'message': 'Profile created successfully',
            'profile': profile.to_dict()
        }), 201
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Profile creation error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/hdt/roles', methods=['GET'])
def get_roles():
    """Get available roles and capabilities"""
    roles = {
        'software_engineer': ai_service.get_role_capabilities('software_engineer'),
        'office_worker': ai_service.get_role_capabilities('office_worker'),
        'factory_worker': ai_service.get_role_capabilities('factory_worker')
    }
    return jsonify({'roles': roles}), 200

# ============================================
# SESSION MANAGEMENT
# ============================================

@api.route('/sessions/start', methods=['POST'])
@token_required
def start_session(current_user_id):
    """Start new work session"""
    data = request.json
    db = Session()
    
    try:
        # Validate profile
        profile = db.query(HDTProfile).filter_by(
            profile_id=data['profile_id'],
            user_id=current_user_id
        ).first()
        
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Create session
        session = WorkSession(
            user_id=current_user_id,
            profile_id=data['profile_id'],
            start_time=datetime.now(),
            is_active=True
        )
        
        db.add(session)
        db.commit()
        
        # Initialize AI session
        ai_service.create_session(session.session_id, profile.role_type)
        
        logger.info(f"✓ Session started: {session.session_id}")
        return jsonify({
            'message': 'Session started successfully',
            'session': session.to_dict()
        }), 201
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Session start error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/sessions/<int:session_id>/end', methods=['POST'])
@token_required
def end_session(current_user_id, session_id):
    """End work session"""
    db = Session()
    
    try:
        session = db.query(WorkSession).filter_by(
            session_id=session_id,
            user_id=current_user_id
        ).first()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session.end_time = datetime.now()
        session.session_duration = int((session.end_time - session.start_time).total_seconds())
        session.is_active = False
        
        # Calculate averages
        physio_data = db.query(PhysiologicalData).filter_by(session_id=session_id).all()
        if physio_data:
            session.avg_cognitive_load = sum(p.cognitive_load or 0 for p in physio_data) / len(physio_data)
            session.avg_stress_level = sum(p.stress_level or 0 for p in physio_data) / len(physio_data)
        
        db.commit()
        
        # Clear AI session
        ai_service.clear_session(session_id)
        
        logger.info(f"✓ Session ended: {session_id}")
        return jsonify({
            'message': 'Session ended successfully',
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Session end error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/sessions', methods=['GET'])
@token_required
def get_sessions(current_user_id):
    """Get user sessions"""
    db = Session()
    try:
        sessions = db.query(WorkSession).filter_by(user_id=current_user_id).order_by(WorkSession.start_time.desc()).limit(10).all()
        return jsonify({
            'sessions': [s.to_dict() for s in sessions]
        }), 200
    finally:
        db.close()

# ============================================
# MONITORING ENDPOINTS
# ============================================

@api.route('/monitoring/physiological', methods=['POST'])
@token_required
def submit_physiological_data(current_user_id):
    """Submit physiological data"""
    data = request.json
    db = Session()
    
    try:
        physio = PhysiologicalData(
            session_id=data['session_id'],
            heart_rate=data.get('heart_rate'),
            hrv=data.get('hrv'),
            skin_temperature=data.get('skin_temperature'),
            stress_level=data.get('stress_level'),
            cognitive_load=data.get('cognitive_load'),
            fatigue_score=data.get('fatigue_score'),
            posture_score=data.get('posture_score'),
            raw_sensor_data=data.get('raw_sensor_data', {})
        )
        
        db.add(physio)
        db.commit()
        
        return jsonify({
            'message': 'Data recorded',
            'data': physio.to_dict()
        }), 201
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Physiological data error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/monitoring/work-activity', methods=['POST'])
@token_required
def submit_work_activity(current_user_id):
    """Submit work activity data"""
    data = request.json
    db = Session()
    
    try:
        activity = WorkActivity(
            session_id=data['session_id'],
            activity_type=data.get('activity_type'),
            typing_speed=data.get('typing_speed'),
            mouse_movements=data.get('mouse_movements'),
            application_name=data.get('application_name'),
            focus_score=data.get('focus_score')
        )
        
        db.add(activity)
        db.commit()
        
        return jsonify({
            'message': 'Activity recorded',
            'activity': activity.to_dict()
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/monitoring/current-state/<int:session_id>', methods=['GET'])
@token_required
def get_current_state(current_user_id, session_id):
    """Get current HDT state"""
    db = Session()
    try:
        # Get latest physiological data
        latest_physio = db.query(PhysiologicalData).filter_by(
            session_id=session_id
        ).order_by(PhysiologicalData.timestamp.desc()).first()
        
        # Get latest activity
        latest_activity = db.query(WorkActivity).filter_by(
            session_id=session_id
        ).order_by(WorkActivity.timestamp.desc()).first()
        
        return jsonify({
            'physiological': latest_physio.to_dict() if latest_physio else None,
            'activity': latest_activity.to_dict() if latest_activity else None
        }), 200
        
    finally:
        db.close()

# ============================================
# AI TASK ENDPOINTS
# ============================================

@api.route('/tasks', methods=['POST'])
@token_required
def create_task(current_user_id):
    """Create new AI task"""
    data = request.json
    db = Session()
    
    try:
        task = AITask(
            session_id=data['session_id'],
            profile_id=data['profile_id'],
            task_type=data.get('task_type', 'general'),
            command_text=data['command'],
            task_status='pending',
            priority=data.get('priority', 5)
        )
        
        db.add(task)
        db.commit()
        
        # Execute task
        task.task_status = 'processing'
        task.started_at = datetime.now()
        db.commit()
        
        result = ai_service.process_task(
            session_id=data['session_id'],
            task_type=task.task_type,
            command=task.command_text,
            context=data.get('context')
        )
        
        if result['success']:
            task.task_status = 'completed'
            task.result_data = result['result']
            task.tokens_used = result.get('tokens_used', 0)
        else:
            task.task_status = 'failed'
            task.error_message = result.get('error', 'Unknown error')
        
        task.completed_at = datetime.now()
        task.execution_time_seconds = int((task.completed_at - task.started_at).total_seconds())
        db.commit()
        
        logger.info(f"✓ Task completed: {task.task_id}")
        return jsonify({
            'message': 'Task completed',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Task error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/tasks', methods=['GET'])
@token_required
def get_tasks(current_user_id):
    """Get user tasks"""
    session_id = request.args.get('session_id', type=int)
    db = Session()
    
    try:
        query = db.query(AITask).join(WorkSession).filter(WorkSession.user_id == current_user_id)
        
        if session_id:
            query = query.filter(AITask.session_id == session_id)
        
        tasks = query.order_by(AITask.created_at.desc()).limit(20).all()
        
        return jsonify({
            'tasks': [t.to_dict() for t in tasks]
        }), 200
        
    finally:
        db.close()

@api.route('/chat', methods=['POST'])
@token_required
def chat(current_user_id):
    """Send message to AI"""
    data = request.json
    db = Session()
    
    try:
        # Save user message
        user_msg = AIInteraction(
            session_id=data['session_id'],
            role='user',
            message_text=data['message']
        )
        db.add(user_msg)
        
        # Process with AI
        result = ai_service.process_task(
            session_id=data['session_id'],
            task_type='general',
            command=data['message']
        )
        
        # Save assistant response
        if result['success']:
            assistant_msg = AIInteraction(
                session_id=data['session_id'],
                role='assistant',
                message_text=result['raw_response'],
                tokens_used=result.get('tokens_used', 0)
            )
            db.add(assistant_msg)
        
        db.commit()
        
        return jsonify({
            'response': result.get('raw_response', result.get('error', 'No response')),
            'success': result['success']
        }), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@api.route('/chat/history/<int:session_id>', methods=['GET'])
@token_required
def get_chat_history(current_user_id, session_id):
    """Get chat history"""
    db = Session()
    try:
        messages = db.query(AIInteraction).filter_by(
            session_id=session_id
        ).order_by(AIInteraction.timestamp).all()
        
        return jsonify({
            'messages': [m.to_dict() for m in messages]
        }), 200
    finally:
        db.close()