from flask import Blueprint, jsonify, request
from . import bp
from .services import start_focus, start_break, stop_active_session, get_state, get_stats_by_tag, get_recent_tags
from .validators import ValidationError

@bp.post('/start')
def start_focus_route():
    data = request.get_json(silent=True) or {}
    duration = data.get('duration_minutes', 25)
    tag = data.get('tag', None)
    try:
        session = start_focus(duration, tag)
        return jsonify({'id': session.id, 'type': session.type, 'planned_end_at': session.planned_end_at.isoformat()}), 201
    except ValidationError as e:
        import logging; logging.exception("Validation error in start_focus_route")
        return jsonify({'error': 'Invalid value for duration_minutes.', 'field': 'duration_minutes'}), 400
    except ValueError as e:
        import logging; logging.exception("Error in start_focus_route")
        return jsonify({'error': 'Invalid input provided.'}), 409

@bp.post('/break')
def start_break_route():
    data = request.get_json(silent=True) or {}
    duration = data.get('duration_minutes', 5)
    tag = data.get('tag', None)
    try:
        session = start_break(duration, tag)
        return jsonify({'id': session.id, 'type': session.type, 'planned_end_at': session.planned_end_at.isoformat()}), 201
    except ValidationError as e:
        import logging; logging.exception("Validation error in start_break_route")
        return jsonify({'error': 'Invalid value for duration_minutes.', 'field': 'duration_minutes'}), 400
    except ValueError as e:
        import logging; logging.exception("Error in start_break_route")
        return jsonify({'error': 'Invalid input provided.'}), 409

@bp.post('/stop')
def stop_route():
    stop_active_session()
    return jsonify({'status': 'stopped'})

@bp.get('/state')
def state_route():
    return jsonify(get_state())

@bp.get('/stats/by-tag')
def stats_by_tag_route():
    """Get statistics grouped by tag."""
    return jsonify(get_stats_by_tag())

@bp.get('/tags/recent')
def recent_tags_route():
    """Get recently used tags."""
    limit = request.args.get('limit', 10, type=int)
    return jsonify(get_recent_tags(limit))
