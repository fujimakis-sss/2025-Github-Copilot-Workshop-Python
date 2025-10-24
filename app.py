from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import os

def create_app():
	# .env読み込み (存在しない場合は無視)
	load_dotenv()

	app = Flask(__name__)
	app.config.from_object('config.Config')

	# SQLAlchemy初期化
	from pomodoro.models import db, User
	db.init_app(app)
	
	# Flask-Login初期化
	login_manager = LoginManager()
	login_manager.init_app(app)
	login_manager.login_view = 'auth.login'
	login_manager.login_message = 'Please log in to access this page.'
	
	# Custom unauthorized handler for API routes
	@login_manager.unauthorized_handler
	def unauthorized():
		from flask import request, jsonify, redirect, url_for
		# Return 401 for API requests
		if request.path.startswith('/api/'):
			return jsonify({'error': 'Authentication required'}), 401
		# Redirect to login for web pages
		return redirect(url_for('auth.login', next=request.path))
	
	@login_manager.user_loader
	def load_user(user_id):
		return User.query.get(int(user_id))
	
	with app.app_context():
		db.create_all()

	# Blueprint登録
	try:
		from pomodoro.routes import bp as pomodoro_bp
		app.register_blueprint(pomodoro_bp, url_prefix='/api/pomodoro')
	except Exception as e:
		# 初期段階では雛形なので失敗しても警告のみ
		app.logger.warning(f"Pomodoro blueprint not registered yet: {e}")
	
	# Auth blueprint登録
	from pomodoro.auth import auth_bp
	app.register_blueprint(auth_bp)

	# トップページ
	@app.route('/')
	def index():
		from flask import render_template
		return render_template('pomodoro/index.html')
	
	# Make index route require login
	from flask_login import login_required
	index = login_required(index)

	@app.route('/health')
	def health():
		return {'status': 'ok'}

	return app

if __name__ == '__main__':
	app = create_app()
	app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')
