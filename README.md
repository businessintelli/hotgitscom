# 🚀 Hotgigs.com - AI-Powered Job Portal

A comprehensive AI-powered job portal platform featuring intelligent resume parsing, job matching, and career assistance.

## ✨ Features

- **AI-Powered Resume Parsing** - Extract skills, experience, and qualifications from resumes
- **Intelligent Job Matching** - ML-based job recommendations with confidence scoring
- **AI Career Assistant** - Interactive chat for career guidance and advice
- **Analytics Dashboard** - Comprehensive data visualization and insights
- **Multi-Role Support** - Candidates, recruiters, and admin interfaces
- **Mobile Responsive** - Perfect experience on all devices
- **Secure Authentication** - JWT-based auth with role-based access control

## 🛠️ Technology Stack

### Backend
- **Python 3.11** with Flask framework
- **PostgreSQL** database with SQLAlchemy ORM
- **spaCy** for natural language processing
- **scikit-learn** for machine learning algorithms
- **JWT** for secure authentication

### Frontend
- **React 18** with modern hooks and context
- **Vite** for fast development and building
- **Tailwind CSS** for responsive styling
- **Recharts** for data visualization
- **Lucide React** for beautiful icons

## 🚀 Quick Start

### Prerequisites
- **macOS** (for setup-mac.sh) or **Linux/Windows** (manual setup)
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 15+**
- **Git**

### Option 1: Automated Setup (macOS)

```bash
# Clone the repository
git clone https://github.com/businessintelli/hotgitscom.git
cd hotgitscom

# Run the automated setup script
./setup-mac.sh
```

### Option 2: Manual Setup

#### Backend Setup

```bash
# Navigate to backend directory
cd hotgigs-backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create environment file
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python src/main.py
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd hotgigs-frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
# Edit .env.local with your API URL

# Start development server
npm run dev
```

## 🔧 Configuration

### Database Setup

1. **Install PostgreSQL 15+**
2. **Create database and user:**
   ```sql
   CREATE DATABASE hotgigs;
   CREATE USER hotgigs_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE hotgigs TO hotgigs_user;
   ```

3. **Update .env file in backend:**
   ```env
   DATABASE_URL=postgresql://hotgigs_user:your_password@localhost:5432/hotgigs
   ```

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://hotgigs_user:password@localhost:5432/hotgigs

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Email (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

#### Frontend (.env.local)
```env
VITE_API_BASE_URL=http://localhost:5000
```

## 🚀 Deployment

### Cloud Deployment Scripts

Choose your preferred cloud platform:

```bash
# AWS Deployment
./deploy-aws.sh

# Google Cloud Platform
./deploy-gcp.sh

# Microsoft Azure
./deploy-azure.sh
```

Each script provides:
- ✅ **Automated infrastructure setup**
- ✅ **Database provisioning**
- ✅ **Container deployment**
- ✅ **Load balancer configuration**
- ✅ **SSL certificate setup**
- ✅ **Monitoring and logging**

## 🔍 Troubleshooting

### Common Issues

#### 1. NVIDIA CUDA Package Errors
```
ERROR: No matching distribution found for nvidia-cublas-cu12
```

**Solution:** The base requirements.txt excludes GPU packages. For GPU acceleration:
```bash
pip install -r requirements-gpu.txt
```

#### 2. Python Version Compatibility
```
Requires-Python >=3.7,<3.11
```

**Solution:** Use Python 3.11:
```bash
python3.11 -m venv venv
```

#### 3. spaCy Model Download Issues
```bash
# Manual model installation
python -m spacy download en_core_web_sm

# Alternative: Direct download
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
```

#### 4. NPM Dependency Resolution Errors
```
npm error ERESOLVE unable to resolve dependency tree
npm error peer date-fns@"^2.28.0 || ^3.0.0" from react-day-picker
```

**Quick Fix:**
```bash
# Use the automated fix script
./fix-frontend-deps.sh

# Or manual fix:
cd hotgigs-frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

#### 5. Database Connection Issues
- Ensure PostgreSQL is running
- Check database credentials in .env
- Verify database exists and user has permissions

#### 6. Frontend Build Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Performance Optimization

#### For CPU-Only Systems
The default installation is optimized for CPU-only systems. GPU packages are optional.

#### For GPU Systems
```bash
# Install GPU acceleration (optional)
pip install -r requirements-gpu.txt
```

## 📚 Documentation

- **[User Guide](user_documentation.md)** - Complete user documentation
- **[Technical Documentation](technical_documentation.md)** - Developer reference
- **[Deployment Guide](deployment_guide.md)** - Multi-platform deployment
- **[API Documentation](api_specification.md)** - REST API reference

## 🏗️ Architecture

### System Architecture
![System Architecture](system_architecture.png)

### Database Schema
![Database Schema](database_schema.png)

## 🧪 Testing

```bash
# Backend tests
cd hotgigs-backend
python -m pytest

# Frontend tests
cd hotgigs-frontend
npm test
```

## 📈 Monitoring

### Health Checks
- **Backend**: http://localhost:5000/api/health
- **Frontend**: http://localhost:5173

### Logs
- **Backend**: Check console output or logs directory
- **Frontend**: Browser developer console

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Documentation**: Check the docs directory
- **Issues**: Create a GitHub issue
- **Email**: developer@hotgigs.com

## 🎯 Roadmap

- [ ] Advanced AI features
- [ ] Mobile applications
- [ ] Integration with job boards
- [ ] Advanced analytics
- [ ] Multi-language support

---

**Built with ❤️ for the future of recruitment**

