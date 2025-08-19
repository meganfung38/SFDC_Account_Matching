from urllib.parse import urlparse
import re
from difflib import SequenceMatcher
from typing import Optional, Tuple


class FuzzyMatchingService:
    """Service for fuzzy matching operations used in account relationship assessment"""
    
    def __init__(self):
        # Common domain prefixes and suffixes to normalize
        self.domain_prefixes = ['www.', 'app.', 'portal.', 'my.', 'secure.', 'admin.']
        self.domain_suffixes = ['.com', '.org', '.net', '.edu', '.gov', '.co', '.io', '.ai']
        
    def extract_domain_from_url(self, url: str) -> Optional[str]:
        """Extract clean domain name from URL"""
        if not url:
            return None
            
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes
            for prefix in self.domain_prefixes:
                if domain.startswith(prefix):
                    domain = domain[len(prefix):]
                    break
                    
            return domain
        except Exception:
            return None
    
    def extract_company_name_from_domain(self, domain: str) -> Optional[str]:
        """Extract company name from domain (remove TLD and common patterns)"""
        if not domain:
            return None
            
        # Remove TLD
        for suffix in self.domain_suffixes:
            if domain.endswith(suffix):
                domain = domain[:-len(suffix)]
                break
        
        # Remove common patterns
        domain = re.sub(r'[^a-zA-Z0-9]', '', domain)  # Remove special chars
        return domain.lower() if domain else None
    
    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for comparison"""
        if not name:
            return ""
            
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common business suffixes
        business_suffixes = [
            'inc', 'incorporated', 'corp', 'corporation', 'ltd', 'limited', 
            'llc', 'llp', 'company', 'co', 'group', 'holdings', 'enterprises'
        ]
        
        for suffix in business_suffixes:
            # Remove suffix with various separators
            patterns = [f' {suffix}', f'.{suffix}', f',{suffix}', f'-{suffix}']
            for pattern in patterns:
                if normalized.endswith(pattern):
                    normalized = normalized[:-len(pattern)]
                    break
        
        # Remove special characters and extra spaces
        normalized = re.sub(r'[^a-zA-Z0-9\s]', ' ', normalized)
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        return normalized
    
    def compute_fuzzy_similarity(self, str1: str, str2: str) -> float:
        """Compute fuzzy similarity between two strings (0.0 to 1.0)"""
        if not str1 or not str2:
            return 0.0
            
        # Normalize both strings
        norm1 = self.normalize_company_name(str1)
        norm2 = self.normalize_company_name(str2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Use SequenceMatcher for fuzzy comparison
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity
    
    def compute_name_website_consistency(self, name: str, website: str) -> Tuple[float, str]:
        """
        Compute consistency score between company name and website
        Returns (score_0_to_100, explanation)
        """
        if not name:
            return 0.0, "No company name provided"
            
        if not website:
            return 0.0, "No website provided"
        
        # Extract domain and company name from domain
        domain = self.extract_domain_from_url(website)
        if not domain:
            return 0.0, f"Could not extract valid domain from website: {website}"
        
        domain_company = self.extract_company_name_from_domain(domain)
        if not domain_company:
            return 0.0, f"Could not extract company name from domain: {domain}"
        
        # Compute similarity
        similarity = self.compute_fuzzy_similarity(name, domain_company)
        score = similarity * 100
        
        explanation = f"Comparing '{self.normalize_company_name(name)}' with domain '{domain_company}' from {domain}"
        
        return score, explanation
    
    def compute_name_zi_consistency(self, name: str, zi_company: str, zi_website: str) -> Tuple[float, str]:
        """
        Compute consistency between name and ZoomInfo fields when website is missing
        Returns (score_0_to_100, explanation)
        """
        if not name:
            return 0.0, "No company name provided"
        
        scores = []
        explanations = []
        
        # Compare with ZI Company Name
        if zi_company:
            zi_similarity = self.compute_fuzzy_similarity(name, zi_company)
            scores.append(zi_similarity)
            explanations.append(f"Name vs ZI Company: {zi_similarity:.2f}")
        
        # Compare with ZI Website
        if zi_website:
            zi_website_score, zi_website_explanation = self.compute_name_website_consistency(name, zi_website)
            scores.append(zi_website_score / 100)  # Convert back to 0-1 scale
            explanations.append(f"Name vs ZI Website: {zi_website_score:.1f}")
        
        if not scores:
            return 0.0, "No ZoomInfo data available for comparison"
        
        # Take the maximum score from available comparisons
        best_score = max(scores) * 100
        explanation = f"Best match from ZI fields: {'; '.join(explanations)}"
        
        return best_score, explanation
    
    def compute_customer_consistency_score(self, name: str, website: str, zi_company: str, zi_website: str) -> Tuple[float, str]:
        """
        Main method to compute Customer_Consistency flag
        Returns (score_0_to_100, explanation)
        """
        # First try name vs website
        if website:
            score, explanation = self.compute_name_website_consistency(name, website)
            return score, f"Using Website: {explanation}"
        
        # Fall back to ZI fields if no website
        score, explanation = self.compute_name_zi_consistency(name, zi_company, zi_website)
        return score, f"Using ZI fields: {explanation}"
    
    def get_best_field_value_with_source(self, primary_field: str, fallback_field: str, primary_name: str, fallback_name: str) -> Tuple[str, str]:
        """Get the best available value for a field, using fallback if primary is missing
        Returns (value, source_field_name)"""
        if primary_field and primary_field.strip():
            return primary_field.strip(), primary_name
        elif fallback_field and fallback_field.strip():
            return fallback_field.strip(), fallback_name
        else:
            return "", ""
    
    def get_best_field_value(self, primary_field: str, fallback_field: str, field_type: str) -> str:
        """Get the best available value for a field, using fallback if primary is missing"""
        if primary_field and primary_field.strip():
            return primary_field.strip()
        elif fallback_field and fallback_field.strip():
            return fallback_field.strip()
        else:
            return ""
    
    def compute_customer_shell_coherence_score(self, customer_data: dict, shell_data: dict) -> Tuple[float, str]:
        """
        Compute Customer_Shell_Coherence flag - compare customer account with shell account metadata
        Returns (score_0_to_100, explanation)
        """
        if not shell_data:
            return 0.0, "No shell account data available"
        
        # Get best available values for customer with source tracking
        customer_name, customer_name_source = self.get_best_field_value_with_source(
            customer_data.get('Name', ''), 
            customer_data.get('ZI_Company_Name__c', ''),
            'Name', 'ZI_Company_Name__c'
        )
        customer_website, customer_website_source = self.get_best_field_value_with_source(
            customer_data.get('Website', ''), 
            customer_data.get('ZI_Website__c', ''),
            'Website', 'ZI_Website__c'
        )
        
        # Get best available values for shell with source tracking
        shell_name, shell_name_source = self.get_best_field_value_with_source(
            shell_data.get('Name', ''), 
            shell_data.get('ZI_Company_Name__c', ''),
            'Name', 'ZI_Company_Name__c'
        )
        shell_website, shell_website_source = self.get_best_field_value_with_source(
            shell_data.get('Website', ''), 
            shell_data.get('ZI_Website__c', ''),
            'Website', 'ZI_Website__c'
        )
        
        scores = []
        explanations = []
        
        # Direct comparisons with field values
        if customer_name and shell_name:
            name_similarity = self.compute_fuzzy_similarity(customer_name, shell_name)
            scores.append(name_similarity)
            explanations.append(f"Comparing Customer {customer_name_source}: '{customer_name}' with Shell {shell_name_source}: '{shell_name}' (similarity: {name_similarity * 100:.1f}%)")
        
        if customer_website and shell_website:
            # Compare website domains directly
            customer_domain = self.extract_domain_from_url(customer_website)
            shell_domain = self.extract_domain_from_url(shell_website)
            if customer_domain and shell_domain:
                customer_domain_company = self.extract_company_name_from_domain(customer_domain)
                shell_domain_company = self.extract_company_name_from_domain(shell_domain)
                if customer_domain_company and shell_domain_company:
                    website_similarity = self.compute_fuzzy_similarity(customer_domain_company, shell_domain_company)
                    scores.append(website_similarity)
                    explanations.append(f"Comparing Customer {customer_website_source}: '{customer_website}' with Shell {shell_website_source}: '{shell_website}' (similarity: {website_similarity * 100:.1f}%)")
        
        # Cross comparisons with field values
        if customer_name and shell_website:
            cross_score_1, cross_explanation_1 = self.compute_name_website_consistency(customer_name, shell_website)
            if cross_score_1 > 0:
                scores.append(cross_score_1 / 100)  # Convert to 0-1 scale for scoring
                explanations.append(f"Comparing Customer {customer_name_source}: '{customer_name}' with Shell {shell_website_source}: '{shell_website}' (similarity: {cross_score_1:.1f}%)")
        
        if customer_website and shell_name:
            # Extract domain from customer website and compare with shell name
            customer_domain = self.extract_domain_from_url(customer_website)
            if customer_domain:
                customer_domain_company = self.extract_company_name_from_domain(customer_domain)
                if customer_domain_company:
                    cross_similarity = self.compute_fuzzy_similarity(shell_name, customer_domain_company)
                    scores.append(cross_similarity)
                    explanations.append(f"Comparing Customer {customer_website_source}: '{customer_website}' with Shell {shell_name_source}: '{shell_name}' (similarity: {cross_similarity * 100:.1f}%)")
        
        if not scores:
            return 0.0, "Insufficient data for shell coherence comparison"
        
        # Comprehensive scoring: take weighted average with higher weight on direct comparisons
        direct_scores = scores[:2] if len(scores) >= 2 else scores
        cross_scores = scores[2:] if len(scores) > 2 else []
        
        if direct_scores and cross_scores:
            # Weight direct comparisons more heavily (70%) than cross comparisons (30%)
            avg_direct = sum(direct_scores) / len(direct_scores)
            avg_cross = sum(cross_scores) / len(cross_scores)
            final_score = (avg_direct * 0.7) + (avg_cross * 0.3)
        elif direct_scores:
            final_score = sum(direct_scores) / len(direct_scores)
        else:
            final_score = sum(cross_scores) / len(cross_scores)
        
        final_score_100 = final_score * 100
        explanation = "\n    ".join(explanations)
        
        return final_score_100, explanation
    
    def compute_address_consistency(self, customer_data: dict, shell_data: dict) -> Tuple[bool, str]:
        """
        Compute Address_Consistency flag - compare billing addresses using precedence:
        Customer Billing_Address vs Parent ZI_Billing_Address
        If no Customer Billing_Address, use Customer ZI_Billing_Address
        If no Parent ZI_Billing_Address, use Parent Billing_Address
        Returns (boolean, explanation)
        """
        if not shell_data:
            return False, "No shell account data available"
        
        # Helper function to format address from individual fields
        def format_address_from_fields(data, field_prefix):
            if field_prefix == "Billing":
                state_field = 'BillingState'
                country_field = 'BillingCountry'
                postal_field = 'BillingPostalCode'
            else:  # ZI fields
                state_field = 'ZI_Company_State__c'
                country_field = 'ZI_Company_Country__c'
                postal_field = 'ZI_Company_Postal_Code__c'
            
            parts = []
            if data.get(state_field):
                parts.append(data[state_field])
            if data.get(country_field):
                parts.append(data[country_field])
            if data.get(postal_field):
                parts.append(data[postal_field])
            
            return ', '.join(parts) if parts else None
        
        # Helper function to check if address fields exist
        def has_address_data(data, field_prefix):
            if field_prefix == "Billing":
                return any(data.get(field) for field in ['BillingState', 'BillingCountry', 'BillingPostalCode'])
            else:  # ZI fields
                return any(data.get(field) for field in ['ZI_Company_State__c', 'ZI_Company_Country__c', 'ZI_Company_Postal_Code__c'])
        
        # Determine which customer address to use (precedence: Billing first, then ZI)
        if has_address_data(customer_data, "Billing"):
            customer_address = format_address_from_fields(customer_data, "Billing")
            customer_source = "Customer Billing_Address"
        elif has_address_data(customer_data, "ZI"):
            customer_address = format_address_from_fields(customer_data, "ZI")
            customer_source = "Customer ZI_Billing_Address"
        else:
            customer_address = None
            customer_source = None
        
        # Determine which parent address to use (precedence: ZI first, then Billing)
        if has_address_data(shell_data, "ZI"):
            parent_address = format_address_from_fields(shell_data, "ZI")
            parent_source = "Parent ZI_Billing_Address"
        elif has_address_data(shell_data, "Billing"):
            parent_address = format_address_from_fields(shell_data, "Billing")
            parent_source = "Parent Billing_Address"
        else:
            parent_address = None
            parent_source = None
        
        # Check if we have data to compare
        if not customer_address or not parent_address:
            missing_sources = []
            if not customer_address:
                missing_sources.append("customer address data")
            if not parent_address:
                missing_sources.append("parent address data")
            return False, f"No address comparison possible - missing: {', '.join(missing_sources)}"
        
        # Compare addresses
        customer_normalized = customer_address.lower().strip()
        parent_normalized = parent_address.lower().strip()
        
        is_consistent = customer_normalized == parent_normalized
        
        # Create explanation showing which fields were compared
        comparison_text = f"Comparing {customer_source}: '{customer_address}' with {parent_source}: '{parent_address}'"
        
        if is_consistent:
            explanation = f"Address match: {comparison_text}"
        else:
            explanation = f"Address differences: {comparison_text}"
        
        return is_consistent, explanation 