import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).resolve().parent
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///pomodoro.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
