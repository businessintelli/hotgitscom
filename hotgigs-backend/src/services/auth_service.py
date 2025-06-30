import secrets
import hashlib
from datetime import datetime, timedelta
from flask import current_app, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from src.models.database import db, User, Candidate, Recruiter
import requests
import json

class AuthService:
    """Enhanced authentication service with email verification and social login"""
    
    @staticmethod
    def generate_verification_token(email):
        """Generate email verification token"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(email, salt='email-verification')
    
    @staticmethod
    def verify_email_token(token, max_age=3600):
        """Verify email verification token"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='email-verification', max_age=max_age)
            return email
        except (SignatureExpired, BadSignature):
            return None
    
    @staticmethod
    def generate_password_reset_token(email):
        """Generate password reset token"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(email, salt='password-reset')
    
    @staticmethod
    def verify_password_reset_token(token, max_age=3600):
        """Verify password reset token"""
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='password-reset', max_age=max_age)
            return email
        except (SignatureExpired, BadSignature):
            return None
    
    @staticmethod
    def send_verification_email(user, mail):
        """Send email verification email"""
        token = AuthService.generate_verification_token(user.email)
        verification_url = url_for('auth.verify_email', token=token, _external=True)
        
        msg = Message(
            subject='Verify Your Email - Hotgigs.com',
            recipients=[user.email],
            html=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Welcome to Hotgigs.com!</h2>
                <p>Thank you for registering with Hotgigs.com. Please verify your email address by clicking the button below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #2563eb; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #6b7280;">{verification_url}</p>
                <p>This link will expire in 1 hour for security reasons.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 14px;">
                    If you didn't create an account with Hotgigs.com, please ignore this email.
                </p>
            </div>
            '''
        )
        mail.send(msg)
    
    @staticmethod
    def send_password_reset_email(user, mail):
        """Send password reset email"""
        token = AuthService.generate_password_reset_token(user.email)
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        msg = Message(
            subject='Reset Your Password - Hotgigs.com',
            recipients=[user.email],
            html=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Password Reset Request</h2>
                <p>You have requested to reset your password for your Hotgigs.com account.</p>
                <p>Click the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #dc2626; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #6b7280;">{reset_url}</p>
                <p>This link will expire in 1 hour for security reasons.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 14px;">
                    If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
                </p>
            </div>
            '''
        )
        mail.send(msg)
    
    @staticmethod
    def create_user_from_social(provider, user_info, role='candidate'):
        """Create user from social authentication"""
        try:
            # Extract user information from social provider
            email = user_info.get('email')
            first_name = user_info.get('given_name', user_info.get('first_name', ''))
            last_name = user_info.get('family_name', user_info.get('last_name', ''))
            
            if not email:
                raise ValueError("Email is required from social provider")
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return existing_user, False  # User exists, not created
            
            # Create new user
            user = User(
                email=email,
                role=role,
                is_active=True  # Social users are automatically verified
            )
            # Set a random password (user will use social login)
            user.set_password(secrets.token_urlsafe(32))
            
            db.session.add(user)
            db.session.flush()  # Get user ID
            
            # Create role-specific profile
            if role == 'candidate':
                candidate = Candidate(
                    user_id=user.id,
                    first_name=first_name,
                    last_name=last_name,
                    linkedin_profile=user_info.get('profile_url', '') if provider == 'linkedin' else ''
                )
                db.session.add(candidate)
            elif role == 'recruiter':
                recruiter = Recruiter(
                    user_id=user.id,
                    first_name=first_name,
                    last_name=last_name,
                    company_name='',  # Will be filled later
                    linkedin_profile=user_info.get('profile_url', '') if provider == 'linkedin' else ''
                )
                db.session.add(recruiter)
            
            db.session.commit()
            return user, True  # User created
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_google_user_info(access_token):
        """Get user info from Google OAuth"""
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_linkedin_user_info(access_token):
        """Get user info from LinkedIn OAuth"""
        try:
            # Get basic profile
            profile_response = requests.get(
                'https://api.linkedin.com/v2/people/~:(id,firstName,lastName)',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            # Get email
            email_response = requests.get(
                'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if profile_response.status_code == 200 and email_response.status_code == 200:
                profile_data = profile_response.json()
                email_data = email_response.json()
                
                user_info = {
                    'id': profile_data.get('id'),
                    'first_name': profile_data.get('firstName', {}).get('localized', {}).get('en_US', ''),
                    'last_name': profile_data.get('lastName', {}).get('localized', {}).get('en_US', ''),
                    'email': email_data.get('elements', [{}])[0].get('handle~', {}).get('emailAddress', '')
                }
                return user_info
            return None
        except Exception:
            return None
    
    @staticmethod
    def get_github_user_info(access_token):
        """Get user info from GitHub OAuth"""
        try:
            # Get user profile
            response = requests.get(
                'https://api.github.com/user',
                headers={'Authorization': f'token {access_token}'}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Get primary email if not public
                email = user_data.get('email')
                if not email:
                    email_response = requests.get(
                        'https://api.github.com/user/emails',
                        headers={'Authorization': f'token {access_token}'}
                    )
                    if email_response.status_code == 200:
                        emails = email_response.json()
                        primary_email = next((e for e in emails if e.get('primary')), None)
                        if primary_email:
                            email = primary_email.get('email')
                
                user_info = {
                    'id': user_data.get('id'),
                    'email': email,
                    'first_name': user_data.get('name', '').split(' ')[0] if user_data.get('name') else '',
                    'last_name': ' '.join(user_data.get('name', '').split(' ')[1:]) if user_data.get('name') else '',
                    'profile_url': user_data.get('html_url', '')
                }
                return user_info
            return None
        except Exception:
            return None

class TokenBlacklist:
    """Simple token blacklist implementation"""
    
    def __init__(self):
        self.blacklisted_tokens = set()
    
    def add_token(self, jti):
        """Add token to blacklist"""
        self.blacklisted_tokens.add(jti)
    
    def is_blacklisted(self, jti):
        """Check if token is blacklisted"""
        return jti in self.blacklisted_tokens
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens (implement based on your needs)"""
        # In production, you would implement this with a database or Redis
        pass

# Global token blacklist instance
token_blacklist = TokenBlacklist()

