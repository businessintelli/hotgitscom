from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from src.models.database import db, User, Candidate, Recruiter
from src.services.auth_service import AuthService, token_blacklist
from datetime import datetime, timedelta
import re
import secrets

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with email verification"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'role', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate email format
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Validate role
        if data['role'] not in ['candidate', 'recruiter']:
            return jsonify({'error': 'Role must be either candidate or recruiter'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        # Create new user (inactive until email verification)
        user = User(
            email=data['email'],
            role=data['role'],
            is_active=False  # Require email verification
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create role-specific profile
        if data['role'] == 'candidate':
            candidate = Candidate(
                user_id=user.id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone=data.get('phone', ''),
                linkedin_profile=data.get('linkedin_profile', ''),
                current_title=data.get('current_title', ''),
                location=data.get('location', ''),
                years_experience=data.get('years_experience', 0)
            )
            db.session.add(candidate)
            
        elif data['role'] == 'recruiter':
            if 'company_name' not in data or not data['company_name']:
                return jsonify({'error': 'Company name is required for recruiters'}), 400
            
            recruiter = Recruiter(
                user_id=user.id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                company_name=data['company_name'],
                company_website=data.get('company_website', ''),
                phone=data.get('phone', ''),
                linkedin_profile=data.get('linkedin_profile', ''),
                bio=data.get('bio', '')
            )
            db.session.add(recruiter)
        
        db.session.commit()
        
        # Send verification email
        try:
            mail = current_app.extensions.get('mail')
            if mail:
                AuthService.send_verification_email(user, mail)
                verification_sent = True
            else:
                verification_sent = False
        except Exception as e:
            verification_sent = False
            current_app.logger.error(f"Failed to send verification email: {str(e)}")
        
        return jsonify({
            'message': 'User registered successfully. Please check your email for verification.',
            'user': user.to_dict(),
            'verification_email_sent': verification_sent
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """Verify email address"""
    try:
        email = AuthService.verify_email_token(token)
        if not email:
            return jsonify({'error': 'Invalid or expired verification token'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_active:
            return jsonify({'message': 'Email already verified'}), 200
        
        user.is_active = True
        db.session.commit()
        
        return jsonify({'message': 'Email verified successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """Resend verification email"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.is_active:
            return jsonify({'message': 'Email already verified'}), 200
        
        # Send verification email
        try:
            mail = current_app.extensions.get('mail')
            if mail:
                AuthService.send_verification_email(user, mail)
                return jsonify({'message': 'Verification email sent'}), 200
            else:
                return jsonify({'error': 'Email service not configured'}), 500
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {str(e)}")
            return jsonify({'error': 'Failed to send verification email'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return tokens"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = User.query.filter_by(email=data['email']).first()
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if user is active (email verified)
        if not user.is_active:
            return jsonify({'error': 'Please verify your email before logging in'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        # Get profile data
        profile_data = None
        if user.role == 'candidate' and user.candidate_profile:
            profile_data = user.candidate_profile.to_dict()
        elif user.role == 'recruiter' and user.recruiter_profile:
            profile_data = user.recruiter_profile.to_dict()
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'profile': profile_data,
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            # Don't reveal if user exists or not for security
            return jsonify({'message': 'If the email exists, a password reset link has been sent'}), 200
        
        # Send password reset email
        try:
            mail = current_app.extensions.get('mail')
            if mail:
                AuthService.send_password_reset_email(user, mail)
                return jsonify({'message': 'Password reset email sent'}), 200
            else:
                return jsonify({'error': 'Email service not configured'}), 500
        except Exception as e:
            current_app.logger.error(f"Failed to send password reset email: {str(e)}")
            return jsonify({'error': 'Failed to send password reset email'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    """Reset password with token"""
    try:
        email = AuthService.verify_password_reset_token(token)
        if not email:
            return jsonify({'error': 'Invalid or expired reset token'}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data.get('password'):
            return jsonify({'error': 'New password is required'}), 400
        
        # Validate new password
        is_valid, message = validate_password(data['password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        user.set_password(data['password'])
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/social/google', methods=['POST'])
def google_auth():
    """Google OAuth authentication"""
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        role = data.get('role', 'candidate')
        
        if not access_token:
            return jsonify({'error': 'Access token is required'}), 400
        
        # Get user info from Google
        user_info = AuthService.get_google_user_info(access_token)
        if not user_info:
            return jsonify({'error': 'Failed to get user info from Google'}), 400
        
        # Create or get user
        user, created = AuthService.create_user_from_social('google', user_info, role)
        
        # Generate tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        # Get profile data
        profile_data = None
        if user.role == 'candidate' and user.candidate_profile:
            profile_data = user.candidate_profile.to_dict()
        elif user.role == 'recruiter' and user.recruiter_profile:
            profile_data = user.recruiter_profile.to_dict()
        
        return jsonify({
            'message': 'Authentication successful',
            'user': user.to_dict(),
            'profile': profile_data,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'is_new_user': created
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/social/linkedin', methods=['POST'])
def linkedin_auth():
    """LinkedIn OAuth authentication"""
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        role = data.get('role', 'candidate')
        
        if not access_token:
            return jsonify({'error': 'Access token is required'}), 400
        
        # Get user info from LinkedIn
        user_info = AuthService.get_linkedin_user_info(access_token)
        if not user_info:
            return jsonify({'error': 'Failed to get user info from LinkedIn'}), 400
        
        # Create or get user
        user, created = AuthService.create_user_from_social('linkedin', user_info, role)
        
        # Generate tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        # Get profile data
        profile_data = None
        if user.role == 'candidate' and user.candidate_profile:
            profile_data = user.candidate_profile.to_dict()
        elif user.role == 'recruiter' and user.recruiter_profile:
            profile_data = user.recruiter_profile.to_dict()
        
        return jsonify({
            'message': 'Authentication successful',
            'user': user.to_dict(),
            'profile': profile_data,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'is_new_user': created
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/social/github', methods=['POST'])
def github_auth():
    """GitHub OAuth authentication"""
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        role = data.get('role', 'candidate')
        
        if not access_token:
            return jsonify({'error': 'Access token is required'}), 400
        
        # Get user info from GitHub
        user_info = AuthService.get_github_user_info(access_token)
        if not user_info:
            return jsonify({'error': 'Failed to get user info from GitHub'}), 400
        
        # Create or get user
        user, created = AuthService.create_user_from_social('github', user_info, role)
        
        # Generate tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        # Get profile data
        profile_data = None
        if user.role == 'candidate' and user.candidate_profile:
            profile_data = user.candidate_profile.to_dict()
        elif user.role == 'recruiter' and user.recruiter_profile:
            profile_data = user.recruiter_profile.to_dict()
        
        return jsonify({
            'message': 'Authentication successful',
            'user': user.to_dict(),
            'profile': profile_data,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'is_new_user': created
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 404
        
        # Generate new access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user and blacklist token"""
    try:
        jti = get_jwt()['jti']
        token_blacklist.add_token(jti)
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get profile data
        profile_data = None
        if user.role == 'candidate' and user.candidate_profile:
            profile_data = user.candidate_profile.to_dict()
        elif user.role == 'recruiter' and user.recruiter_profile:
            profile_data = user.recruiter_profile.to_dict()
        
        return jsonify({
            'user': user.to_dict(),
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Validate new password
        is_valid, message = validate_password(data['new_password'])
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Update password
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

