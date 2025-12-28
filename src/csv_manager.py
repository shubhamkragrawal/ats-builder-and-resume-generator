"""
CSV Manager - Handle application tracking CSV operations
"""
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


class CSVManager:
    """Manager for CSV-based application tracking"""
    
    def __init__(self, csv_path: str):
        """
        Initialize CSV Manager
        
        Args:
            csv_path: Path to applications CSV file
        """
        self.csv_path = csv_path
        self.columns = [
            'company',
            'date',
            'resume_created',
            'ats_score',
            'changes_required',
            'job_description_summary',
            'notes'
        ]
        
        self._initialize_csv()
        logging.info(f"CSV Manager initialized with file: {csv_path}")
    
    def _initialize_csv(self):
        """Initialize CSV file if it doesn't exist"""
        try:
            csv_file = Path(self.csv_path)
            
            # Create directory if it doesn't exist
            csv_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create CSV with headers if it doesn't exist
            if not csv_file.exists():
                df = pd.DataFrame(columns=self.columns)
                df.to_csv(self.csv_path, index=False)
                logging.info("Created new applications CSV file")
            else:
                logging.info("Applications CSV file already exists")
                
        except Exception as e:
            logging.error(f"Error initializing CSV: {str(e)}")
    
    def add_entry(
        self,
        company: str,
        resume_created: bool,
        ats_score: Optional[int] = None,
        changes_required: Optional[str] = None,
        job_description_summary: Optional[str] = None,
        notes: Optional[str] = None
    ) -> bool:
        """
        Add a new entry to the CSV
        
        Args:
            company: Company name
            resume_created: Whether resume was created by program
            ats_score: ATS score (0-100)
            changes_required: Summary of required changes
            job_description_summary: Brief JD summary
            notes: Additional notes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create entry dict
            entry = {
                'company': company,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'resume_created': 'Yes' if resume_created else 'No',
                'ats_score': ats_score if ats_score is not None else 'N/A',
                'changes_required': changes_required or 'None specified',
                'job_description_summary': job_description_summary or 'N/A',
                'notes': notes or ''
            }
            
            # Read existing CSV
            try:
                df = pd.read_csv(self.csv_path)
            except pd.errors.EmptyDataError:
                df = pd.DataFrame(columns=self.columns)
            
            # Append new entry
            df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
            
            # Save to CSV
            df.to_csv(self.csv_path, index=False)
            
            logging.info(f"Added entry for company: {company}")
            return True
            
        except Exception as e:
            logging.error(f"Error adding CSV entry: {str(e)}")
            return False
    
    def get_all_entries(self) -> Optional[pd.DataFrame]:
        """
        Get all entries from CSV
        
        Returns:
            DataFrame with all entries or None if error
        """
        try:
            df = pd.read_csv(self.csv_path)
            logging.info(f"Retrieved {len(df)} entries from CSV")
            return df
            
        except pd.errors.EmptyDataError:
            logging.warning("CSV file is empty")
            return pd.DataFrame(columns=self.columns)
        except Exception as e:
            logging.error(f"Error reading CSV: {str(e)}")
            return None
    
    def get_entries_by_company(self, company: str) -> Optional[pd.DataFrame]:
        """
        Get entries for a specific company
        
        Args:
            company: Company name
            
        Returns:
            DataFrame with matching entries or None if error
        """
        try:
            df = pd.read_csv(self.csv_path)
            filtered = df[df['company'].str.lower() == company.lower()]
            
            logging.info(f"Found {len(filtered)} entries for company: {company}")
            return filtered
            
        except Exception as e:
            logging.error(f"Error filtering by company: {str(e)}")
            return None
    
    def get_recent_entries(self, n: int = 10) -> Optional[pd.DataFrame]:
        """
        Get most recent n entries
        
        Args:
            n: Number of entries to retrieve
            
        Returns:
            DataFrame with recent entries or None if error
        """
        try:
            df = pd.read_csv(self.csv_path)
            
            # Sort by date descending
            df['date'] = pd.to_datetime(df['date'])
            df_sorted = df.sort_values('date', ascending=False)
            
            recent = df_sorted.head(n)
            logging.info(f"Retrieved {len(recent)} recent entries")
            return recent
            
        except Exception as e:
            logging.error(f"Error getting recent entries: {str(e)}")
            return None
    
    def get_statistics(self) -> Optional[Dict]:
        """
        Get statistics from applications
        
        Returns:
            Dict with statistics or None if error
        """
        try:
            df = pd.read_csv(self.csv_path)
            
            if len(df) == 0:
                return {
                    'total_applications': 0,
                    'resumes_created': 0,
                    'average_score': 0,
                    'highest_score': 0,
                    'lowest_score': 0,
                    'companies': []
                }
            
            # Calculate statistics
            stats = {
                'total_applications': len(df),
                'resumes_created': len(df[df['resume_created'] == 'Yes']),
                'companies': df['company'].unique().tolist()
            }
            
            # Score statistics (only for numeric scores)
            scores = pd.to_numeric(df['ats_score'], errors='coerce').dropna()
            if len(scores) > 0:
                stats['average_score'] = round(scores.mean(), 2)
                stats['highest_score'] = int(scores.max())
                stats['lowest_score'] = int(scores.min())
            else:
                stats['average_score'] = 0
                stats['highest_score'] = 0
                stats['lowest_score'] = 0
            
            logging.info("Generated application statistics")
            return stats
            
        except Exception as e:
            logging.error(f"Error calculating statistics: {str(e)}")
            return None
    
    def update_entry(
        self,
        company: str,
        date: str,
        updates: Dict
    ) -> bool:
        """
        Update an existing entry
        
        Args:
            company: Company name
            date: Entry date
            updates: Dict of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            df = pd.read_csv(self.csv_path)
            
            # Find matching entry
            mask = (df['company'] == company) & (df['date'] == date)
            
            if not mask.any():
                logging.warning(f"No entry found for {company} on {date}")
                return False
            
            # Update fields
            for key, value in updates.items():
                if key in df.columns:
                    df.loc[mask, key] = value
            
            # Save
            df.to_csv(self.csv_path, index=False)
            
            logging.info(f"Updated entry for {company} on {date}")
            return True
            
        except Exception as e:
            logging.error(f"Error updating entry: {str(e)}")
            return False
    
    def delete_entry(self, company: str, date: str) -> bool:
        """
        Delete an entry
        
        Args:
            company: Company name
            date: Entry date
            
        Returns:
            True if successful, False otherwise
        """
        try:
            df = pd.read_csv(self.csv_path)
            
            # Remove matching entries
            df = df[~((df['company'] == company) & (df['date'] == date))]
            
            # Save
            df.to_csv(self.csv_path, index=False)
            
            logging.info(f"Deleted entry for {company} on {date}")
            return True
            
        except Exception as e:
            logging.error(f"Error deleting entry: {str(e)}")
            return False
    
    def export_to_excel(self, output_path: str) -> bool:
        """
        Export CSV to Excel format
        
        Args:
            output_path: Path for Excel file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            df = pd.read_csv(self.csv_path)
            df.to_excel(output_path, index=False)
            
            logging.info(f"Exported to Excel: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting to Excel: {str(e)}")
            return False