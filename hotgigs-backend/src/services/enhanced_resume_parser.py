import os
import re
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import PyPDF2
import docx
from PIL import Image
import pytesseract
import io
from .spacy_resume_parser import spacy_resume_parser

class EnhancedResumeParsingService:
    """
    Enhanced resume parsing service with spaCy NLP as the default method.
    Provides intelligent parsing with fallback to other methods.
    """
    
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        self.providers = {
            'spacy_nlp': self._parse_with_spacy,  # Default provider
            'ocr_space': self._parse_with_ocr_space,
            'local_ocr': self._parse_with_local_ocr,
            'text_extraction': self._parse_with_text_extraction
        }
        
        # Domain expertise keywords
        self.domain_keywords = {
            'automobile': ['automotive', 'car', 'vehicle', 'ford', 'toyota', 'bmw', 'honda', 'nissan', 'mercedes', 'audi'],
            'e-commerce': ['ecommerce', 'amazon', 'ebay', 'shopify', 'online retail', 'marketplace', 'digital commerce'],
            'government': ['government', 'public sector', 'federal', 'state', 'municipal', 'civil service', 'policy'],
            'defense': ['defense', 'military', 'army', 'navy', 'air force', 'security', 'homeland security'],
            'healthcare': ['healthcare', 'medical', 'hospital', 'pharmaceutical', 'clinical', 'patient care', 'nursing'],
            'banking': ['bank', 'banking', 'financial services', 'credit', 'loan', 'mortgage', 'investment banking'],
            'finance': ['finance', 'investment', 'trading', 'portfolio', 'hedge fund', 'private equity', 'fintech'],
            'technology': ['tech', 'software', 'IT', 'programming', 'development', 'artificial intelligence', 'machine learning'],
            'education': ['education', 'teaching', 'academic', 'university', 'school', 'training', 'curriculum'],
            'retail': ['retail', 'sales', 'customer service', 'merchandising', 'store operations', 'fashion'],
            'manufacturing': ['manufacturing', 'production', 'operations', 'supply chain', 'quality control', 'lean'],
            'consulting': ['consulting', 'advisory', 'strategy', 'management consulting', 'business consulting']
        }
    
    def parse_resume(self, file, provider='spacy_nlp') -> Dict[str, Any]:
        """
        Parse resume using specified provider (default: spaCy NLP)
        
        Args:
            file: File object containing resume
            provider: Parsing provider ('spacy_nlp', 'ocr_space', 'local_ocr', 'text_extraction')
        
        Returns:
            Dictionary with parsing results
        """
        try:
            # Validate file
            if not self._validate_file(file):
                return {
                    'success': False,
                    'error': 'Invalid file format or size',
                    'data': {}
                }
            
            # Use specified provider
            if provider not in self.providers:
                provider = 'spacy_nlp'  # Fallback to default
            
            return self.providers[provider](file)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Resume parsing failed: {str(e)}',
                'data': {}
            }
    
    def _parse_with_spacy(self, file) -> Dict[str, Any]:
        """Parse resume using spaCy NLP (default method)"""
        try:
            return spacy_resume_parser.parse_resume(file, 'spacy_nlp')
        except Exception as e:
            # Fallback to text extraction if spaCy fails
            return self._parse_with_text_extraction(file)
    
    def _parse_with_ocr_space(self, file) -> Dict[str, Any]:
        """Parse resume using OCR.space API"""
        try:
            # Get OCR.space API key from environment
            api_key = os.getenv('OCR_SPACE_API_KEY')
            if not api_key:
                return self._parse_with_local_ocr(file)
            
            # Prepare file for OCR
            file.seek(0)
            
            # OCR.space API endpoint
            url = 'https://api.ocr.space/parse/image'
            
            payload = {
                'apikey': api_key,
                'language': 'eng',
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2
            }
            
            files = {'file': file}
            
            response = requests.post(url, data=payload, files=files, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('IsErroredOnProcessing'):
                    raise Exception(result.get('ErrorMessage', 'OCR processing failed'))
                
                # Extract text from OCR result
                text_content = ""
                if result.get('ParsedResults'):
                    text_content = result['ParsedResults'][0].get('ParsedText', '')
                
                if not text_content:
                    raise Exception('No text extracted from OCR')
                
                # Parse extracted text
                parsed_data = self._parse_text_content(text_content)
                parsed_data['parsing_metadata']['provider'] = 'ocr_space'
                
                return {
                    'success': True,
                    'data': parsed_data,
                    'raw_text': text_content,
                    'provider': 'ocr_space'
                }
            else:
                raise Exception(f'OCR API request failed: {response.status_code}')
                
        except Exception as e:
            # Fallback to local OCR
            return self._parse_with_local_ocr(file)
    
    def _parse_with_local_ocr(self, file) -> Dict[str, Any]:
        """Parse resume using local Tesseract OCR"""
        try:
            file.seek(0)
            
            # Check if file is an image
            filename = getattr(file, 'filename', '')
            file_ext = filename.lower().split('.')[-1] if filename else 'txt'
            
            if file_ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']:
                # Direct image OCR
                text_content = self._extract_text_from_image(file)
            elif file_ext == 'pdf':
                # Convert PDF to images and OCR
                text_content = self._extract_text_from_pdf_ocr(file)
            else:
                # Fallback to text extraction
                return self._parse_with_text_extraction(file)
            
            if not text_content or len(text_content.strip()) < 10:
                raise Exception('Insufficient text extracted from OCR')
            
            # Parse extracted text
            parsed_data = self._parse_text_content(text_content)
            parsed_data['parsing_metadata']['provider'] = 'local_ocr'
            
            return {
                'success': True,
                'data': parsed_data,
                'raw_text': text_content,
                'provider': 'local_ocr'
            }
            
        except Exception as e:
            # Fallback to text extraction
            return self._parse_with_text_extraction(file)
    
    def _parse_with_text_extraction(self, file) -> Dict[str, Any]:
        """Parse resume using basic text extraction"""
        try:
            file.seek(0)
            
            # Extract text based on file type
            filename = getattr(file, 'filename', '')
            file_ext = filename.lower().split('.')[-1] if filename else 'txt'
            
            if file_ext == 'pdf':
                text_content = self._extract_text_from_pdf(file)
            elif file_ext in ['doc', 'docx']:
                text_content = self._extract_text_from_docx(file)
            else:
                # Assume text file
                text_content = file.read().decode('utf-8', errors='ignore')
            
            if not text_content or len(text_content.strip()) < 10:
                raise Exception('No text content extracted')
            
            # Parse extracted text
            parsed_data = self._parse_text_content(text_content)
            parsed_data['parsing_metadata']['provider'] = 'text_extraction'
            
            return {
                'success': True,
                'data': parsed_data,
                'raw_text': text_content,
                'provider': 'text_extraction'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Text extraction failed: {str(e)}',
                'data': {}
            }
    
    def _validate_file(self, file) -> bool:
        """Validate file format and size"""
        try:
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > self.MAX_FILE_SIZE:
                return False
            
            # Check file extension
            filename = getattr(file, 'filename', '')
            if filename:
                file_ext = filename.lower().split('.')[-1]
                return file_ext in self.ALLOWED_EXTENSIONS
            
            return True
            
        except Exception:
            return False
    
    def _extract_text_from_pdf(self, file) -> str:
        """Extract text from PDF using PyPDF2"""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text_content = ""
            
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content.strip()
        except Exception as e:
            raise Exception(f"PDF text extraction failed: {str(e)}")
    
    def _extract_text_from_docx(self, file) -> str:
        """Extract text from DOCX using python-docx"""
        try:
            doc = docx.Document(file)
            text_content = ""
            
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            
            return text_content.strip()
        except Exception as e:
            raise Exception(f"DOCX text extraction failed: {str(e)}")
    
    def _extract_text_from_image(self, file) -> str:
        """Extract text from image using Tesseract OCR"""
        try:
            image = Image.open(file)
            
            # Preprocess image for better OCR
            image = image.convert('RGB')
            
            # Extract text using Tesseract
            text_content = pytesseract.image_to_string(image, config='--psm 6')
            
            return text_content.strip()
        except Exception as e:
            raise Exception(f"Image OCR failed: {str(e)}")
    
    def _extract_text_from_pdf_ocr(self, file) -> str:
        """Extract text from PDF using OCR (for scanned PDFs)"""
        try:
            from pdf2image import convert_from_bytes
            
            file.seek(0)
            pdf_bytes = file.read()
            
            # Convert PDF to images
            images = convert_from_bytes(pdf_bytes)
            
            text_content = ""
            for image in images:
                # Extract text from each page image
                page_text = pytesseract.image_to_string(image, config='--psm 6')
                text_content += page_text + "\n"
            
            return text_content.strip()
        except Exception as e:
            raise Exception(f"PDF OCR failed: {str(e)}")
    
    def _parse_text_content(self, text: str) -> Dict[str, Any]:
        """Parse text content using rule-based extraction (fallback method)"""
        try:
            # Basic parsing for fallback
            personal_info = self._extract_basic_personal_info(text)
            contact_info = self._extract_basic_contact_info(text)
            skills = self._extract_basic_skills(text)
            education = self._extract_basic_education(text)
            experience = self._extract_basic_experience(text)
            summary = self._extract_basic_summary(text)
            domain_expertise = self._identify_domain_expertise_basic(text)
            
            # Calculate basic scores
            confidence_score = 0.6  # Lower confidence for basic parsing
            completeness_score = self._calculate_basic_completeness(
                personal_info, contact_info, skills, education, experience, summary
            )
            
            return {
                'personal_info': personal_info,
                'contact_info': contact_info,
                'summary': summary,
                'skills': skills,
                'education': education,
                'work_experience': experience,
                'domain_expertise': domain_expertise,
                'parsing_metadata': {
                    'provider': 'basic_extraction',
                    'confidence_score': confidence_score,
                    'completeness_score': completeness_score,
                    'parsed_at': datetime.now().isoformat(),
                    'text_length': len(text)
                }
            }
            
        except Exception as e:
            raise Exception(f"Text parsing failed: {str(e)}")
    
    def _extract_basic_personal_info(self, text: str) -> Dict[str, str]:
        """Extract basic personal information using regex"""
        personal_info = {}
        
        # Extract name (first line that looks like a name)
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line.split()) <= 4 and all(word.replace('.', '').isalpha() for word in line.split()):
                name_parts = line.split()
                personal_info['full_name'] = line
                personal_info['first_name'] = name_parts[0] if name_parts else ""
                personal_info['last_name'] = name_parts[-1] if len(name_parts) > 1 else ""
                break
        
        return personal_info
    
    def _extract_basic_contact_info(self, text: str) -> Dict[str, str]:
        """Extract basic contact information using regex"""
        contact_info = {}
        
        # Email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Phone
        phone_match = re.search(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', text)
        if phone_match:
            contact_info['phone'] = phone_match.group()
        
        # LinkedIn
        linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text, re.IGNORECASE)
        if linkedin_match:
            contact_info['linkedin'] = linkedin_match.group()
        
        return contact_info
    
    def _extract_basic_skills(self, text: str) -> List[Dict[str, Any]]:
        """Extract basic skills using keyword matching"""
        skills_found = []
        text_lower = text.lower()
        
        # Basic skill keywords
        basic_skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'node.js', 'sql', 'mysql',
            'postgresql', 'mongodb', 'aws', 'azure', 'docker', 'kubernetes', 'git',
            'html', 'css', 'machine learning', 'data analysis', 'project management'
        ]
        
        for skill in basic_skills:
            if skill in text_lower:
                skills_found.append({
                    'name': skill.title(),
                    'category': 'Technical',
                    'proficiency_level': 'intermediate',
                    'mentioned_count': text_lower.count(skill)
                })
        
        return skills_found[:20]  # Limit to 20 skills
    
    def _extract_basic_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract basic education information"""
        education = []
        
        # Look for degree keywords
        degree_patterns = [
            r'\b(bachelor|master|phd|doctorate|bs|ba|ms|ma|mba)\b.*?(?:in|of)\s+([^.\n]+)',
            r'\b(bachelor\'s|master\'s)\s+(?:degree\s+)?(?:in|of)\s+([^.\n]+)'
        ]
        
        for pattern in degree_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                education.append({
                    'degree': match.group(1).title(),
                    'field_of_study': match.group(2).strip(),
                    'institution': '',
                    'year': ''
                })
        
        return education
    
    def _extract_basic_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract basic work experience"""
        experience = []
        
        # Look for job titles
        job_patterns = [
            r'\b(software engineer|developer|manager|analyst|consultant|director)\b',
            r'\b(senior|junior|lead)\s+(engineer|developer|manager|analyst)\b'
        ]
        
        for pattern in job_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                experience.append({
                    'job_title': match.group().title(),
                    'company': '',
                    'duration': '',
                    'description': '',
                    'start_date': '',
                    'end_date': ''
                })
        
        return experience[:5]  # Limit to 5 entries
    
    def _extract_basic_summary(self, text: str) -> str:
        """Extract basic summary"""
        # Take first paragraph as summary
        paragraphs = text.split('\n\n')
        for paragraph in paragraphs:
            if len(paragraph.strip()) > 50:
                return paragraph.strip()[:500]  # Limit to 500 chars
        return ""
    
    def _identify_domain_expertise_basic(self, text: str) -> List[str]:
        """Identify domain expertise using basic keyword matching"""
        text_lower = text.lower()
        identified_domains = []
        
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score >= 1:  # Require at least 1 keyword match
                identified_domains.append(domain)
        
        return identified_domains[:3]  # Limit to 3 domains
    
    def _calculate_basic_completeness(self, personal_info: Dict, contact_info: Dict,
                                    skills: List, education: List, experience: List,
                                    summary: str) -> float:
        """Calculate basic completeness score"""
        total_fields = 6
        completed_fields = 0
        
        if personal_info.get('full_name'):
            completed_fields += 1
        if contact_info.get('email') or contact_info.get('phone'):
            completed_fields += 1
        if skills:
            completed_fields += 1
        if education:
            completed_fields += 1
        if experience:
            completed_fields += 1
        if summary:
            completed_fields += 1
        
        return round(completed_fields / total_fields, 2)

# Create global instance
enhanced_resume_parser = EnhancedResumeParsingService()

