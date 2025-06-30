# Hotgigs.com - AI-Powered Job Portal Analysis

## Key Requirements Summary

### Vision
- Create a "futuristic" and "simple" job portal similar to Jobright.ai
- AI-powered job search copilot experience
- Streamlined, data-driven talent acquisition ecosystem

### Core Features Required

#### 1. User Management & Authentication
- Distinct user roles: Recruiters and Candidates
- Role-Based Access Control (RBAC)
- Secure authentication with GDPR compliance

#### 2. Database Design
- Hybrid approach: Relational (PostgreSQL) + NoSQL/Cloud Storage
- Structured data: User profiles, jobs, applications
- Unstructured data: Raw resumes, AI insights

#### 3. AI/ML Integration
- **Resume Parsing**: Extract structured data from resumes (PDF, DOCX)
- **Semantic Matching**: Beyond keyword matching using NLP models
- **Match Scoring**: 0-100 score with explanations
- **Analytics**: Single page candidate strength visualization

#### 4. Key Functionalities
- AI Resume Parser with 95%+ accuracy
- Smart job matching with detailed match scores
- Candidate strength analytics dashboard
- Match reports for every application
- Real-time job alerts and updates
- Fraud detection for job postings

### Technology Stack Recommendations

#### Backend
- **Framework**: Django (Python) - built-in auth, RBAC support
- **Database**: PostgreSQL + MongoDB/AWS S3
- **AI/ML**: Commercial APIs (Affinda, Klippa) + Custom NLP models

#### Frontend
- **Framework**: React with responsive design
- **Visualization**: Plotly/Recharts for analytics dashboards
- **UI**: Clean, intuitive interface

#### AI Services
- **Resume Parsing**: Commercial APIs (Affinda ~$80/month, Airparser ~$39/month)
- **Semantic Matching**: Sentence-BERT, Fine-tuned BERT models
- **Embeddings**: OpenAI/Hugging Face transformers

### Key Differentiators
1. **Proactive AI Assistant**: GPT-like interface for guidance
2. **Explainable AI**: Transparent match scoring with actionable insights
3. **Advanced Analytics**: Single-page candidate strength visualization
4. **Automation**: Reduce manual effort through intelligent automation
5. **Real-time Processing**: Handle large datasets with real-time AI insights

### Success Metrics
- High accuracy resume parsing (95%+)
- Semantic matching beyond keywords
- User-friendly interface with minimal manual effort
- GDPR compliant and secure data handling
- Scalable architecture for growth

