from flask import Flask
from flask_socketio import SocketIO
from dotenv import load_dotenv
import os

socketio = None

def create_app():
	# .env読み込み (存在しない場合は無視)
	load_dotenv()

	app = Flask(__name__)
	app.config.from_object('config.Config')

	# SocketIO初期化
	global socketio
	socketio = SocketIO(app, cors_allowed_origins="*")

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
	socketio.run(app, debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')
