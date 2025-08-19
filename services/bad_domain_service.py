import csv
import os
import re
from urllib.parse import urlparse
from typing import Tuple, Set
from config.config import BAD_EMAIL_DOMAINS

class BadDomainService:
    """
    Service for detecting bad domains from email addresses and websites
    """
    
    def __init__(self):
        """Initialize the service with bad domains from config"""
        self.bad_domains = BAD_EMAIL_DOMAINS
        print(f"✅ Loaded {len(self.bad_domains)} bad domains from config")
    
    def _load_bad_domains(self) -> Set[str]:
        """
        DEPRECATED: Load bad domains from CSV file into a set for fast lookup
        Returns set of lowercase domain names
        """
        bad_domains = set()
        
        # Try multiple potential paths for the CSV file
        potential_paths = [
            'docs/bad_domains_latest_2025_01_27.csv',  # From project root
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'bad_domains_latest_2025_01_27.csv'),  # Relative to this file
            os.path.join(os.getcwd(), 'docs', 'bad_domains_latest_2025_01_27.csv')  # From current working directory
        ]
        
        csv_path = None
        for path in potential_paths:
            if os.path.exists(path):
                csv_path = path
                break
        
        if not csv_path:
            print(f"Warning: Bad domains CSV file not found. Tried paths: {potential_paths}")
            return bad_domains
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as file:  # utf-8-sig handles BOM
                reader = csv.DictReader(file)
                for row in reader:
                    # Handle potential BOM in column name
                    domain = row.get('bad_domains', '') or row.get('\ufeffbad_domains', '')
                    domain = domain.strip().lower()
                    if domain:
                        # Clean up any extra characters or formatting
                        domain = domain.replace('\t', '').replace('"', '')
                        if domain:
                            bad_domains.add(domain)
        except FileNotFoundError:
            print(f"Warning: Bad domains CSV file not found at {csv_path}")
        except Exception as e:
            print(f"Error loading bad domains CSV: {e}")
        
        return bad_domains
    
    def _clean_domain(self, domain: str) -> str:
        """
        Clean and normalize domain to handle malformed data
        Returns the best possible domain extraction
        """
        if not domain:
            return ""
        
        domain = domain.strip().lower()
        
        # Check if domain is already in bad domains list - return as-is
        if domain in self.bad_domains:
            return domain
        
        # Handle common malformed patterns
        # Pattern 1: Known bad domain + extra characters (e.g., "gmail.comno" -> "gmail.com")
        for bad_domain in self.bad_domains:
            if domain.startswith(bad_domain) and len(domain) > len(bad_domain):
                # Check if it's just extra characters appended
                extra_chars = domain[len(bad_domain):]
                # If extra chars are just letters/numbers (not a valid TLD), treat as malformed
                if extra_chars.isalnum() and len(extra_chars) <= 4:
                    return bad_domain
        
        # Pattern 1.5: Check if domain is a subdomain of a known bad domain
        # (e.g., "test.ringcentral.com" should match "ringcentral.com")
        for bad_domain in self.bad_domains:
            if domain.endswith('.' + bad_domain):
                return bad_domain
        
        # Pattern 2: Missing common TLDs - try to extract base domain
        # ONLY for clearly malformed TLDs (not valid TLDs like .xyz, .io, etc.)
        if '.' in domain:
            parts = domain.split('.')
            if len(parts) >= 2:
                base_domain = '.'.join(parts[:-1])  # Everything except last part
                tld = parts[-1]
                
                # Only apply this pattern for clearly invalid/malformed TLDs
                # Don't convert legitimate TLDs like .xyz, .io, .co, etc.
                invalid_tlds = ['comno', 'comxyz', 'com123', 'netno', 'orgno', 'comabc']
                if tld in invalid_tlds or (tld.isalnum() and len(tld) > 4):
                    for common_tld in ['com', 'net', 'org']:
                        potential_domain = f"{base_domain}.{common_tld}"
                        if potential_domain in self.bad_domains:
                            return potential_domain
        
        # Return original domain if no patterns matched
        return domain
    
    def extract_domain_from_email(self, email: str) -> str:
        """
        Extract domain from email address
        Returns lowercase domain or empty string if invalid
        """
        if not email or not isinstance(email, str):
            return ""
        
        email = email.strip()
        if not email:
            return ""
        
        # Simple email validation and domain extraction
        if '@' in email:
            try:
                domain = email.split('@')[-1].lower()
                # Basic validation - domain should have at least one dot
                if '.' in domain:
                    return self._clean_domain(domain)
            except Exception:
                pass
        
        return ""
    
    def extract_domain_from_url(self, url: str) -> str:
        """
        Extract domain from website URL
        Returns lowercase domain or empty string if invalid
        """
        if not url or not isinstance(url, str):
            return ""
        
        url = url.strip()
        if not url:
            return ""
        
        try:
            # Add protocol if missing for proper parsing
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return self._clean_domain(domain)
        except Exception:
            return ""
    
    def check_account_for_bad_domains(self, account_data: dict) -> Tuple[bool, str]:
        """
        Check account data for bad domains in email and website
        
        Args:
            account_data: Dictionary containing account fields
            
        Returns:
            Tuple of (is_bad_domain, explanation)
        """
        bad_matches = []
        
        # Check email domain
        email = account_data.get('ContactMostFrequentEmail__c', '')
        if email:
            email_domain = self.extract_domain_from_email(email)
            if email_domain and email_domain in self.bad_domains:
                bad_matches.append(f"Email domain '{email_domain}' from ContactMostFrequentEmail__c")
        
        # Check website domain
        website = account_data.get('Website', '')
        if website:
            website_domain = self.extract_domain_from_url(website)
            if website_domain and website_domain in self.bad_domains:
                bad_matches.append(f"Website domain '{website_domain}' from Website")
        
        # Generate result
        if bad_matches:
            if len(bad_matches) == 1:
                explanation = f"{bad_matches[0]} matches bad domain list"
            else:
                explanation = f"{' and '.join(bad_matches)} both match bad domain list"
            return True, explanation
        else:
            return False, "No bad domains detected" 