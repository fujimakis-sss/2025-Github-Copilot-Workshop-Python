import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).resolve().parent
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///pomodoro.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')
    
    # Pomodoro Presets (focus_minutes, break_minutes)
    POMODORO_PRESETS = {
        'default': {'focus': 25, 'break': 5, 'label': '25/5 (標準)'},
        'long': {'focus': 50, 'break': 10, 'label': '50/10 (長時間)'},
        'short': {'focus': 15, 'break': 3, 'label': '15/3 (短時間)'}
    }
    DEFAULT_PRESET = 'default'
