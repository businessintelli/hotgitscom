import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.models.database import db
from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.job import job_bp
from src.routes.application import application_bp
from src.routes.resume import resume_bp
from src.routes.matching import matching_bp
from src.routes.analytics import analytics_bp
from src.services.auth_service import token_blacklist

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = 'hotgigs-secret-key-change-in-production'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string-change-in-production'

# Email configuration (for development - use environment variables in production)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@hotgigs.com')

# Database configuration - using SQLite for development
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
jwt = JWTManager(app)
mail = Mail(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# JWT token blacklist check
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return token_blacklist.is_blacklisted(jti)

# Enable CORS for all routes
CORS(app, origins="*")

# Apply rate limiting to auth routes
limiter.limit("5 per minute")(auth_bp)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(job_bp, url_prefix='/api/jobs')
app.register_blueprint(application_bp, url_prefix='/api/applications')
app.register_blueprint(resume_bp, url_prefix='/api/resumes')
app.register_blueprint(matching_bp, url_prefix='/api/matching')
app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'hotgigs-api'}, 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
