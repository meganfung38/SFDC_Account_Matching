from urllib.parse import urlparse
import re
from difflib import SequenceMatcher
from typing import Optional, Tuple, List, Dict


class FuzzyMatchingService:
    """Service for fuzzy matching operations used in dual-file account matching"""
    
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
        """Normalize company name for comparison (with legal suffix handling)"""
        if not name:
            return ""
            
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common business suffixes (legal suffix handling)
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
        
        # Remove special characters and extra spaces (de-noising)
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
    
    # NEW MATCHING ALGORITHM METHODS FOR DUAL-FILE SYSTEM
    
    def compute_website_match(self, customer_website: str, shell_zi_website: str) -> Tuple[float, str]:
        """
        Compute Website_Match score between customer Website and shell ZI_Website__c
        Returns (score_0_to_100, explanation)
        """
        if not customer_website:
            return 0.0, "No customer website provided"
            
        if not shell_zi_website:
            return 0.0, "No shell ZI website provided"
        
        # Extract domains from both websites
        customer_domain = self.extract_domain_from_url(customer_website)
        shell_domain = self.extract_domain_from_url(shell_zi_website)
        
        if not customer_domain:
            return 0.0, f"Could not extract valid domain from customer website: {customer_website}"
        
        if not shell_domain:
            return 0.0, f"Could not extract valid domain from shell ZI website: {shell_zi_website}"
        
        # Extract company names from domains
        customer_domain_company = self.extract_company_name_from_domain(customer_domain)
        shell_domain_company = self.extract_company_name_from_domain(shell_domain)
        
        if not customer_domain_company:
            return 0.0, f"Could not extract company name from customer domain: {customer_domain}"
        
        if not shell_domain_company:
            return 0.0, f"Could not extract company name from shell domain: {shell_domain}"
        
        # Compute similarity between domain-derived company names
        similarity = self.compute_fuzzy_similarity(customer_domain_company, shell_domain_company)
        score = similarity * 100
        
        explanation = f"Comparing customer domain '{customer_domain}' with shell ZI domain '{shell_domain}' (similarity: {score:.1f}%)"
        
        return score, explanation
    
    def compute_name_match(self, customer_name: str, shell_zi_name: str) -> Tuple[float, str]:
        """
        Compute Name_Match score between customer Name and shell ZI_Company_Name__c
        Returns (score_0_to_100, explanation)
        """
        if not customer_name:
            return 0.0, "No customer name provided"
            
        if not shell_zi_name:
            return 0.0, "No shell ZI company name provided"
        
        # Compute similarity between normalized names
        similarity = self.compute_fuzzy_similarity(customer_name, shell_zi_name)
        score = similarity * 100
        
        # Create explanation with normalized names for transparency
        customer_normalized = self.normalize_company_name(customer_name)
        shell_normalized = self.normalize_company_name(shell_zi_name)
        
        explanation = f"Comparing customer name '{customer_normalized}' with shell ZI name '{shell_normalized}' (similarity: {score:.1f}%)"
        
        return score, explanation
    
    def compute_address_consistency_score(self, customer_data: dict, shell_data: dict) -> Tuple[float, str]:
        """
        Compute Address_Consistency score using project breakdown scoring:
        Country match (+30), State match (+30), City match (+30), Postal code match (+10)
        Returns (score_0_to_100, explanation)
        """
        if not customer_data or not shell_data:
            return 0.0, "Missing customer or shell address data"
        
        score = 0.0
        matches = []
        mismatches = []
        
        # Country match (+30 points)
        customer_country = customer_data.get('BillingCountry', '').strip().lower()
        shell_country = shell_data.get('ZI_Company_Country__c', '').strip().lower()
        
        if customer_country and shell_country:
            if customer_country == shell_country:
                score += 30
                matches.append(f"Country: {customer_country}")
            else:
                mismatches.append(f"Country: {customer_country} ≠ {shell_country}")
        
        # State match (+30 points)
        customer_state = customer_data.get('BillingState', '').strip().lower()
        shell_state = shell_data.get('ZI_Company_State__c', '').strip().lower()
        
        if customer_state and shell_state:
            if customer_state == shell_state:
                score += 30
                matches.append(f"State: {customer_state}")
            else:
                mismatches.append(f"State: {customer_state} ≠ {shell_state}")
        
        # City match (+30 points)
        customer_city = customer_data.get('BillingCity', '').strip().lower()
        shell_city = shell_data.get('ZI_Company_City__c', '').strip().lower()
        
        if customer_city and shell_city:
            if customer_city == shell_city:
                score += 30
                matches.append(f"City: {customer_city}")
            else:
                mismatches.append(f"City: {customer_city} ≠ {shell_city}")
        
        # Postal code match (+10 points)
        customer_postal = customer_data.get('BillingPostalCode', '').strip().lower()
        shell_postal = shell_data.get('ZI_Company_Postal_Code__c', '').strip().lower()
        
        if customer_postal and shell_postal:
            if customer_postal == shell_postal:
                score += 10
                matches.append(f"Postal: {customer_postal}")
        else:
                mismatches.append(f"Postal: {customer_postal} ≠ {shell_postal}")
        
        # Create explanation
        explanation_parts = []
        if matches:
            explanation_parts.append(f"Matches: {', '.join(matches)}")
        if mismatches:
            explanation_parts.append(f"Mismatches: {', '.join(mismatches)}")
        
        explanation = '; '.join(explanation_parts) if explanation_parts else "No address data to compare"
        
        return score, explanation
    
    # CORE MATCHING ALGORITHM - TWO STAGE RETRIEVAL
    
    def create_hash_buckets(self, shell_accounts: List[dict]) -> Dict[str, List[dict]]:
        """
        Create hash buckets for fast filtering by website/name
        Returns dict mapping hash keys to lists of shell accounts
        """
        website_buckets = {}
        name_buckets = {}
        
        for shell in shell_accounts:
            shell_id = shell.get('Id', '')
            
            # Website hash bucket
            zi_website = shell.get('ZI_Website__c', '')
            if zi_website:
                domain = self.extract_domain_from_url(zi_website)
                if domain:
                    domain_company = self.extract_company_name_from_domain(domain)
                    if domain_company:
                        if domain_company not in website_buckets:
                            website_buckets[domain_company] = []
                        website_buckets[domain_company].append(shell)
            
            # Name hash bucket
            zi_name = shell.get('ZI_Company_Name__c', '')
            if zi_name:
                normalized_name = self.normalize_company_name(zi_name)
                if normalized_name:
                    # Create multiple hash keys from name tokens
                    name_tokens = normalized_name.split()
                    for token in name_tokens:
                        if len(token) > 2:  # Skip very short tokens
                            if token not in name_buckets:
                                name_buckets[token] = []
                            name_buckets[token].append(shell)
        
        return {
            'website_buckets': website_buckets,
            'name_buckets': name_buckets
        }
    
    def fast_filter_candidates(self, customer: dict, hash_buckets: Dict[str, Dict[str, List[dict]]]) -> List[dict]:
        """
        Fast filter stage: Use hash buckets to quickly identify potential shell candidates
        Data precedence: Website > Account Name for entity identity
        """
        candidates = set()
        website_buckets = hash_buckets['website_buckets']
        name_buckets = hash_buckets['name_buckets']
        
        # STEP 1: Website-based filtering (highest precedence)
        customer_website = customer.get('Website', '')
        if customer_website:
            domain = self.extract_domain_from_url(customer_website)
            if domain:
                domain_company = self.extract_company_name_from_domain(domain)
                if domain_company and domain_company in website_buckets:
                    for shell in website_buckets[domain_company]:
                        candidates.add(shell['Id'])
        
        # STEP 2: Name-based filtering (if website filtering yielded few results)
        customer_name = customer.get('Name', '')
        if customer_name and len(candidates) < 10:  # Threshold for adding name-based candidates
            normalized_name = self.normalize_company_name(customer_name)
            if normalized_name:
                name_tokens = normalized_name.split()
                for token in name_tokens:
                    if len(token) > 2 and token in name_buckets:
                        for shell in name_buckets[token]:
                            candidates.add(shell['Id'])
        
        # Convert candidate IDs back to shell account objects
        candidate_shells = []
        candidate_id_set = {shell['Id'] for shell in hash_buckets['website_buckets'].get('', []) + 
                           sum(hash_buckets['name_buckets'].values(), [])}
        
        # Get shell objects for candidates
        all_shells = []
        for bucket_list in website_buckets.values():
            all_shells.extend(bucket_list)
        for bucket_list in name_buckets.values():
            all_shells.extend(bucket_list)
        
        # Deduplicate and filter
        seen_ids = set()
        for shell in all_shells:
            if shell['Id'] in candidates and shell['Id'] not in seen_ids:
                candidate_shells.append(shell)
                seen_ids.add(shell['Id'])
        
        return candidate_shells
    
    def compute_overall_similarity(self, customer: dict, shell: dict) -> Dict[str, float]:
        """
        Compute overall similarity scores for re-ranking stage
        Returns dict with individual signal scores and overall score
        """
        # Compute individual signals
        website_score, website_explanation = self.compute_website_match(
            customer.get('Website', ''), 
            shell.get('ZI_Website__c', '')
        )
        
        name_score, name_explanation = self.compute_name_match(
            customer.get('Name', ''), 
            shell.get('ZI_Company_Name__c', '')
        )
        
        address_score, address_explanation = self.compute_address_consistency_score(
            customer, shell
        )
        
        # Data precedence: Website > Account Name for entity identity
        # If website and name conflict, website wins
        primary_score = 0.0
        if customer.get('Website') and shell.get('ZI_Website__c'):
            primary_score = website_score * 0.6  # Website gets higher weight when available
            secondary_score = name_score * 0.3
        elif customer.get('Name') and shell.get('ZI_Company_Name__c'):
            # Fall back to name match if no website
            primary_score = name_score * 0.6
            secondary_score = 0.0
        else:
            # If both website and name null, use address signals
            primary_score = address_score * 0.6 / 100  # Address score is 0-100, normalize to 0-1
            secondary_score = 0.0
        
        # Address consistency always contributes
        geo_score = address_score * 0.1 / 100  # Normalize and weight
        
        # Overall score combines all signals
        overall_score = primary_score + secondary_score + geo_score
        
        return {
            'website_match': website_score,
            'name_match': name_score,
            'address_consistency': address_score,
            'overall_score': min(overall_score, 100.0),  # Cap at 100
            'explanations': {
                'website': website_explanation,
                'name': name_explanation,
                'address': address_explanation
            }
        }
    
    def rank_shell_candidates(self, customer: dict, candidates: List[dict]) -> List[Dict]:
        """
        Re-rank candidates with richer similarity computation
        Returns list of candidates ranked by overall similarity score
        """
        scored_candidates = []
        
        for shell in candidates:
            similarity_data = self.compute_overall_similarity(customer, shell)
            
            candidate_result = {
                'shell_account': shell,
                'scores': similarity_data,
                'rank_score': similarity_data['overall_score']
            }
            scored_candidates.append(candidate_result)
        
        # Sort by rank score (descending)
        scored_candidates.sort(key=lambda x: x['rank_score'], reverse=True)
        
        return scored_candidates
    
    def find_best_shell_match(self, customer: dict, shell_accounts: List[dict]) -> Dict:
        """
        Main method: Find the best shell match for a customer account using two-stage retrieval
        Returns best match with scores and explanations
        """
        if not shell_accounts:
            return {
                'success': False,
                'message': 'No shell accounts provided',
                'best_match': None
            }
        
        # STAGE 1: Fast filter by website/name hash buckets
        hash_buckets = self.create_hash_buckets(shell_accounts)
        candidates = self.fast_filter_candidates(customer, hash_buckets)
        
        # If fast filter found no candidates, fall back to all shells
        if not candidates:
            candidates = shell_accounts
        
        # STAGE 2: Re-rank with richer similarity
        ranked_candidates = self.rank_shell_candidates(customer, candidates)
        
        if not ranked_candidates:
            return {
                'success': False,
                'message': 'No viable shell candidates found',
                'best_match': None
            }
        
        # Return best match
        best_candidate = ranked_candidates[0]
        
        return {
            'success': True,
            'message': f'Found best match with {best_candidate["rank_score"]:.1f}% confidence',
            'best_match': {
                'shell_id': best_candidate['shell_account']['Id'],
                'shell_account': best_candidate['shell_account'],
                'confidence_score': best_candidate['rank_score'],
                'website_match': best_candidate['scores']['website_match'],
                'name_match': best_candidate['scores']['name_match'],
                'address_consistency': best_candidate['scores']['address_consistency'],
                'explanations': best_candidate['scores']['explanations']
            },
            'candidate_count': len(candidates),
            'total_shells': len(shell_accounts)
        } 