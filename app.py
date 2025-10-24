from flask import Flask, request, session
from dotenv import load_dotenv
from flask_babel import Babel, get_locale as babel_get_locale
import os

def get_locale():
	# Check if user has set language preference in session
	if 'language' in session:
		return session['language']
	# Otherwise, try to guess from Accept-Language header
	best_match = request.accept_languages.best_match(['en', 'ja'])
	return best_match if best_match else 'ja'

def create_app():
	# .env読み込み (存在しない場合は無視)
	load_dotenv()

	app = Flask(__name__)
	app.config.from_object('config.Config')
	
	# Babel configuration
	app.config['BABEL_DEFAULT_LOCALE'] = 'ja'
	app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'ja']
	app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
	
	# Initialize Babel
	babel = Babel(app, locale_selector=get_locale)
	
	# Make get_locale available in templates
	@app.context_processor
	def inject_locale():
		return dict(get_locale=babel_get_locale)

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
	
	@app.route('/set-language/<language>')
	def set_language(language):
		if language in ['en', 'ja']:
			session['language'] = language
		from flask import redirect, url_for
		return redirect(url_for('index'))

	return app

if __name__ == '__main__':
	app = create_app()
	app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')
