from simple_salesforce.api import Salesforce
from config.config import Config
from services.fuzzy_matching_service import FuzzyMatchingService
from services.bad_domain_service import BadDomainService
from services.openai_service import ask_openai, client, get_system_prompt
from typing import Optional, Dict, Any
import json
import time


class SalesforceService:
    """Service class for handling Salesforce operations"""
    
    def __init__(self):
        self.sf: Optional[Salesforce] = None
        self._is_connected = False
        self.fuzzy_matcher = FuzzyMatchingService()
        self._last_connection_time = 0
        self._connection_timeout = 3600  # 1 hour in seconds
        self.bad_domain_service = BadDomainService()
    
    def _convert_15_to_18_char_id(self, id_15):
        """Convert 15-character Salesforce ID to 18-character format"""
        if len(id_15) != 15:
            return id_15
        
        # Salesforce ID conversion algorithm
        suffix = ""
        for i in range(3):
            chunk = id_15[i*5:(i+1)*5]
            chunk_value = 0
            for j, char in enumerate(chunk):
                if char.isupper():
                    chunk_value += 2 ** j
            
            # Convert to base-32 character
            if chunk_value < 26:
                suffix += chr(ord('A') + chunk_value)
            else:
                suffix += str(chunk_value - 26)
        
        return id_15 + suffix
    
    def _convert_18_to_15_char_id(self, id_18):
        """Convert 18-character Salesforce ID to 15-character format"""
        if len(id_18) == 15:
            return id_18
        elif len(id_18) == 18:
            return id_18[:15]
        else:
            return id_18  # Return as-is if invalid format
    
    def _are_same_account_id(self, id1: str, id2: str) -> bool:
        """Check if two Salesforce IDs refer to the same account (handles 15/18 char conversion)"""
        if not id1 or not id2:
            return False
        
        # Convert both to 15-character format for comparison
        id1_15 = self._convert_18_to_15_char_id(str(id1).strip())
        id2_15 = self._convert_18_to_15_char_id(str(id2).strip())
        
        return id1_15 == id2_15
    
    def _is_valid_salesforce_id_format(self, account_id: str) -> bool:
        """
        Check if an account ID has valid Salesforce ID format (15 or 18 chars, alphanumeric)
        Args:
            account_id: The account ID string to validate
        Returns:
            True if format is valid, False otherwise
        """
        if not account_id:
            return False
        
        account_id = str(account_id).strip()
        
        # Must be 15 or 18 characters
        if len(account_id) not in [15, 18]:
            return False
        
        # Must be alphanumeric (Salesforce IDs contain letters and numbers only)
        if not account_id.isalnum():
            return False
        
        # Must start with "001" (Account object prefix)
        if not account_id.startswith('001'):
            return False
        
        return True
    
    # NEW METHODS FOR DUAL-FILE MATCHING SYSTEM
    
    def get_customer_accounts_bulk(self, account_ids: list) -> tuple[Optional[list], str]:
        """
        Query customer account data for matching - returns customer account fields only
        Args:
            account_ids: List of customer account IDs
        Returns:
            Tuple of (account_data_list, message)
        """
        try:
            if not self.ensure_connection():
                return None, "Failed to connect to Salesforce"
            
            if not account_ids:
                return [], "No account IDs provided"
            
            # Convert all Account IDs to 18-character format for querying
            query_account_ids = []
            for aid in account_ids:
                if len(str(aid).strip()) == 15:
                    query_account_ids.append(self._convert_15_to_18_char_id(str(aid).strip()))
                else:
                    query_account_ids.append(str(aid).strip())
            
            # Build batch query for customer account fields
            ids_string = "', '".join(query_account_ids)
            customer_query = f"""
            SELECT Id, Name, Website, 
                   BillingCity, BillingState, BillingCountry, BillingPostalCode
            FROM Account
            WHERE Id IN ('{ids_string}')
            """
            
            assert self.sf is not None
            result = self.sf.query(customer_query)
            
            customer_accounts = []
            for record in result['records']:
                # Remove Salesforce metadata if present
                if 'attributes' in record:
                    del record['attributes']
                customer_accounts.append(record)
            
            return customer_accounts, f"Successfully retrieved {len(customer_accounts)} customer accounts"
            
        except Exception as e:
            return None, f"Error querying customer accounts: {str(e)}"
    
    def get_shell_accounts_bulk(self, account_ids: list) -> tuple[Optional[list], str]:
        """
        Query shell account data for matching - returns ZI enriched fields only
        Args:
            account_ids: List of shell account IDs
        Returns:
            Tuple of (account_data_list, message)
        """
        try:
            if not self.ensure_connection():
                return None, "Failed to connect to Salesforce"
            
            if not account_ids:
                return [], "No account IDs provided"
            
            # Convert all Account IDs to 18-character format for querying
            query_account_ids = []
            for aid in account_ids:
                if len(str(aid).strip()) == 15:
                    query_account_ids.append(self._convert_15_to_18_char_id(str(aid).strip()))
                else:
                    query_account_ids.append(str(aid).strip())
            
            # Build batch query for shell account ZI fields
            ids_string = "', '".join(query_account_ids)
            shell_query = f"""
            SELECT Id, ZI_Id__c, ZI_Company_Name__c, ZI_Website__c, 
                   ZI_Company_City__c, ZI_Company_State__c, ZI_Company_Country__c, ZI_Company_Postal_Code__c
            FROM Account 
            WHERE Id IN ('{ids_string}')
            """
            
            assert self.sf is not None
            result = self.sf.query(shell_query)
            
            shell_accounts = []
            for record in result['records']:
                # Remove Salesforce metadata if present
                if 'attributes' in record:
                    del record['attributes']
                shell_accounts.append(record)
            
            return shell_accounts, f"Successfully retrieved {len(shell_accounts)} shell accounts"
            
        except Exception as e:
            return None, f"Error querying shell accounts: {str(e)}"
    
    def validate_customer_account_ids(self, account_ids: list) -> tuple[Optional[dict], str]:
        """
        Validate that customer account IDs exist in Salesforce
        Args:
            account_ids: List of customer account ID strings
        Returns:
            Tuple of (validation_result, message)
        """
        try:
            if not self.ensure_connection():
                return None, "Failed to connect to Salesforce"
            
            if not account_ids:
                return {'valid_account_ids': [], 'invalid_account_ids': []}, "No account IDs to validate"
            
            # Separate valid format IDs from obviously invalid ones
            format_valid_ids = []
            format_invalid_ids = []
            
            for original_id in account_ids:
                original_id_str = str(original_id).strip()
                if self._is_valid_salesforce_id_format(original_id_str):
                    format_valid_ids.append(original_id_str)
                else:
                    format_invalid_ids.append(original_id_str)
            
            # Convert format-valid IDs to 18-character format for querying
            query_account_ids = []
            id_mapping = {}  # Map 18-char to original format
            
            for original_id in format_valid_ids:
                if len(original_id) == 15:
                    query_id = self._convert_15_to_18_char_id(original_id)
                else:
                    query_id = original_id
                query_account_ids.append(query_id)
                id_mapping[query_id] = original_id
            
            # Query to check which format-valid IDs actually exist in Salesforce
            valid_account_ids = []
            salesforce_invalid_ids = []
            
            if query_account_ids:  # Only query if we have format-valid IDs
                ids_string = "', '".join(query_account_ids)
                validation_query = f"SELECT Id FROM Account WHERE Id IN ('{ids_string}')"
                
                assert self.sf is not None
                result = self.sf.query(validation_query)
                
                # Get valid IDs (convert back to original format)
                found_ids = {record['Id'] for record in result['records']}
                valid_account_ids = [id_mapping[query_id] for query_id in query_account_ids if query_id in found_ids]
                salesforce_invalid_ids = [id_mapping[query_id] for query_id in query_account_ids if query_id not in found_ids]
            
            # Combine format-invalid and Salesforce-invalid IDs
            invalid_account_ids = format_invalid_ids + salesforce_invalid_ids
            
            validation_result = {
                'valid_account_ids': valid_account_ids,
                'invalid_account_ids': invalid_account_ids,
                'total_requested': len(account_ids),
                'valid_count': len(valid_account_ids),
                'invalid_count': len(invalid_account_ids)
            }
            
            if invalid_account_ids:
                message = f"Validation complete: {len(valid_account_ids)} valid, {len(invalid_account_ids)} invalid account IDs"
            else:
                message = f"All {len(valid_account_ids)} account IDs are valid"
            
            return validation_result, message
            
        except Exception as e:
            return None, f"Error validating customer account IDs: {str(e)}"
    
    def validate_shell_account_ids(self, account_ids: list) -> tuple[Optional[dict], str]:
        """
        Validate that shell account IDs exist in Salesforce and have ZI data
        Args:
            account_ids: List of shell account ID strings
        Returns:
            Tuple of (validation_result, message)
        """
        try:
            if not self.ensure_connection():
                return None, "Failed to connect to Salesforce"
            
            if not account_ids:
                return {'valid_account_ids': [], 'invalid_account_ids': []}, "No account IDs to validate"
            
            # Separate valid format IDs from obviously invalid ones
            format_valid_ids = []
            format_invalid_ids = []
            
            for original_id in account_ids:
                original_id_str = str(original_id).strip()
                if self._is_valid_salesforce_id_format(original_id_str):
                    format_valid_ids.append(original_id_str)
                else:
                    format_invalid_ids.append(original_id_str)
            
            # Convert format-valid IDs to 18-character format for querying
            query_account_ids = []
            id_mapping = {}  # Map 18-char to original format
            
            for original_id in format_valid_ids:
                if len(original_id) == 15:
                    query_id = self._convert_15_to_18_char_id(original_id)
                else:
                    query_id = original_id
                query_account_ids.append(query_id)
                id_mapping[query_id] = original_id
            
            # Query to check which format-valid IDs actually exist in Salesforce
            valid_account_ids = []
            salesforce_invalid_ids = []
            zi_data_stats = {
                'accounts_with_zi_name': 0,
                'accounts_with_zi_website': 0,
                'accounts_with_complete_zi_data': 0
            }
            
            if query_account_ids:  # Only query if we have format-valid IDs
                ids_string = "', '".join(query_account_ids)
                validation_query = f"""
                SELECT Id, ZI_Company_Name__c, ZI_Website__c 
                FROM Account 
                WHERE Id IN ('{ids_string}')
                """
                
                assert self.sf is not None
                result = self.sf.query(validation_query)
                
                # Get valid IDs (accounts that exist, regardless of ZI data completeness)
                found_ids = {record['Id'] for record in result['records']}
                valid_account_ids = [id_mapping[query_id] for query_id in query_account_ids if query_id in found_ids]
                salesforce_invalid_ids = [id_mapping[query_id] for query_id in query_account_ids if query_id not in found_ids]
                
                # Check ZI data completeness for reporting (but don't reject accounts)
                for record in result['records']:
                    if record.get('ZI_Company_Name__c'):
                        zi_data_stats['accounts_with_zi_name'] += 1
                    if record.get('ZI_Website__c'):
                        zi_data_stats['accounts_with_zi_website'] += 1
                    if record.get('ZI_Company_Name__c') and record.get('ZI_Website__c'):
                        zi_data_stats['accounts_with_complete_zi_data'] += 1
            
            # Combine format-invalid and Salesforce-invalid IDs
            invalid_account_ids = format_invalid_ids + salesforce_invalid_ids
            
            validation_result = {
                'valid_account_ids': valid_account_ids,
                'invalid_account_ids': invalid_account_ids,
                'total_requested': len(account_ids),
                'valid_count': len(valid_account_ids),
                'invalid_count': len(invalid_account_ids),
                'zi_data_stats': zi_data_stats
            }
            
            if invalid_account_ids:
                message = f"Validation complete: {len(valid_account_ids)} valid, {len(invalid_account_ids)} invalid shell account IDs"
            else:
                message = f"All {len(valid_account_ids)} shell account IDs are valid"
            
            return validation_result, message
            
        except Exception as e:
            return None, f"Error validating shell account IDs: {str(e)}"
    
    def compute_bad_domain_flag(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute Bad_Domain flag using domain checking
        Returns dict with is_bad boolean and explanation
        """
        is_bad, explanation = self.bad_domain_service.check_account_for_bad_domains(account_data)
        
        return {
            'is_bad': is_bad,
            'explanation': explanation
        }
    
    def filter_customer_accounts_by_bad_domains(self, customer_accounts: list) -> tuple[list, list]:
        """
        Filter customer accounts by bad domains - separate clean accounts from flagged ones
        Args:
            customer_accounts: List of customer account dictionaries with Website field
        Returns:
            Tuple of (clean_accounts, flagged_accounts)
            - clean_accounts: Accounts safe for matching
            - flagged_accounts: Accounts with bad domains (excluded from matching)
        """
        clean_accounts = []
        flagged_accounts = []
        
        for account in customer_accounts:
            # Check for bad domains (only checks Website field for customer accounts)
            bad_domain_result = self.compute_bad_domain_flag(account)
            
            # Add the bad domain flag to the account data
            account_with_flag = account.copy()
            account_with_flag['Bad_Domain'] = bad_domain_result
            
            if bad_domain_result['is_bad']:
                flagged_accounts.append(account_with_flag)
            else:
                clean_accounts.append(account_with_flag)
        
        return clean_accounts, flagged_accounts
    
    def connect(self):
        """Establish connection to Salesforce"""
        try:
            # Validate configuration first
            Config.validate_salesforce_config()
            
            # Create Salesforce connection
            self.sf = Salesforce(
                username=Config.SF_USERNAME,
                password=Config.SF_PASSWORD,
                security_token=Config.SF_SECURITY_TOKEN,
                domain=Config.SF_DOMAIN
            )
            
            self._is_connected = True
            self._last_connection_time = time.time()
            return True
        except Exception as e:
            print(f"Failed to connect to Salesforce: {str(e)}")
            self._is_connected = False
            return False
    
    def ensure_connection(self):
        """Ensure we have an active Salesforce connection"""
        current_time = time.time()
        
        # If we have a connection and it's not timed out, use it
        if self._is_connected and self.sf and (current_time - self._last_connection_time) < self._connection_timeout:
            return True
            
        # Otherwise, establish a new connection
        return self.connect()
    
    def test_connection(self):
        """Test if connection is working by running a simple query"""
        try:
            if not self.ensure_connection():
                return False, "Failed to establish connection"
            
            # Simple test - query 5 Account IDs
            assert self.sf is not None  # Type hint for linter
            query_result = self.sf.query("SELECT Id FROM Account LIMIT 5")
            
            # If we get here, connection is working and we can query data
            record_count = len(query_result['records'])
            return True, f"Connection successful - Retrieved {record_count} Account records"
            
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_connection_info(self):
        """Get Salesforce connection information for debugging"""
        try:
            if self.sf:
                return {
                    "connected": True,
                    "instance_url": getattr(self.sf, 'sf_instance', 'Unknown'),
                    "session_id_present": bool(getattr(self.sf, 'session_id', None)),
                    "api_version": getattr(self.sf, 'sf_version', 'Unknown')
                }
            else:
                return {"connected": False}
        except Exception as e:
            return {"connected": False, "error": str(e)} 