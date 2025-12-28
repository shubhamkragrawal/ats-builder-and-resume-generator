"""
ATS Analyzer - Analyze resumes and provide ATS scores
"""
import logging
from typing import Dict, Optional, Tuple
from src.llm_handler import LLMHandler
from src.utils import extract_score_from_response


class ATSAnalyzer:
    """Analyzer for ATS scoring and resume review"""
    
    def __init__(self, llm_handler: LLMHandler, prompts: Dict, config: Dict):
        """
        Initialize ATS Analyzer
        
        Args:
            llm_handler: LLM handler instance
            prompts: Prompt templates
            config: Configuration dict
        """
        self.llm = llm_handler
        self.prompts = prompts
        self.config = config
        logging.info("ATS Analyzer initialized")
    
    def review_resume(self, resume_text: str) -> Optional[str]:
        """
        Review resume without job description
        
        Args:
            resume_text: Resume content
            
        Returns:
            Review feedback or None if error
        """
        try:
            logging.info("Starting resume review (no JD)")
            
            template = self.prompts.get('resume_review')
            if not template:
                logging.error("Resume review template not found")
                return None
            
            feedback = self.llm.generate_with_template(
                template,
                resume_text=resume_text
            )
            
            if feedback:
                logging.info("Resume review completed successfully")
                return feedback
            else:
                logging.error("LLM returned no feedback for resume review")
                return None
                
        except Exception as e:
            logging.error(f"Error in resume review: {str(e)}")
            return None
    
    def analyze_ats_score(
        self,
        resume_text: str,
        job_description: str,
        background: Optional[str] = None
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Analyze ATS compatibility and get score
        
        Args:
            resume_text: Resume content
            job_description: Job description
            background: Optional candidate background
            
        Returns:
            Tuple of (score, detailed_feedback)
        """
        try:
            logging.info("Starting ATS score analysis")
            
            # Choose template based on whether background is provided
            if background:
                template = self.prompts.get('ats_scoring_with_background')
                if not template:
                    logging.warning("Background template not found, using standard")
                    template = self.prompts.get('ats_scoring')
                
                feedback = self.llm.generate_with_template(
                    template,
                    resume_text=resume_text,
                    job_description=job_description,
                    background=background
                )
            else:
                template = self.prompts.get('ats_scoring')
                if not template:
                    logging.error("ATS scoring template not found")
                    return None, None
                
                feedback = self.llm.generate_with_template(
                    template,
                    resume_text=resume_text,
                    job_description=job_description
                )
            
            if not feedback:
                logging.error("LLM returned no feedback for ATS analysis")
                return None, None
            
            # Extract score from feedback
            score = extract_score_from_response(feedback)
            
            if score is not None:
                logging.info(f"ATS analysis completed with score: {score}")
            else:
                logging.warning("Could not extract score from ATS feedback")
            
            return score, feedback
            
        except Exception as e:
            logging.error(f"Error in ATS score analysis: {str(e)}")
            return None, None
    
    def extract_keywords(self, job_description: str) -> Optional[str]:
        """
        Extract keywords from job description
        
        Args:
            job_description: Job description text
            
        Returns:
            Extracted keywords analysis or None if error
        """
        try:
            logging.info("Extracting keywords from job description")
            
            template = self.prompts.get('keyword_extraction')
            if not template:
                logging.error("Keyword extraction template not found")
                return None
            
            keywords = self.llm.generate_with_template(
                template,
                job_description=job_description
            )
            
            if keywords:
                logging.info("Keywords extracted successfully")
                return keywords
            else:
                logging.error("LLM returned no keywords")
                return None
                
        except Exception as e:
            logging.error(f"Error extracting keywords: {str(e)}")
            return None
    
    def identify_gaps(
        self,
        resume_text: str,
        job_description: str
    ) -> Optional[str]:
        """
        Identify gaps between resume and job requirements
        
        Args:
            resume_text: Resume content
            job_description: Job description
            
        Returns:
            Gap analysis or None if error
        """
        try:
            logging.info("Starting gap analysis")
            
            template = self.prompts.get('gap_analysis')
            if not template:
                logging.error("Gap analysis template not found")
                return None
            
            gaps = self.llm.generate_with_template(
                template,
                resume_text=resume_text,
                job_description=job_description
            )
            
            if gaps:
                logging.info("Gap analysis completed successfully")
                return gaps
            else:
                logging.error("LLM returned no gap analysis")
                return None
                
        except Exception as e:
            logging.error(f"Error in gap analysis: {str(e)}")
            return None
    
    def quick_match_check(
        self,
        resume_text: str,
        job_description: str
    ) -> Dict[str, any]:
        """
        Quick keyword matching analysis (non-LLM based)
        
        Args:
            resume_text: Resume content
            job_description: Job description
            
        Returns:
            Dict with match statistics
        """
        try:
            resume_lower = resume_text.lower()
            jd_lower = job_description.lower()
            
            # Extract common technical keywords and skills
            common_keywords = [
                'python', 'java', 'javascript', 'react', 'node', 'sql',
                'aws', 'azure', 'docker', 'kubernetes', 'git',
                'machine learning', 'data science', 'agile', 'scrum',
                'leadership', 'management', 'communication'
            ]
            
            matches = []
            missing = []
            
            for keyword in common_keywords:
                if keyword in jd_lower:
                    if keyword in resume_lower:
                        matches.append(keyword)
                    else:
                        missing.append(keyword)
            
            match_rate = len(matches) / len(matches + missing) * 100 if (matches + missing) else 0
            
            result = {
                'matched_keywords': matches,
                'missing_keywords': missing,
                'match_rate': round(match_rate, 2),
                'total_checked': len(matches + missing)
            }
            
            logging.info(f"Quick match: {match_rate:.2f}% ({len(matches)}/{len(matches + missing)})")
            return result
            
        except Exception as e:
            logging.error(f"Error in quick match check: {str(e)}")
            return {
                'matched_keywords': [],
                'missing_keywords': [],
                'match_rate': 0,
                'total_checked': 0
            }
    
    def get_score_interpretation(self, score: Optional[int]) -> Dict[str, str]:
        """
        Get interpretation and recommendations based on score
        
        Args:
            score: ATS score (0-100)
            
        Returns:
            Dict with interpretation details
        """
        if score is None:
            return {
                'category': 'Unknown',
                'interpretation': 'Unable to determine score',
                'recommendation': 'Please try analyzing again',
                'color': 'gray'
            }
        
        thresholds = self.config['scoring']
        
        if score >= thresholds['excellent_threshold']:
            return {
                'category': 'Excellent',
                'interpretation': 'Your resume is well-matched to this position',
                'recommendation': 'Consider applying with confidence. Minor tweaks may further optimize.',
                'color': 'green'
            }
        elif score >= thresholds['good_threshold']:
            return {
                'category': 'Good',
                'interpretation': 'Your resume shows good alignment with requirements',
                'recommendation': 'Apply after implementing suggested improvements for better chances.',
                'color': 'blue'
            }
        elif score >= thresholds['fair_threshold']:
            return {
                'category': 'Fair',
                'interpretation': 'Your resume partially matches the requirements',
                'recommendation': 'Significant improvements needed. Focus on addressing key gaps.',
                'color': 'orange'
            }
        else:
            return {
                'category': 'Needs Improvement',
                'interpretation': 'Your resume has limited alignment with this position',
                'recommendation': 'Consider if this role matches your background. Major revisions needed.',
                'color': 'red'
            }