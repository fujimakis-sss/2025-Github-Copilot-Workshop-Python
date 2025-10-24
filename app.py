from flask import Flask
from dotenv import load_dotenv
import os
import logging
import json
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
	"""Custom JSON formatter for structured logging."""
	def format(self, record):
		log_data = {
			'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
			'level': record.levelname,
			'message': record.getMessage(),
		}
		
		# Add extra fields if present
		if hasattr(record, 'event'):
			log_data['event'] = record.event
		if hasattr(record, 'session_id'):
			log_data['session_id'] = record.session_id
		if hasattr(record, 'session_type'):
			log_data['type'] = record.session_type
		if hasattr(record, 'duration'):
			log_data['duration'] = record.duration
		if hasattr(record, 'status'):
			log_data['status'] = record.status
		
		return json.dumps(log_data)

def create_app():
	# .env読み込み (存在しない場合は無視)
	load_dotenv()

	app = Flask(__name__)
	app.config.from_object('config.Config')

	# Configure JSON logging
	log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
	
	# Remove existing handlers and add JSON handler
	app.logger.handlers.clear()
	handler = logging.StreamHandler()
	handler.setFormatter(JsonFormatter())
	app.logger.addHandler(handler)
	app.logger.setLevel(log_level)
	
	# Configure root logger for services
	root_logger = logging.getLogger()
	root_logger.handlers.clear()
	root_handler = logging.StreamHandler()
	root_handler.setFormatter(JsonFormatter())
	root_logger.addHandler(root_handler)
	root_logger.setLevel(log_level)

	# SQLAlchemy初期化
	from pomodoro.models import db
	db.init_app(app)
	
	with app.app_context():
		db.create_all()

	# Blueprint登録 (後で詳細実装)
	try:
		from pomodoro.routes import bp as pomodoro_bp
		app.register_blueprint(pomodoro_bp, url_prefix='/api/pomodoro')
	except Exception as e:
		# 初期段階では雛形なので失敗しても警告のみ
		app.logger.warning(f"Pomodoro blueprint not registered yet: {e}")

	# トップページ
	@app.route('/')
	def index():
		from flask import render_template
		return render_template('pomodoro/index.html')

	@app.route('/health')
	def health():
		return {'status': 'ok'}

	return app

if __name__ == '__main__':
	app = create_app()
	app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')
