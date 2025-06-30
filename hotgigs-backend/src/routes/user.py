from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Candidate, Recruiter, Skill, CandidateSkill
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user's profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get profile data based on role
        profile_data = None
        if user.role == 'candidate' and user.candidate_profile:
            profile_data = user.candidate_profile.to_dict()
            # Include skills
            skills = []
            for candidate_skill in user.candidate_profile.skills:
                skill_data = candidate_skill.skill.to_dict()
                skill_data['proficiency_level'] = candidate_skill.proficiency_level
                skill_data['years_experience'] = candidate_skill.years_experience
                skills.append(skill_data)
            profile_data['skills'] = skills
            
        elif user.role == 'recruiter' and user.recruiter_profile:
            profile_data = user.recruiter_profile.to_dict()
        
        return jsonify({
            'user': user.to_dict(),
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user's profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update profile based on role
        if user.role == 'candidate':
            candidate = user.candidate_profile
            if not candidate:
                return jsonify({'error': 'Candidate profile not found'}), 404
            
            # Update candidate fields
            updatable_fields = [
                'first_name', 'last_name', 'phone', 'linkedin_profile',
                'current_title', 'location', 'years_experience', 'bio',
                'desired_salary_min', 'desired_salary_max', 'availability',
                'domain_expertise'
            ]
            
            for field in updatable_fields:
                if field in data:
                    setattr(candidate, field, data[field])
            
            # Handle skills update
            if 'skills' in data:
                # Remove existing skills
                CandidateSkill.query.filter_by(candidate_id=candidate.id).delete()
                
                # Add new skills
                for skill_data in data['skills']:
                    skill_name = skill_data.get('name', '').strip()
                    if not skill_name:
                        continue
                    
                    # Get or create skill
                    skill = Skill.query.filter_by(name=skill_name).first()
                    if not skill:
                        skill = Skill(
                            name=skill_name,
                            category=skill_data.get('category', 'other')
                        )
                        db.session.add(skill)
                        db.session.flush()
                    
                    # Create candidate skill relationship
                    candidate_skill = CandidateSkill(
                        candidate_id=candidate.id,
                        skill_id=skill.id,
                        proficiency_level=skill_data.get('proficiency_level', 'intermediate'),
                        years_experience=skill_data.get('years_experience', 0),
                        verified=False
                    )
                    db.session.add(candidate_skill)
            
        elif user.role == 'recruiter':
            recruiter = user.recruiter_profile
            if not recruiter:
                return jsonify({'error': 'Recruiter profile not found'}), 404
            
            # Update recruiter fields
            updatable_fields = [
                'first_name', 'last_name', 'phone', 'linkedin_profile',
                'company_name', 'company_website', 'bio', 'location'
            ]
            
            for field in updatable_fields:
                if field in data:
                    setattr(recruiter, field, data[field])
        
        db.session.commit()
        
        return jsonify({'message': 'Profile updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """Get user settings and preferences"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Default settings (in production, store in database)
        settings = {
            'email_notifications': True,
            'job_alerts': True,
            'application_updates': True,
            'marketing_emails': False,
            'profile_visibility': 'public',
            'timezone': 'UTC',
            'language': 'en'
        }
        
        return jsonify({'settings': settings}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update user settings and preferences"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # In production, you would store these in a UserSettings table
        # For now, just validate and return success
        valid_settings = [
            'email_notifications', 'job_alerts', 'application_updates',
            'marketing_emails', 'profile_visibility', 'timezone', 'language'
        ]
        
        updated_settings = {}
        for setting in valid_settings:
            if setting in data:
                updated_settings[setting] = data[setting]
        
        return jsonify({
            'message': 'Settings updated successfully',
            'settings': updated_settings
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/deactivate', methods=['POST'])
@jwt_required()
def deactivate_account():
    """Deactivate user account"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Verify password for security
        if not data.get('password'):
            return jsonify({'error': 'Password is required to deactivate account'}), 400
        
        if not user.check_password(data['password']):
            return jsonify({'error': 'Invalid password'}), 401
        
        # Deactivate account
        user.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Account deactivated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/skills/search', methods=['GET'])
def search_skills():
    """Search for skills (public endpoint)"""
    try:
        query = request.args.get('q', '').strip()
        category = request.args.get('category', '')
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({'skills': []}), 200
        
        # Build query
        skills_query = Skill.query.filter(Skill.name.ilike(f'%{query}%'))
        
        if category:
            skills_query = skills_query.filter_by(category=category)
        
        # Order by popularity (most used first)
        skills = skills_query.order_by(Skill.popularity_score.desc()).limit(limit).all()
        
        return jsonify({
            'skills': [skill.to_dict() for skill in skills]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/skills/categories', methods=['GET'])
def get_skill_categories():
    """Get available skill categories"""
    try:
        categories = db.session.query(Skill.category).distinct().all()
        category_list = [cat[0] for cat in categories if cat[0]]
        
        return jsonify({'categories': category_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/onboarding/status', methods=['GET'])
@jwt_required()
def get_onboarding_status():
    """Get user onboarding completion status"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check onboarding completion based on role
        onboarding_steps = []
        
        if user.role == 'candidate':
            candidate = user.candidate_profile
            if candidate:
                onboarding_steps = [
                    {
                        'step': 'basic_info',
                        'completed': bool(candidate.first_name and candidate.last_name),
                        'title': 'Basic Information'
                    },
                    {
                        'step': 'contact_info',
                        'completed': bool(candidate.phone and candidate.location),
                        'title': 'Contact Information'
                    },
                    {
                        'step': 'professional_info',
                        'completed': bool(candidate.current_title and candidate.years_experience > 0),
                        'title': 'Professional Information'
                    },
                    {
                        'step': 'skills',
                        'completed': len(candidate.skills) > 0,
                        'title': 'Skills & Expertise'
                    },
                    {
                        'step': 'preferences',
                        'completed': bool(candidate.desired_salary_min or candidate.availability),
                        'title': 'Job Preferences'
                    }
                ]
        
        elif user.role == 'recruiter':
            recruiter = user.recruiter_profile
            if recruiter:
                onboarding_steps = [
                    {
                        'step': 'basic_info',
                        'completed': bool(recruiter.first_name and recruiter.last_name),
                        'title': 'Basic Information'
                    },
                    {
                        'step': 'company_info',
                        'completed': bool(recruiter.company_name),
                        'title': 'Company Information'
                    },
                    {
                        'step': 'contact_info',
                        'completed': bool(recruiter.phone),
                        'title': 'Contact Information'
                    },
                    {
                        'step': 'profile',
                        'completed': bool(recruiter.bio),
                        'title': 'Professional Profile'
                    }
                ]
        
        completed_steps = sum(1 for step in onboarding_steps if step['completed'])
        total_steps = len(onboarding_steps)
        completion_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        return jsonify({
            'onboarding_steps': onboarding_steps,
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'completion_percentage': completion_percentage,
            'is_complete': completion_percentage == 100
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get user dashboard statistics"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        stats = {}
        
        if user.role == 'candidate':
            from src.models.database import Application
            candidate = user.candidate_profile
            if candidate:
                # Get application statistics
                total_applications = Application.query.filter_by(candidate_id=candidate.id).count()
                pending_applications = Application.query.filter_by(
                    candidate_id=candidate.id, 
                    status='submitted'
                ).count()
                interview_applications = Application.query.filter_by(
                    candidate_id=candidate.id, 
                    status='interview'
                ).count()
                
                stats = {
                    'total_applications': total_applications,
                    'pending_applications': pending_applications,
                    'interview_applications': interview_applications,
                    'profile_views': 0,  # Implement profile view tracking
                    'skills_count': len(candidate.skills)
                }
        
        elif user.role == 'recruiter':
            from src.models.database import Job, Application
            recruiter = user.recruiter_profile
            if recruiter:
                # Get job and application statistics
                total_jobs = Job.query.filter_by(recruiter_id=recruiter.id).count()
                active_jobs = Job.query.filter_by(
                    recruiter_id=recruiter.id, 
                    status='active'
                ).count()
                
                # Get applications for recruiter's jobs
                total_applications = db.session.query(Application).join(Job).filter(
                    Job.recruiter_id == recruiter.id
                ).count()
                
                new_applications = db.session.query(Application).join(Job).filter(
                    Job.recruiter_id == recruiter.id,
                    Application.status == 'submitted'
                ).count()
                
                stats = {
                    'total_jobs': total_jobs,
                    'active_jobs': active_jobs,
                    'total_applications': total_applications,
                    'new_applications': new_applications
                }
        
        return jsonify({'stats': stats}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

