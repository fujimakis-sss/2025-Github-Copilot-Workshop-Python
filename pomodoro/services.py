from datetime import datetime, timedelta, timezone
from typing import Optional
from .models import db, PomodoroSession, DailyStat
from .validators import validate_duration, validate_tag

FOCUS_DEFAULT_MINUTES = 25
BREAK_DEFAULT_MINUTES = 5


def start_focus(duration_minutes: int = FOCUS_DEFAULT_MINUTES, tag: Optional[str] = None) -> PomodoroSession:
    # Validate duration and tag
    validate_duration(duration_minutes)
    validate_tag(tag)
    
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
        status='active',
        tag=tag
    )
    db.session.add(session)
    db.session.commit()
    return session


def start_break(duration_minutes: int = BREAK_DEFAULT_MINUTES, tag: Optional[str] = None) -> PomodoroSession:
    # Validate duration and tag
    validate_duration(duration_minutes)
    validate_tag(tag)
    
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
        status='active',
        tag=tag
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


def get_stats_by_tag() -> list:
    """
    Get statistics grouped by tag.
    
    Returns:
        List of dictionaries with tag statistics
    """
    from sqlalchemy import func
    
    # Query sessions grouped by tag, counting completed focus sessions
    stats = db.session.query(
        PomodoroSession.tag,
        func.count(PomodoroSession.id).label('count'),
        func.sum(PomodoroSession.planned_duration_sec).label('total_seconds')
    ).filter(
        PomodoroSession.type == 'focus',
        PomodoroSession.status == 'completed'
    ).group_by(PomodoroSession.tag).all()
    
    result = []
    for tag, count, total_seconds in stats:
        result.append({
            'tag': tag,
            'completed_focus_count': count,
            'total_focus_seconds': total_seconds or 0
        })
    
    return result


def get_recent_tags(limit: int = 10) -> list:
    """
    Get recently used tags.
    
    Args:
        limit: Maximum number of tags to return
        
    Returns:
        List of unique tags ordered by most recent use
    """
    from sqlalchemy import func
    
    # Get unique tags from recent sessions, excluding None
    tags = db.session.query(
        PomodoroSession.tag
    ).filter(
        PomodoroSession.tag.isnot(None)
    ).group_by(
        PomodoroSession.tag
    ).order_by(
        func.max(PomodoroSession.start_at).desc()
    ).limit(limit).all()
    
    return [tag[0] for tag in tags]

