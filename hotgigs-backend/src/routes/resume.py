from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from src.models.database import db, User, Candidate, Resume, Skill, CandidateSkill
from src.services.enhanced_resume_parser_test import enhanced_resume_parser
import os
import uuid
from datetime import datetime

resume_bp = Blueprint('resume', __name__)

@resume_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    """Upload and parse resume"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'candidate':
            return jsonify({'error': 'Only candidates can upload resumes'}), 403
        
        candidate = user.candidate_profile
        if not candidate:
            return jsonify({'error': 'Candidate profile not found'}), 404
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get parsing provider from request
        provider = request.form.get('provider', 'spacy_nlp')  # Default to spaCy NLP
        
        # Parse resume
        parsing_result = enhanced_resume_parser.parse_resume(file, provider)
        
        if not parsing_result['success']:
            return jsonify({'error': parsing_result['error']}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        file_extension = filename.rsplit('.', 1)[1].lower()
        stored_filename = f"{file_id}.{file_extension}"
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'resumes')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, stored_filename)
        file.seek(0)  # Reset file pointer
        file.save(file_path)
        
        # Create resume record
        resume = Resume(
            candidate_id=candidate.id,
            filename=filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            content_type=file.content_type,
            parsed_data=parsing_result['data'],
            raw_text=parsing_result.get('raw_text', ''),
            parsing_provider=parsing_result.get('provider', provider),
            parsing_confidence=parsing_result['data'].get('parsing_metadata', {}).get('confidence_score', 0.0),
            is_primary=True  # Set as primary resume
        )
        
        # Set other resumes as non-primary
        Resume.query.filter_by(candidate_id=candidate.id).update({'is_primary': False})
        
        db.session.add(resume)
        db.session.flush()
        
        # Update candidate profile with parsed data
        parsed_data = parsing_result['data']
        personal_info = parsed_data.get('personal_info', {})
        contact_info = parsed_data.get('contact_info', {})
        
        # Update candidate fields if not already set
        if not candidate.first_name and personal_info.get('first_name'):
            candidate.first_name = personal_info['first_name']
        if not candidate.last_name and personal_info.get('last_name'):
            candidate.last_name = personal_info['last_name']
        if not candidate.phone and contact_info.get('phone'):
            candidate.phone = contact_info['phone']
        if not candidate.linkedin_profile and contact_info.get('linkedin'):
            candidate.linkedin_profile = contact_info['linkedin']
        if not candidate.location and contact_info.get('location'):
            candidate.location = contact_info['location']
        if not candidate.bio and parsed_data.get('summary'):
            candidate.bio = parsed_data['summary']
        
        # Set domain expertise
        domain_expertise = parsed_data.get('domain_expertise', [])
        if domain_expertise:
            candidate.domain_expertise = ', '.join(domain_expertise)
        
        # Add skills from resume
        skills_data = parsed_data.get('skills', [])
        for skill_data in skills_data:
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
            
            # Check if candidate already has this skill
            existing_skill = CandidateSkill.query.filter_by(
                candidate_id=candidate.id,
                skill_id=skill.id
            ).first()
            
            if not existing_skill:
                candidate_skill = CandidateSkill(
                    candidate_id=candidate.id,
                    skill_id=skill.id,
                    proficiency_level=skill_data.get('proficiency_level', 'intermediate'),
                    years_experience=0,
                    verified=False,
                    source='resume_parsing'
                )
                db.session.add(candidate_skill)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Resume uploaded and parsed successfully',
            'resume_id': resume.id,
            'parsing_result': {
                'confidence_score': resume.parsing_confidence,
                'completeness_score': parsed_data.get('parsing_metadata', {}).get('completeness_score', 0.0),
                'fields_extracted': list(parsed_data.keys()),
                'skills_found': len(skills_data),
                'domain_expertise': domain_expertise
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Resume upload error: {str(e)}")
        return jsonify({'error': 'Resume upload failed'}), 500

@resume_bp.route('/list', methods=['GET'])
@jwt_required()
def list_resumes():
    """List user's resumes"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'candidate':
            return jsonify({'error': 'Only candidates can view resumes'}), 403
        
        candidate = user.candidate_profile
        if not candidate:
            return jsonify({'error': 'Candidate profile not found'}), 404
        
        resumes = Resume.query.filter_by(candidate_id=candidate.id).order_by(Resume.uploaded_at.desc()).all()
        
        resume_list = []
        for resume in resumes:
            resume_data = {
                'id': resume.id,
                'filename': resume.filename,
                'uploaded_at': resume.uploaded_at.isoformat(),
                'file_size': resume.file_size,
                'is_primary': resume.is_primary,
                'parsing_confidence': resume.parsing_confidence,
                'parsing_provider': resume.parsing_provider
            }
            
            # Add parsing metadata if available
            if resume.parsed_data and 'parsing_metadata' in resume.parsed_data:
                metadata = resume.parsed_data['parsing_metadata']
                resume_data['completeness_score'] = metadata.get('completeness_score', 0.0)
                resume_data['parsed_at'] = metadata.get('parsed_at')
            
            resume_list.append(resume_data)
        
        return jsonify({'resumes': resume_list}), 200
        
    except Exception as e:
        current_app.logger.error(f"Resume list error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve resumes'}), 500

@resume_bp.route('/<int:resume_id>', methods=['GET'])
@jwt_required()
def get_resume_details():
    """Get detailed resume information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        resume_id = request.view_args['resume_id']
        resume = Resume.query.get(resume_id)
        
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Check permissions
        if user.role == 'candidate':
            candidate = user.candidate_profile
            if not candidate or resume.candidate_id != candidate.id:
                return jsonify({'error': 'Access denied'}), 403
        elif user.role == 'recruiter':
            # Recruiters can view resumes of candidates who applied to their jobs
            # This would require additional logic to check job applications
            pass
        else:
            return jsonify({'error': 'Access denied'}), 403
        
        # Prepare detailed resume data
        resume_data = {
            'id': resume.id,
            'filename': resume.filename,
            'uploaded_at': resume.uploaded_at.isoformat(),
            'file_size': resume.file_size,
            'is_primary': resume.is_primary,
            'parsing_confidence': resume.parsing_confidence,
            'parsing_provider': resume.parsing_provider,
            'parsed_data': resume.parsed_data,
            'raw_text': resume.raw_text if user.role == 'candidate' else None  # Only show raw text to owner
        }
        
        return jsonify({'resume': resume_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Resume details error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve resume details'}), 500

@resume_bp.route('/<int:resume_id>/set-primary', methods=['PUT'])
@jwt_required()
def set_primary_resume():
    """Set resume as primary"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'candidate':
            return jsonify({'error': 'Only candidates can set primary resume'}), 403
        
        candidate = user.candidate_profile
        if not candidate:
            return jsonify({'error': 'Candidate profile not found'}), 404
        
        resume_id = request.view_args['resume_id']
        resume = Resume.query.get(resume_id)
        
        if not resume or resume.candidate_id != candidate.id:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Set all resumes as non-primary
        Resume.query.filter_by(candidate_id=candidate.id).update({'is_primary': False})
        
        # Set this resume as primary
        resume.is_primary = True
        
        db.session.commit()
        
        return jsonify({'message': 'Primary resume updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Set primary resume error: {str(e)}")
        return jsonify({'error': 'Failed to update primary resume'}), 500

@resume_bp.route('/<int:resume_id>', methods=['DELETE'])
@jwt_required()
def delete_resume():
    """Delete resume"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'candidate':
            return jsonify({'error': 'Only candidates can delete resumes'}), 403
        
        candidate = user.candidate_profile
        if not candidate:
            return jsonify({'error': 'Candidate profile not found'}), 404
        
        resume_id = request.view_args['resume_id']
        resume = Resume.query.get(resume_id)
        
        if not resume or resume.candidate_id != candidate.id:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Delete file from filesystem
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
        
        # Delete from database
        db.session.delete(resume)
        db.session.commit()
        
        return jsonify({'message': 'Resume deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Delete resume error: {str(e)}")
        return jsonify({'error': 'Failed to delete resume'}), 500

@resume_bp.route('/reparse/<int:resume_id>', methods=['POST'])
@jwt_required()
def reparse_resume():
    """Reparse existing resume with different provider"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'candidate':
            return jsonify({'error': 'Only candidates can reparse resumes'}), 403
        
        candidate = user.candidate_profile
        if not candidate:
            return jsonify({'error': 'Candidate profile not found'}), 404
        
        resume_id = request.view_args['resume_id']
        resume = Resume.query.get(resume_id)
        
        if not resume or resume.candidate_id != candidate.id:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Get new provider
        data = request.get_json()
        provider = data.get('provider', 'spacy_nlp')  # Default to spaCy NLP
        
        # Reparse the file
        with open(resume.file_path, 'rb') as file:
            parsing_result = enhanced_resume_parser.parse_resume(file, provider)
        
        if not parsing_result['success']:
            return jsonify({'error': parsing_result['error']}), 400
        
        # Update resume with new parsing results
        resume.parsed_data = parsing_result['data']
        resume.raw_text = parsing_result.get('raw_text', '')
        resume.parsing_provider = parsing_result.get('provider', provider)
        resume.parsing_confidence = parsing_result['data'].get('parsing_metadata', {}).get('confidence_score', 0.0)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Resume reparsed successfully',
            'parsing_result': {
                'confidence_score': resume.parsing_confidence,
                'completeness_score': parsing_result['data'].get('parsing_metadata', {}).get('completeness_score', 0.0),
                'provider': resume.parsing_provider
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Resume reparse error: {str(e)}")
        return jsonify({'error': 'Failed to reparse resume'}), 500

@resume_bp.route('/bulk-upload', methods=['POST'])
@jwt_required()
def bulk_upload_resumes():
    """Bulk upload multiple resumes"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'recruiter':
            return jsonify({'error': 'Only recruiters can bulk upload resumes'}), 403
        
        # This would be used for importing candidate resumes
        # Implementation would depend on specific requirements
        
        return jsonify({'message': 'Bulk upload feature coming soon'}), 501
        
    except Exception as e:
        current_app.logger.error(f"Bulk upload error: {str(e)}")
        return jsonify({'error': 'Bulk upload failed'}), 500

@resume_bp.route('/parsing-providers', methods=['GET'])
def get_parsing_providers():
    """Get available parsing providers"""
    try:
        providers = [
            {
                'id': 'spacy_nlp',
                'name': 'spaCy NLP Parser',
                'description': 'Advanced NLP-based parsing with Named Entity Recognition and intelligent extraction',
                'supported_formats': ['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif'],
                'free': True,
                'default': True,
                'features': [
                    'Named Entity Recognition',
                    'Advanced skills categorization',
                    'Domain expertise identification',
                    'Experience level assessment',
                    'Intelligent pattern matching',
                    'High accuracy parsing'
                ]
            },
            {
                'id': 'text_extraction',
                'name': 'Text Extraction',
                'description': 'Basic text extraction from documents with rule-based parsing',
                'supported_formats': ['pdf', 'docx', 'txt'],
                'free': True,
                'default': False,
                'features': [
                    'Fast processing',
                    'Basic information extraction',
                    'Keyword-based skills detection'
                ]
            },
            {
                'id': 'ocr_space',
                'name': 'OCR.space',
                'description': 'Cloud-based OCR for scanned documents and images',
                'supported_formats': ['pdf', 'png', 'jpg', 'jpeg', 'gif'],
                'free': True,
                'default': False,
                'features': [
                    'High-quality OCR',
                    'Scanned document support',
                    'Multiple language support'
                ]
            },
            {
                'id': 'local_ocr',
                'name': 'Local OCR',
                'description': 'Local Tesseract OCR processing for privacy-focused parsing',
                'supported_formats': ['png', 'jpg', 'jpeg', 'gif', 'pdf'],
                'free': True,
                'default': False,
                'features': [
                    'Privacy-focused processing',
                    'No external API calls',
                    'Image preprocessing'
                ]
            }
        ]
        
        return jsonify({'providers': providers}), 200
        
    except Exception as e:
        current_app.logger.error(f"Get providers error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve providers'}), 500

@resume_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_resume_analytics():
    """Get resume parsing analytics"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'candidate':
            return jsonify({'error': 'Only candidates can view resume analytics'}), 403
        
        candidate = user.candidate_profile
        if not candidate:
            return jsonify({'error': 'Candidate profile not found'}), 404
        
        resumes = Resume.query.filter_by(candidate_id=candidate.id).all()
        
        if not resumes:
            return jsonify({'analytics': {'total_resumes': 0}}), 200
        
        # Calculate analytics
        total_resumes = len(resumes)
        avg_confidence = sum(r.parsing_confidence for r in resumes) / total_resumes
        
        # Provider usage
        provider_usage = {}
        for resume in resumes:
            provider = resume.parsing_provider
            provider_usage[provider] = provider_usage.get(provider, 0) + 1
        
        # Skills extracted
        all_skills = set()
        for resume in resumes:
            if resume.parsed_data and 'skills' in resume.parsed_data:
                for skill in resume.parsed_data['skills']:
                    all_skills.add(skill.get('name', ''))
        
        analytics = {
            'total_resumes': total_resumes,
            'average_confidence': round(avg_confidence, 2),
            'provider_usage': provider_usage,
            'unique_skills_found': len(all_skills),
            'primary_resume_id': next((r.id for r in resumes if r.is_primary), None)
        }
        
        return jsonify({'analytics': analytics}), 200
        
    except Exception as e:
        current_app.logger.error(f"Resume analytics error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500

