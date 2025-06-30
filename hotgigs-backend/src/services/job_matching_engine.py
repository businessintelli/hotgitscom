import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Any, Tuple, Optional
import re
import json
from datetime import datetime, timedelta
from collections import defaultdict
import math

class SemanticJobMatchingEngine:
    """
    Advanced semantic job matching engine that uses NLP and machine learning
    to match candidates with relevant job opportunities based on multiple factors.
    """
    
    def __init__(self):
        # Initialize vectorizers and scalers
        self.skill_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.description_vectorizer = TfidfVectorizer(
            max_features=2000,
            stop_words='english',
            ngram_range=(1, 3),
            lowercase=True
        )
        self.scaler = StandardScaler()
        
        # Skill importance weights
        self.skill_weights = {
            'programming_languages': 1.0,
            'web_development': 0.9,
            'data_science': 0.95,
            'databases': 0.8,
            'cloud_technologies': 0.85,
            'mobile_development': 0.8,
            'design': 0.7,
            'project_management': 0.75,
            'soft_skills': 0.6,
            'cybersecurity': 0.9,
            'devops': 0.85
        }
        
        # Experience level mappings
        self.experience_levels = {
            'entry': 0,
            'junior': 1,
            'mid': 2,
            'senior': 3,
            'lead': 4,
            'principal': 5,
            'director': 6
        }
        
        # Domain compatibility matrix
        self.domain_compatibility = {
            'technology': ['technology', 'finance', 'healthcare', 'education', 'e-commerce'],
            'finance': ['finance', 'banking', 'technology', 'consulting'],
            'healthcare': ['healthcare', 'technology', 'consulting'],
            'education': ['education', 'technology', 'government'],
            'retail': ['retail', 'e-commerce', 'technology'],
            'manufacturing': ['manufacturing', 'technology', 'consulting'],
            'consulting': ['consulting', 'technology', 'finance', 'healthcare'],
            'government': ['government', 'technology', 'defense'],
            'defense': ['defense', 'government', 'technology'],
            'banking': ['banking', 'finance', 'technology'],
            'automobile': ['automobile', 'manufacturing', 'technology'],
            'e-commerce': ['e-commerce', 'retail', 'technology']
        }
        
        # Initialize fitted models flag
        self._models_fitted = False
    
    def fit_models(self, candidates: List[Dict], jobs: List[Dict]):
        """
        Fit the vectorizers and scalers on the available data
        
        Args:
            candidates: List of candidate data
            jobs: List of job data
        """
        try:
            # Prepare skill texts for vectorization
            candidate_skills = []
            job_skills = []
            
            for candidate in candidates:
                skills = candidate.get('skills', [])
                skill_text = ' '.join([skill.get('name', '') for skill in skills])
                candidate_skills.append(skill_text)
            
            for job in jobs:
                skills = job.get('required_skills', [])
                skill_text = ' '.join([skill.get('name', '') for skill in skills])
                job_skills.append(skill_text)
            
            # Combine all skill texts
            all_skills = candidate_skills + job_skills
            
            if all_skills:
                self.skill_vectorizer.fit(all_skills)
            
            # Prepare description texts
            candidate_descriptions = []
            job_descriptions = []
            
            for candidate in candidates:
                desc = candidate.get('summary', '') + ' ' + ' '.join([
                    exp.get('description', '') for exp in candidate.get('work_experience', [])
                ])
                candidate_descriptions.append(desc)
            
            for job in jobs:
                desc = job.get('description', '') + ' ' + job.get('requirements', '')
                job_descriptions.append(desc)
            
            # Combine all descriptions
            all_descriptions = candidate_descriptions + job_descriptions
            
            if all_descriptions:
                self.description_vectorizer.fit(all_descriptions)
            
            self._models_fitted = True
            
        except Exception as e:
            print(f"Warning: Model fitting failed: {str(e)}")
            # Continue with default models
            self._models_fitted = False
    
    def calculate_match_score(self, candidate: Dict, job: Dict) -> Dict[str, Any]:
        """
        Calculate comprehensive match score between candidate and job
        
        Args:
            candidate: Candidate data with parsed resume information
            job: Job posting data
        
        Returns:
            Dictionary containing match score and detailed breakdown
        """
        try:
            # Calculate individual component scores
            skill_score = self._calculate_skill_match(candidate, job)
            experience_score = self._calculate_experience_match(candidate, job)
            domain_score = self._calculate_domain_match(candidate, job)
            location_score = self._calculate_location_match(candidate, job)
            semantic_score = self._calculate_semantic_match(candidate, job)
            
            # Weight the components
            weights = {
                'skills': 0.35,
                'experience': 0.25,
                'domain': 0.15,
                'location': 0.10,
                'semantic': 0.15
            }
            
            # Calculate overall score
            overall_score = (
                skill_score['score'] * weights['skills'] +
                experience_score['score'] * weights['experience'] +
                domain_score['score'] * weights['domain'] +
                location_score['score'] * weights['location'] +
                semantic_score['score'] * weights['semantic']
            )
            
            # Calculate confidence based on data completeness
            confidence = self._calculate_confidence(candidate, job)
            
            return {
                'overall_score': round(overall_score, 3),
                'confidence': round(confidence, 3),
                'breakdown': {
                    'skills': skill_score,
                    'experience': experience_score,
                    'domain': domain_score,
                    'location': location_score,
                    'semantic': semantic_score
                },
                'weights': weights,
                'match_reasons': self._generate_match_reasons(candidate, job, {
                    'skills': skill_score,
                    'experience': experience_score,
                    'domain': domain_score
                }),
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'overall_score': 0.0,
                'confidence': 0.0,
                'error': f'Match calculation failed: {str(e)}',
                'calculated_at': datetime.now().isoformat()
            }
    
    def _calculate_skill_match(self, candidate: Dict, job: Dict) -> Dict[str, Any]:
        """Calculate skill-based matching score"""
        try:
            candidate_skills = candidate.get('skills', [])
            job_skills = job.get('required_skills', [])
            
            if not candidate_skills or not job_skills:
                return {'score': 0.0, 'details': 'Insufficient skill data'}
            
            # Create skill dictionaries for easier lookup
            candidate_skill_dict = {
                skill['name'].lower(): skill for skill in candidate_skills
            }
            job_skill_dict = {
                skill['name'].lower(): skill for skill in job_skills
            }
            
            # Calculate matches
            matched_skills = []
            missing_skills = []
            skill_scores = []
            
            for job_skill_name, job_skill in job_skill_dict.items():
                if job_skill_name in candidate_skill_dict:
                    candidate_skill = candidate_skill_dict[job_skill_name]
                    
                    # Calculate skill-level match
                    skill_match_score = self._calculate_skill_level_match(
                        candidate_skill, job_skill
                    )
                    
                    # Apply category weight
                    category = job_skill.get('category', 'technical').lower().replace(' ', '_')
                    weight = self.skill_weights.get(category, 0.7)
                    
                    weighted_score = skill_match_score * weight
                    skill_scores.append(weighted_score)
                    
                    matched_skills.append({
                        'name': job_skill_name.title(),
                        'candidate_level': candidate_skill.get('proficiency_level', 'unknown'),
                        'required_level': job_skill.get('proficiency_level', 'intermediate'),
                        'match_score': skill_match_score,
                        'weighted_score': weighted_score,
                        'category': category
                    })
                else:
                    missing_skills.append({
                        'name': job_skill_name.title(),
                        'required_level': job_skill.get('proficiency_level', 'intermediate'),
                        'category': job_skill.get('category', 'technical')
                    })
            
            # Calculate overall skill score
            if skill_scores:
                avg_skill_score = np.mean(skill_scores)
                coverage_ratio = len(matched_skills) / len(job_skills)
                overall_score = avg_skill_score * coverage_ratio
            else:
                overall_score = 0.0
            
            return {
                'score': round(overall_score, 3),
                'matched_skills': matched_skills,
                'missing_skills': missing_skills,
                'coverage_ratio': round(len(matched_skills) / len(job_skills), 3) if job_skills else 0.0,
                'details': f'{len(matched_skills)}/{len(job_skills)} skills matched'
            }
            
        except Exception as e:
            return {'score': 0.0, 'error': str(e)}
    
    def _calculate_skill_level_match(self, candidate_skill: Dict, job_skill: Dict) -> float:
        """Calculate match score between candidate and required skill levels"""
        try:
            candidate_level = candidate_skill.get('proficiency_level', 'intermediate').lower()
            required_level = job_skill.get('proficiency_level', 'intermediate').lower()
            
            level_scores = {
                'beginner': 1,
                'intermediate': 2,
                'advanced': 3,
                'expert': 4
            }
            
            candidate_score = level_scores.get(candidate_level, 2)
            required_score = level_scores.get(required_level, 2)
            
            if candidate_score >= required_score:
                # Candidate meets or exceeds requirement
                return 1.0
            else:
                # Candidate is below requirement
                gap = required_score - candidate_score
                return max(0.0, 1.0 - (gap * 0.25))
                
        except Exception:
            return 0.5  # Default moderate match
    
    def _calculate_experience_match(self, candidate: Dict, job: Dict) -> Dict[str, Any]:
        """Calculate experience-based matching score"""
        try:
            candidate_experience = candidate.get('work_experience', [])
            job_requirements = job.get('experience_requirements', {})
            
            # Calculate years of experience
            candidate_years = self._calculate_years_of_experience(candidate_experience)
            required_years = job_requirements.get('min_years', 0)
            max_years = job_requirements.get('max_years', 20)
            
            # Calculate experience level match
            candidate_level = self._determine_experience_level(candidate_years)
            required_level = job_requirements.get('level', 'mid')
            
            # Years match score
            if candidate_years >= required_years:
                if candidate_years <= max_years:
                    years_score = 1.0
                else:
                    # Overqualified penalty
                    excess = candidate_years - max_years
                    years_score = max(0.7, 1.0 - (excess * 0.05))
            else:
                # Underqualified
                gap = required_years - candidate_years
                years_score = max(0.0, 1.0 - (gap * 0.15))
            
            # Level match score
            level_score = self._calculate_level_match(candidate_level, required_level)
            
            # Industry experience match
            industry_score = self._calculate_industry_experience_match(
                candidate_experience, job.get('industry', '')
            )
            
            # Combine scores
            overall_score = (years_score * 0.4 + level_score * 0.4 + industry_score * 0.2)
            
            return {
                'score': round(overall_score, 3),
                'candidate_years': candidate_years,
                'required_years': required_years,
                'candidate_level': candidate_level,
                'required_level': required_level,
                'years_score': round(years_score, 3),
                'level_score': round(level_score, 3),
                'industry_score': round(industry_score, 3),
                'details': f'{candidate_years} years experience ({candidate_level} level)'
            }
            
        except Exception as e:
            return {'score': 0.0, 'error': str(e)}
    
    def _calculate_years_of_experience(self, experience: List[Dict]) -> float:
        """Calculate total years of experience from work history"""
        try:
            total_years = 0.0
            
            for exp in experience:
                duration = exp.get('duration', '')
                years = self._parse_duration_to_years(duration)
                total_years += years
            
            return total_years
            
        except Exception:
            return 0.0
    
    def _parse_duration_to_years(self, duration: str) -> float:
        """Parse duration string to years"""
        try:
            if not duration:
                return 0.0
            
            duration = duration.lower()
            
            # Look for year patterns
            year_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:year|yr)', duration)
            if year_match:
                return float(year_match.group(1))
            
            # Look for month patterns
            month_match = re.search(r'(\d+)\s*(?:month|mo)', duration)
            if month_match:
                return float(month_match.group(1)) / 12
            
            # Look for date ranges
            date_pattern = r'(\d{4})\s*[-–]\s*(\d{4}|present|current)'
            date_match = re.search(date_pattern, duration)
            if date_match:
                start_year = int(date_match.group(1))
                end_year = datetime.now().year if date_match.group(2).lower() in ['present', 'current'] else int(date_match.group(2))
                return max(0, end_year - start_year)
            
            return 1.0  # Default to 1 year if can't parse
            
        except Exception:
            return 0.0
    
    def _determine_experience_level(self, years: float) -> str:
        """Determine experience level based on years"""
        if years < 1:
            return 'entry'
        elif years < 3:
            return 'junior'
        elif years < 6:
            return 'mid'
        elif years < 10:
            return 'senior'
        elif years < 15:
            return 'lead'
        else:
            return 'principal'
    
    def _calculate_level_match(self, candidate_level: str, required_level: str) -> float:
        """Calculate match score between experience levels"""
        try:
            candidate_score = self.experience_levels.get(candidate_level, 2)
            required_score = self.experience_levels.get(required_level, 2)
            
            if candidate_score >= required_score:
                # Meets or exceeds requirement
                if candidate_score - required_score <= 1:
                    return 1.0
                else:
                    # Overqualified penalty
                    return max(0.7, 1.0 - ((candidate_score - required_score - 1) * 0.1))
            else:
                # Underqualified
                gap = required_score - candidate_score
                return max(0.0, 1.0 - (gap * 0.2))
                
        except Exception:
            return 0.5
    
    def _calculate_industry_experience_match(self, experience: List[Dict], job_industry: str) -> float:
        """Calculate industry experience match"""
        try:
            if not job_industry or not experience:
                return 0.5
            
            job_industry = job_industry.lower()
            industry_matches = 0
            
            for exp in experience:
                exp_description = (exp.get('description', '') + ' ' + 
                                 exp.get('company', '')).lower()
                
                if job_industry in exp_description:
                    industry_matches += 1
            
            if industry_matches > 0:
                return min(1.0, industry_matches / len(experience) + 0.3)
            else:
                return 0.3  # Base score for no direct industry match
                
        except Exception:
            return 0.5
    
    def _calculate_domain_match(self, candidate: Dict, job: Dict) -> Dict[str, Any]:
        """Calculate domain expertise matching score"""
        try:
            candidate_domains = candidate.get('domain_expertise', [])
            job_domain = job.get('industry', '').lower()
            
            if not candidate_domains or not job_domain:
                return {'score': 0.5, 'details': 'Insufficient domain data'}
            
            # Direct domain match
            if job_domain in [d.lower() for d in candidate_domains]:
                return {
                    'score': 1.0,
                    'match_type': 'direct',
                    'matched_domain': job_domain,
                    'details': f'Direct domain match: {job_domain}'
                }
            
            # Compatible domain match
            compatible_domains = self.domain_compatibility.get(job_domain, [])
            for candidate_domain in candidate_domains:
                if candidate_domain.lower() in compatible_domains:
                    return {
                        'score': 0.7,
                        'match_type': 'compatible',
                        'matched_domain': candidate_domain,
                        'details': f'Compatible domain: {candidate_domain} -> {job_domain}'
                    }
            
            # No domain match
            return {
                'score': 0.3,
                'match_type': 'none',
                'details': 'No domain expertise match'
            }
            
        except Exception as e:
            return {'score': 0.0, 'error': str(e)}
    
    def _calculate_location_match(self, candidate: Dict, job: Dict) -> Dict[str, Any]:
        """Calculate location-based matching score"""
        try:
            candidate_location = candidate.get('contact_info', {}).get('location', '').lower()
            job_location = job.get('location', '').lower()
            remote_ok = job.get('remote_ok', False)
            
            if remote_ok:
                return {
                    'score': 1.0,
                    'match_type': 'remote',
                    'details': 'Remote work available'
                }
            
            if not candidate_location or not job_location:
                return {'score': 0.5, 'details': 'Insufficient location data'}
            
            # Exact location match
            if candidate_location == job_location:
                return {
                    'score': 1.0,
                    'match_type': 'exact',
                    'details': f'Exact location match: {job_location}'
                }
            
            # City/state match
            if self._locations_compatible(candidate_location, job_location):
                return {
                    'score': 0.8,
                    'match_type': 'compatible',
                    'details': f'Compatible locations: {candidate_location} / {job_location}'
                }
            
            # No location match
            return {
                'score': 0.2,
                'match_type': 'different',
                'details': f'Different locations: {candidate_location} / {job_location}'
            }
            
        except Exception as e:
            return {'score': 0.0, 'error': str(e)}
    
    def _locations_compatible(self, loc1: str, loc2: str) -> bool:
        """Check if two locations are compatible (same city/state)"""
        try:
            # Simple compatibility check
            loc1_parts = set(loc1.replace(',', ' ').split())
            loc2_parts = set(loc2.replace(',', ' ').split())
            
            # Check for common words (city, state names)
            common_parts = loc1_parts.intersection(loc2_parts)
            return len(common_parts) > 0
            
        except Exception:
            return False
    
    def _calculate_semantic_match(self, candidate: Dict, job: Dict) -> Dict[str, Any]:
        """Calculate semantic similarity between candidate and job descriptions"""
        try:
            # Prepare candidate text
            candidate_text = self._prepare_candidate_text(candidate)
            job_text = self._prepare_job_text(job)
            
            if not candidate_text or not job_text:
                return {'score': 0.0, 'details': 'Insufficient text data'}
            
            # Use TF-IDF for semantic similarity if models are fitted
            if self._models_fitted:
                try:
                    candidate_vector = self.description_vectorizer.transform([candidate_text])
                    job_vector = self.description_vectorizer.transform([job_text])
                    
                    similarity = cosine_similarity(candidate_vector, job_vector)[0][0]
                    
                    return {
                        'score': round(similarity, 3),
                        'method': 'tfidf_cosine',
                        'details': f'TF-IDF cosine similarity: {similarity:.3f}'
                    }
                except Exception:
                    pass
            
            # Fallback to keyword-based similarity
            similarity = self._calculate_keyword_similarity(candidate_text, job_text)
            
            return {
                'score': round(similarity, 3),
                'method': 'keyword_based',
                'details': f'Keyword-based similarity: {similarity:.3f}'
            }
            
        except Exception as e:
            return {'score': 0.0, 'error': str(e)}
    
    def _prepare_candidate_text(self, candidate: Dict) -> str:
        """Prepare candidate text for semantic analysis"""
        try:
            text_parts = []
            
            # Add summary
            if candidate.get('summary'):
                text_parts.append(candidate['summary'])
            
            # Add work experience descriptions
            for exp in candidate.get('work_experience', []):
                if exp.get('description'):
                    text_parts.append(exp['description'])
                if exp.get('job_title'):
                    text_parts.append(exp['job_title'])
            
            # Add skills
            skills = [skill.get('name', '') for skill in candidate.get('skills', [])]
            text_parts.extend(skills)
            
            # Add education
            for edu in candidate.get('education', []):
                if edu.get('field_of_study'):
                    text_parts.append(edu['field_of_study'])
                if edu.get('degree'):
                    text_parts.append(edu['degree'])
            
            return ' '.join(text_parts)
            
        except Exception:
            return ''
    
    def _prepare_job_text(self, job: Dict) -> str:
        """Prepare job text for semantic analysis"""
        try:
            text_parts = []
            
            # Add job title
            if job.get('title'):
                text_parts.append(job['title'])
            
            # Add description
            if job.get('description'):
                text_parts.append(job['description'])
            
            # Add requirements
            if job.get('requirements'):
                text_parts.append(job['requirements'])
            
            # Add required skills
            skills = [skill.get('name', '') for skill in job.get('required_skills', [])]
            text_parts.extend(skills)
            
            # Add industry
            if job.get('industry'):
                text_parts.append(job['industry'])
            
            return ' '.join(text_parts)
            
        except Exception:
            return ''
    
    def _calculate_keyword_similarity(self, text1: str, text2: str) -> float:
        """Calculate keyword-based similarity between two texts"""
        try:
            # Simple keyword overlap similarity
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            # Remove common stop words
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            words1 = words1 - stop_words
            words2 = words2 - stop_words
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_confidence(self, candidate: Dict, job: Dict) -> float:
        """Calculate confidence score based on data completeness"""
        try:
            candidate_completeness = 0.0
            job_completeness = 0.0
            
            # Candidate data completeness
            if candidate.get('personal_info', {}).get('full_name'):
                candidate_completeness += 0.1
            if candidate.get('contact_info', {}).get('email'):
                candidate_completeness += 0.1
            if candidate.get('skills'):
                candidate_completeness += 0.3
            if candidate.get('work_experience'):
                candidate_completeness += 0.3
            if candidate.get('education'):
                candidate_completeness += 0.1
            if candidate.get('summary'):
                candidate_completeness += 0.1
            
            # Job data completeness
            if job.get('title'):
                job_completeness += 0.2
            if job.get('description'):
                job_completeness += 0.3
            if job.get('required_skills'):
                job_completeness += 0.3
            if job.get('experience_requirements'):
                job_completeness += 0.1
            if job.get('location'):
                job_completeness += 0.1
            
            return (candidate_completeness + job_completeness) / 2
            
        except Exception:
            return 0.5
    
    def _generate_match_reasons(self, candidate: Dict, job: Dict, scores: Dict) -> List[str]:
        """Generate human-readable match reasons"""
        reasons = []
        
        try:
            # Skill-based reasons
            skill_score = scores.get('skills', {})
            if skill_score.get('score', 0) > 0.7:
                matched_count = len(skill_score.get('matched_skills', []))
                reasons.append(f"Strong skill match with {matched_count} relevant skills")
            
            # Experience-based reasons
            exp_score = scores.get('experience', {})
            if exp_score.get('score', 0) > 0.7:
                years = exp_score.get('candidate_years', 0)
                level = exp_score.get('candidate_level', 'unknown')
                reasons.append(f"Good experience match with {years} years ({level} level)")
            
            # Domain-based reasons
            domain_score = scores.get('domain', {})
            if domain_score.get('score', 0) > 0.7:
                match_type = domain_score.get('match_type', 'unknown')
                if match_type == 'direct':
                    reasons.append("Direct industry experience match")
                elif match_type == 'compatible':
                    reasons.append("Compatible industry background")
            
            if not reasons:
                reasons.append("Partial match based on available criteria")
            
            return reasons
            
        except Exception:
            return ["Match calculated based on available data"]
    
    def find_best_matches(self, candidate: Dict, jobs: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Find best job matches for a candidate
        
        Args:
            candidate: Candidate data
            jobs: List of available jobs
            limit: Maximum number of matches to return
        
        Returns:
            List of job matches sorted by score
        """
        try:
            matches = []
            
            for job in jobs:
                match_result = self.calculate_match_score(candidate, job)
                
                if match_result.get('overall_score', 0) > 0:
                    matches.append({
                        'job_id': job.get('id'),
                        'job_title': job.get('title', 'Unknown Title'),
                        'company': job.get('company', 'Unknown Company'),
                        'location': job.get('location', 'Unknown Location'),
                        'match_score': match_result['overall_score'],
                        'confidence': match_result['confidence'],
                        'match_breakdown': match_result.get('breakdown', {}),
                        'match_reasons': match_result.get('match_reasons', []),
                        'job_data': job
                    })
            
            # Sort by match score (descending)
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            return matches[:limit]
            
        except Exception as e:
            return []
    
    def find_best_candidates(self, job: Dict, candidates: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Find best candidate matches for a job
        
        Args:
            job: Job posting data
            candidates: List of available candidates
            limit: Maximum number of matches to return
        
        Returns:
            List of candidate matches sorted by score
        """
        try:
            matches = []
            
            for candidate in candidates:
                match_result = self.calculate_match_score(candidate, job)
                
                if match_result.get('overall_score', 0) > 0:
                    matches.append({
                        'candidate_id': candidate.get('id'),
                        'candidate_name': candidate.get('personal_info', {}).get('full_name', 'Unknown'),
                        'email': candidate.get('contact_info', {}).get('email', ''),
                        'experience_years': self._calculate_years_of_experience(
                            candidate.get('work_experience', [])
                        ),
                        'top_skills': [skill.get('name') for skill in candidate.get('skills', [])[:5]],
                        'match_score': match_result['overall_score'],
                        'confidence': match_result['confidence'],
                        'match_breakdown': match_result.get('breakdown', {}),
                        'match_reasons': match_result.get('match_reasons', []),
                        'candidate_data': candidate
                    })
            
            # Sort by match score (descending)
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            return matches[:limit]
            
        except Exception as e:
            return []

# Create global instance
job_matching_engine = SemanticJobMatchingEngine()

