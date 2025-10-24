from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('PomodoroSession', backref='user', lazy=True)
    daily_stats = db.relationship('DailyStat', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set the password."""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class PomodoroSession(db.Model):
    __tablename__ = 'pomodoro_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.String(10), nullable=False)  # 'focus' or 'break'
    planned_duration_sec = db.Column(db.Integer, nullable=False)
    start_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    planned_end_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active','completed','aborted'
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'planned_duration_sec': self.planned_duration_sec,
            'start_at': self.start_at.isoformat(),
            'planned_end_at': self.planned_end_at.isoformat(),
            'end_at': self.end_at.isoformat() if self.end_at else None,
            'status': self.status
        }

class DailyStat(db.Model):
    __tablename__ = 'daily_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    total_focus_seconds = db.Column(db.Integer, nullable=False, default=0)
    completed_focus_count = db.Column(db.Integer, nullable=False, default=0)
    
    # Add composite unique constraint for user_id and date
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),)
    
    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'total_focus_seconds': self.total_focus_seconds,
            'completed_focus_count': self.completed_focus_count
        }

