from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.database import db, User, Candidate, Recruiter, Job, Resume, Application, Skill
from src.services.job_matching_engine import job_matching_engine
from sqlalchemy import and_, or_
from datetime import datetime
import json

matching_bp = Blueprint('matching', __name__)

@matching_bp.route('/find-jobs', methods=['POST'])
@jwt_required()
def find_matching_jobs():
    """Find matching jobs for a candidate"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'candidate':
            return jsonify({'error': 'Access denied. Candidates only.'}), 403
        
        candidate = Candidate.query.filter_by(user_id=current_user_id).first()
        if not candidate:
            return jsonify({'error': 'Candidate profile not found'}), 404
        
        # Get request parameters
        data = request.get_json() or {}
        limit = data.get('limit', 10)
        min_score = data.get('min_score', 0.3)
        location_filter = data.get('location')
        industry_filter = data.get('industry')
        remote_only = data.get('remote_only', False)
        
        # Get candidate's latest resume data
        latest_resume = Resume.query.filter_by(
            candidate_id=candidate.id,
            is_primary=True
        ).first()
        
        if not latest_resume or not latest_resume.parsed_data:
            return jsonify({'error': 'No parsed resume data found. Please upload and parse a resume first.'}), 400
        
        # Prepare candidate data
        candidate_data = {
            'id': candidate.id,
            'personal_info': latest_resume.parsed_data.get('personal_info', {}),
            'contact_info': latest_resume.parsed_data.get('contact_info', {}),
            'summary': latest_resume.parsed_data.get('summary', ''),
            'skills': latest_resume.parsed_data.get('skills', []),
            'education': latest_resume.parsed_data.get('education', []),
            'work_experience': latest_resume.parsed_data.get('work_experience', []),
            'domain_expertise': latest_resume.parsed_data.get('domain_expertise', [])
        }
        
        # Get available jobs with filters
        job_query = Job.query.filter(Job.status == 'active')
        
        if location_filter:
            job_query = job_query.filter(Job.location.ilike(f'%{location_filter}%'))
        
        if industry_filter:
            job_query = job_query.filter(Job.industry.ilike(f'%{industry_filter}%'))
        
        if remote_only:
            job_query = job_query.filter(Job.remote_ok == True)
        
        jobs = job_query.all()
        
        # Prepare job data
        job_data_list = []
        for job in jobs:
            job_data = {
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'industry': job.industry,
                'description': job.description,
                'requirements': job.requirements,
                'remote_ok': job.remote_ok,
                'salary_min': job.salary_min,
                'salary_max': job.salary_max,
                'experience_requirements': {
                    'min_years': job.min_experience_years,
                    'max_years': job.max_experience_years,
                    'level': job.experience_level
                },
                'required_skills': _get_job_skills(job)
            }
            job_data_list.append(job_data)
        
        # Fit models if not already fitted
        if not job_matching_engine._models_fitted:
            all_candidates = _get_all_candidates_data()
            job_matching_engine.fit_models(all_candidates, job_data_list)
        
        # Find matches
        matches = job_matching_engine.find_best_matches(candidate_data, job_data_list, limit)
        
        # Filter by minimum score
        filtered_matches = [match for match in matches if match['match_score'] >= min_score]
        
        # Format response
        response_matches = []
        for match in filtered_matches:
            job_data = match['job_data']
            response_matches.append({
                'job_id': match['job_id'],
                'job_title': match['job_title'],
                'company': match['company'],
                'location': match['location'],
                'industry': job_data.get('industry'),
                'salary_range': _format_salary_range(job_data),
                'remote_ok': job_data.get('remote_ok', False),
                'match_score': match['match_score'],
                'confidence': match['confidence'],
                'match_reasons': match['match_reasons'],
                'skill_match': match['match_breakdown'].get('skills', {}),
                'experience_match': match['match_breakdown'].get('experience', {}),
                'created_at': datetime.now().isoformat()
            })
        
        return jsonify({
            'matches': response_matches,
            'total_found': len(response_matches),
            'search_criteria': {
                'location': location_filter,
                'industry': industry_filter,
                'remote_only': remote_only,
                'min_score': min_score
            },
            'candidate_profile': {
                'name': candidate_data['personal_info'].get('full_name'),
                'skills_count': len(candidate_data['skills']),
                'experience_count': len(candidate_data['work_experience']),
                'domains': candidate_data['domain_expertise']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Job matching failed: {str(e)}'}), 500

@matching_bp.route('/find-candidates', methods=['POST'])
@jwt_required()
def find_matching_candidates():
    """Find matching candidates for a job (recruiters only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'recruiter':
            return jsonify({'error': 'Access denied. Recruiters only.'}), 403
        
        recruiter = Recruiter.query.filter_by(user_id=current_user_id).first()
        if not recruiter:
            return jsonify({'error': 'Recruiter profile not found'}), 404
        
        # Get request parameters
        data = request.get_json()
        job_id = data.get('job_id')
        limit = data.get('limit', 10)
        min_score = data.get('min_score', 0.3)
        
        if not job_id:
            return jsonify({'error': 'job_id is required'}), 400
        
        # Get job data
        job = Job.query.filter_by(id=job_id, recruiter_id=recruiter.id).first()
        if not job:
            return jsonify({'error': 'Job not found or access denied'}), 404
        
        # Prepare job data
        job_data = {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'industry': job.industry,
            'description': job.description,
            'requirements': job.requirements,
            'remote_ok': job.remote_ok,
            'experience_requirements': {
                'min_years': job.min_experience_years,
                'max_years': job.max_experience_years,
                'level': job.experience_level
            },
            'required_skills': _get_job_skills(job)
        }
        
        # Get all candidates with parsed resumes
        candidates_data = _get_all_candidates_data()
        
        # Fit models if not already fitted
        if not job_matching_engine._models_fitted:
            job_matching_engine.fit_models(candidates_data, [job_data])
        
        # Find matches
        matches = job_matching_engine.find_best_candidates(job_data, candidates_data, limit)
        
        # Filter by minimum score
        filtered_matches = [match for match in matches if match['match_score'] >= min_score]
        
        # Format response
        response_matches = []
        for match in filtered_matches:
            candidate_data = match['candidate_data']
            response_matches.append({
                'candidate_id': match['candidate_id'],
                'candidate_name': match['candidate_name'],
                'email': match['email'],
                'location': candidate_data.get('contact_info', {}).get('location'),
                'experience_years': match['experience_years'],
                'top_skills': match['top_skills'],
                'domains': candidate_data.get('domain_expertise', []),
                'match_score': match['match_score'],
                'confidence': match['confidence'],
                'match_reasons': match['match_reasons'],
                'skill_match': match['match_breakdown'].get('skills', {}),
                'experience_match': match['match_breakdown'].get('experience', {}),
                'summary': candidate_data.get('summary', '')[:200] + '...' if candidate_data.get('summary') else '',
                'created_at': datetime.now().isoformat()
            })
        
        return jsonify({
            'matches': response_matches,
            'total_found': len(response_matches),
            'job_info': {
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'industry': job.industry
            },
            'search_criteria': {
                'min_score': min_score
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Candidate matching failed: {str(e)}'}), 500

@matching_bp.route('/match-score', methods=['POST'])
@jwt_required()
def calculate_match_score():
    """Calculate detailed match score between candidate and job"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        job_id = data.get('job_id')
        
        if not candidate_id or not job_id:
            return jsonify({'error': 'candidate_id and job_id are required'}), 400
        
        # Get candidate data
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Get job data
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Check access permissions
        if user.role == 'candidate' and candidate.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        elif user.role == 'recruiter':
            recruiter = Recruiter.query.filter_by(user_id=current_user_id).first()
            if not recruiter or job.recruiter_id != recruiter.id:
                return jsonify({'error': 'Access denied'}), 403
        
        # Get candidate's resume data
        latest_resume = Resume.query.filter_by(
            candidate_id=candidate.id,
            is_primary=True
        ).first()
        
        if not latest_resume or not latest_resume.parsed_data:
            return jsonify({'error': 'No parsed resume data found'}), 400
        
        # Prepare data
        candidate_data = {
            'id': candidate.id,
            'personal_info': latest_resume.parsed_data.get('personal_info', {}),
            'contact_info': latest_resume.parsed_data.get('contact_info', {}),
            'summary': latest_resume.parsed_data.get('summary', ''),
            'skills': latest_resume.parsed_data.get('skills', []),
            'education': latest_resume.parsed_data.get('education', []),
            'work_experience': latest_resume.parsed_data.get('work_experience', []),
            'domain_expertise': latest_resume.parsed_data.get('domain_expertise', [])
        }
        
        job_data = {
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'industry': job.industry,
            'description': job.description,
            'requirements': job.requirements,
            'remote_ok': job.remote_ok,
            'experience_requirements': {
                'min_years': job.min_experience_years,
                'max_years': job.max_experience_years,
                'level': job.experience_level
            },
            'required_skills': _get_job_skills(job)
        }
        
        # Calculate detailed match score
        match_result = job_matching_engine.calculate_match_score(candidate_data, job_data)
        
        return jsonify({
            'candidate_info': {
                'id': candidate.id,
                'name': candidate_data['personal_info'].get('full_name'),
                'email': candidate_data['contact_info'].get('email')
            },
            'job_info': {
                'id': job.id,
                'title': job.title,
                'company': job.company
            },
            'match_analysis': match_result
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Match score calculation failed: {str(e)}'}), 500

@matching_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_matching_analytics():
    """Get matching analytics for the current user"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role == 'candidate':
            return _get_candidate_analytics(current_user_id)
        elif user.role == 'recruiter':
            return _get_recruiter_analytics(current_user_id)
        else:
            return jsonify({'error': 'Analytics not available for this user type'}), 403
            
    except Exception as e:
        return jsonify({'error': f'Analytics retrieval failed: {str(e)}'}), 500

def _get_candidate_analytics(user_id: int):
    """Get analytics for candidate"""
    try:
        candidate = Candidate.query.filter_by(user_id=user_id).first()
        if not candidate:
            return jsonify({'error': 'Candidate profile not found'}), 404
        
        # Get applications and their match scores
        applications = Application.query.filter_by(candidate_id=candidate.id).all()
        
        analytics = {
            'total_applications': len(applications),
            'application_status_breakdown': {},
            'average_match_scores': {},
            'top_matching_industries': [],
            'skill_demand_analysis': {},
            'profile_completeness': _calculate_profile_completeness(candidate)
        }
        
        # Application status breakdown
        status_counts = {}
        for app in applications:
            status = app.status
            status_counts[status] = status_counts.get(status, 0) + 1
        analytics['application_status_breakdown'] = status_counts
        
        # Calculate average match scores by industry (mock data for now)
        analytics['average_match_scores'] = {
            'technology': 0.75,
            'finance': 0.65,
            'healthcare': 0.55
        }
        
        return jsonify({'analytics': analytics}), 200
        
    except Exception as e:
        return jsonify({'error': f'Candidate analytics failed: {str(e)}'}), 500

def _get_recruiter_analytics(user_id: int):
    """Get analytics for recruiter"""
    try:
        recruiter = Recruiter.query.filter_by(user_id=user_id).first()
        if not recruiter:
            return jsonify({'error': 'Recruiter profile not found'}), 404
        
        # Get jobs and applications
        jobs = Job.query.filter_by(recruiter_id=recruiter.id).all()
        total_applications = sum(len(job.applications) for job in jobs)
        
        analytics = {
            'total_jobs_posted': len(jobs),
            'total_applications_received': total_applications,
            'jobs_by_status': {},
            'average_applications_per_job': total_applications / len(jobs) if jobs else 0,
            'top_skills_in_demand': [],
            'hiring_funnel_metrics': {}
        }
        
        # Jobs by status
        status_counts = {}
        for job in jobs:
            status = job.status
            status_counts[status] = status_counts.get(status, 0) + 1
        analytics['jobs_by_status'] = status_counts
        
        return jsonify({'analytics': analytics}), 200
        
    except Exception as e:
        return jsonify({'error': f'Recruiter analytics failed: {str(e)}'}), 500

def _get_job_skills(job):
    """Get skills associated with a job"""
    try:
        # For now, parse skills from requirements text
        # In a full implementation, you'd have a proper job-skills relationship
        skills = []
        if job.requirements:
            # Simple skill extraction from requirements
            common_skills = [
                'python', 'java', 'javascript', 'react', 'angular', 'node.js',
                'sql', 'mysql', 'postgresql', 'mongodb', 'aws', 'azure',
                'docker', 'kubernetes', 'git', 'html', 'css'
            ]
            
            requirements_lower = job.requirements.lower()
            for skill in common_skills:
                if skill in requirements_lower:
                    skills.append({
                        'name': skill.title(),
                        'category': 'Technical',
                        'proficiency_level': 'intermediate',
                        'required': True
                    })
        
        return skills
        
    except Exception:
        return []

def _get_all_candidates_data():
    """Get all candidates with parsed resume data"""
    try:
        candidates_data = []
        
        # Get all candidates with primary resumes
        candidates = db.session.query(Candidate, Resume).join(
            Resume, and_(
                Resume.candidate_id == Candidate.id,
                Resume.is_primary == True
            )
        ).all()
        
        for candidate, resume in candidates:
            if resume.parsed_data:
                candidate_data = {
                    'id': candidate.id,
                    'personal_info': resume.parsed_data.get('personal_info', {}),
                    'contact_info': resume.parsed_data.get('contact_info', {}),
                    'summary': resume.parsed_data.get('summary', ''),
                    'skills': resume.parsed_data.get('skills', []),
                    'education': resume.parsed_data.get('education', []),
                    'work_experience': resume.parsed_data.get('work_experience', []),
                    'domain_expertise': resume.parsed_data.get('domain_expertise', [])
                }
                candidates_data.append(candidate_data)
        
        return candidates_data
        
    except Exception:
        return []

def _format_salary_range(job_data):
    """Format salary range for display"""
    try:
        salary_min = job_data.get('salary_min')
        salary_max = job_data.get('salary_max')
        
        if salary_min and salary_max:
            return f"${salary_min:,} - ${salary_max:,}"
        elif salary_min:
            return f"${salary_min:,}+"
        elif salary_max:
            return f"Up to ${salary_max:,}"
        else:
            return "Salary not specified"
            
    except Exception:
        return "Salary not specified"

def _calculate_profile_completeness(candidate):
    """Calculate candidate profile completeness"""
    try:
        resume = Resume.query.filter_by(
            candidate_id=candidate.id,
            is_primary=True
        ).first()
        
        if not resume or not resume.parsed_data:
            return 0.0
        
        completeness = 0.0
        data = resume.parsed_data
        
        if data.get('personal_info', {}).get('full_name'):
            completeness += 0.15
        if data.get('contact_info', {}).get('email'):
            completeness += 0.15
        if data.get('summary'):
            completeness += 0.15
        if data.get('skills'):
            completeness += 0.25
        if data.get('work_experience'):
            completeness += 0.20
        if data.get('education'):
            completeness += 0.10
        
        return round(completeness, 2)
        
    except Exception:
        return 0.0

