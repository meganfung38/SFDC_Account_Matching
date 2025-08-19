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
    
    def compute_has_shell_flag(self, account_id: str, parent_account_id: str) -> bool:
        """
        Compute Has_Shell flag: True if ParentId points to a different account
        False if null or points to itself
        """
        if not parent_account_id:
            return False
        
        # If parent account ID points to itself, it's not a child account
        if self._are_same_account_id(account_id, parent_account_id):
            return False
        
        return True
    
    def compute_customer_consistency_flag(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute Customer_Consistency flag using fuzzy matching
        Returns dict with score and explanation
        """
        name = account_data.get('Name', '')
        website = account_data.get('Website', '')
        zi_company = account_data.get('ZI_Company_Name__c', '')
        zi_website = account_data.get('ZI_Website__c', '')
        
        score, explanation = self.fuzzy_matcher.compute_customer_consistency_score(
            name, website, zi_company, zi_website
        )
        
        return {
            'score': round(score, 1),
            'explanation': explanation
        }
    
    def get_shell_account_data(self, shell_account_id: str) -> Optional[Dict[str, Any]]:
        """Query shell account data for comparison purposes"""
        try:
            if not self.ensure_connection():
                return None
            
            # Query shell account fields needed for comparison
            query = """
            SELECT Id, Name, Website, 
                   BillingState, BillingCountry, BillingPostalCode,
                   ZI_Company_Name__c, ZI_Website__c, ZI_Company_State__c, ZI_Company_Country__c, ZI_Company_Postal_Code__c
            FROM Account 
            WHERE Id = '{}'
            """.format(shell_account_id)
            
            assert self.sf is not None
            result = self.sf.query(query)
            
            if result['totalSize'] == 0:
                return None
                
            shell_account = result['records'][0]
            
            # Remove Salesforce metadata
            if 'attributes' in shell_account:
                del shell_account['attributes']
                
            return shell_account
            
        except Exception as e:
            print(f"Error querying shell account {shell_account_id}: {str(e)}")
            return None
    
    def compute_customer_shell_coherence_flag(self, account_data: Dict[str, Any], shell_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute Customer_Shell_Coherence flag using fuzzy matching between customer and shell
        Returns dict with score and explanation
        """
        score, explanation = self.fuzzy_matcher.compute_customer_shell_coherence_score(
            account_data, shell_data
        )
        
        return {
            'score': round(score, 1),
            'explanation': explanation
        }
    
    def compute_address_consistency_flag(self, account_data: Dict[str, Any], shell_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute Address_Consistency flag comparing billing addresses
        Returns dict with boolean result and explanation
        """
        is_consistent, explanation = self.fuzzy_matcher.compute_address_consistency(
            account_data, shell_data
        )
        
        return {
            'is_consistent': is_consistent,
            'explanation': explanation
        }
    
    def compute_bad_domain_flag(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute Bad_Domain flag by checking email and website domains against bad domain list
        Returns dict with boolean result and explanation
        """
        is_bad, explanation = self.bad_domain_service.check_account_for_bad_domains(account_data)
        
        return {
            'is_bad': is_bad,
            'explanation': explanation
        }
    
    def format_data_for_openai(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format account data according to the system prompt specification"""
        
        # Helper function to format billing address
        def format_billing_address(data):
            address_parts = []
            if data.get('BillingState'):
                address_parts.append(data['BillingState'])
            if data.get('BillingCountry'):
                address_parts.append(data['BillingCountry'])
            if data.get('BillingPostalCode'):
                address_parts.append(data['BillingPostalCode'])
            return ', '.join(address_parts) if address_parts else None
        
        # Helper function to format ZI billing address
        def format_zi_billing_address(data):
            address_parts = []
            if data.get('ZI_Company_State__c'):
                address_parts.append(data['ZI_Company_State__c'])
            if data.get('ZI_Company_Country__c'):
                address_parts.append(data['ZI_Company_Country__c'])
            if data.get('ZI_Company_Postal_Code__c'):
                address_parts.append(data['ZI_Company_Postal_Code__c'])
            return ', '.join(address_parts) if address_parts else None
        
        # Customer account data (always present)
        formatted_data = {
            "customer": {
                "Name": account_data.get('Name'),
                "ParentId": account_data.get('ParentId'),
                "Parent": account_data.get('Parent'),
                "Website": account_data.get('Website'),
                "Billing_Address": format_billing_address(account_data),
                "ZI_Company_Name__c": account_data.get('ZI_Company_Name__c'),
                "ZI_Website__c": account_data.get('ZI_Website__c'),
                "ZI_Billing_Address": format_zi_billing_address(account_data)
            },
            "flags": {
                "Has_Shell": account_data.get('Has_Shell', False),
                "Customer_Consistency": {
                    "score": account_data.get('Customer_Consistency', {}).get('score', 0),
                    "explanation": account_data.get('Customer_Consistency', {}).get('explanation', '')
                }
            }
        }
        
        # Parent/Shell account data (only if Has_Shell is True)
        if account_data.get('Has_Shell') and account_data.get('Shell_Account_Data'):
            shell_data = account_data['Shell_Account_Data']
            formatted_data["parent"] = {
                "Name": shell_data.get('Name'),
                "Website": shell_data.get('Website'),
                "Billing_Address": format_billing_address(shell_data),
                "ZI_Company_Name__c": shell_data.get('ZI_Company_Name__c'),
                "ZI_Website__c": shell_data.get('ZI_Website__c'),
                "ZI_Billing_Address": format_zi_billing_address(shell_data)
            }
            
            # Add shell-related flags
            if account_data.get('Customer_Shell_Coherence'):
                formatted_data["flags"]["Customer_Shell_Coherence"] = {
                    "score": account_data['Customer_Shell_Coherence'].get('score', 0),
                    "explanation": account_data['Customer_Shell_Coherence'].get('explanation', '')
                }
            
            if account_data.get('Address_Consistency'):
                formatted_data["flags"]["Address_Consistency"] = {
                    "is_consistent": account_data['Address_Consistency'].get('is_consistent', False),
                    "explanation": account_data['Address_Consistency'].get('explanation', '')
                }
        
        return formatted_data
    
    def get_ai_assessment(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered confidence assessment for account relationship"""
        try:
            # Format data according to system prompt specification
            formatted_data = self.format_data_for_openai(account_data)
            
            # Get system prompt from openai_service
            system_prompt = get_system_prompt()

            # Create user prompt with formatted data
            user_prompt = f"Please assess this account relationship:\n\n{json.dumps(formatted_data, indent=2)}"
            
            # Call OpenAI
            response = ask_openai(client, system_prompt, user_prompt)
            
            # Parse JSON response
            try:
                ai_assessment = json.loads(response)
                return {
                    'success': True,
                    'confidence_score': ai_assessment.get('confidence_score', 0),
                    'explanation_bullets': ai_assessment.get('explanation_bullets', []),
                    'raw_response': response
                }
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f"Failed to parse AI response as JSON: {str(e)}",
                    'raw_response': response
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error calling OpenAI: {str(e)}"
            }

    def enrich_account_with_flags(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich account data with computed flags
        """
        enriched_account = account_data.copy()
        
        # FIRST: Check for bad domains - if found, stop all further analysis
        bad_domain_flag = self.compute_bad_domain_flag(account_data)
        enriched_account['Bad_Domain'] = bad_domain_flag
        
        # If bad domain detected, stop here - no further analysis
        if bad_domain_flag.get('is_bad', False):
            return enriched_account
        
        # If clean domain, proceed with full analysis
        # Compute Has_Shell flag - safely access ParentId
        parent_id = account_data.get('ParentId', '')
        
        has_shell = self.compute_has_shell_flag(
            account_data.get('Id', ''), 
            parent_id
        )
        enriched_account['Has_Shell'] = has_shell
        
        # Compute Customer_Consistency flag
        customer_consistency = self.compute_customer_consistency_flag(account_data)
        enriched_account['Customer_Consistency'] = customer_consistency
        
        # If has shell, get shell account data and compute shell-related flags
        shell_account_data = None
        if has_shell and parent_id:
            shell_account_data = self.get_shell_account_data(parent_id)
            if shell_account_data:
                enriched_account['Shell_Account_Data'] = shell_account_data
                
                # Compute Customer_Shell_Coherence flag (only when Has_Shell is True)
                customer_shell_coherence = self.compute_customer_shell_coherence_flag(account_data, shell_account_data)
                enriched_account['Customer_Shell_Coherence'] = customer_shell_coherence
                
                # Compute Address_Consistency flag (only when Has_Shell is True)
                address_consistency = self.compute_address_consistency_flag(account_data, shell_account_data)
                enriched_account['Address_Consistency'] = address_consistency
        
        # Get AI-powered confidence assessment
        ai_assessment = self.get_ai_assessment(enriched_account)
        enriched_account['AI_Assessment'] = ai_assessment
        
        return enriched_account
    
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
        """Get basic connection information"""
        if not self._is_connected or not self.sf:
            return None
        
        return {
            "instance_url": self.sf.sf_instance,
            "session_id": "Connected" if self.sf.session_id else "Not Connected",
            "api_version": self.sf.sf_version
        }

    def get_account_by_id(self, account_id):
        """Get specific Account data by Account ID"""
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Validate Account ID format
            account_id = str(account_id).strip()
            if not account_id:
                return None, "Account ID cannot be empty"
            
            # Basic Account ID format validation
            if len(account_id) not in [15, 18]:
                return None, f"Invalid Account ID format. Account IDs must be 15 or 18 characters long. Provided: '{account_id}' ({len(account_id)} characters)"
            
            if not account_id.startswith('001'):
                return None, f"Invalid Account ID format. Account IDs must start with '001'. Provided: '{account_id}'"
            
            # Query for Account fields including custom fields and RecordType
            query = """
            SELECT Id, Name, ParentId, Parent.Name, Website, 
                   BillingState, BillingCountry, BillingPostalCode,
                   ZI_Company_Name__c, ZI_Website__c, ZI_Company_State__c, ZI_Company_Country__c, ZI_Company_Postal_Code__c, 
                   ContactMostFrequentEmail__c, RecordType.Name
            FROM Account 
            WHERE Id = '{}'
            """.format(account_id)
            
            assert self.sf is not None  # Type hint for linter
            result = self.sf.query(query)
            
            if result['totalSize'] == 0:
                return None, f"No Account found with ID: {account_id}. Please verify the Account ID exists in your Salesforce org."
            
            # Get the account record
            account_record = result['records'][0]
            
            # Remove Salesforce metadata if present
            if 'attributes' in account_record:
                del account_record['attributes']
            
            # Enrich account with computed flags
            enriched_account = self.enrich_account_with_flags(account_record)
            
            # Format response the same way as batch analysis
            import time
            execution_time = f"{time.time():.2f}s"
            
            response = {
                'accounts': [enriched_account],  # Wrap in array to match batch format
                'summary': {
                    'total_requested': 1,
                    'accounts_retrieved': 1
                },
                'execution_time': execution_time
            }
            
            return response, "Account retrieved successfully"
                
        except Exception as e:
            error_msg = str(e)
            # Provide cleaner error messages for common issues
            if "invalid ID field" in error_msg.lower():
                return None, f"Invalid Account ID: '{account_id}'. Please check the Account ID format and try again."
            elif "malformed request" in error_msg.lower():
                return None, f"Account ID '{account_id}' is not valid. Please provide a valid 15 or 18-character Salesforce Account ID."
            else:
                return None, f"Error retrieving Account: {error_msg}"

    def query_accounts(self, query_conditions=None, limit=100):
        """Query accounts with optional conditions"""
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Base query with Account fields including custom fields and RecordType
            base_query = """
            SELECT Id, Name, ParentId, Parent.Name, Website, 
                   BillingState, BillingCountry, BillingPostalCode,
                   ZI_Company_Name__c, ZI_Website__c, ZI_Company_State__c, ZI_Company_Country__c, ZI_Company_Postal_Code__c, 
                   ContactMostFrequentEmail__c, RecordType.Name
            FROM Account
            """
            
            # Add conditions if provided
            if query_conditions:
                base_query += f" WHERE {query_conditions}"
            
            # Add limit
            base_query += f" LIMIT {limit}"
            
            assert self.sf is not None  # Type hint for linter
            result = self.sf.query(base_query)
            
            # Clean up records by removing metadata
            clean_records = []
            for record in result['records']:
                if 'attributes' in record:
                    del record['attributes']
                clean_records.append(record)
            
            return {
                'records': clean_records,
                'totalSize': result['totalSize'],
                'done': result['done']
            }, "Query executed successfully"
            
        except Exception as e:
            return None, f"Error executing query: {str(e)}"

    def validate_account_ids(self, account_ids):
        """Validate that all provided Account IDs exist in Salesforce"""
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            if not account_ids:
                return {'valid_account_ids': [], 'invalid_account_ids': []}, "No Account IDs provided"
            
            # Clean and validate Account ID format first
            cleaned_account_ids = []
            format_invalid_ids = []
            id_mapping = {}  # Maps original ID to cleaned ID for response
            
            for aid in account_ids:
                aid_str = str(aid).strip()
                # Basic Account ID format validation (15 or 18 characters, starts with 001)
                if len(aid_str) in [15, 18] and aid_str.startswith('001'):
                    # Convert 15-char IDs to 18-char for consistent querying
                    if len(aid_str) == 15:
                        converted_id = self._convert_15_to_18_char_id(aid_str)
                        cleaned_account_ids.append(converted_id)
                        id_mapping[converted_id] = aid_str  # Remember original format
                    else:
                        cleaned_account_ids.append(aid_str)
                        id_mapping[aid_str] = aid_str
                else:
                    format_invalid_ids.append(aid_str)
            
            # Query Salesforce to check which Account IDs exist (only for format-valid IDs)
            valid_account_ids = []
            sf_invalid_ids = []
            
            if cleaned_account_ids:
                # Process in batches to avoid SOQL query limits
                batch_size = 200  # Salesforce IN clause limit
                for i in range(0, len(cleaned_account_ids), batch_size):
                    batch = cleaned_account_ids[i:i + batch_size]
                    ids_string = "', '".join(batch)
                    validation_query = f"SELECT Id FROM Account WHERE Id IN ('{ids_string}')"
                    
                    assert self.sf is not None  # Type hint for linter
                    result = self.sf.query(validation_query)
                    
                    # Extract valid Account IDs from this batch (in 18-char format from Salesforce)
                    batch_valid_18char = [record['Id'] for record in result['records']]
                    
                    # Convert back to original format for response
                    for valid_18char in batch_valid_18char:
                        original_format = id_mapping.get(valid_18char, valid_18char)
                        valid_account_ids.append(original_format)
                    
                    # Find invalid Account IDs in this batch (return in original format)
                    for clean_id in batch:
                        if clean_id not in batch_valid_18char:
                            original_format = id_mapping.get(clean_id, clean_id)
                            sf_invalid_ids.append(original_format)
            
            # Combine all invalid Account IDs (format issues + Salesforce not found)
            all_invalid_ids = format_invalid_ids + sf_invalid_ids
            
            return {
                'valid_account_ids': valid_account_ids,
                'invalid_account_ids': all_invalid_ids,
                'format_invalid_count': len(format_invalid_ids),
                'sf_invalid_count': len(sf_invalid_ids)
            }, f"Validated {len(valid_account_ids)} valid and {len(all_invalid_ids)} invalid Account IDs"
            
        except Exception as e:
            return None, f"Error validating Account IDs: {str(e)}"

    def get_account_ids_from_query(self, soql_query, max_ids=100):
        """Get Account IDs from a custom SOQL query that returns Account IDs only"""
        import time
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Quick validation of query structure
            if not soql_query.strip().upper().startswith('SELECT'):
                return None, "Query must start with SELECT"
            
            # Build the proper query with smart limit handling
            try:
                final_query = self._build_account_soql_query(soql_query, max_ids)
            except ValueError as ve:
                return None, str(ve)
            
            # Execute query
            assert self.sf is not None
            id_result = self.sf.query(final_query)
            
            # Extract IDs efficiently
            account_ids = [record['Id'] for record in id_result['records']]
            total_found = id_result['totalSize'] if not id_result.get('done', True) else len(account_ids)
            
            # Return early if no results
            if total_found == 0:
                return None, "No Account IDs found matching the query criteria."
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Build result
            result = {
                'account_ids': account_ids,
                'summary': {
                    'total_found': total_found,
                    'execution_time': f"{execution_time:.2f}s",
                    'effective_limit': min(self._extract_limit_from_query(soql_query) or float('inf'), max_ids) if soql_query and soql_query.strip() and max_ids is not None else (self._extract_limit_from_query(soql_query) or 'No limit')
                }
            }
            
            return result, f"Successfully retrieved {len(account_ids)} Account IDs from query"
            
        except Exception as e:
            error_msg = str(e)
            # Provide cleaner error messages for common SOQL issues
            if "malformed request" in error_msg.lower() or "malformed_query" in error_msg.lower():
                return None, "Invalid SOQL syntax. Please check your query and try again."
            elif "unexpected token" in error_msg.lower():
                return None, "SOQL syntax error. Please check for typos, missing keywords, or incorrect field names."
            elif "no such column" in error_msg.lower() or "invalid field" in error_msg.lower():
                return None, "Invalid field name in query. Please check that all field names exist in the Account object."
            elif "invalid object name" in error_msg.lower():
                return None, "Invalid object name in query. This API only supports queries on the Account object."
            else:
                return None, f"Error executing SOQL query: {error_msg}"

    def get_accounts_data_by_ids(self, account_ids):
        """Get full Account data for a list of Account IDs"""
        import time
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            if not account_ids:
                return {'accounts': []}, "No Account IDs provided"
            
            # Get account data in batch
            analyzed_accounts = self._analyze_account_batch(account_ids)
            
            execution_time = time.time() - start_time
            
            result = {
                'accounts': analyzed_accounts,
                'summary': {
                    'total_requested': len(account_ids),
                    'accounts_retrieved': len(analyzed_accounts)
                },
                'execution_time': f"{execution_time:.2f}s"
            }
            
            return result, f"Successfully retrieved data for {len(analyzed_accounts)} of {len(account_ids)} accounts"
            
        except Exception as e:
            return None, f"Error retrieving Account data: {str(e)}"

    def analyze_accounts_from_query(self, soql_query, max_analyze=100):
        """Analyze accounts from a custom SOQL query that returns Account IDs only"""
        import time
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Validate SOQL query
            is_valid, error_msg = self._validate_account_soql_query(soql_query, return_error=True)
            if not is_valid:
                return None, error_msg
            
            # Execute the SOQL query to get account IDs only
            assert self.sf is not None  # Type hint for linter
            
            # Build the proper query with smart limit handling
            try:
                final_query = self._build_account_soql_query(soql_query, max_analyze)
            except ValueError as ve:
                return None, str(ve)
            
            id_result = self.sf.query(final_query)
            account_ids_to_analyze = [record['Id'] for record in id_result['records']]
            actual_analyze_count = len(account_ids_to_analyze)
            
            # If no accounts found, return early
            if actual_analyze_count == 0:
                return {
                    'summary': {
                        'total_query_results': 0,
                        'accounts_analyzed': 0
                    },
                    'accounts': [],
                    'query_info': {
                        'original_query': soql_query,
                        'execution_time': f"{time.time() - start_time:.2f}s",
                        'total_found': 0,
                        'analyzed_count': 0
                    }
                }, "No accounts found matching the query"
            
            # For total count
            total_found = id_result['totalSize'] if not id_result.get('done', True) else actual_analyze_count
            
            # Get account data in batch
            analyzed_accounts = self._analyze_account_batch(account_ids_to_analyze)
            
            execution_time = time.time() - start_time
            
            result = {
                'summary': {
                    'total_query_results': total_found,
                    'accounts_analyzed': actual_analyze_count
                },
                'accounts': analyzed_accounts,
                'query_info': {
                    'original_query': soql_query,
                    'final_query': final_query,
                    'execution_time': f"{execution_time:.2f}s",
                    'total_found': total_found,
                    'analyzed_count': actual_analyze_count,
                    'effective_limit': min(self._extract_limit_from_query(soql_query) or float('inf'), max_analyze) if soql_query and soql_query.strip() else max_analyze
                }
            }
            
            return result, f"Successfully analyzed {actual_analyze_count} accounts from query"
            
        except Exception as e:
            return None, f"Error analyzing accounts from query: {str(e)}"

    def _validate_account_soql_query(self, soql_query, return_error=False):
        """
        Validate SOQL query for safety - must be complete SELECT query returning Account IDs only
        If return_error is True, returns (bool, str) tuple with validation result and error message
        """
        # Empty query is no longer valid - require complete SELECT statement
        if not soql_query or not soql_query.strip():
            return (False, "Empty query not allowed") if return_error else False
        
        # Convert to uppercase for checking
        query_upper = soql_query.upper().strip()
        
        # Must be a complete SELECT query, not a WHERE/LIMIT clause
        if not query_upper.startswith('SELECT'):
            return (False, "Query must start with SELECT") if return_error else False
        
        # For full SELECT queries, validate for security and Account ID requirement
        import re
        
        # Check for dangerous operations
        dangerous_keywords = ['DELETE', 'UPDATE', 'INSERT', 'UPSERT', 'MERGE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in query_upper for keyword in dangerous_keywords):
            return (False, "Query contains dangerous keywords") if return_error else False
        
        # Extract the main SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query_upper, re.DOTALL)
        if not select_match:
            return (False, "Invalid SELECT clause") if return_error else False
        
        select_fields = select_match.group(1).strip()
        select_fields_clean = re.sub(r'\s+', '', select_fields)
        
        # Convert to uppercase for pattern matching
        select_fields_clean = select_fields_clean.upper()
        
        # Allow: "Id", "Account.Id", "a.Id" (with alias), etc.
        if not re.match(r'^(ID|ACCOUNT\.ID|\w+\.ID)$', select_fields_clean):
            return (False, "Query must select only Account ID field") if return_error else False
        
        # For the main FROM clause, ensure it involves Account object
        if 'ACCOUNT' not in query_upper:
            return (False, "Query must be from Account object") if return_error else False
        
        return (True, "Valid query") if return_error else True

    def _build_account_soql_query(self, user_query, max_limit):
        """Build the final SOQL query for accounts with smart limit handling"""
        # No longer handle empty queries - require full SELECT query
        if not user_query or not user_query.strip():
            raise ValueError("Empty query not allowed. Please provide a complete SOQL SELECT query.")
        
        user_query = user_query.strip()
        
        # Only accept full SELECT queries, not WHERE/LIMIT clauses
        if not user_query.upper().startswith('SELECT'):
            raise ValueError("Query must be a complete SELECT statement. WHERE/LIMIT clauses alone are not accepted.")
        
        # For full SELECT queries, handle LIMIT clause intelligently
        query_upper = user_query.upper()
        if 'LIMIT' in query_upper:
            # Extract existing LIMIT value and use the smaller of the two
            import re
            limit_match = re.search(r'LIMIT\s+(\d+)', query_upper)
            if limit_match:
                existing_limit = int(limit_match.group(1))
                effective_limit = min(existing_limit, max_limit)
                # Replace the existing LIMIT with the effective limit
                final_query = re.sub(r'LIMIT\s+\d+', f'LIMIT {effective_limit}', user_query, flags=re.IGNORECASE)
                return final_query
            return user_query
        else:
            # No existing LIMIT, add our own only if max_limit is not None
            if max_limit is not None:
                return f"{user_query} LIMIT {max_limit}"
            else:
                return user_query

    def _extract_limit_from_query(self, query):
        """Extract the LIMIT value from a SOQL query, returns None if no LIMIT found"""
        if not query:
            return None
        
        import re
        limit_match = re.search(r'LIMIT\s+(\d+)', query.upper())
        return int(limit_match.group(1)) if limit_match else None

    def _analyze_account_batch(self, account_ids):
        """Analyze a batch of accounts by their IDs"""
        try:
            # Convert all Account IDs to 18-character format for querying
            query_account_ids = []
            for aid in account_ids:
                if len(str(aid).strip()) == 15:
                    query_account_ids.append(self._convert_15_to_18_char_id(str(aid).strip()))
                else:
                    query_account_ids.append(str(aid).strip())
            
            # Build batch query for all account IDs including custom fields and RecordType
            ids_string = "', '".join(query_account_ids)
            batch_query = f"""
            SELECT Id, Name, ParentId, Parent.Name, Website, 
                   BillingState, BillingCountry, BillingPostalCode,
                   ZI_Company_Name__c, ZI_Website__c, ZI_Company_State__c, ZI_Company_Country__c, ZI_Company_Postal_Code__c, 
                   ContactMostFrequentEmail__c, RecordType.Name
            FROM Account
            WHERE Id IN ('{ids_string}')
            """
            
            assert self.sf is not None  # Type hint for linter
            result = self.sf.query(batch_query)
            
            analyzed_accounts = []
            for record in result['records']:
                # Remove Salesforce metadata if present
                if 'attributes' in record:
                    del record['attributes']
                
                # Enrich account with computed flags
                enriched_account = self.enrich_account_with_flags(record)
                analyzed_accounts.append(enriched_account)
            
            return analyzed_accounts
            
        except Exception as e:
            # Return empty results for this batch on error
            print(f"Error analyzing account batch: {str(e)}")
            return [] 