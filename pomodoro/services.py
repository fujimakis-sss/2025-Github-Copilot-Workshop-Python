from datetime import datetime, timedelta, timezone
from typing import Optional
from .models import db, PomodoroSession, DailyStat
from .validators import validate_duration

FOCUS_DEFAULT_MINUTES = 25
BREAK_DEFAULT_MINUTES = 5


def start_focus(duration_minutes: int = FOCUS_DEFAULT_MINUTES) -> PomodoroSession:
    # Validate duration
    validate_duration(duration_minutes)
    
    # アクティブなセッションがあればエラー
    active = PomodoroSession.query.filter_by(status='active').first()
    if active:
        raise ValueError('Active session already exists')
    
    duration_sec = duration_minutes * 60
    now = datetime.now(timezone.utc)
    session = PomodoroSession(
        type='focus',
        planned_duration_sec=duration_sec,
        start_at=now,
        planned_end_at=now + timedelta(seconds=duration_sec),
        status='active'
    )
    db.session.add(session)
    db.session.commit()
    return session


def start_break(duration_minutes: int = BREAK_DEFAULT_MINUTES) -> PomodoroSession:
    # Validate duration
    validate_duration(duration_minutes)
    
    # アクティブなセッションがあればエラー
    active = PomodoroSession.query.filter_by(status='active').first()
    if active:
        raise ValueError('Active session already exists')
    
    duration_sec = duration_minutes * 60
    now = datetime.now(timezone.utc)
    session = PomodoroSession(
        type='break',
        planned_duration_sec=duration_sec,
        start_at=now,
        planned_end_at=now + timedelta(seconds=duration_sec),
        status='active'
    )
    db.session.add(session)
    db.session.commit()
    return session


def stop_active_session() -> None:
    active = PomodoroSession.query.filter_by(status='active').first()
    if active:
        active.status = 'aborted'
        active.end_at = datetime.now(timezone.utc)
        db.session.commit()


def complete_session(session_id: int) -> None:
    session = PomodoroSession.query.get(session_id)
    if not session or session.status != 'active':
        return
    
    session.status = 'completed'
    session.end_at = datetime.now(timezone.utc)
    
    # フォーカスセッション完了時、統計を更新
    if session.type == 'focus':
        today = datetime.now(timezone.utc).date()
        stat = DailyStat.query.filter_by(date=today).first()
        if not stat:
            stat = DailyStat(date=today, total_focus_seconds=0, completed_focus_count=0)
            db.session.add(stat)
        stat.completed_focus_count += 1
        stat.total_focus_seconds += session.planned_duration_sec
    
    db.session.commit()


def get_state() -> dict:
    now = datetime.now(timezone.utc)
    active = PomodoroSession.query.filter_by(status='active').first()
    
    if active:
        # DBから取得したdatetimeはnaiveなのでUTCとして扱う
        planned_end = active.planned_end_at.replace(tzinfo=timezone.utc) if active.planned_end_at.tzinfo is None else active.planned_end_at
        remaining = int((planned_end - now).total_seconds())
        if remaining <= 0:
            complete_session(active.id)
            remaining = 0
            mode = 'idle'
        else:
            mode = active.type
    else:
        remaining = 0
        mode = 'idle'
    
    # 今日の統計取得
    today = datetime.now(timezone.utc).date()
    stat = DailyStat.query.filter_by(date=today).first()
    
    return {
        'mode': mode,
        'remaining_seconds': remaining,
        'completed_focus_count': stat.completed_focus_count if stat else 0,
        'total_focus_seconds': stat.total_focus_seconds if stat else 0
    }


def get_weekly_stats() -> list:
    """Get statistics for the last 7 days."""
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=6)
    
    stats = DailyStat.query.filter(
        DailyStat.date >= start_date,
        DailyStat.date <= today
    ).order_by(DailyStat.date).all()
    
    # Create a dict for easy lookup
    stats_dict = {stat.date: stat for stat in stats}
    
    # Build result with all days in range, filling in missing days with zeros
    result = []
    for i in range(7):
        date = start_date + timedelta(days=i)
        stat = stats_dict.get(date)
        
        if stat:
            total_sessions = stat.completed_focus_count
            completion_rate = 1.0 if total_sessions > 0 else 0.0
            result.append({
                'date': date.isoformat(),
                'focus_count': stat.completed_focus_count,
                'total_seconds': stat.total_focus_seconds,
                'completion_rate': completion_rate
            })
        else:
            result.append({
                'date': date.isoformat(),
                'focus_count': 0,
                'total_seconds': 0,
                'completion_rate': 0.0
            })
    
    return result


def get_monthly_stats() -> list:
    """Get statistics for the last 30 days."""
    today = datetime.now(timezone.utc).date()
    start_date = today - timedelta(days=29)
    
    stats = DailyStat.query.filter(
        DailyStat.date >= start_date,
        DailyStat.date <= today
    ).order_by(DailyStat.date).all()
    
    # Create a dict for easy lookup
    stats_dict = {stat.date: stat for stat in stats}
    
    # Build result with all days in range, filling in missing days with zeros
    result = []
    for i in range(30):
        date = start_date + timedelta(days=i)
        stat = stats_dict.get(date)
        
        if stat:
            total_sessions = stat.completed_focus_count
            completion_rate = 1.0 if total_sessions > 0 else 0.0
            result.append({
                'date': date.isoformat(),
                'focus_count': stat.completed_focus_count,
                'total_seconds': stat.total_focus_seconds,
                'completion_rate': completion_rate
            })
        else:
            result.append({
                'date': date.isoformat(),
                'focus_count': 0,
                'total_seconds': 0,
                'completion_rate': 0.0
            })
    
    return result

