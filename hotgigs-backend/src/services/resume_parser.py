import os
import re
import json
import requests
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from werkzeug.utils import secure_filename
from flask import current_app
import PyPDF2
import docx
from PIL import Image
import pytesseract
import io
import base64

class ResumeParsingService:
    """Comprehensive resume parsing service with multiple provider support"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        self.providers = {
            'ocr_space': self._parse_with_ocr_space,
            'local_ocr': self._parse_with_local_ocr,
            'text_extraction': self._parse_with_text_extraction
        }
        
        # Domain expertise mapping
        self.domain_keywords = {
            'automobile': ['automotive', 'car', 'vehicle', 'ford', 'toyota', 'bmw', 'mercedes', 'honda', 'nissan', 'auto'],
            'e-commerce': ['ecommerce', 'e-commerce', 'amazon', 'ebay', 'shopify', 'online retail', 'marketplace'],
            'government': ['government', 'public sector', 'federal', 'state', 'municipal', 'civil service'],
            'defense': ['defense', 'military', 'army', 'navy', 'air force', 'security', 'homeland'],
            'healthcare': ['healthcare', 'medical', 'hospital', 'clinic', 'pharmaceutical', 'biotech', 'health'],
            'banking': ['bank', 'banking', 'financial services', 'credit', 'loan', 'mortgage', 'investment'],
            'finance': ['finance', 'fintech', 'trading', 'investment', 'hedge fund', 'private equity', 'insurance'],
            'technology': ['tech', 'software', 'IT', 'computer', 'programming', 'development', 'engineering'],
            'education': ['education', 'school', 'university', 'college', 'academic', 'teaching', 'learning'],
            'retail': ['retail', 'store', 'shopping', 'consumer', 'merchandise', 'sales'],
            'manufacturing': ['manufacturing', 'production', 'factory', 'industrial', 'assembly', 'operations'],
            'consulting': ['consulting', 'advisory', 'strategy', 'management consulting', 'business consulting']
        }
        
        # Skills categorization
        self.skill_categories = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift'],
            'web_development': ['html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask'],
            'data_science': ['machine learning', 'data analysis', 'statistics', 'pandas', 'numpy', 'tensorflow', 'pytorch'],
            'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins'],
            'mobile': ['ios', 'android', 'react native', 'flutter', 'swift', 'kotlin'],
            'design': ['ui/ux', 'photoshop', 'illustrator', 'figma', 'sketch', 'adobe creative'],
            'project_management': ['agile', 'scrum', 'kanban', 'jira', 'project management', 'pmp'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'analytical thinking']
        }
    
    def validate_file(self, file) -> Tuple[bool, str]:
        """Validate uploaded file"""
        if not file:
            return False, "No file provided"
        
        if file.filename == '':
            return False, "No file selected"
        
        # Check file extension
        if not self._allowed_file(file.filename):
            return False, f"File type not allowed. Supported types: {', '.join(self.ALLOWED_EXTENSIONS)}"
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.MAX_FILE_SIZE:
            return False, f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB"
        
        return True, "File is valid"
    
    def _allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def parse_resume(self, file, provider: str = 'text_extraction') -> Dict[str, Any]:
        """Parse resume using specified provider"""
        try:
            # Validate file
            is_valid, message = self.validate_file(file)
            if not is_valid:
                return {'success': False, 'error': message}
            
            # Get file extension
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            # Parse based on provider
            if provider in self.providers:
                result = self.providers[provider](file, file_ext)
            else:
                result = self._parse_with_text_extraction(file, file_ext)
            
            if result['success']:
                # Enhance parsed data
                enhanced_data = self._enhance_parsed_data(result['data'])
                result['data'] = enhanced_data
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Resume parsing error: {str(e)}")
            return {'success': False, 'error': f"Parsing failed: {str(e)}"}
    
    def _parse_with_text_extraction(self, file, file_ext: str) -> Dict[str, Any]:
        """Parse resume using local text extraction"""
        try:
            text_content = ""
            
            if file_ext == 'pdf':
                text_content = self._extract_text_from_pdf(file)
            elif file_ext in ['doc', 'docx']:
                text_content = self._extract_text_from_docx(file)
            elif file_ext == 'txt':
                text_content = file.read().decode('utf-8')
            elif file_ext in ['png', 'jpg', 'jpeg', 'gif']:
                text_content = self._extract_text_from_image(file)
            else:
                return {'success': False, 'error': f"Unsupported file type: {file_ext}"}
            
            if not text_content.strip():
                return {'success': False, 'error': "No text content found in file"}
            
            # Parse the extracted text
            parsed_data = self._parse_text_content(text_content)
            
            return {
                'success': True,
                'data': parsed_data,
                'raw_text': text_content,
                'provider': 'text_extraction'
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Text extraction failed: {str(e)}"}
    
    def _parse_with_ocr_space(self, file, file_ext: str) -> Dict[str, Any]:
        """Parse resume using OCR.space API"""
        try:
            api_key = os.environ.get('OCR_SPACE_API_KEY', 'helloworld')  # Free tier key
            
            # Prepare file for OCR
            file.seek(0)
            files = {'file': (file.filename, file, f'application/{file_ext}')}
            
            payload = {
                'apikey': api_key,
                'language': 'eng',
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2
            }
            
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files=files,
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('IsErroredOnProcessing', False):
                    return {'success': False, 'error': result.get('ErrorMessage', 'OCR processing failed')}
                
                # Extract text from OCR result
                text_content = ""
                for parsed_result in result.get('ParsedResults', []):
                    text_content += parsed_result.get('ParsedText', '')
                
                if not text_content.strip():
                    return {'success': False, 'error': "No text extracted from document"}
                
                # Parse the extracted text
                parsed_data = self._parse_text_content(text_content)
                
                return {
                    'success': True,
                    'data': parsed_data,
                    'raw_text': text_content,
                    'provider': 'ocr_space'
                }
            else:
                return {'success': False, 'error': f"OCR API error: {response.status_code}"}
                
        except Exception as e:
            return {'success': False, 'error': f"OCR processing failed: {str(e)}"}
    
    def _parse_with_local_ocr(self, file, file_ext: str) -> Dict[str, Any]:
        """Parse resume using local OCR (Tesseract)"""
        try:
            if file_ext in ['png', 'jpg', 'jpeg', 'gif']:
                text_content = self._extract_text_from_image(file)
            elif file_ext == 'pdf':
                # Convert PDF to images and OCR
                text_content = self._extract_text_from_pdf_ocr(file)
            else:
                return {'success': False, 'error': f"Local OCR not supported for {file_ext}"}
            
            if not text_content.strip():
                return {'success': False, 'error': "No text extracted from document"}
            
            # Parse the extracted text
            parsed_data = self._parse_text_content(text_content)
            
            return {
                'success': True,
                'data': parsed_data,
                'raw_text': text_content,
                'provider': 'local_ocr'
            }
            
        except Exception as e:
            return {'success': False, 'error': f"Local OCR failed: {str(e)}"}
    
    def _extract_text_from_pdf(self, file) -> str:
        """Extract text from PDF file"""
        try:
            file.seek(0)
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""
            
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content
        except Exception as e:
            current_app.logger.error(f"PDF text extraction error: {str(e)}")
            return ""
    
    def _extract_text_from_docx(self, file) -> str:
        """Extract text from DOCX file"""
        try:
            file.seek(0)
            doc = docx.Document(file)
            text_content = ""
            
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            return text_content
        except Exception as e:
            current_app.logger.error(f"DOCX text extraction error: {str(e)}")
            return ""
    
    def _extract_text_from_image(self, file) -> str:
        """Extract text from image using OCR"""
        try:
            file.seek(0)
            image = Image.open(file)
            text_content = pytesseract.image_to_string(image)
            return text_content
        except Exception as e:
            current_app.logger.error(f"Image OCR error: {str(e)}")
            return ""
    
    def _extract_text_from_pdf_ocr(self, file) -> str:
        """Extract text from PDF using OCR (for scanned PDFs)"""
        try:
            # This would require pdf2image library
            # For now, fallback to regular PDF text extraction
            return self._extract_text_from_pdf(file)
        except Exception as e:
            current_app.logger.error(f"PDF OCR error: {str(e)}")
            return ""
    
    def _parse_text_content(self, text: str) -> Dict[str, Any]:
        """Parse text content to extract structured data"""
        parsed_data = {
            'personal_info': self._extract_personal_info(text),
            'contact_info': self._extract_contact_info(text),
            'work_experience': self._extract_work_experience(text),
            'education': self._extract_education(text),
            'skills': self._extract_skills(text),
            'summary': self._extract_summary(text),
            'certifications': self._extract_certifications(text),
            'languages': self._extract_languages(text)
        }
        
        return parsed_data
    
    def _extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extract personal information"""
        lines = text.split('\n')
        first_lines = lines[:5]  # Usually name is in first few lines
        
        # Simple name extraction (first non-empty line that looks like a name)
        name = ""
        for line in first_lines:
            line = line.strip()
            if line and len(line.split()) >= 2 and not any(char.isdigit() for char in line):
                if not any(keyword in line.lower() for keyword in ['email', 'phone', 'address', 'linkedin']):
                    name = line
                    break
        
        name_parts = name.split() if name else []
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        return {
            'full_name': name,
            'first_name': first_name,
            'last_name': last_name
        }
    
    def _extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information"""
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Phone pattern
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, text)
        
        # LinkedIn pattern
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        
        # Location extraction (simple approach)
        location_keywords = ['address', 'location', 'city', 'state']
        location = ""
        for line in text.split('\n'):
            if any(keyword in line.lower() for keyword in location_keywords):
                location = line.strip()
                break
        
        return {
            'email': emails[0] if emails else "",
            'phone': phones[0] if phones else "",
            'linkedin': linkedin_matches[0] if linkedin_matches else "",
            'location': location
        }
    
    def _extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience"""
        experience_keywords = ['experience', 'employment', 'work history', 'professional experience']
        education_keywords = ['education', 'academic', 'degree', 'university', 'college']
        
        lines = text.split('\n')
        experience_section = []
        in_experience_section = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Check if we're entering experience section
            if any(keyword in line_lower for keyword in experience_keywords):
                in_experience_section = True
                continue
            
            # Check if we're leaving experience section
            if in_experience_section and any(keyword in line_lower for keyword in education_keywords):
                break
            
            # Collect experience lines
            if in_experience_section and line.strip():
                experience_section.append(line.strip())
        
        # Parse experience entries (simplified)
        experiences = []
        current_experience = {}
        
        for line in experience_section:
            # Date pattern
            date_pattern = r'\b(19|20)\d{2}\b'
            if re.search(date_pattern, line):
                if current_experience:
                    experiences.append(current_experience)
                current_experience = {'dates': line, 'description': ''}
            elif current_experience:
                current_experience['description'] += line + ' '
        
        if current_experience:
            experiences.append(current_experience)
        
        return experiences
    
    def _extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information"""
        education_keywords = ['education', 'academic', 'degree', 'university', 'college', 'school']
        
        lines = text.split('\n')
        education_section = []
        in_education_section = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if any(keyword in line_lower for keyword in education_keywords):
                in_education_section = True
                continue
            
            if in_education_section and line.strip():
                education_section.append(line.strip())
        
        # Simple education parsing
        education = []
        for line in education_section[:5]:  # Limit to first 5 entries
            if line:
                education.append({
                    'institution': line,
                    'degree': '',
                    'year': ''
                })
        
        return education
    
    def _extract_skills(self, text: str) -> List[Dict[str, str]]:
        """Extract skills from text"""
        text_lower = text.lower()
        found_skills = []
        
        # Check for skills in each category
        for category, skills_list in self.skill_categories.items():
            for skill in skills_list:
                if skill.lower() in text_lower:
                    found_skills.append({
                        'name': skill,
                        'category': category,
                        'proficiency_level': 'intermediate'  # Default level
                    })
        
        # Remove duplicates
        unique_skills = []
        seen_skills = set()
        for skill in found_skills:
            if skill['name'].lower() not in seen_skills:
                unique_skills.append(skill)
                seen_skills.add(skill['name'].lower())
        
        return unique_skills
    
    def _extract_summary(self, text: str) -> str:
        """Extract summary/objective"""
        summary_keywords = ['summary', 'objective', 'profile', 'about']
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in summary_keywords):
                # Get next few lines as summary
                summary_lines = lines[i+1:i+5]
                return ' '.join([l.strip() for l in summary_lines if l.strip()])
        
        return ""
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        cert_keywords = ['certification', 'certificate', 'certified', 'license']
        certifications = []
        
        for line in text.split('\n'):
            if any(keyword in line.lower() for keyword in cert_keywords):
                certifications.append(line.strip())
        
        return certifications
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract languages"""
        language_keywords = ['languages', 'language skills']
        languages = []
        
        for line in text.split('\n'):
            if any(keyword in line.lower() for keyword in language_keywords):
                languages.append(line.strip())
        
        return languages
    
    def _enhance_parsed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance parsed data with AI insights"""
        # Add domain expertise
        data['domain_expertise'] = self._identify_domain_expertise(data)
        
        # Enhance skills with categories
        data['skills_by_category'] = self._categorize_skills(data.get('skills', []))
        
        # Calculate experience level
        data['experience_level'] = self._calculate_experience_level(data)
        
        # Add parsing metadata
        data['parsing_metadata'] = {
            'parsed_at': datetime.utcnow().isoformat(),
            'confidence_score': self._calculate_confidence_score(data),
            'completeness_score': self._calculate_completeness_score(data)
        }
        
        return data
    
    def _identify_domain_expertise(self, data: Dict[str, Any]) -> List[str]:
        """Identify domain expertise from work experience"""
        domains = []
        text_content = ""
        
        # Combine work experience text
        for exp in data.get('work_experience', []):
            text_content += exp.get('description', '') + " "
        
        text_lower = text_content.lower()
        
        # Check for domain keywords
        for domain, keywords in self.domain_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                domains.append(domain)
        
        return domains
    
    def _categorize_skills(self, skills: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
        """Categorize skills by type"""
        categorized = {}
        
        for skill in skills:
            category = skill.get('category', 'other')
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(skill)
        
        return categorized
    
    def _calculate_experience_level(self, data: Dict[str, Any]) -> str:
        """Calculate experience level based on work history"""
        experience_count = len(data.get('work_experience', []))
        
        if experience_count == 0:
            return 'entry'
        elif experience_count <= 2:
            return 'junior'
        elif experience_count <= 4:
            return 'mid'
        else:
            return 'senior'
    
    def _calculate_confidence_score(self, data: Dict[str, Any]) -> float:
        """Calculate parsing confidence score"""
        score = 0.0
        
        # Check for key fields
        if data.get('personal_info', {}).get('full_name'):
            score += 0.2
        if data.get('contact_info', {}).get('email'):
            score += 0.2
        if data.get('work_experience'):
            score += 0.3
        if data.get('skills'):
            score += 0.2
        if data.get('education'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_completeness_score(self, data: Dict[str, Any]) -> float:
        """Calculate data completeness score"""
        total_fields = 8
        filled_fields = 0
        
        if data.get('personal_info', {}).get('full_name'):
            filled_fields += 1
        if data.get('contact_info', {}).get('email'):
            filled_fields += 1
        if data.get('contact_info', {}).get('phone'):
            filled_fields += 1
        if data.get('work_experience'):
            filled_fields += 1
        if data.get('education'):
            filled_fields += 1
        if data.get('skills'):
            filled_fields += 1
        if data.get('summary'):
            filled_fields += 1
        if data.get('domain_expertise'):
            filled_fields += 1
        
        return filled_fields / total_fields

# Global instance
resume_parser = ResumeParsingService()

