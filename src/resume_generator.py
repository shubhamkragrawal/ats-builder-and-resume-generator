"""
Resume Generator - Create tailored resumes based on job descriptions
"""
import logging
from typing import Dict, Optional
from src.llm_handler import LLMHandler


class ResumeGenerator:
    """Generator for creating tailored resumes"""
    
    def __init__(self, llm_handler: LLMHandler, prompts: Dict):
        """
        Initialize Resume Generator
        
        Args:
            llm_handler: LLM handler instance
            prompts: Prompt templates
        """
        self.llm = llm_handler
        self.prompts = prompts
        logging.info("Resume Generator initialized")
    
    def generate_tailored_resume(
        self,
        base_resume: str,
        job_description: str,
        background: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a tailored resume based on base resume and JD
        
        Args:
            base_resume: Base/master resume content
            job_description: Target job description
            background: Optional candidate background for context
            
        Returns:
            Generated tailored resume or None if error
        """
        try:
            logging.info("Starting tailored resume generation")
            
            # Validate inputs
            if not base_resume or not base_resume.strip():
                logging.error("Base resume is empty")
                return None
            
            if not job_description or not job_description.strip():
                logging.error("Job description is empty")
                return None
            
            # Choose template based on whether background is provided
            if background and background.strip():
                template = self.prompts.get('resume_generation_with_background')
                if not template:
                    logging.warning("Background template not found, using standard")
                    template = self.prompts.get('resume_generation')
                
                generated_resume = self.llm.generate_with_template(
                    template,
                    base_resume=base_resume,
                    job_description=job_description,
                    background=background
                )
            else:
                template = self.prompts.get('resume_generation')
                if not template:
                    logging.error("Resume generation template not found")
                    return None
                
                generated_resume = self.llm.generate_with_template(
                    template,
                    base_resume=base_resume,
                    job_description=job_description
                )
            
            if generated_resume:
                logging.info("Resume generation completed successfully")
                logging.debug(f"Generated resume length: {len(generated_resume)} characters")
                return generated_resume
            else:
                logging.error("LLM returned no generated resume")
                return None
                
        except Exception as e:
            logging.error(f"Error generating tailored resume: {str(e)}")
            return None
    
    def identify_missing_qualifications(
        self,
        base_resume: str,
        job_description: str
    ) -> Optional[str]:
        """
        Identify what's missing from base resume for the job
        
        Args:
            base_resume: Base resume content
            job_description: Job description
            
        Returns:
            Analysis of missing qualifications or None if error
        """
        try:
            logging.info("Identifying missing qualifications")
            
            template = self.prompts.get('gap_analysis')
            if not template:
                logging.error("Gap analysis template not found")
                return None
            
            gap_analysis = self.llm.generate_with_template(
                template,
                resume_text=base_resume,
                job_description=job_description
            )
            
            if gap_analysis:
                logging.info("Gap identification completed")
                return gap_analysis
            else:
                logging.error("LLM returned no gap analysis")
                return None
                
        except Exception as e:
            logging.error(f"Error identifying gaps: {str(e)}")
            return None
    
    def suggest_improvements(
        self,
        resume_text: str,
        job_description: str,
        background: Optional[str] = None
    ) -> Optional[str]:
        """
        Suggest specific improvements to align resume with JD
        
        Args:
            resume_text: Current resume
            job_description: Target job description
            background: Optional background context
            
        Returns:
            Improvement suggestions or None if error
        """
        try:
            logging.info("Generating improvement suggestions")
            
            # Use ATS scoring template to get suggestions
            if background:
                template = self.prompts.get('ats_scoring_with_background')
                if not template:
                    template = self.prompts.get('ats_scoring')
                
                suggestions = self.llm.generate_with_template(
                    template,
                    resume_text=resume_text,
                    job_description=job_description,
                    background=background
                )
            else:
                template = self.prompts.get('ats_scoring')
                if not template:
                    logging.error("ATS scoring template not found")
                    return None
                
                suggestions = self.llm.generate_with_template(
                    template,
                    resume_text=resume_text,
                    job_description=job_description
                )
            
            if suggestions:
                logging.info("Improvement suggestions generated")
                return suggestions
            else:
                logging.error("LLM returned no suggestions")
                return None
                
        except Exception as e:
            logging.error(f"Error generating suggestions: {str(e)}")
            return None
    
    def optimize_for_ats(self, resume_text: str) -> Optional[str]:
        """
        Optimize resume for general ATS compatibility
        
        Args:
            resume_text: Resume content
            
        Returns:
            ATS optimization suggestions or None if error
        """
        try:
            logging.info("Generating ATS optimization tips")
            
            template = self.prompts.get('resume_review')
            if not template:
                logging.error("Resume review template not found")
                return None
            
            optimization = self.llm.generate_with_template(
                template,
                resume_text=resume_text
            )
            
            if optimization:
                logging.info("ATS optimization completed")
                return optimization
            else:
                logging.error("LLM returned no optimization")
                return None
                
        except Exception as e:
            logging.error(f"Error optimizing for ATS: {str(e)}")
            return None
    
    def format_resume(self, resume_text: str) -> str:
        """
        Basic formatting cleanup for resume text
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Formatted resume text
        """
        try:
            # Remove excessive whitespace
            lines = [line.strip() for line in resume_text.split('\n')]
            
            # Remove empty lines but preserve section breaks
            formatted_lines = []
            prev_empty = False
            
            for line in lines:
                if line:
                    formatted_lines.append(line)
                    prev_empty = False
                elif not prev_empty:
                    formatted_lines.append('')
                    prev_empty = True
            
            formatted = '\n'.join(formatted_lines)
            
            logging.info("Resume formatting completed")
            return formatted
            
        except Exception as e:
            logging.error(f"Error formatting resume: {str(e)}")
            return resume_text
    
    def validate_generated_resume(self, generated_resume: str, base_resume: str) -> Dict:
        """
        Validate that generated resume maintains integrity
        
        Args:
            generated_resume: Generated resume
            base_resume: Original base resume
            
        Returns:
            Validation results dict
        """
        try:
            validation = {
                'is_valid': True,
                'has_content': len(generated_resume.strip()) > 100,
                'is_different': generated_resume != base_resume,
                'length_reasonable': 500 < len(generated_resume) < 10000,
                'issues': []
            }
            
            if not validation['has_content']:
                validation['issues'].append("Generated resume is too short")
                validation['is_valid'] = False
            
            if not validation['is_different']:
                validation['issues'].append("Generated resume is identical to base")
                validation['is_valid'] = False
            
            if not validation['length_reasonable']:
                validation['issues'].append("Generated resume length is unusual")
                validation['is_valid'] = False
            
            logging.info(f"Resume validation: {'PASS' if validation['is_valid'] else 'FAIL'}")
            return validation
            
        except Exception as e:
            logging.error(f"Error validating resume: {str(e)}")
            return {
                'is_valid': False,
                'issues': [f"Validation error: {str(e)}"]
            }