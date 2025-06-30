# Hotgigs.com Technical Documentation

## 🏗️ System Architecture Overview

Hotgigs.com is a modern, full-stack web application built with a React frontend and Flask backend, designed for scalability, performance, and maintainability. The application leverages artificial intelligence for resume parsing, job matching, and career assistance.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Backend Documentation](#backend-documentation)
4. [Frontend Documentation](#frontend-documentation)
5. [Database Schema](#database-schema)
6. [API Documentation](#api-documentation)
7. [AI Services](#ai-services)
8. [Security Implementation](#security-implementation)
9. [Deployment Guide](#deployment-guide)
10. [Development Setup](#development-setup)
11. [Testing Strategy](#testing-strategy)
12. [Performance Optimization](#performance-optimization)
13. [Monitoring & Logging](#monitoring--logging)
14. [Troubleshooting](#troubleshooting)

## 🏛️ Architecture Overview

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │    Database     │
│   (React)       │◄──►│    (Flask)      │◄──►│  (PostgreSQL)   │
│   Port: 5173    │    │   Port: 5002    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Static Files  │    │   AI Services   │    │   File Storage  │
│   (Assets)      │    │   (NLP/ML)      │    │   (Resumes)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Architecture

#### Frontend (React)
- **Component-Based**: Modular React components for reusability
- **State Management**: Context API for global state
- **Routing**: React Router for client-side navigation
- **Styling**: Tailwind CSS for responsive design
- **Build Tool**: Vite for fast development and building

#### Backend (Flask)
- **RESTful API**: Clean API design with proper HTTP methods
- **Modular Structure**: Blueprints for route organization
- **ORM**: SQLAlchemy for database operations
- **Authentication**: JWT-based authentication system
- **File Processing**: Multi-format resume parsing capabilities

#### Database (PostgreSQL)
- **Relational Design**: Normalized schema with proper relationships
- **Indexing**: Optimized indexes for query performance
- **Constraints**: Data integrity through foreign keys and constraints
- **Scalability**: Designed for horizontal and vertical scaling

## 🛠️ Technology Stack

### Frontend Technologies
- **React 18.2.0**: Modern React with hooks and functional components
- **Vite 5.0.0**: Fast build tool and development server
- **React Router 6.8.0**: Client-side routing and navigation
- **Tailwind CSS 3.3.0**: Utility-first CSS framework
- **Lucide React**: Modern icon library
- **Recharts**: Data visualization and charting library

### Backend Technologies
- **Python 3.11**: Modern Python with type hints support
- **Flask 3.1.1**: Lightweight web framework
- **SQLAlchemy 2.0.41**: Modern ORM with async support
- **Flask-JWT-Extended**: JWT authentication implementation
- **Flask-CORS**: Cross-origin resource sharing
- **Flask-Limiter**: Rate limiting and API protection
- **Flask-Mail**: Email functionality

### AI/ML Technologies
- **spaCy 3.8.7**: Natural language processing library
- **scikit-learn 1.7.0**: Machine learning algorithms
- **PyPDF2**: PDF text extraction
- **python-docx**: Word document processing
- **Pillow**: Image processing for OCR
- **pytesseract**: Optical character recognition

### Development Tools
- **Git**: Version control system
- **npm/pnpm**: Package management
- **pip**: Python package management
- **ESLint**: JavaScript linting
- **Prettier**: Code formatting
- **pytest**: Python testing framework

## 🔧 Backend Documentation

### Project Structure

```
hotgigs-backend/
├── src/
│   ├── main.py                 # Application entry point
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # Database configuration
│   │   └── user.py            # User models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication routes
│   │   ├── user.py            # User management routes
│   │   ├── job.py             # Job-related routes
│   │   ├── application.py     # Application management
│   │   ├── resume.py          # Resume processing routes
│   │   ├── matching.py        # Job matching routes
│   │   └── analytics.py       # Analytics routes
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py    # Authentication logic
│       ├── enhanced_resume_parser.py  # Resume parsing
│       ├── spacy_resume_parser.py     # NLP parsing
│       └── job_matching_engine.py     # Matching algorithms
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables
└── README.md                 # Project documentation
```

### Core Components

#### Application Factory (main.py)
```python
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.database import db

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    JWTManager(app)
    
    # Register blueprints
    from src.routes import auth_bp, user_bp, job_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(job_bp, url_prefix='/api/jobs')
    
    return app
```

#### Database Models (models/database.py)
```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('candidate', 'recruiter', 'admin'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = db.relationship('Candidate', backref='user', uselist=False)
    recruiter = db.relationship('Recruiter', backref='user', uselist=False)
```

#### Authentication Service (services/auth_service.py)
```python
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt

class AuthService:
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def generate_token(user_id, role):
        additional_claims = {"role": role}
        return create_access_token(identity=user_id, additional_claims=additional_claims)
```

### API Routes

#### Authentication Routes (routes/auth.py)
```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validation
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    # Create user
    user = AuthService.create_user(data)
    token = AuthService.generate_token(user.id, user.role)
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'role': user.role
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = AuthService.authenticate_user(data.get('email'), data.get('password'))
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = AuthService.generate_token(user.id, user.role)
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'role': user.role
        }
    }), 200
```

#### Resume Processing Routes (routes/resume.py)
```python
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.enhanced_resume_parser import enhanced_resume_parser

resume_bp = Blueprint('resume', __name__)

@resume_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # Parse resume
    try:
        result = enhanced_resume_parser.parse_resume(file_path)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resume_bp.route('/providers', methods=['GET'])
def get_providers():
    providers = enhanced_resume_parser.get_providers()
    return jsonify(providers), 200
```

### Configuration Management

#### Environment Variables (.env)
```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/hotgigs
SQLALCHEMY_DATABASE_URI=postgresql://username:password@localhost:5432/hotgigs

# Security
SECRET_KEY=your-super-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-string-change-in-production

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=10485760  # 10MB

# AI Services
OPENAI_API_KEY=your-openai-api-key
OCR_SPACE_API_KEY=your-ocr-space-api-key

# Development
FLASK_ENV=development
FLASK_DEBUG=True
```

## ⚛️ Frontend Documentation

### Project Structure

```
hotgigs-frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── App.jsx                 # Main application component
│   ├── App.css                 # Global styles
│   ├── main.jsx               # Application entry point
│   ├── components/
│   │   ├── Navbar.jsx         # Navigation component
│   │   ├── Footer.jsx         # Footer component
│   │   ├── HomePage.jsx       # Landing page
│   │   ├── auth/
│   │   │   ├── LoginPage.jsx  # Login form
│   │   │   └── RegisterPage.jsx # Registration form
│   │   ├── dashboard/
│   │   │   └── DashboardPage.jsx # User dashboard
│   │   ├── jobs/
│   │   │   ├── JobsPage.jsx   # Job listings
│   │   │   └── JobDetailsPage.jsx # Job details
│   │   ├── profile/
│   │   │   └── ProfilePage.jsx # User profile
│   │   ├── matching/
│   │   │   └── MatchingPage.jsx # AI matching
│   │   ├── analytics/
│   │   │   └── AnalyticsPage.jsx # Analytics dashboard
│   │   ├── chat/
│   │   │   ├── ChatInterface.jsx # Chat component
│   │   │   └── ChatPage.jsx   # Chat page
│   │   └── ui/
│   │       ├── Button.jsx     # Reusable button
│   │       ├── Card.jsx       # Card component
│   │       ├── Badge.jsx      # Badge component
│   │       └── LoadingSpinner.jsx # Loading indicator
├── package.json               # Dependencies and scripts
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # Tailwind CSS configuration
└── README.md                 # Project documentation
```

### Core Components

#### Main Application (App.jsx)
```jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HomePage from './components/HomePage';
import LoginPage from './components/auth/LoginPage';
import DashboardPage from './components/dashboard/DashboardPage';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              {/* Additional routes */}
            </Routes>
          </main>
          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
```

#### Authentication Context
```jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      // Verify token and set user
      verifyToken(token);
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      const data = await response.json();
      if (response.ok) {
        localStorage.setItem('token', data.token);
        setUser(data.user);
        return { success: true };
      }
      return { success: false, error: data.error };
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value = {
    user,
    login,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
```

#### Reusable UI Components
```jsx
// Button Component (components/ui/Button.jsx)
import React from 'react';

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  disabled = false, 
  onClick, 
  className = '',
  ...props 
}) => {
  const baseClasses = 'font-medium rounded-lg transition-colors focus:outline-none focus:ring-2';
  
  const variants = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    outline: 'border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500'
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };
  
  const classes = `${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`;
  
  return (
    <button
      className={classes}
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
```

### State Management

#### Global State with Context API
```jsx
// contexts/AppContext.jsx
import React, { createContext, useContext, useReducer } from 'react';

const AppContext = createContext();

const initialState = {
  jobs: [],
  applications: [],
  analytics: {},
  notifications: [],
  loading: false,
  error: null
};

const appReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_JOBS':
      return { ...state, jobs: action.payload, loading: false };
    case 'ADD_APPLICATION':
      return { ...state, applications: [...state.applications, action.payload] };
    default:
      return state;
  }
};

export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  const actions = {
    setLoading: (loading) => dispatch({ type: 'SET_LOADING', payload: loading }),
    setError: (error) => dispatch({ type: 'SET_ERROR', payload: error }),
    setJobs: (jobs) => dispatch({ type: 'SET_JOBS', payload: jobs }),
    addApplication: (application) => dispatch({ type: 'ADD_APPLICATION', payload: application })
  };
  
  return (
    <AppContext.Provider value={{ state, actions }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
```

### API Integration

#### API Service Layer
```jsx
// services/api.js
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5002';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem('token');
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers
      },
      ...options
    };
    
    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'API request failed');
      }
      
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }
  
  // Authentication
  async login(email, password) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  }
  
  async register(userData) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }
  
  // Jobs
  async getJobs(filters = {}) {
    const queryString = new URLSearchParams(filters).toString();
    return this.request(`/api/jobs?${queryString}`);
  }
  
  async getJobById(id) {
    return this.request(`/api/jobs/${id}`);
  }
  
  // Resume
  async uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    return this.request('/api/resume/upload', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
      body: formData
    });
  }
}

export default new ApiService();
```

## 🗄️ Database Schema

### Entity Relationship Diagram

```
Users (1) ──── (1) Candidates
  │                   │
  │                   │ (1)
  │                   │
  │                   ▼ (*)
  │              CandidateSkills ──── (*) Skills
  │                   │
  │                   │ (1)
  │                   │
  │                   ▼ (*)
  │               Resumes
  │                   │
  │                   │ (1)
  │                   │
  │                   ▼ (*)
  │              Applications ──── (*) Jobs ──── (1) Recruiters ──── (1) Users
  │                                   │
  │                                   │ (*)
  │                                   │
  │                                   ▼ (*)
  │                              JobSkills ──── (*) Skills
  │
  └── (1) Recruiters
```

### Table Definitions

#### Users Table
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    location VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE user_role AS ENUM ('candidate', 'recruiter', 'admin');
```

#### Candidates Table
```sql
CREATE TABLE candidates (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    professional_summary TEXT,
    experience_level experience_level_enum,
    current_job_title VARCHAR(255),
    current_company VARCHAR(255),
    desired_salary_min INTEGER,
    desired_salary_max INTEGER,
    willing_to_relocate BOOLEAN DEFAULT FALSE,
    remote_work_preference remote_preference_enum,
    availability_date DATE,
    linkedin_url VARCHAR(500),
    github_url VARCHAR(500),
    portfolio_url VARCHAR(500),
    ai_context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE experience_level_enum AS ENUM ('entry', 'junior', 'mid', 'senior', 'lead', 'executive');
CREATE TYPE remote_preference_enum AS ENUM ('remote_only', 'hybrid', 'onsite_only', 'flexible');
```

#### Jobs Table
```sql
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id VARCHAR(36) NOT NULL REFERENCES recruiters(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT,
    location VARCHAR(255),
    remote_work_option remote_preference_enum,
    employment_type employment_type_enum,
    experience_level experience_level_enum,
    salary_min INTEGER,
    salary_max INTEGER,
    benefits TEXT,
    application_deadline DATE,
    is_active BOOLEAN DEFAULT TRUE,
    ai_context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE employment_type_enum AS ENUM ('full_time', 'part_time', 'contract', 'freelance', 'internship');
```

#### Skills Table
```sql
CREATE TABLE skills (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    category skill_category_enum,
    description TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TYPE skill_category_enum AS ENUM (
    'programming', 'web_development', 'mobile_development', 'data_science',
    'databases', 'cloud_technologies', 'design', 'project_management',
    'soft_skills', 'languages', 'certifications'
);
```

#### Applications Table
```sql
CREATE TABLE applications (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id VARCHAR(36) NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id VARCHAR(36) NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    resume_id VARCHAR(36) REFERENCES resumes(id),
    cover_letter TEXT,
    status application_status_enum DEFAULT 'pending',
    match_score DECIMAL(5,2),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(candidate_id, job_id)
);

CREATE TYPE application_status_enum AS ENUM (
    'pending', 'reviewed', 'shortlisted', 'interview_scheduled',
    'interviewed', 'offered', 'accepted', 'rejected', 'withdrawn'
);
```

### Indexes for Performance

```sql
-- User authentication
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Job search optimization
CREATE INDEX idx_jobs_active ON jobs(is_active);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_experience_level ON jobs(experience_level);
CREATE INDEX idx_jobs_employment_type ON jobs(employment_type);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

-- Application tracking
CREATE INDEX idx_applications_candidate ON applications(candidate_id);
CREATE INDEX idx_applications_job ON applications(job_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_applied_at ON applications(applied_at DESC);

-- Skills matching
CREATE INDEX idx_candidate_skills_candidate ON candidate_skills(candidate_id);
CREATE INDEX idx_candidate_skills_skill ON candidate_skills(skill_id);
CREATE INDEX idx_job_skills_job ON job_skills(job_id);
CREATE INDEX idx_job_skills_skill ON job_skills(skill_id);

-- Full-text search
CREATE INDEX idx_jobs_title_description ON jobs USING gin(to_tsvector('english', title || ' ' || description));
CREATE INDEX idx_candidates_summary ON candidates USING gin(to_tsvector('english', professional_summary));
```

## 📡 API Documentation

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "role": "candidate",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (201):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "role": "candidate",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

#### POST /api/auth/login
Authenticate user and receive access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "role": "candidate"
  }
}
```

### Job Management Endpoints

#### GET /api/jobs
Retrieve job listings with optional filtering.

**Query Parameters:**
- `title` (string): Filter by job title
- `location` (string): Filter by location
- `experience_level` (string): Filter by experience level
- `employment_type` (string): Filter by employment type
- `remote_work` (boolean): Filter for remote work options
- `page` (integer): Page number for pagination
- `limit` (integer): Number of results per page

**Response (200):**
```json
{
  "jobs": [
    {
      "id": "job-uuid",
      "title": "Senior Software Engineer",
      "company": "TechCorp Inc.",
      "location": "San Francisco, CA",
      "employment_type": "full_time",
      "experience_level": "senior",
      "salary_min": 120000,
      "salary_max": 180000,
      "remote_work_option": "hybrid",
      "created_at": "2025-06-30T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

#### POST /api/jobs
Create a new job posting (Recruiter only).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "title": "Senior Software Engineer",
  "company": "TechCorp Inc.",
  "description": "We are looking for an experienced software engineer...",
  "requirements": "5+ years of experience with Python, React...",
  "location": "San Francisco, CA",
  "employment_type": "full_time",
  "experience_level": "senior",
  "salary_min": 120000,
  "salary_max": 180000,
  "remote_work_option": "hybrid"
}
```

### Resume Processing Endpoints

#### POST /api/resume/upload
Upload and parse a resume file.

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <resume_file> (PDF, DOCX, TXT, or image)
provider: "spacy_nlp" (optional, defaults to best available)
```

**Response (200):**
```json
{
  "personal_info": {
    "full_name": "John Doe",
    "first_name": "John",
    "last_name": "Doe"
  },
  "contact_info": {
    "email": "john.doe@email.com",
    "phone": "+1-555-123-4567",
    "linkedin": "linkedin.com/in/johndoe",
    "github": "github.com/johndoe"
  },
  "skills": [
    {
      "skill": "Python",
      "category": "programming",
      "proficiency_level": "advanced",
      "source": "spacy_nlp"
    }
  ],
  "experience": [
    {
      "job_title": "Software Engineer",
      "company": "TechCorp",
      "duration": "2020-2023",
      "description": "Developed web applications..."
    }
  ],
  "education": [
    {
      "degree": "Bachelor of Science",
      "field_of_study": "Computer Science",
      "institution": "University of Technology",
      "year": "2020"
    }
  ],
  "confidence_score": 0.95,
  "completeness_score": 0.87,
  "provider": "spacy_nlp"
}
```

#### GET /api/resume/providers
Get information about available resume parsing providers.

**Response (200):**
```json
{
  "spacy_nlp": {
    "name": "spaCy NLP Parser",
    "description": "Advanced NLP-based parsing with high accuracy",
    "features": ["Named Entity Recognition", "Pattern Matching"],
    "accuracy": "95%",
    "speed": "Fast (2-3 seconds)",
    "available": true
  },
  "text_extraction": {
    "name": "Text Extraction Parser",
    "description": "Fast basic text extraction and pattern matching",
    "features": ["Basic Pattern Matching", "Contact Information"],
    "accuracy": "75%",
    "speed": "Very Fast (1-2 seconds)",
    "available": true
  }
}
```

### Job Matching Endpoints

#### GET /api/matching/candidates/{candidate_id}
Get job matches for a specific candidate.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
- `limit` (integer): Number of matches to return (default: 20)
- `min_score` (float): Minimum match score (0.0-1.0)

**Response (200):**
```json
{
  "matches": [
    {
      "job": {
        "id": "job-uuid",
        "title": "Senior Python Developer",
        "company": "TechCorp Inc.",
        "location": "Remote"
      },
      "match_score": 0.92,
      "match_factors": {
        "skills_match": 0.95,
        "experience_match": 0.88,
        "location_match": 1.0,
        "salary_match": 0.90
      },
      "missing_skills": ["Docker", "Kubernetes"],
      "matching_skills": ["Python", "React", "PostgreSQL"]
    }
  ],
  "total_matches": 45,
  "candidate_profile_completeness": 0.87
}
```

### Analytics Endpoints

#### GET /api/analytics/candidate/{candidate_id}
Get analytics data for a candidate.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200):**
```json
{
  "overview": {
    "applications_sent": 12,
    "profile_views": 48,
    "match_score_avg": 0.85,
    "response_rate": 0.23
  },
  "timeline_data": [
    {
      "date": "2025-06-01",
      "applications": 2,
      "responses": 1,
      "interviews": 0
    }
  ],
  "industry_distribution": {
    "technology": 0.45,
    "finance": 0.25,
    "healthcare": 0.15,
    "education": 0.10,
    "other": 0.05
  },
  "skills_demand": [
    {
      "skill": "Python",
      "demand_score": 0.95,
      "job_count": 234
    }
  ]
}
```

## 🤖 AI Services

### Resume Parsing Service

#### Architecture
```python
class EnhancedResumeParsingService:
    def __init__(self):
        self.providers = {
            'spacy_nlp': SpacyResumeParser(),
            'text_extraction': TextExtractionParser(),
            'ocr_space': OCRSpaceParser(),
            'local_ocr': TesseractParser()
        }
        self.default_provider = 'spacy_nlp'
    
    def parse_resume(self, file_path, provider=None):
        provider = provider or self.default_provider
        
        try:
            parser = self.providers[provider]
            result = parser.parse(file_path)
            return self.enhance_result(result)
        except Exception as e:
            # Fallback to text extraction
            return self.providers['text_extraction'].parse(file_path)
```

#### spaCy NLP Parser
```python
import spacy
from spacy.matcher import Matcher

class SpacyResumeParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = Matcher(self.nlp.vocab)
        self.setup_patterns()
    
    def setup_patterns(self):
        # Email pattern
        email_pattern = [{"LIKE_EMAIL": True}]
        self.matcher.add("EMAIL", [email_pattern])
        
        # Phone pattern
        phone_pattern = [{"TEXT": {"REGEX": r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"}}]
        self.matcher.add("PHONE", [phone_pattern])
        
        # Skills patterns
        skills_pattern = [{"LOWER": {"IN": self.skills_list}}]
        self.matcher.add("SKILLS", [skills_pattern])
    
    def parse(self, file_path):
        text = self.extract_text(file_path)
        doc = self.nlp(text)
        
        return {
            'personal_info': self.extract_personal_info(doc),
            'contact_info': self.extract_contact_info(doc),
            'skills': self.extract_skills(doc),
            'experience': self.extract_experience(doc),
            'education': self.extract_education(doc),
            'confidence_score': self.calculate_confidence(doc)
        }
```

### Job Matching Engine

#### Semantic Matching Algorithm
```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class JobMatchingEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.skill_weights = {
            'programming': 0.3,
            'web_development': 0.25,
            'databases': 0.2,
            'cloud_technologies': 0.15,
            'soft_skills': 0.1
        }
    
    def calculate_match_score(self, candidate_profile, job_description):
        # Text similarity
        text_similarity = self.calculate_text_similarity(
            candidate_profile['summary'], 
            job_description['description']
        )
        
        # Skills matching
        skills_match = self.calculate_skills_match(
            candidate_profile['skills'],
            job_description['required_skills']
        )
        
        # Experience matching
        experience_match = self.calculate_experience_match(
            candidate_profile['experience_level'],
            job_description['experience_level']
        )
        
        # Location matching
        location_match = self.calculate_location_match(
            candidate_profile['location'],
            job_description['location'],
            job_description['remote_work_option']
        )
        
        # Weighted final score
        final_score = (
            text_similarity * 0.3 +
            skills_match * 0.4 +
            experience_match * 0.2 +
            location_match * 0.1
        )
        
        return {
            'overall_score': final_score,
            'text_similarity': text_similarity,
            'skills_match': skills_match,
            'experience_match': experience_match,
            'location_match': location_match
        }
    
    def calculate_skills_match(self, candidate_skills, required_skills):
        candidate_skill_names = {skill['skill'].lower() for skill in candidate_skills}
        required_skill_names = {skill.lower() for skill in required_skills}
        
        if not required_skill_names:
            return 1.0
        
        matched_skills = candidate_skill_names.intersection(required_skill_names)
        match_ratio = len(matched_skills) / len(required_skill_names)
        
        # Apply skill category weights
        weighted_score = 0
        total_weight = 0
        
        for skill in matched_skills:
            category = self.get_skill_category(skill)
            weight = self.skill_weights.get(category, 0.1)
            weighted_score += weight
            total_weight += weight
        
        return min(weighted_score / max(total_weight, 0.1), 1.0)
```

### AI Career Assistant

#### Conversation Engine
```python
class AICareerAssistant:
    def __init__(self):
        self.conversation_history = {}
        self.response_templates = {
            'resume_optimization': self.get_resume_advice,
            'job_search': self.get_job_search_advice,
            'interview_prep': self.get_interview_advice,
            'career_planning': self.get_career_advice
        }
    
    def process_message(self, user_id, message, context=None):
        intent = self.classify_intent(message)
        user_profile = self.get_user_profile(user_id)
        
        response = self.generate_response(intent, message, user_profile, context)
        
        # Store conversation history
        self.store_conversation(user_id, message, response)
        
        return {
            'response': response,
            'suggestions': self.get_contextual_suggestions(intent, user_profile),
            'intent': intent
        }
    
    def classify_intent(self, message):
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['resume', 'cv', 'optimize']):
            return 'resume_optimization'
        elif any(word in message_lower for word in ['job', 'search', 'find', 'opportunity']):
            return 'job_search'
        elif any(word in message_lower for word in ['interview', 'prepare', 'questions']):
            return 'interview_prep'
        elif any(word in message_lower for word in ['career', 'growth', 'plan', 'future']):
            return 'career_planning'
        else:
            return 'general'
    
    def generate_response(self, intent, message, user_profile, context):
        if intent in self.response_templates:
            return self.response_templates[intent](message, user_profile, context)
        else:
            return self.get_general_response(message, user_profile)
```

## 🔒 Security Implementation

### Authentication & Authorization

#### JWT Token Management
```python
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta

class SecurityManager:
    def __init__(self, app):
        self.jwt = JWTManager(app)
        self.token_blacklist = set()
        
        # Configure JWT
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
        
        # Register JWT callbacks
        self.setup_jwt_callbacks()
    
    def setup_jwt_callbacks(self):
        @self.jwt.token_in_blocklist_loader
        def check_if_token_revoked(jwt_header, jwt_payload):
            return jwt_payload['jti'] in self.token_blacklist
        
        @self.jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            return jsonify({'error': 'Token has expired'}), 401
        
        @self.jwt.invalid_token_loader
        def invalid_token_callback(error):
            return jsonify({'error': 'Invalid token'}), 401
```

#### Role-Based Access Control
```python
from functools import wraps
from flask_jwt_extended import get_jwt

def require_role(required_role):
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')
            
            if user_role != required_role and user_role != 'admin':
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@app.route('/api/jobs', methods=['POST'])
@require_role('recruiter')
def create_job():
    # Only recruiters can create jobs
    pass
```

### Input Validation & Sanitization

#### Request Validation
```python
from marshmallow import Schema, fields, validate, ValidationError

class UserRegistrationSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    role = fields.Str(required=True, validate=validate.OneOf(['candidate', 'recruiter']))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))

def validate_request(schema_class):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            schema = schema_class()
            try:
                data = schema.load(request.get_json())
                request.validated_data = data
                return f(*args, **kwargs)
            except ValidationError as err:
                return jsonify({'errors': err.messages}), 400
        return decorated_function
    return decorator

# Usage
@app.route('/api/auth/register', methods=['POST'])
@validate_request(UserRegistrationSchema)
def register():
    data = request.validated_data
    # Process validated data
```

### File Upload Security

#### Secure File Handling
```python
import os
import uuid
from werkzeug.utils import secure_filename

class FileUploadManager:
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def is_allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def save_file(self, file):
        if not file or file.filename == '':
            raise ValueError('No file provided')
        
        if not self.is_allowed_file(file.filename):
            raise ValueError('File type not allowed')
        
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(self.upload_folder, unique_filename)
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError('File too large')
        
        file.save(file_path)
        return file_path, unique_filename
```

### Rate Limiting

#### API Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

# Apply rate limits to specific endpoints
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Login logic with rate limiting
    pass

@app.route('/api/resume/upload', methods=['POST'])
@limiter.limit("10 per hour")
@jwt_required()
def upload_resume():
    # Resume upload with rate limiting
    pass
```

## 🚀 Deployment Guide

### Production Environment Setup

#### Docker Configuration

**Dockerfile (Backend)**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "src.main:app"]
```

**Dockerfile (Frontend)**
```dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  database:
    image: postgres:15
    environment:
      POSTGRES_DB: hotgigs
      POSTGRES_USER: hotgigs_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./hotgigs-backend
    environment:
      DATABASE_URL: postgresql://hotgigs_user:secure_password@database:5432/hotgigs
      SECRET_KEY: your-production-secret-key
      JWT_SECRET_KEY: your-jwt-secret-key
    depends_on:
      - database
    ports:
      - "5000:5000"
    volumes:
      - ./uploads:/app/uploads

  frontend:
    build: ./hotgigs-frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### Cloud Deployment (AWS)

#### Infrastructure as Code (Terraform)
```hcl
# main.tf
provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "hotgigs-vpc"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "hotgigs-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# RDS Database
resource "aws_db_instance" "main" {
  identifier     = "hotgigs-db"
  engine         = "postgres"
  engine_version = "15.3"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true
  
  db_name  = "hotgigs"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = false
  final_snapshot_identifier = "hotgigs-db-final-snapshot"
  
  tags = {
    Name = "hotgigs-database"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "hotgigs-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name = "hotgigs-alb"
  }
}
```

#### ECS Task Definitions
```json
{
  "family": "hotgigs-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "hotgigs-backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/hotgigs-backend:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://username:password@rds-endpoint:5432/hotgigs"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:hotgigs/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/hotgigs-backend",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Environment Configuration

#### Production Environment Variables
```bash
# Database
DATABASE_URL=postgresql://username:password@host:5432/hotgigs
SQLALCHEMY_DATABASE_URI=postgresql://username:password@host:5432/hotgigs

# Security
SECRET_KEY=your-super-secure-secret-key-for-production
JWT_SECRET_KEY=your-jwt-secret-key-for-production

# Email Configuration
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key

# File Storage
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=10485760

# AI Services
OPENAI_API_KEY=your-openai-api-key
OCR_SPACE_API_KEY=your-ocr-space-api-key

# Monitoring
SENTRY_DSN=your-sentry-dsn
NEW_RELIC_LICENSE_KEY=your-new-relic-key

# Application
FLASK_ENV=production
FLASK_DEBUG=False
```

### SSL/TLS Configuration

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name hotgigs.com www.hotgigs.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name hotgigs.com www.hotgigs.com;

    ssl_certificate /etc/ssl/certs/hotgigs.com.crt;
    ssl_certificate_key /etc/ssl/private/hotgigs.com.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 Development Setup

### Local Development Environment

#### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Git

#### Backend Setup
```bash
# Clone repository
git clone https://github.com/your-org/hotgigs.git
cd hotgigs/hotgigs-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run development server
python src/main.py
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd ../hotgigs-frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

#### Database Setup
```sql
-- Create database
CREATE DATABASE hotgigs;
CREATE USER hotgigs_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE hotgigs TO hotgigs_user;

-- Connect to database
\c hotgigs

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

### Development Tools

#### Code Quality Tools
```bash
# Backend linting and formatting
pip install black flake8 isort mypy
black src/
flake8 src/
isort src/
mypy src/

# Frontend linting and formatting
npm install -D eslint prettier
npm run lint
npm run format
```

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.44.0
    hooks:
      - id: eslint
        files: \.(js|jsx|ts|tsx)$
        types: [file]
```

## 🧪 Testing Strategy

### Backend Testing

#### Unit Tests
```python
# tests/test_auth_service.py
import pytest
from src.services.auth_service import AuthService
from src.models.database import User, db

class TestAuthService:
    def test_hash_password(self):
        password = "testpassword123"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert AuthService.verify_password(password, hashed)
    
    def test_verify_password_invalid(self):
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = AuthService.hash_password(password)
        
        assert not AuthService.verify_password(wrong_password, hashed)
    
    @pytest.fixture
    def sample_user(self):
        return {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'role': 'candidate',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_create_user(self, sample_user):
        user = AuthService.create_user(sample_user)
        
        assert user.email == sample_user['email']
        assert user.role == sample_user['role']
        assert user.first_name == sample_user['first_name']
        assert AuthService.verify_password(sample_user['password'], user.password_hash)
```

#### Integration Tests
```python
# tests/test_api_endpoints.py
import pytest
import json
from src.main import create_app
from src.models.database import db

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

class TestAuthEndpoints:
    def test_register_success(self, client):
        response = client.post('/api/auth/register', 
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'testpassword123',
                'role': 'candidate',
                'first_name': 'Test',
                'last_name': 'User'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'token' in data
        assert data['user']['email'] == 'test@example.com'
    
    def test_login_success(self, client):
        # First register a user
        client.post('/api/auth/register', 
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'testpassword123',
                'role': 'candidate'
            }),
            content_type='application/json'
        )
        
        # Then login
        response = client.post('/api/auth/login',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'testpassword123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data
```

### Frontend Testing

#### Component Tests
```jsx
// src/components/__tests__/Button.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Button from '../ui/Button';

describe('Button Component', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies correct variant classes', () => {
    render(<Button variant="secondary">Secondary Button</Button>);
    const button = screen.getByText('Secondary Button');
    expect(button).toHaveClass('bg-gray-200');
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled Button</Button>);
    const button = screen.getByText('Disabled Button');
    expect(button).toBeDisabled();
  });
});
```

#### Integration Tests
```jsx
// src/components/__tests__/LoginPage.test.jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import LoginPage from '../auth/LoginPage';

const renderWithProviders = (component) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        {component}
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('LoginPage', () => {
  it('renders login form', () => {
    renderWithProviders(<LoginPage />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows validation errors for empty fields', async () => {
    renderWithProviders(<LoginPage />);
    
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });
});
```

### Test Configuration

#### Jest Configuration (Frontend)
```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    globals: true,
  },
});
```

#### Pytest Configuration (Backend)
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=src
    --cov-report=html
    --cov-report=term-missing
```

## 📊 Performance Optimization

### Backend Optimization

#### Database Query Optimization
```python
# Efficient queries with proper joins and indexing
def get_job_matches_optimized(candidate_id, limit=20):
    return db.session.query(Job)\
        .join(JobSkill)\
        .join(Skill)\
        .join(CandidateSkill, CandidateSkill.skill_id == Skill.id)\
        .filter(CandidateSkill.candidate_id == candidate_id)\
        .filter(Job.is_active == True)\
        .options(
            joinedload(Job.recruiter),
            joinedload(Job.skills)
        )\
        .limit(limit)\
        .all()

# Use database-level aggregations
def get_candidate_stats(candidate_id):
    stats = db.session.query(
        func.count(Application.id).label('total_applications'),
        func.avg(Application.match_score).label('avg_match_score'),
        func.count(case([(Application.status == 'interviewed', 1)])).label('interviews')
    ).filter(Application.candidate_id == candidate_id).first()
    
    return {
        'total_applications': stats.total_applications or 0,
        'avg_match_score': float(stats.avg_match_score or 0),
        'interviews': stats.interviews or 0
    }
```

#### Caching Strategy
```python
from flask_caching import Cache
import redis

# Configure Redis cache
cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Cache expensive operations
@cache.memoize(timeout=3600)
def get_job_recommendations(candidate_id):
    # Expensive ML computation
    return job_matching_engine.get_recommendations(candidate_id)

@cache.memoize(timeout=1800)
def get_industry_analytics():
    # Expensive aggregation query
    return analytics_service.get_industry_trends()

# Cache with dynamic keys
def get_cached_user_profile(user_id):
    cache_key = f"user_profile_{user_id}"
    profile = cache.get(cache_key)
    
    if profile is None:
        profile = UserService.get_complete_profile(user_id)
        cache.set(cache_key, profile, timeout=1800)
    
    return profile
```

#### Asynchronous Processing
```python
from celery import Celery
import asyncio

# Configure Celery for background tasks
celery = Celery('hotgigs', broker='redis://localhost:6379/1')

@celery.task
def process_resume_async(file_path, user_id):
    """Process resume in background"""
    try:
        result = enhanced_resume_parser.parse_resume(file_path)
        
        # Update user profile with parsed data
        UserService.update_profile_from_resume(user_id, result)
        
        # Send notification to user
        NotificationService.send_resume_processed_notification(user_id)
        
        return result
    except Exception as e:
        # Handle errors and notify user
        NotificationService.send_error_notification(user_id, str(e))
        raise

@celery.task
def update_job_matches_async(candidate_id):
    """Update job matches in background"""
    matches = job_matching_engine.calculate_matches(candidate_id)
    MatchingService.update_candidate_matches(candidate_id, matches)
    return len(matches)
```

### Frontend Optimization

#### Code Splitting and Lazy Loading
```jsx
// Lazy load components
import { lazy, Suspense } from 'react';
import LoadingSpinner from './components/ui/LoadingSpinner';

const DashboardPage = lazy(() => import('./components/dashboard/DashboardPage'));
const AnalyticsPage = lazy(() => import('./components/analytics/AnalyticsPage'));
const ChatPage = lazy(() => import('./components/chat/ChatPage'));

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route 
          path="/dashboard" 
          element={
            <Suspense fallback={<LoadingSpinner />}>
              <DashboardPage />
            </Suspense>
          } 
        />
        <Route 
          path="/analytics" 
          element={
            <Suspense fallback={<LoadingSpinner />}>
              <AnalyticsPage />
            </Suspense>
          } 
        />
      </Routes>
    </Router>
  );
}
```

#### Performance Monitoring
```jsx
// Performance monitoring hook
import { useEffect } from 'react';

const usePerformanceMonitoring = (componentName) => {
  useEffect(() => {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // Log performance metrics
      if (renderTime > 100) {
        console.warn(`Slow render detected in ${componentName}: ${renderTime}ms`);
      }
      
      // Send to analytics service
      analytics.track('component_render_time', {
        component: componentName,
        duration: renderTime
      });
    };
  }, [componentName]);
};

// Usage in components
const DashboardPage = () => {
  usePerformanceMonitoring('DashboardPage');
  
  return (
    <div>
      {/* Component content */}
    </div>
  );
};
```

#### Image Optimization
```jsx
// Optimized image component
import { useState, useEffect } from 'react';

const OptimizedImage = ({ src, alt, className, placeholder }) => {
  const [imageSrc, setImageSrc] = useState(placeholder);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      setImageSrc(src);
      setIsLoaded(true);
    };
    img.src = src;
  }, [src]);

  return (
    <img
      src={imageSrc}
      alt={alt}
      className={`${className} ${isLoaded ? 'opacity-100' : 'opacity-50'} transition-opacity`}
      loading="lazy"
    />
  );
};
```

## 📈 Monitoring & Logging

### Application Monitoring

#### Health Check Endpoints
```python
from flask import Blueprint, jsonify
import psutil
import time

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Basic health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0'
    })

@health_bp.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with system metrics"""
    try:
        # Database connectivity
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'timestamp': time.time(),
        'checks': {
            'database': db_status,
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': (disk.used / disk.total) * 100
            }
        }
    })
```

#### Structured Logging
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def log_event(self, event_type, **kwargs):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            **kwargs
        }
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, error, **context):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'error',
            'error': str(error),
            'error_type': type(error).__name__,
            **context
        }
        self.logger.error(json.dumps(log_data))

# Usage
logger = StructuredLogger('hotgigs.api')

@app.route('/api/jobs/<job_id>/apply', methods=['POST'])
@jwt_required()
def apply_to_job(job_id):
    user_id = get_jwt_identity()
    
    try:
        application = ApplicationService.create_application(user_id, job_id)
        
        logger.log_event(
            'job_application_created',
            user_id=user_id,
            job_id=job_id,
            application_id=application.id
        )
        
        return jsonify(application.to_dict()), 201
        
    except Exception as e:
        logger.log_error(
            e,
            user_id=user_id,
            job_id=job_id,
            endpoint='/api/jobs/apply'
        )
        raise
```

### Error Tracking

#### Sentry Integration
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[
        FlaskIntegration(transaction_style='endpoint'),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,
    environment="production"
)

# Custom error context
@app.before_request
def add_sentry_context():
    if current_user.is_authenticated:
        sentry_sdk.set_user({
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role
        })
```

### Performance Monitoring

#### Custom Metrics
```python
import time
from functools import wraps

class MetricsCollector:
    def __init__(self):
        self.metrics = {}
    
    def time_function(self, func_name):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                start_time = time.time()
                try:
                    result = f(*args, **kwargs)
                    status = 'success'
                    return result
                except Exception as e:
                    status = 'error'
                    raise
                finally:
                    duration = time.time() - start_time
                    self.record_metric(func_name, duration, status)
            return decorated_function
        return decorator
    
    def record_metric(self, name, duration, status):
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            'duration': duration,
            'status': status,
            'timestamp': time.time()
        })

metrics = MetricsCollector()

@metrics.time_function('resume_parsing')
def parse_resume(file_path):
    return enhanced_resume_parser.parse_resume(file_path)
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### Database Connection Issues
```python
# Connection pool configuration
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Connection retry logic
import time
from sqlalchemy.exc import OperationalError

def execute_with_retry(query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return db.session.execute(query)
        except OperationalError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

#### Memory Management
```python
# Large file processing with streaming
def process_large_resume(file_path):
    chunk_size = 1024 * 1024  # 1MB chunks
    
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            
            # Process chunk
            yield process_chunk(chunk)

# Memory monitoring
import psutil
import gc

def monitor_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    
    if memory_info.rss > 500 * 1024 * 1024:  # 500MB
        logger.warning(f"High memory usage: {memory_info.rss / 1024 / 1024:.2f}MB")
        gc.collect()  # Force garbage collection
```

#### API Rate Limiting Issues
```python
# Graceful rate limit handling
from flask import request, jsonify
import time

def handle_rate_limit_exceeded():
    return jsonify({
        'error': 'Rate limit exceeded',
        'retry_after': 60,
        'message': 'Please wait before making another request'
    }), 429

@app.errorhandler(429)
def rate_limit_handler(e):
    return handle_rate_limit_exceeded()

# Client-side retry logic
async function apiRequestWithRetry(url, options, maxRetries = 3) {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const response = await fetch(url, options);
            
            if (response.status === 429) {
                const retryAfter = response.headers.get('Retry-After') || 60;
                await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
                continue;
            }
            
            return response;
        } catch (error) {
            if (attempt === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
        }
    }
}
```

---

*This technical documentation is maintained alongside the codebase and updated with each release. For the most current information, please refer to the inline code documentation and API specifications.*

**Last Updated**: June 30, 2025  
**Version**: 1.0  
**Maintainer**: Development Team  
**Contact**: tech@hotgigs.com

