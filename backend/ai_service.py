import google.generativeai as genai
from config import Config
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AIService:
    """Google Gemini AI Service for HDT"""
    
    def __init__(self):
        if not Config.GEMINI_API_KEY:
            logger.warning("Gemini API key not configured")
            self.model = None
            return
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
        self.chat_sessions = {}
        logger.info("✓ Gemini AI Service initialized")
    
    def get_role_capabilities(self, role_type: str) -> Dict:
        """Get capabilities for each role"""
        capabilities = {
            'software_engineer': {
                'tasks': [
                    'code_generation',
                    'debugging',
                    'documentation',
                    'code_review',
                    'tutorial'
                ],
                'languages': ['Python', 'JavaScript', 'HTML', 'CSS'],
                'description': 'Software development and coding assistance'
            },
            'office_worker': {
                'tasks': [
                    'document_creation',
                    'data_analysis',
                    'email_drafting',
                    'meeting_scheduling',
                    'report_generation'
                ],
                'tools': ['Documents', 'Spreadsheets', 'Presentations'],
                'description': 'Office productivity and administrative tasks'
            },
            'factory_worker': {
                'tasks': [
                    'safety_monitoring',
                    'equipment_guidance',
                    'performance_insights',
                    'maintenance_scheduling',
                    'incident_reporting'
                ],
                'focus': ['Safety', 'Efficiency', 'Training'],
                'description': 'Factory and field work support'
            }
        }
        return capabilities.get(role_type, capabilities['software_engineer'])
    
    def get_system_prompt(self, role_type: str) -> str:
        """Get role-specific system prompt"""
        prompts = {
            'software_engineer': """You are a Software Engineer Digital Twin AI assistant.
Your capabilities:
- Generate clean, documented code in Python, JavaScript, HTML, CSS
- Debug and analyze code
- Create technical documentation
- Provide coding tutorials and explanations
- Review code and suggest improvements

Guidelines:
- Keep code under 1000 lines per task
- Include helpful comments
- Follow best practices and conventions
- Provide clear explanations
- Format code with proper syntax

When generating code, use markdown code blocks with language specification.""",

            'office_worker': """You are an Office Worker Digital Twin AI assistant.
Your capabilities:
- Create and edit documents
- Analyze data and create reports
- Draft professional emails
- Help with scheduling and organization
- Automate administrative tasks

Guidelines:
- Be professional and concise
- Focus on productivity
- Provide actionable suggestions
- Format outputs clearly""",

            'factory_worker': """You are a Factory/Field Worker Digital Twin AI assistant.
Your capabilities:
- Provide safety guidance and protocols
- Assist with equipment operation
- Track performance metrics
- Schedule maintenance tasks
- Help with incident reporting

Guidelines:
- Prioritize safety above all
- Be clear and direct
- Use simple language
- Provide step-by-step instructions"""
        }
        return prompts.get(role_type, prompts['software_engineer'])
    
    def create_session(self, session_id: int, role_type: str):
        """Create a new chat session"""
        if not self.model:
            return False
        
        try:
            chat = self.model.start_chat(history=[])
            self.chat_sessions[session_id] = {
                'chat': chat,
                'role': role_type,
                'system_prompt': self.get_system_prompt(role_type),
                'history': []
            }
            logger.info(f"✓ Created AI session {session_id} for {role_type}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create session: {e}")
            return False
    
    def process_task(self, session_id: int, task_type: str, command: str, context: Optional[Dict] = None) -> Dict:
        """Process AI task"""
        if not self.model:
            return {
                'success': False,
                'error': 'AI service not configured. Please set GEMINI_API_KEY.'
            }
        
        if session_id not in self.chat_sessions:
            return {
                'success': False,
                'error': f'Session {session_id} not found. Please start a session first.'
            }
        
        session = self.chat_sessions[session_id]
        prompt = self._build_prompt(task_type, command, session['role'], context)
        
        try:
            # Send message to Gemini
            response = session['chat'].send_message(prompt)
            
            # Parse response
            result = self._parse_response(response.text, task_type)
            
            # Save to history
            session['history'].append({
                'command': command,
                'response': response.text,
                'task_type': task_type
            })
            
            return {
                'success': True,
                'result': result,
                'raw_response': response.text,
                'tokens_used': len(response.text.split())  # Approximate
            }
            
        except Exception as e:
            logger.error(f"✗ Task processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_prompt(self, task_type: str, command: str, role_type: str, context: Optional[Dict]) -> str:
        """Build task-specific prompt"""
        system = self.get_system_prompt(role_type)
        
        if task_type == 'code_generation':
            return f"""{system}

Generate code for the following request:
{command}

Requirements:
- Maximum {Config.CODE_GENERATION_MAX_LINES} lines
- Include comments explaining key parts
- Follow best practices
- Provide a brief explanation after the code

Format your response with code in markdown blocks:
```language
code here
```

Then provide explanation."""

        elif task_type == 'debugging':
            code = context.get('code', '') if context else ''
            return f"""{system}

Debug the following code:
```
{code}
```

Issue description: {command}

Provide:
1. What's wrong
2. Corrected code
3. Explanation of the fix"""

        elif task_type == 'documentation':
            code = context.get('code', '') if context else ''
            return f"""{system}

Generate documentation for:
```
{code}
```

Additional requirements: {command}

Include:
- Overview
- Function/class descriptions
- Usage examples
- Parameters and return values"""

        else:
            # General query
            return f"{system}\n\nUser request: {command}"
    
    def _parse_response(self, response_text: str, task_type: str) -> Dict:
        """Parse Gemini response"""
        result = {
            'type': task_type,
            'content': response_text,
            'code_blocks': [],
            'explanation': ''
        }
        
        # Extract code blocks
        code_pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(code_pattern, response_text, re.DOTALL)
        
        for language, code in matches:
            result['code_blocks'].append({
                'language': language or 'plaintext',
                'code': code.strip()
            })
        
        # Extract text outside code blocks
        explanation = re.sub(code_pattern, '', response_text, flags=re.DOTALL)
        result['explanation'] = explanation.strip()
        
        return result
    
    def get_history(self, session_id: int) -> List[Dict]:
        """Get chat history"""
        if session_id in self.chat_sessions:
            return self.chat_sessions[session_id]['history']
        return []
    
    def clear_session(self, session_id: int):
        """Clear chat session"""
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            logger.info(f"✓ Cleared session {session_id}")

# Global AI service instance
ai_service = AIService()