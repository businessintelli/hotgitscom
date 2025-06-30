# Hotgigs.com API Specification

**Version:** 1.0  
**Base URL:** `https://api.hotgigs.com/v1`  
**Authentication:** JWT Bearer Token

## Authentication Endpoints

### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "role": "candidate|recruiter",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Tech Corp" // Required for recruiters
}
```

**Response:**
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "role": "candidate",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 3600
}
```

### POST /auth/login
Authenticate user and obtain access tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### POST /auth/logout
Invalidate current session and tokens.

## User Management Endpoints

### GET /users/profile
Get current user profile information.

**Response:**
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "role": "candidate",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "linkedin_profile": "https://linkedin.com/in/johndoe",
    "current_title": "Software Engineer",
    "years_experience": 5,
    "skills_summary": "Python, React, Machine Learning",
    "education_summary": "BS Computer Science"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-12-30T08:15:00Z"
}
```

### PUT /users/profile
Update user profile information.

### DELETE /users/account
Delete user account and all associated data.

## Job Management Endpoints

### GET /jobs
Search and filter job listings.

**Query Parameters:**
- `q`: Search query
- `location`: Job location
- `salary_min`: Minimum salary
- `salary_max`: Maximum salary
- `experience_level`: Required experience level
- `skills`: Comma-separated list of skills
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 20)

**Response:**
```json
{
  "jobs": [
    {
      "job_id": 456,
      "title": "Senior Software Engineer",
      "company_name": "Tech Corp",
      "location": "San Francisco, CA",
      "salary_range": "$120,000 - $180,000",
      "description": "We are looking for a senior software engineer...",
      "requirements": "5+ years experience, Python, React",
      "posted_at": "2024-12-28T14:20:00Z",
      "deadline": "2025-01-28T23:59:59Z",
      "status": "active",
      "match_score": 85.5 // Only for authenticated candidates
    }
  ],
  "total_count": 150,
  "page": 1,
  "total_pages": 8
}
```

### GET /jobs/{job_id}
Get detailed information about a specific job.

### POST /jobs
Create a new job listing (Recruiters only).

**Request Body:**
```json
{
  "title": "Senior Software Engineer",
  "description": "We are looking for a senior software engineer...",
  "requirements": "5+ years experience, Python, React",
  "location": "San Francisco, CA",
  "salary_range": "$120,000 - $180,000",
  "company_name": "Tech Corp",
  "deadline": "2025-01-28T23:59:59Z",
  "skills": ["Python", "React", "Machine Learning"]
}
```

### PUT /jobs/{job_id}
Update job listing (Recruiters only).

### DELETE /jobs/{job_id}
Delete job listing (Recruiters only).

## Resume Management Endpoints

### POST /resumes/upload
Upload and parse resume file.

**Request:** Multipart form data with file upload

**Response:**
```json
{
  "resume_id": 789,
  "filename": "john_doe_resume.pdf",
  "upload_date": "2024-12-30T10:15:00Z",
  "parsing_status": "completed",
  "parsed_data": {
    "personal_info": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890"
    },
    "experience": [
      {
        "title": "Software Engineer",
        "company": "Previous Corp",
        "duration": "2020-2024",
        "description": "Developed web applications..."
      }
    ],
    "education": [
      {
        "degree": "Bachelor of Science",
        "field": "Computer Science",
        "institution": "University of Technology",
        "year": "2020"
      }
    ],
    "skills": ["Python", "JavaScript", "React", "Django"],
    "certifications": []
  },
  "ai_insights": {
    "strengths": ["Strong technical skills", "Relevant experience"],
    "suggestions": ["Add more quantifiable achievements"],
    "ats_score": 92
  }
}
```

### GET /resumes
Get list of uploaded resumes for current user.

### GET /resumes/{resume_id}
Get detailed resume information and parsed data.

### DELETE /resumes/{resume_id}
Delete resume file and associated data.

## Application Management Endpoints

### POST /applications
Submit job application.

**Request Body:**
```json
{
  "job_id": 456,
  "cover_letter": "I am excited to apply for this position...",
  "resume_id": 789
}
```

**Response:**
```json
{
  "application_id": 101112,
  "job_id": 456,
  "candidate_id": 123,
  "submission_date": "2024-12-30T11:30:00Z",
  "status": "submitted",
  "match_score": 87.3,
  "match_report": {
    "overall_score": 87.3,
    "skill_match": 92.0,
    "experience_match": 85.0,
    "education_match": 88.0,
    "strengths": [
      "Strong Python and React skills",
      "Relevant industry experience"
    ],
    "gaps": [
      "Limited machine learning experience"
    ],
    "recommendations": [
      "Highlight specific Python projects",
      "Consider ML certification"
    ]
  }
}
```

### GET /applications
Get list of applications for current user.

**Query Parameters:**
- `status`: Filter by application status
- `job_id`: Filter by specific job
- `page`: Page number
- `limit`: Results per page

### GET /applications/{application_id}
Get detailed application information.

### PUT /applications/{application_id}/status
Update application status (Recruiters only).

**Request Body:**
```json
{
  "status": "under_review|interview|rejected|hired",
  "notes": "Candidate shows strong technical skills"
}
```

## Job Matching Endpoints

### GET /matching/jobs
Get personalized job recommendations for candidate.

**Query Parameters:**
- `limit`: Number of recommendations (default: 10)
- `min_score`: Minimum match score (default: 70)

**Response:**
```json
{
  "recommendations": [
    {
      "job_id": 456,
      "title": "Senior Software Engineer",
      "company_name": "Tech Corp",
      "match_score": 92.5,
      "match_reasons": [
        "Strong skill alignment (95%)",
        "Experience level match (90%)",
        "Location preference match"
      ],
      "job_summary": {
        "location": "San Francisco, CA",
        "salary_range": "$120,000 - $180,000",
        "posted_at": "2024-12-28T14:20:00Z"
      }
    }
  ],
  "total_matches": 25
}
```

### GET /matching/candidates
Get candidate recommendations for job (Recruiters only).

**Query Parameters:**
- `job_id`: Job ID for matching
- `limit`: Number of recommendations
- `min_score`: Minimum match score

### POST /matching/calculate
Calculate match score between candidate and job.

**Request Body:**
```json
{
  "candidate_id": 123,
  "job_id": 456
}
```

## Analytics Endpoints

### GET /analytics/dashboard
Get dashboard analytics for current user.

**Response for Candidates:**
```json
{
  "profile_views": 45,
  "applications_sent": 12,
  "interview_invitations": 3,
  "avg_match_score": 78.5,
  "top_skills": ["Python", "React", "Machine Learning"],
  "skill_gaps": ["DevOps", "Cloud Computing"],
  "market_insights": {
    "avg_salary_range": "$110,000 - $160,000",
    "demand_trend": "increasing",
    "top_hiring_companies": ["Tech Corp", "Innovation Inc"]
  }
}
```

**Response for Recruiters:**
```json
{
  "active_jobs": 8,
  "total_applications": 156,
  "avg_time_to_hire": 21,
  "top_performing_jobs": [
    {
      "job_id": 456,
      "title": "Senior Software Engineer",
      "applications": 45,
      "avg_match_score": 82.3
    }
  ],
  "candidate_pipeline": {
    "applied": 156,
    "under_review": 23,
    "interview": 8,
    "hired": 3
  }
}
```

### GET /analytics/reports
Generate detailed analytics reports.

**Query Parameters:**
- `type`: Report type (applications, matches, performance)
- `period`: Time period (week, month, quarter, year)
- `format`: Response format (json, csv)

## AI Assistant Endpoints

### POST /ai/chat
Interact with AI assistant.

**Request Body:**
```json
{
  "message": "How can I improve my resume for software engineering roles?",
  "context": {
    "user_type": "candidate",
    "current_page": "profile"
  }
}
```

**Response:**
```json
{
  "response": "Based on your profile, here are some suggestions to improve your resume...",
  "suggestions": [
    {
      "type": "skill_addition",
      "title": "Add Cloud Computing Skills",
      "description": "Consider adding AWS or Azure certifications"
    }
  ],
  "follow_up_questions": [
    "Would you like specific course recommendations?",
    "Should I help you find relevant job openings?"
  ]
}
```

### GET /ai/suggestions
Get proactive AI suggestions for user.

### POST /ai/resume-optimization
Get AI-powered resume optimization suggestions.

## Notification Endpoints

### GET /notifications
Get user notifications.

**Response:**
```json
{
  "notifications": [
    {
      "id": 1001,
      "type": "application_status",
      "title": "Application Status Update",
      "message": "Your application for Senior Software Engineer has been reviewed",
      "created_at": "2024-12-30T09:15:00Z",
      "read": false,
      "action_url": "/applications/101112"
    }
  ],
  "unread_count": 3
}
```

### PUT /notifications/{notification_id}/read
Mark notification as read.

### POST /notifications/preferences
Update notification preferences.

## Error Responses

All endpoints return standardized error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": ["This field is required"],
      "password": ["Password must be at least 8 characters"]
    }
  },
  "timestamp": "2024-12-30T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Rate Limiting

- Authentication endpoints: 5 requests per minute
- Search endpoints: 100 requests per minute
- Upload endpoints: 10 requests per minute
- General API endpoints: 1000 requests per hour

## Pagination

List endpoints support pagination with the following parameters:
- `page`: Page number (starting from 1)
- `limit`: Items per page (max 100)

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_count": 150,
    "total_pages": 8,
    "has_next": true,
    "has_previous": false
  }
}
```

