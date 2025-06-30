from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, Application, Job, Candidate, User

application_bp = Blueprint('application', __name__)

@application_bp.route('/', methods=['GET'])
@jwt_required()
def get_applications():
    """Get applications for current user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        status = request.args.get('status', '')
        
        if user.role == 'candidate':
            candidate = Candidate.query.filter_by(user_id=current_user_id).first()
            if not candidate:
                return jsonify({'error': 'Candidate profile not found'}), 404
            
            query = Application.query.filter_by(candidate_id=candidate.id)
            
        elif user.role == 'recruiter':
            # Get applications for recruiter's jobs
            query = db.session.query(Application).join(Job).filter(
                Job.recruiter_id == user.recruiter_profile.id
            )
        else:
            return jsonify({'error': 'Invalid user role'}), 403
        
        if status:
            query = query.filter_by(status=status)
        
        # Order by submission date (newest first)
        query = query.order_by(Application.submission_date.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, 
            per_page=limit, 
            error_out=False
        )
        
        applications = [app.to_dict() for app in pagination.items]
        
        return jsonify({
            'applications': applications,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_count': pagination.total,
                'total_pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_previous': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@application_bp.route('/', methods=['POST'])
@jwt_required()
def submit_application():
    """Submit job application (Candidates only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'candidate':
            return jsonify({'error': 'Only candidates can submit applications'}), 403
        
        candidate = Candidate.query.filter_by(user_id=current_user_id).first()
        if not candidate:
            return jsonify({'error': 'Candidate profile not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if 'job_id' not in data:
            return jsonify({'error': 'job_id is required'}), 400
        
        # Check if job exists and is active
        job = Job.query.filter_by(id=data['job_id'], status='active').first()
        if not job:
            return jsonify({'error': 'Job not found or not active'}), 404
        
        # Check if application already exists
        existing_application = Application.query.filter_by(
            candidate_id=candidate.id,
            job_id=job.id
        ).first()
        
        if existing_application:
            return jsonify({'error': 'Application already submitted for this job'}), 409
        
        # Create new application
        application = Application(
            candidate_id=candidate.id,
            job_id=job.id,
            resume_id=data.get('resume_id'),
            cover_letter=data.get('cover_letter', ''),
            status='submitted'
        )
        
        db.session.add(application)
        
        # Update job application count
        job.application_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': 'Application submitted successfully',
            'application': application.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@application_bp.route('/<int:application_id>', methods=['GET'])
@jwt_required()
def get_application(application_id):
    """Get specific application details"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check access permissions
        if user.role == 'candidate':
            candidate = Candidate.query.filter_by(user_id=current_user_id).first()
            if not candidate or application.candidate_id != candidate.id:
                return jsonify({'error': 'Access denied'}), 403
        elif user.role == 'recruiter':
            if application.job.recruiter_id != user.recruiter_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        else:
            return jsonify({'error': 'Invalid user role'}), 403
        
        return jsonify({'application': application.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@application_bp.route('/<int:application_id>/status', methods=['PUT'])
@jwt_required()
def update_application_status(application_id):
    """Update application status (Recruiters only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'recruiter':
            return jsonify({'error': 'Only recruiters can update application status'}), 403
        
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Check if recruiter owns the job
        if application.job.recruiter_id != user.recruiter_profile.id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Validate status
        valid_statuses = ['submitted', 'under_review', 'interview', 'rejected', 'hired']
        if 'status' not in data or data['status'] not in valid_statuses:
            return jsonify({'error': f'Status must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Update application
        application.status = data['status']
        if 'notes' in data:
            application.recruiter_notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Application status updated successfully',
            'application': application.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

