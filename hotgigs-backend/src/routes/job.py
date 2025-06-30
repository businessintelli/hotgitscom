from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, Job, Recruiter, User
from datetime import datetime

job_bp = Blueprint('job', __name__)

@job_bp.route('/', methods=['GET'])
def get_jobs():
    """Get list of jobs with filtering and pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search_query = request.args.get('q', '')
        location = request.args.get('location', '')
        experience_level = request.args.get('experience_level', '')
        employment_type = request.args.get('employment_type', '')
        remote_option = request.args.get('remote_option', type=bool)
        
        # Build query
        query = Job.query.filter_by(status='active')
        
        if search_query:
            query = query.filter(
                db.or_(
                    Job.title.ilike(f'%{search_query}%'),
                    Job.description.ilike(f'%{search_query}%'),
                    Job.company_name.ilike(f'%{search_query}%')
                )
            )
        
        if location:
            query = query.filter(Job.location.ilike(f'%{location}%'))
        
        if experience_level:
            query = query.filter_by(experience_level=experience_level)
        
        if employment_type:
            query = query.filter_by(employment_type=employment_type)
        
        if remote_option is not None:
            query = query.filter_by(remote_option=remote_option)
        
        # Order by posted date (newest first)
        query = query.order_by(Job.posted_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, 
            per_page=limit, 
            error_out=False
        )
        
        jobs = [job.to_dict() for job in pagination.items]
        
        return jsonify({
            'jobs': jobs,
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

@job_bp.route('/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get specific job details"""
    try:
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Increment view count
        job.view_count += 1
        db.session.commit()
        
        return jsonify({'job': job.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@job_bp.route('/', methods=['POST'])
@jwt_required()
def create_job():
    """Create a new job posting (Recruiters only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'recruiter':
            return jsonify({'error': 'Only recruiters can create job postings'}), 403
        
        recruiter = Recruiter.query.filter_by(user_id=current_user_id).first()
        if not recruiter:
            return jsonify({'error': 'Recruiter profile not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description', 'requirements', 'location', 'company_name']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create new job
        job = Job(
            recruiter_id=recruiter.id,
            title=data['title'],
            description=data['description'],
            requirements=data['requirements'],
            location=data['location'],
            company_name=data['company_name'],
            salary_range=data.get('salary_range', ''),
            employment_type=data.get('employment_type', 'full-time'),
            experience_level=data.get('experience_level', 'mid'),
            remote_option=data.get('remote_option', False),
            deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
            status=data.get('status', 'active')
        )
        
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'message': 'Job created successfully',
            'job': job.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@job_bp.route('/<int:job_id>', methods=['PUT'])
@jwt_required()
def update_job(job_id):
    """Update job posting (Recruiters only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'recruiter':
            return jsonify({'error': 'Only recruiters can update job postings'}), 403
        
        recruiter = Recruiter.query.filter_by(user_id=current_user_id).first()
        if not recruiter:
            return jsonify({'error': 'Recruiter profile not found'}), 404
        
        job = Job.query.filter_by(id=job_id, recruiter_id=recruiter.id).first()
        if not job:
            return jsonify({'error': 'Job not found or access denied'}), 404
        
        data = request.get_json()
        
        # Update job fields
        updatable_fields = [
            'title', 'description', 'requirements', 'location', 'salary_range',
            'employment_type', 'experience_level', 'remote_option', 'status'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(job, field, data[field])
        
        if 'deadline' in data and data['deadline']:
            job.deadline = datetime.fromisoformat(data['deadline'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Job updated successfully',
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@job_bp.route('/<int:job_id>', methods=['DELETE'])
@jwt_required()
def delete_job(job_id):
    """Delete job posting (Recruiters only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'recruiter':
            return jsonify({'error': 'Only recruiters can delete job postings'}), 403
        
        recruiter = Recruiter.query.filter_by(user_id=current_user_id).first()
        if not recruiter:
            return jsonify({'error': 'Recruiter profile not found'}), 404
        
        job = Job.query.filter_by(id=job_id, recruiter_id=recruiter.id).first()
        if not job:
            return jsonify({'error': 'Job not found or access denied'}), 404
        
        db.session.delete(job)
        db.session.commit()
        
        return jsonify({'message': 'Job deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

