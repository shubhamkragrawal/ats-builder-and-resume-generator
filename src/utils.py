"""
Utility functions for the ATS Resume Builder
"""
import logging
import os
import yaml
from pathlib import Path
from logging.handlers import RotatingFileHandler


def load_config(config_path="config/config.yaml"):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        logging.warning(f"Config file not found at {config_path}, using defaults")
        return get_default_config()
    except Exception as e:
        logging.error(f"Error loading config: {str(e)}")
        return get_default_config()


def get_default_config():
    """Return default configuration"""
    return {
        'ollama': {
            'base_url': 'http://localhost:11434',
            'model': 'mistral',
            'timeout': 120,
            'temperature': 0.7,
            'max_tokens': 2000
        },
        'paths': {
            'base_resume': 'data/base_resume.txt',
            'applications_csv': 'data/applications.csv',
            'log_file': 'data/logs/app.log',
            'prompts': 'templates/prompts.yaml'
        },
        'scoring': {
            'keyword_weight': 0.35,
            'skills_weight': 0.30,
            'experience_weight': 0.20,
            'education_weight': 0.10,
            'format_weight': 0.05,
            'excellent_threshold': 80,
            'good_threshold': 60,
            'fair_threshold': 40
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'max_bytes': 10485760,
            'backup_count': 5
        }
    }


def setup_logging(config):
    """Setup logging configuration"""
    log_dir = Path(config['paths']['log_file']).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_level = getattr(logging, config['logging']['level'])
    log_format = config['logging']['format']
    log_file = config['paths']['log_file']
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Setup file handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config['logging']['max_bytes'],
        backupCount=config['logging']['backup_count']
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info("Logging initialized successfully")


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        'data',
        'data/logs',
        'config',
        'src',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    logging.info("Directory structure verified")


def load_prompts(prompts_path="templates/prompts.yaml"):
    """Load prompt templates from YAML file"""
    try:
        with open(prompts_path, 'r') as file:
            prompts = yaml.safe_load(file)
        return prompts
    except FileNotFoundError:
        logging.error(f"Prompts file not found at {prompts_path}")
        return {}
    except Exception as e:
        logging.error(f"Error loading prompts: {str(e)}")
        return {}


def save_base_resume(resume_text, config):
    """Save base resume to file"""
    try:
        base_resume_path = config['paths']['base_resume']
        Path(base_resume_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(base_resume_path, 'w', encoding='utf-8') as file:
            file.write(resume_text)
        
        logging.info("Base resume saved successfully")
        return True
    except Exception as e:
        logging.error(f"Error saving base resume: {str(e)}")
        return False


def load_base_resume(config):
    """Load base resume from file"""
    try:
        base_resume_path = config['paths']['base_resume']
        
        if not os.path.exists(base_resume_path):
            logging.warning("Base resume file not found")
            return None
        
        with open(base_resume_path, 'r', encoding='utf-8') as file:
            resume_text = file.read()
        
        if resume_text.strip():
            logging.info("Base resume loaded successfully")
            return resume_text
        else:
            logging.warning("Base resume file is empty")
            return None
            
    except Exception as e:
        logging.error(f"Error loading base resume: {str(e)}")
        return None


def extract_score_from_response(response_text):
    """Extract ATS score from LLM response"""
    try:
        # Look for patterns like "ATS Score: 75/100" or "Score: 75"
        import re
        
        patterns = [
            r'ATS Score[:\s]+(\d+)(?:/100)?',
            r'Score[:\s]+(\d+)(?:/100)?',
            r'(\d+)/100',
            r'score[:\s]+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                # Ensure score is between 0 and 100
                return max(0, min(100, score))
        
        logging.warning("Could not extract score from response")
        return None
        
    except Exception as e:
        logging.error(f"Error extracting score: {str(e)}")
        return None


def format_feedback(feedback_text):
    """Format feedback text for better display"""
    # Remove excessive newlines
    feedback_text = '\n'.join(line for line in feedback_text.split('\n') if line.strip())
    return feedback_text


def get_score_category(score):
    """Get category based on ATS score"""
    if score is None:
        return "Unknown"
    elif score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Needs Improvement"


def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
