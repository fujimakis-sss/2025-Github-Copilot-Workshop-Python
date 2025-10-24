from flask import Blueprint, jsonify, request
from . import bp
from .services import start_focus, start_break, stop_active_session, get_state
from .validators import ValidationError

@bp.post('/start')
def start_focus_route():
    data = request.get_json(silent=True) or {}
    duration = data.get('duration_minutes', 25)
    try:
        session = start_focus(duration)
        return jsonify({'id': session.id, 'type': session.type, 'planned_end_at': session.planned_end_at.isoformat()}), 201
    except ValidationError as e:
        import logging; logging.warning(f"Validation error in start_focus_route: {str(e)}")
        return jsonify({'error': str(e), 'field': 'duration_minutes'}), 400
    except ValueError as e:
        import logging; logging.warning(f"Error in start_focus_route: {type(e).__name__}")
        return jsonify({'error': 'Invalid input provided.'}), 409

@bp.post('/break')
def start_break_route():
    data = request.get_json(silent=True) or {}
    duration = data.get('duration_minutes', 5)
    try:
        session = start_break(duration)
        return jsonify({'id': session.id, 'type': session.type, 'planned_end_at': session.planned_end_at.isoformat()}), 201
    except ValidationError as e:
        import logging; logging.warning(f"Validation error in start_break_route: {str(e)}")
        return jsonify({'error': str(e), 'field': 'duration_minutes'}), 400
    except ValueError as e:
        import logging; logging.warning(f"Error in start_break_route: {type(e).__name__}")
        return jsonify({'error': 'Invalid input provided.'}), 409

@bp.post('/stop')
def stop_route():
    stop_active_session()
    return jsonify({'status': 'stopped'})

@bp.get('/state')
def state_route():
    return jsonify(get_state())
