# Industry-Level Human Digital Twin

An AI-powered digital twin system that monitors professional workers in real-time and provides autonomous task execution capabilities using Google Gemini AI.

## 🎯 Features

- **Real-time Monitoring**: Track physiological data, cognitive load, and work patterns
- **3D Avatar Visualization**: Interactive 3D models representing different professional roles
- **AI-Powered Task Execution**: Natural language commands for code generation, debugging, and more
- **Role-Based Capabilities**: Software Engineer, Office Worker, and Factory Worker profiles
- **WebSocket Real-time Updates**: Live data streaming for monitoring
- **Analytics Dashboard**: Historical data and productivity insights

## 🏗️ Tech Stack

### Backend
- **Python 3.9+**
- **Flask** - Web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **Google Gemini API** - AI capabilities
- **Flask-SocketIO** - Real-time communication

### Frontend
- **HTML/CSS/JavaScript** (Vanilla)
- **Three.js** - 3D visualization
- **Socket.IO** - WebSocket client

## 📋 Prerequisites

1. **Python 3.9 or higher**
2. **PostgreSQL 12 or higher**
3. **Google Gemini API Key** (Get from [Google AI Studio](https://makersuite.google.com/app/apikey))
4. **Modern web browser** (Chrome, Firefox, Edge)

## 🚀 Installation

### Step 1: Run Setup Script

```bash
# Run the setup script to create project structure
python setup_project.py
```

This will create the complete project structure with all files.

### Step 2: Database Setup

1. Install PostgreSQL if not already installed
2. Create database:

```bash
# Login to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE hdt_database;

# Exit
\q
```

### Step 3: Backend Setup

```bash
# Navigate to backend directory
cd hdt-project/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
copy .env.example .env    # Windows
# OR
cp .env.example .env      # Mac/Linux

# Edit .env file and add your credentials:
# - GEMINI_API_KEY=your_api_key_here
# - DB_PASSWORD=your_postgres_password
# - SECRET_KEY=generate_a_random_secret_key
```

### Step 4: Initialize Database

```bash
# Still in backend directory with venv activated
python -c "from database import init_db, DatabaseManager; DatabaseManager.test_connection(); init_db()"
```

### Step 5: Place 3D Models

Copy your 3D models to the frontend models directory:

```
hdt-project/frontend/models/
├── avatars/
│   ├── software_engineer.fbx
│   ├── office_worker.fbx
│   └── factory_worker.fbx
└── environment/
    ├── chair.glb
    ├── laptop.glb
    └── table.glb
```

## ▶️ Running the Application

### Start Backend Server

```bash
# In backend directory with venv activated
python app.py
```

The backend will start on `http://localhost:5000`

### Start Frontend

You can use any of these methods:

**Option 1: Python HTTP Server**
```bash
# In frontend directory
cd ../frontend
python -m http.server 8000
```

**Option 2: VS Code Live Server**
- Install "Live Server" extension in VS Code
- Right-click on `index.html`
- Select "Open with Live Server"

**Option 3: Node.js HTTP Server**
```bash
npx http-server frontend -p 8000
```

Then open your browser to `http://localhost:8000`

## 📖 Usage Guide

### 1. Register/Login
- Open the frontend in your browser
- Register a new account or login
- You'll be redirected to the main dashboard

### 2. Select Role
- Choose a professional role (Software Engineer, Office Worker, Factory Worker)
- The 3D avatar will load for that role

### 3. Start Session
- Click "Start Session" to begin monitoring
- Real-time physiological data will be simulated
- The avatar will change color based on stress levels:
  - 🟢 Green: Optimal (stress < 30%)
  - 🟡 Yellow: Moderate (stress 30-60%)
  - 🔴 Red: Critical (stress > 60%)

### 4. Interact with AI
Use the chat interface to delegate tasks:

**For Software Engineers:**
```
Create a Python calculator
Debug this code: [paste code]
Generate documentation for this function
Build a simple web page
```

**For Office Workers:**
```
Create a meeting agenda
Analyze this data
Draft a professional email
```

**For Factory Workers:**
```
What are the safety protocols for equipment X?
How do I report an incident?
Show maintenance schedule
```

### 5. Monitor Progress
- View real-time metrics in the left sidebar
- Check task history in the right sidebar
- Watch the 3D avatar reflect your current state

### 6. End Session
- Click "End Session" when done
- View session analytics and statistics

## 🎮 API Endpoints

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### HDT Profiles
- `GET /api/hdt/profiles` - Get user profiles
- `POST /api/hdt/profiles` - Create profile
- `GET /api/hdt/roles` - Get available roles

### Sessions
- `POST /api/sessions/start` - Start work session
- `POST /api/sessions/<id>/end` - End session
- `GET /api/sessions` - Get session history

### Monitoring
- `POST /api/monitoring/physiological` - Submit sensor data
- `POST /api/monitoring/work-activity` - Submit activity data
- `GET /api/monitoring/current-state/<id>` - Get current state

### AI Tasks
- `POST /api/tasks` - Create AI task
- `GET /api/tasks` - Get task list
- `POST /api/chat` - Send chat message
- `GET /api/chat/history/<id>` - Get chat history

## 🔧 Configuration

Edit `.env` file in backend directory:

```env
# Flask
SECRET_KEY=your-secret-key
DEBUG=True

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hdt_database
DB_USER=postgres
DB_PASSWORD=your_password

# Google Gemini API
GEMINI_API_KEY=your_api_key

# Application Settings
MAX_CONCURRENT_TASKS=1
CODE_GENERATION_MAX_LINES=1000
DATA_RETENTION_DAYS=90
REFRESH_RATE_SECONDS=1
```

## 🐛 Troubleshooting

### Backend won't start
- Check if PostgreSQL is running
- Verify database credentials in .env
- Ensure all dependencies are installed
- Check if port 5000 is available

### 3D models not loading
- Verify models are in correct directory
- Check browser console for errors
- Ensure models are in correct format (FBX for avatars, GLB for environment)
- Try the fallback geometric avatar by temporarily moving model files

### AI not responding
- Verify GEMINI_API_KEY is set correctly
- Check API quota limits
- Look for errors in backend console
- Ensure session is started before sending commands

### WebSocket connection failed
- Check if backend is running on port 5000
- Verify CORS settings in backend config
- Check browser console for connection errors

## 📊 Database Schema

Key tables:
- `users` - User accounts
- `hdt_profiles` - Role-based profiles
- `sessions` - Work sessions
- `physiological_data` - Sensor data
- `work_activities` - Activity tracking
- `ai_tasks` - Task execution history
- `ai_interactions` - Chat history

## 🔐 Security Notes

- Change `SECRET_KEY` in production
- Use HTTPS in production
- Never commit `.env` file
- Use environment variables for sensitive data
- Implement rate limiting for API endpoints
- Validate all user inputs

## 📝 Development Notes

### Adding New Roles
1. Add role configuration in `ai_service.py`
2. Create system prompt for the role
3. Add 3D model to `frontend/models/avatars/`
4. Update UI profile selector

### Customizing AI Behavior
Edit system prompts in `ai_service.py`:
```python
def get_system_prompt(self, role_type: str) -> str:
    # Modify prompts here
```

### Extending Database
1. Modify models in `models.py`
2. Run: `python -c "from database import init_db; init_db()"`
3. Add migrations if needed

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📄 License

MIT License - See LICENSE file

## 👨‍💻 Author

**Haseeb Abid Qadri**  
University of Engineering and Technology, Lahore  
2023ce51@student.uet.edu.pk

## 🙏 Acknowledgments

- Google Gemini AI for AI capabilities
- Three.js for 3D visualization
- Flask community for excellent framework
- PostgreSQL team for robust database

## 📞 Support

For issues and questions:
- Check troubleshooting section
- Review backend logs
- Check browser console
- Contact: 2023ce51@student.uet.edu.pk

---

**Version**: 1.0.0  
**Last Updated**: December 2024