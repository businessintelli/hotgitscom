import spacy
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import PyPDF2
import docx
from PIL import Image
import pytesseract
import io
from spacy.matcher import Matcher
from spacy.tokens import Span

class SpacyResumeParser:
    """
    Advanced resume parser using spaCy NLP library for intelligent information extraction.
    This parser uses Named Entity Recognition, pattern matching, and custom rules
    to extract structured data from resumes.
    """
    
    def __init__(self):
        # Load spaCy English model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise Exception("spaCy English model not found. Please install with: python -m spacy download en_core_web_sm")
        
        # Initialize matcher for pattern-based extraction
        self.matcher = Matcher(self.nlp.vocab)
        
        # Initialize skill databases
        self._init_skill_databases()
        
        # Initialize patterns
        self._init_patterns()
        
        # Initialize education patterns
        self._init_education_patterns()
        
        # Initialize experience patterns
        self._init_experience_patterns()
    
    def _init_skill_databases(self):
        """Initialize comprehensive skill databases categorized by domain"""
        self.skills_db = {
            'programming_languages': [
                'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift',
                'kotlin', 'scala', 'r', 'matlab', 'perl', 'shell', 'bash', 'powershell', 'typescript',
                'dart', 'objective-c', 'assembly', 'cobol', 'fortran', 'haskell', 'lua', 'groovy'
            ],
            'web_development': [
                'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask',
                'spring', 'laravel', 'codeigniter', 'symfony', 'rails', 'asp.net', 'jquery',
                'bootstrap', 'sass', 'less', 'webpack', 'gulp', 'grunt', 'npm', 'yarn', 'next.js',
                'nuxt.js', 'svelte', 'ember.js', 'backbone.js', 'meteor', 'gatsby', 'strapi'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'artificial intelligence', 'data analysis',
                'statistics', 'pandas', 'numpy', 'scipy', 'scikit-learn', 'tensorflow', 'pytorch',
                'keras', 'matplotlib', 'seaborn', 'plotly', 'jupyter', 'anaconda', 'data mining',
                'big data', 'hadoop', 'spark', 'kafka', 'airflow', 'mlflow', 'kubeflow', 'dask'
            ],
            'databases': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle',
                'sql server', 'sqlite', 'cassandra', 'dynamodb', 'neo4j', 'couchdb', 'influxdb',
                'mariadb', 'firestore', 'realm', 'hbase', 'clickhouse', 'snowflake', 'bigquery'
            ],
            'cloud_technologies': [
                'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'terraform',
                'jenkins', 'gitlab ci', 'github actions', 'circleci', 'travis ci', 'ansible',
                'puppet', 'chef', 'vagrant', 'helm', 'istio', 'prometheus', 'grafana', 'elk stack'
            ],
            'mobile_development': [
                'ios', 'android', 'react native', 'flutter', 'swift', 'kotlin', 'xamarin',
                'ionic', 'cordova', 'phonegap', 'unity', 'unreal engine', 'cocos2d', 'titanium'
            ],
            'design': [
                'ui/ux', 'photoshop', 'illustrator', 'figma', 'sketch', 'adobe xd', 'indesign',
                'after effects', 'premiere pro', 'blender', 'maya', '3ds max', 'cinema 4d',
                'zbrush', 'substance painter', 'canva', 'invision', 'principle', 'framer'
            ],
            'project_management': [
                'agile', 'scrum', 'kanban', 'jira', 'confluence', 'trello', 'asana', 'monday.com',
                'project management', 'pmp', 'prince2', 'lean', 'six sigma', 'waterfall',
                'risk management', 'stakeholder management', 'budget management'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving', 'analytical thinking',
                'critical thinking', 'creativity', 'adaptability', 'time management', 'negotiation',
                'presentation', 'public speaking', 'mentoring', 'coaching', 'conflict resolution'
            ],
            'cybersecurity': [
                'cybersecurity', 'information security', 'penetration testing', 'ethical hacking',
                'vulnerability assessment', 'incident response', 'forensics', 'compliance',
                'risk assessment', 'security audit', 'firewall', 'ids', 'ips', 'siem', 'soc'
            ],
            'devops': [
                'devops', 'ci/cd', 'continuous integration', 'continuous deployment', 'automation',
                'infrastructure as code', 'monitoring', 'logging', 'containerization', 'orchestration',
                'microservices', 'serverless', 'lambda', 'api gateway', 'load balancing'
            ]
        }
        
        # Create flat skill list for quick lookup
        self.all_skills = []
        for category, skills in self.skills_db.items():
            self.all_skills.extend(skills)
        
        # Convert to lowercase for case-insensitive matching
        self.all_skills = [skill.lower() for skill in self.all_skills]
    
    def _init_patterns(self):
        """Initialize spaCy patterns for various entities"""
        
        # Email pattern
        email_pattern = [
            {"TEXT": {"REGEX": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"}},
        ]
        self.matcher.add("EMAIL", [email_pattern])
        
        # Phone pattern
        phone_patterns = [
            [{"TEXT": {"REGEX": r"\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"}}],
            [{"TEXT": {"REGEX": r"\+?[0-9]{1,3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}"}}],
        ]
        self.matcher.add("PHONE", phone_patterns)
        
        # LinkedIn pattern
        linkedin_patterns = [
            [{"LOWER": "linkedin"}, {"TEXT": ":"}, {"TEXT": {"REGEX": r"https?://.*linkedin\.com.*"}}],
            [{"TEXT": {"REGEX": r"https?://.*linkedin\.com.*"}}],
            [{"LOWER": "linkedin.com"}, {"TEXT": "/"}, {"LOWER": "in"}, {"TEXT": "/"}, {"IS_ALPHA": True}],
        ]
        self.matcher.add("LINKEDIN", linkedin_patterns)
        
        # GitHub pattern
        github_patterns = [
            [{"LOWER": "github"}, {"TEXT": ":"}, {"TEXT": {"REGEX": r"https?://.*github\.com.*"}}],
            [{"TEXT": {"REGEX": r"https?://.*github\.com.*"}}],
        ]
        self.matcher.add("GITHUB", github_patterns)
        
        # Website pattern
        website_patterns = [
            [{"TEXT": {"REGEX": r"https?://[^\s]+"}}],
            [{"TEXT": {"REGEX": r"www\.[^\s]+"}}],
        ]
        self.matcher.add("WEBSITE", website_patterns)
    
    def _init_education_patterns(self):
        """Initialize education-related patterns"""
        
        # Degree patterns
        degree_patterns = [
            [{"LOWER": {"IN": ["bachelor", "bachelor's", "bs", "ba", "bsc", "beng"]}},
             {"LOWER": {"IN": ["of", "in"]}, "OP": "?"}, 
             {"IS_ALPHA": True, "OP": "+"}],
            [{"LOWER": {"IN": ["master", "master's", "ms", "ma", "msc", "meng", "mba"]}},
             {"LOWER": {"IN": ["of", "in"]}, "OP": "?"}, 
             {"IS_ALPHA": True, "OP": "+"}],
            [{"LOWER": {"IN": ["phd", "ph.d", "doctorate", "doctoral"]}},
             {"LOWER": {"IN": ["of", "in"]}, "OP": "?"}, 
             {"IS_ALPHA": True, "OP": "+"}],
        ]
        self.matcher.add("DEGREE", degree_patterns)
        
        # University patterns
        university_patterns = [
            [{"LOWER": {"IN": ["university", "college", "institute", "school"]}},
             {"LOWER": "of", "OP": "?"}, 
             {"IS_TITLE": True, "OP": "+"}],
            [{"IS_TITLE": True, "OP": "+"}, 
             {"LOWER": {"IN": ["university", "college", "institute", "school"]}}],
        ]
        self.matcher.add("UNIVERSITY", university_patterns)
    
    def _init_experience_patterns(self):
        """Initialize work experience patterns"""
        
        # Job title patterns
        job_title_patterns = [
            [{"LOWER": {"IN": ["senior", "junior", "lead", "principal", "chief"]}},
             {"IS_ALPHA": True, "OP": "+"}],
            [{"IS_ALPHA": True}, {"LOWER": {"IN": ["engineer", "developer", "manager", "analyst", "specialist"]}}],
            [{"IS_ALPHA": True}, {"IS_ALPHA": True}, {"LOWER": {"IN": ["engineer", "developer", "manager"]}}],
        ]
        self.matcher.add("JOB_TITLE", job_title_patterns)
        
        # Date patterns
        date_patterns = [
            [{"TEXT": {"REGEX": r"\d{1,2}/\d{1,2}/\d{4}"}}],
            [{"TEXT": {"REGEX": r"\d{4}-\d{1,2}-\d{1,2}"}}],
            [{"LOWER": {"IN": ["january", "february", "march", "april", "may", "june",
                              "july", "august", "september", "october", "november", "december",
                              "jan", "feb", "mar", "apr", "may", "jun",
                              "jul", "aug", "sep", "oct", "nov", "dec"]}},
             {"TEXT": {"REGEX": r"\d{4}"}}],
        ]
        self.matcher.add("DATE", date_patterns)
    
    def parse_resume(self, file, provider='spacy_nlp') -> Dict[str, Any]:
        """
        Main parsing method that extracts structured data from resume
        
        Args:
            file: File object (PDF, DOCX, TXT, or image)
            provider: Parsing provider (default: 'spacy_nlp')
        
        Returns:
            Dictionary containing parsed resume data
        """
        try:
            # Extract text from file
            text_content = self._extract_text_from_file(file)
            
            if not text_content or len(text_content.strip()) < 50:
                return {
                    'success': False,
                    'error': 'Insufficient text content extracted from file',
                    'data': {}
                }
            
            # Process text with spaCy
            doc = self.nlp(text_content)
            
            # Extract various components
            personal_info = self._extract_personal_info(doc, text_content)
            contact_info = self._extract_contact_info(doc, text_content)
            skills = self._extract_skills(doc, text_content)
            education = self._extract_education(doc, text_content)
            experience = self._extract_experience(doc, text_content)
            summary = self._extract_summary(text_content)
            domain_expertise = self._identify_domain_expertise(text_content, experience)
            
            # Calculate confidence and completeness scores
            confidence_score = self._calculate_confidence_score(
                personal_info, contact_info, skills, education, experience
            )
            completeness_score = self._calculate_completeness_score(
                personal_info, contact_info, skills, education, experience, summary
            )
            
            # Prepare parsed data
            parsed_data = {
                'personal_info': personal_info,
                'contact_info': contact_info,
                'summary': summary,
                'skills': skills,
                'education': education,
                'work_experience': experience,
                'domain_expertise': domain_expertise,
                'parsing_metadata': {
                    'provider': 'spacy_nlp',
                    'confidence_score': confidence_score,
                    'completeness_score': completeness_score,
                    'parsed_at': datetime.now().isoformat(),
                    'text_length': len(text_content),
                    'entities_found': len(doc.ents),
                    'sentences_count': len(list(doc.sents))
                }
            }
            
            return {
                'success': True,
                'data': parsed_data,
                'raw_text': text_content,
                'provider': 'spacy_nlp'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'spaCy parsing failed: {str(e)}',
                'data': {}
            }
    
    def _extract_text_from_file(self, file) -> str:
        """Extract text from various file formats"""
        try:
            # Get file extension
            filename = getattr(file, 'filename', '')
            if filename:
                file_ext = filename.lower().split('.')[-1]
            else:
                file_ext = 'txt'
            
            # Reset file pointer
            file.seek(0)
            
            if file_ext == 'pdf':
                return self._extract_text_from_pdf(file)
            elif file_ext in ['doc', 'docx']:
                return self._extract_text_from_docx(file)
            elif file_ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']:
                return self._extract_text_from_image(file)
            else:
                # Assume text file
                return file.read().decode('utf-8', errors='ignore')
                
        except Exception as e:
            raise Exception(f"Text extraction failed: {str(e)}")
    
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
        """Extract text from image using OCR"""
        try:
            image = Image.open(file)
            text_content = pytesseract.image_to_string(image)
            return text_content.strip()
        except Exception as e:
            raise Exception(f"Image OCR failed: {str(e)}")
    
    def _extract_personal_info(self, doc, text: str) -> Dict[str, Any]:
        """Extract personal information using NER and patterns"""
        personal_info = {}
        
        # Extract name using NER
        names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        if names:
            full_name = names[0]  # Take first person entity
            name_parts = full_name.split()
            personal_info['full_name'] = full_name
            personal_info['first_name'] = name_parts[0] if name_parts else ""
            personal_info['last_name'] = name_parts[-1] if len(name_parts) > 1 else ""
        
        # Extract location using NER
        locations = [ent.text for ent in doc.ents if ent.label_ in ["GPE", "LOC"]]
        if locations:
            personal_info['location'] = locations[0]
        
        return personal_info
    
    def _extract_contact_info(self, doc, text: str) -> Dict[str, Any]:
        """Extract contact information using patterns"""
        contact_info = {}
        
        # Use matcher to find patterns
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            
            if label == "EMAIL" and 'email' not in contact_info:
                contact_info['email'] = span.text
            elif label == "PHONE" and 'phone' not in contact_info:
                contact_info['phone'] = span.text
            elif label == "LINKEDIN" and 'linkedin' not in contact_info:
                contact_info['linkedin'] = span.text
            elif label == "GITHUB" and 'github' not in contact_info:
                contact_info['github'] = span.text
            elif label == "WEBSITE" and 'website' not in contact_info:
                contact_info['website'] = span.text
        
        # Additional regex-based extraction for missed patterns
        if 'email' not in contact_info:
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            if email_match:
                contact_info['email'] = email_match.group()
        
        if 'phone' not in contact_info:
            phone_match = re.search(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b', text)
            if phone_match:
                contact_info['phone'] = phone_match.group()
        
        return contact_info
    
    def _extract_skills(self, doc, text: str) -> List[Dict[str, Any]]:
        """Extract skills using comprehensive skill database and NLP"""
        skills_found = []
        text_lower = text.lower()
        
        # Track found skills to avoid duplicates
        found_skill_names = set()
        
        # Search for skills in text
        for category, skills_list in self.skills_db.items():
            for skill in skills_list:
                skill_lower = skill.lower()
                
                # Check if skill is mentioned in text
                if skill_lower in text_lower and skill_lower not in found_skill_names:
                    # Calculate proficiency based on context
                    proficiency = self._assess_skill_proficiency(skill_lower, text_lower)
                    
                    skill_data = {
                        'name': skill.title(),
                        'category': category.replace('_', ' ').title(),
                        'proficiency_level': proficiency,
                        'mentioned_count': text_lower.count(skill_lower)
                    }
                    
                    skills_found.append(skill_data)
                    found_skill_names.add(skill_lower)
        
        # Sort by proficiency and mention count
        skills_found.sort(key=lambda x: (x['mentioned_count'], x['proficiency_level']), reverse=True)
        
        return skills_found[:50]  # Limit to top 50 skills
    
    def _assess_skill_proficiency(self, skill: str, text: str) -> str:
        """Assess skill proficiency based on context"""
        skill_context = []
        
        # Find sentences containing the skill
        sentences = text.split('.')
        for sentence in sentences:
            if skill in sentence.lower():
                skill_context.append(sentence.lower())
        
        context_text = ' '.join(skill_context)
        
        # Proficiency indicators
        expert_indicators = ['expert', 'advanced', 'senior', 'lead', 'architect', 'specialist', 'years']
        intermediate_indicators = ['experienced', 'proficient', 'skilled', 'familiar', 'working knowledge']
        beginner_indicators = ['basic', 'beginner', 'learning', 'exposure', 'introduction']
        
        # Count indicators
        expert_count = sum(1 for indicator in expert_indicators if indicator in context_text)
        intermediate_count = sum(1 for indicator in intermediate_indicators if indicator in context_text)
        beginner_count = sum(1 for indicator in beginner_indicators if indicator in context_text)
        
        # Determine proficiency
        if expert_count > 0:
            return 'expert'
        elif intermediate_count > 0:
            return 'intermediate'
        elif beginner_count > 0:
            return 'beginner'
        else:
            return 'intermediate'  # Default
    
    def _extract_education(self, doc, text: str) -> List[Dict[str, Any]]:
        """Extract education information using patterns and NER"""
        education = []
        
        # Use matcher to find education patterns
        matches = self.matcher(doc)
        
        degrees = []
        universities = []
        
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            
            if label == "DEGREE":
                degrees.append(span.text)
            elif label == "UNIVERSITY":
                universities.append(span.text)
        
        # Extract years using regex
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        
        # Combine education information
        for i, degree in enumerate(degrees):
            edu_entry = {
                'degree': degree,
                'institution': universities[i] if i < len(universities) else "",
                'year': years[i] if i < len(years) else "",
                'field_of_study': self._extract_field_of_study(degree, text)
            }
            education.append(edu_entry)
        
        return education
    
    def _extract_field_of_study(self, degree: str, text: str) -> str:
        """Extract field of study from degree context"""
        # Common fields of study
        fields = [
            'computer science', 'engineering', 'business', 'mathematics', 'physics',
            'chemistry', 'biology', 'economics', 'finance', 'marketing', 'psychology',
            'sociology', 'history', 'literature', 'art', 'design', 'medicine', 'law'
        ]
        
        degree_lower = degree.lower()
        text_lower = text.lower()
        
        for field in fields:
            if field in degree_lower or field in text_lower:
                return field.title()
        
        return ""
    
    def _extract_experience(self, doc, text: str) -> List[Dict[str, Any]]:
        """Extract work experience using patterns and NER"""
        experience = []
        
        # Find organizations using NER
        organizations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        
        # Use matcher to find job titles and dates
        matches = self.matcher(doc)
        
        job_titles = []
        dates = []
        
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            span = doc[start:end]
            
            if label == "JOB_TITLE":
                job_titles.append(span.text)
            elif label == "DATE":
                dates.append(span.text)
        
        # Extract experience sections using common headers
        experience_sections = self._extract_experience_sections(text)
        
        for section in experience_sections:
            exp_entry = {
                'job_title': section.get('title', ''),
                'company': section.get('company', ''),
                'duration': section.get('duration', ''),
                'description': section.get('description', ''),
                'start_date': section.get('start_date', ''),
                'end_date': section.get('end_date', '')
            }
            experience.append(exp_entry)
        
        return experience
    
    def _extract_experience_sections(self, text: str) -> List[Dict[str, Any]]:
        """Extract experience sections from text"""
        sections = []
        
        # Split text into lines
        lines = text.split('\n')
        
        # Look for experience section headers
        experience_headers = [
            'experience', 'work experience', 'professional experience',
            'employment', 'career', 'work history', 'professional background'
        ]
        
        in_experience_section = False
        current_section = {}
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if we're entering experience section
            if any(header in line_lower for header in experience_headers):
                in_experience_section = True
                continue
            
            # Check if we're leaving experience section
            if in_experience_section and any(header in line_lower for header in ['education', 'skills', 'projects']):
                in_experience_section = False
                if current_section:
                    sections.append(current_section)
                    current_section = {}
                continue
            
            if in_experience_section and line.strip():
                # Try to parse experience entry
                if self._looks_like_job_title(line):
                    if current_section:
                        sections.append(current_section)
                    current_section = {'title': line.strip()}
                elif self._looks_like_company(line):
                    current_section['company'] = line.strip()
                elif self._looks_like_duration(line):
                    current_section['duration'] = line.strip()
                else:
                    # Add to description
                    if 'description' not in current_section:
                        current_section['description'] = line.strip()
                    else:
                        current_section['description'] += ' ' + line.strip()
        
        # Add last section
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _looks_like_job_title(self, line: str) -> bool:
        """Check if line looks like a job title"""
        job_keywords = [
            'engineer', 'developer', 'manager', 'analyst', 'specialist', 'consultant',
            'director', 'coordinator', 'assistant', 'associate', 'lead', 'senior', 'junior'
        ]
        return any(keyword in line.lower() for keyword in job_keywords)
    
    def _looks_like_company(self, line: str) -> bool:
        """Check if line looks like a company name"""
        company_indicators = ['inc', 'corp', 'ltd', 'llc', 'company', 'technologies', 'solutions']
        return any(indicator in line.lower() for indicator in company_indicators)
    
    def _looks_like_duration(self, line: str) -> bool:
        """Check if line looks like a duration"""
        date_pattern = r'\b(19|20)\d{2}\b'
        return bool(re.search(date_pattern, line))
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary or objective"""
        summary_headers = [
            'summary', 'professional summary', 'objective', 'profile',
            'about', 'overview', 'introduction', 'career objective'
        ]
        
        lines = text.split('\n')
        summary_lines = []
        in_summary = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if we're entering summary section
            if any(header in line_lower for header in summary_headers):
                in_summary = True
                continue
            
            # Check if we're leaving summary section
            if in_summary and any(header in line_lower for header in ['experience', 'education', 'skills']):
                break
            
            if in_summary and line.strip():
                summary_lines.append(line.strip())
        
        return ' '.join(summary_lines) if summary_lines else ""
    
    def _identify_domain_expertise(self, text: str, experience: List[Dict]) -> List[str]:
        """Identify domain expertise based on text content and experience"""
        domains = {
            'technology': ['software', 'tech', 'it', 'programming', 'development', 'engineering'],
            'finance': ['finance', 'banking', 'investment', 'trading', 'financial'],
            'healthcare': ['healthcare', 'medical', 'hospital', 'pharmaceutical', 'clinical'],
            'education': ['education', 'teaching', 'academic', 'university', 'school'],
            'retail': ['retail', 'sales', 'customer', 'commerce', 'marketing'],
            'manufacturing': ['manufacturing', 'production', 'operations', 'supply chain'],
            'consulting': ['consulting', 'advisory', 'strategy', 'management'],
            'government': ['government', 'public', 'policy', 'administration'],
            'nonprofit': ['nonprofit', 'ngo', 'charity', 'social', 'community']
        }
        
        text_lower = text.lower()
        identified_domains = []
        
        for domain, keywords in domains.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score >= 2:  # Require at least 2 keyword matches
                identified_domains.append(domain)
        
        return identified_domains
    
    def _calculate_confidence_score(self, personal_info: Dict, contact_info: Dict, 
                                  skills: List, education: List, experience: List) -> float:
        """Calculate parsing confidence score based on extracted data quality"""
        score = 0.0
        max_score = 5.0
        
        # Personal info score (0-1)
        if personal_info.get('full_name'):
            score += 1.0
        
        # Contact info score (0-1)
        contact_score = 0
        if contact_info.get('email'):
            contact_score += 0.5
        if contact_info.get('phone'):
            contact_score += 0.5
        score += contact_score
        
        # Skills score (0-1)
        if len(skills) >= 5:
            score += 1.0
        elif len(skills) >= 2:
            score += 0.5
        
        # Education score (0-1)
        if education:
            score += 1.0
        
        # Experience score (0-1)
        if experience:
            score += 1.0
        
        return round(score / max_score, 2)
    
    def _calculate_completeness_score(self, personal_info: Dict, contact_info: Dict,
                                    skills: List, education: List, experience: List,
                                    summary: str) -> float:
        """Calculate data completeness score"""
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
spacy_resume_parser = SpacyResumeParser()

