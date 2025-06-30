from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'candidate', 'recruiter', 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    recruiter_profile = db.relationship('Recruiter', backref='user', uselist=False, cascade='all, delete-orphan')
    candidate_profile = db.relationship('Candidate', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Recruiter(db.Model):
    __tablename__ = 'recruiters'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    company_website = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    linkedin_profile = db.Column(db.String(200))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('Job', backref='recruiter', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'company_name': self.company_name,
            'company_website': self.company_website,
            'phone': self.phone,
            'linkedin_profile': self.linkedin_profile,
            'bio': self.bio,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Candidate(db.Model):
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    linkedin_profile = db.Column(db.String(200))
    current_title = db.Column(db.String(100))
    years_experience = db.Column(db.Integer, default=0)
    skills_summary = db.Column(db.Text)
    education_summary = db.Column(db.Text)
    domain_expertise = db.Column(db.Text)  # JSON string for domain knowledge
    location = db.Column(db.String(100))
    salary_expectation = db.Column(db.String(50))
    availability = db.Column(db.String(50))  # 'immediate', '2weeks', '1month', etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    resumes = db.relationship('Resume', backref='candidate', lazy=True, cascade='all, delete-orphan')
    applications = db.relationship('Application', backref='candidate', lazy=True, cascade='all, delete-orphan')
    candidate_skills = db.relationship('CandidateSkill', backref='candidate', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'linkedin_profile': self.linkedin_profile,
            'current_title': self.current_title,
            'years_experience': self.years_experience,
            'skills_summary': self.skills_summary,
            'education_summary': self.education_summary,
            'domain_expertise': json.loads(self.domain_expertise) if self.domain_expertise else [],
            'location': self.location,
            'salary_expectation': self.salary_expectation,
            'availability': self.availability,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiters.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    salary_range = db.Column(db.String(100))
    company_name = db.Column(db.String(100), nullable=False)
    employment_type = db.Column(db.String(50))  # 'full-time', 'part-time', 'contract', 'freelance'
    experience_level = db.Column(db.String(50))  # 'entry', 'mid', 'senior', 'executive'
    remote_option = db.Column(db.Boolean, default=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # 'active', 'paused', 'closed', 'draft'
    ai_context = db.Column(db.Text)  # JSON string for AI-generated insights
    view_count = db.Column(db.Integer, default=0)
    application_count = db.Column(db.Integer, default=0)
    
    # Relationships
    applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete-orphan')
    job_skills = db.relationship('JobSkill', backref='job', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'recruiter_id': self.recruiter_id,
            'title': self.title,
            'description': self.description,
            'requirements': self.requirements,
            'location': self.location,
            'salary_range': self.salary_range,
            'company_name': self.company_name,
            'employment_type': self.employment_type,
            'experience_level': self.experience_level,
            'remote_option': self.remote_option,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'status': self.status,
            'ai_context': json.loads(self.ai_context) if self.ai_context else {},
            'view_count': self.view_count,
            'application_count': self.application_count
        }

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'))
    cover_letter = db.Column(db.Text)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='submitted')  # 'submitted', 'under_review', 'interview', 'rejected', 'hired'
    match_score = db.Column(db.Float)
    match_report = db.Column(db.Text)  # JSON string with detailed match analysis
    ai_insights = db.Column(db.Text)  # JSON string for AI-generated insights
    recruiter_notes = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate applications
    __table_args__ = (db.UniqueConstraint('candidate_id', 'job_id', name='unique_candidate_job_application'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'job_id': self.job_id,
            'resume_id': self.resume_id,
            'cover_letter': self.cover_letter,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'status': self.status,
            'match_score': self.match_score,
            'match_report': json.loads(self.match_report) if self.match_report else {},
            'ai_insights': json.loads(self.ai_insights) if self.ai_insights else {},
            'recruiter_notes': self.recruiter_notes,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    file_format = db.Column(db.String(10))  # 'pdf', 'docx', 'txt'
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    parsing_status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    parsed_data = db.Column(db.Text)  # JSON string with extracted data
    ai_insights = db.Column(db.Text)  # JSON string for AI-generated insights
    ats_score = db.Column(db.Float)  # ATS compatibility score
    is_primary = db.Column(db.Boolean, default=False)  # Primary resume for the candidate
    
    # Relationships
    applications = db.relationship('Application', backref='resume', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_format': self.file_format,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'parsing_status': self.parsing_status,
            'parsed_data': json.loads(self.parsed_data) if self.parsed_data else {},
            'ai_insights': json.loads(self.ai_insights) if self.ai_insights else {},
            'ats_score': self.ats_score,
            'is_primary': self.is_primary
        }

class Skill(db.Model):
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50))  # 'technical', 'soft', 'language', 'certification'
    description = db.Column(db.Text)
    popularity_score = db.Column(db.Float, default=0.0)  # Based on frequency in job postings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    candidate_skills = db.relationship('CandidateSkill', backref='skill', lazy=True)
    job_skills = db.relationship('JobSkill', backref='skill', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'popularity_score': self.popularity_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CandidateSkill(db.Model):
    __tablename__ = 'candidate_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    proficiency_level = db.Column(db.Integer, default=1)  # 1-5 scale
    years_experience = db.Column(db.Integer, default=0)
    verified = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(50))  # 'resume', 'manual', 'assessment'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('candidate_id', 'skill_id', name='unique_candidate_skill'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'skill_id': self.skill_id,
            'proficiency_level': self.proficiency_level,
            'years_experience': self.years_experience,
            'verified': self.verified,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class JobSkill(db.Model):
    __tablename__ = 'job_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    requirement_level = db.Column(db.String(20), default='preferred')  # 'required', 'preferred', 'nice-to-have'
    years_required = db.Column(db.Integer, default=0)
    weight = db.Column(db.Float, default=1.0)  # Weight for matching algorithm
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('job_id', 'skill_id', name='unique_job_skill'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'skill_id': self.skill_id,
            'requirement_level': self.requirement_level,
            'years_required': self.years_required,
            'weight': self.weight,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='direct')  # 'direct', 'system', 'notification'
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'subject': self.subject,
            'content': self.content,
            'message_type': self.message_type,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'is_read': self.is_read
        }

class Analytics(db.Model):
    __tablename__ = 'analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float)
    metric_data = db.Column(db.Text)  # JSON string for complex metrics
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    period = db.Column(db.String(20))  # 'daily', 'weekly', 'monthly'
    
    # Relationships
    user = db.relationship('User', backref='analytics')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_data': json.loads(self.metric_data) if self.metric_data else {},
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'period': self.period
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'application_status', 'new_job', 'message', 'system'
    action_url = db.Column(db.String(500))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'action_url': self.action_url,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }

