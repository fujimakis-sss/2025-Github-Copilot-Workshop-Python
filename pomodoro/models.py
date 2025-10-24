from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class PomodoroSession(db.Model):
    __tablename__ = 'pomodoro_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
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
    date = db.Column(db.Date, nullable=False, unique=True, index=True)
    total_focus_seconds = db.Column(db.Integer, nullable=False, default=0)
    completed_focus_count = db.Column(db.Integer, nullable=False, default=0)
    
    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'total_focus_seconds': self.total_focus_seconds,
            'completed_focus_count': self.completed_focus_count
        }

