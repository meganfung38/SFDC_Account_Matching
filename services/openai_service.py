import openai
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from config.config import Config

# configure openAI access 
openai.api_key = Config.OPENAI_API_KEY
client = openai.OpenAI()  # creating client instance 

def get_system_prompt():
    """Get the exact system prompt from data_interpretation.md for dual-file matching validation"""
    return """You are an intelligent corporate relationship validator that combines real-world knowledge with SFDC data analysis. Your PRIMARY job is to explain why a customer account was matched to a shell account. Your responsibilities are:

1. FIRST apply your real world knowledge of corporate structures, subsidiaries, business relationships, brand naming conventions, and domain usage.  
2. THEN validate alignment between the customer account and the candidate shell account using Salesforce fields.   
3. LASTLY provide a transparent, concise rationale that highlights which field drove the match, which signals weakened it, and how the final confidence was determined.

You MUST begin EVERY assessment by asking yourself: "Do I know of any relationship between these companies from my knowledge of major corporations, acquisitions, and subsidiaries?"

CRITICAL: Your role is NOT just data validation - you are expected to actively apply your knowledge of corporate structures and relationships BEFORE analyzing any computed metrics or field comparisons.

IMPORTANT: You MUST ONLY return a valid JSON response in the specified format. Do not include any other text, thoughts, or explanations outside the JSON structure.  
For each record, you will output a JSON object with:

* confidence_score (0-100) representing the likelihood of a valid parent-child match  
* explanation_bullets (array of strings) providing your analysis

## 1 Here is the data you will be receiving: 

| Field  | Data Type | Description  | Trust Level  |
| :---- | :---- | :---- | :---- |
| Customer Name  | String  | Customer's Company/ Organization/ Personal Name | Trusted |
| Customer Website | String  | Customer's Website  | Trusted  |
| Customer Billing Address | String  | Customer's City, State, Country, Postal Code | Trusted  |
| Shell Name | String  | Shell's Company/ Organization/ Personal Name | Trusted |
| Shell Website  | String  | Shell's Website | Trusted |
| Shell Billing Address  | String  | Shell's City, State, Country, Postal Code | Trusted  |
| Website_Match  | Fuzzy Match Score (0-100) and Explanation (String)  | Measure how well a customer account's website aligns with the parent shell account's website | Computed (determine its significance based on contextual analysis)  |
| Name_Match | Fuzzy Match Score (0-100) and Explanation (String)  | Measure how well a customer account's name aligns with the parent shell account's name | Computed (determine its significance based on contextual analysis) |
| Address_Consistency | Score (0-100) and Explanation (String)  | Measure how consistent a customer account's address is with the parent shell account's address  | Computed (determine its significance based on contextual analysis)  |

## 2 Validation– Is This a Valid Shell Relationship? 

Apply a layered validation process. You are required to use your world knowledge and assume access to trusted external data sources when evaluating relationships. Fuzzy string comparisons alone are not sufficient: 

* Shell relationship coherence: you must evaluate the relationship the customer account and parent shell using known corporate structures, branding conventions, and public company knowledge  
  * You must determine whether the customer is a known subsidiary, franchise, individual representative, department, regional office, or branch of the shell using external validation and world knowledge:   
  * What does the Website_Match and Name_Match score say about the relationship between the customer and parent shell account?   
  * Do external sources agree that the customer account has some corporate relationship to its parent shell account?   
* Billing address match: compare addresses using precedence (Country > State > City > Postal Match)  
  * What does Address_Consistency say about the relationship between the customer and parent shell account?   
  * Consider acceptable mismatches for independent agents, remote offices, known geographic spread  
  * Do not penalize mismatches when world knowledge supports the relationship (e.g., remote agents or franchise operators) 

## 3 External World Knowledge 

CRITICAL: you MUST prioritize well-established external knowledge over computed sources. Failure to recognize obvious corporate relationships will result in incorrect assessments.

* Mandatory External Knowledge Usage: you have access to comprehensive external databases (LinkedIn, Clearbit, OpenCorporates, Crunchbase, public SEC filings, Wikipedia, major news sources)  
  * You MUST first ask yourself: "Do I know if [Customer Company] has any relationship to [Parent Company]?"  
* Scoring Override Rules:   
  * If external knowledge confirms a relationship: minimum 80/100 confidence regardless of fuzzy scores  
  * If external knowledge contradicts the relationship: maximum 30/100 confidence regardless of fuzzy scores    
  * For well-known subsidiaries/franchises: shell relationship coherence should score 45-50/50 points  
* Required Actions:  
  * Always check your knowledge of the companies involved before relying on computed scores  
  * Explicitly state what external knowledge you used (e.g., "Waymo is a well-known autonomous vehicle subsidiary of Alphabet Inc., confirmed by public records")  
  * If you don't have external knowledge about specific companies, clearly state "No external knowledge available - assessment based solely on field analysis"

## 4 Scoring Logic

Evaluate each account-to-shell relationship based on two weighted pillars. Each is scored then summed and clamped to a maximum of 100. Use contextual judgment, not fixed thresholds. 

| Pillar  | Description |
| :---- | :---- |
| Shell Relationship Coherence (0-70)  | Does the customer logically roll up to the shell? Do their names/ websites indicate affiliation? Use real-world brand knowledge if needed. |
| Billing Address Coherence (0-30)  | Are the customer and shell addresses close enough to suggest affiliation? If they differ, is that expected (e.g. remote rep, franchise)?  |

Assign lower scores for: 

* Weak brand/ domain alignment   
* Vague, noisy, or inconsistent naming  
* Address mismatch with no logical explanation 

Assign higher scores for: 

* Known brand affiliation patterns (e.g., franchisee sites using parent domain)   
* Strong real-world confirmation of relationship 

## 5 Explanation (3-5 bullets) 

Each explanation bullet should: 

* Be concise (<= 25 words)   
* Include an emoji cue:   
  * ✅ strong alignment  
  * ⚠️ partial match or uncertainty  
  * ❌ mismatch or contradiction  
* Summarize a signal that raised or lowered the confidence score   
* You must explicitly state whether external world knowledge was used and what it confirms (e.g., Waymo is a known subsidiary of Alphabet)   
* If world knowledge was not available, you must state this and explain that the decision is based solely on field-level confidence 

Examples:   
✅ Website carlosreyes.zumba.com shows direct affiliation with shell domain zumba.com  
❌ Billing address differs significantly from shell and no match found in public directories  
⚠️ Shell name and customer name share low similarity but share a ZoomInfo org

## 6 Output Format (Strict JSON) 

{  
  "confidence_score": <int 0–100>,  
  "explanation_bullets": [  
    "✅ explanation 1",  
    "⚠️ explanation 2",  
    "❌ explanation 3"  
  ]  
}"""

def format_match_data_for_openai(customer_data: dict, shell_data: dict, match_scores: dict) -> dict:
    """
    Format customer and shell data for OpenAI dual-file matching validation
    Args:
        customer_data: Customer account data from Salesforce
        shell_data: Matched shell account data from Salesforce  
        match_scores: Computed matching scores (Website_Match, Name_Match, Address_Consistency)
    Returns:
        Formatted data dict for OpenAI prompt
    """
    # Helper function to format billing address
    def format_customer_billing_address(data):
        address_parts = []
        if data.get('BillingCity'):
            address_parts.append(data['BillingCity'])
        if data.get('BillingState'):
            address_parts.append(data['BillingState'])
        if data.get('BillingCountry'):
            address_parts.append(data['BillingCountry'])
        if data.get('BillingPostalCode'):
            address_parts.append(data['BillingPostalCode'])
        return ', '.join(address_parts) if address_parts else None
    
    # Helper function to format shell ZI billing address
    def format_shell_billing_address(data):
        address_parts = []
        if data.get('ZI_Company_City__c'):
            address_parts.append(data['ZI_Company_City__c'])
        if data.get('ZI_Company_State__c'):
            address_parts.append(data['ZI_Company_State__c'])
        if data.get('ZI_Company_Country__c'):
            address_parts.append(data['ZI_Company_Country__c'])
        if data.get('ZI_Company_Postal_Code__c'):
            address_parts.append(data['ZI_Company_Postal_Code__c'])
        return ', '.join(address_parts) if address_parts else None
    
    formatted_data = {
        "Customer Name": customer_data.get('Name'),
        "Customer Website": customer_data.get('Website'),
        "Customer Billing Address": format_customer_billing_address(customer_data),
        "Shell Name": shell_data.get('ZI_Company_Name__c'),
        "Shell Website": shell_data.get('ZI_Website__c'),
        "Shell Billing Address": format_shell_billing_address(shell_data),
        "Website_Match": {
            "score": match_scores.get('website_match', 0),
            "explanation": match_scores.get('explanations', {}).get('website', '')
        },
        "Name_Match": {
            "score": match_scores.get('name_match', 0),
            "explanation": match_scores.get('explanations', {}).get('name', '')
        },
        "Address_Consistency": {
            "score": match_scores.get('address_consistency', 0),
            "explanation": match_scores.get('explanations', {}).get('address', '')
        }
    }
    
    return formatted_data

def get_ai_match_assessment(customer_data: dict, shell_data: dict, match_scores: dict) -> dict:
    """
    Get AI-powered confidence assessment for customer-to-shell match recommendation
    Args:
        customer_data: Customer account data from Salesforce
        shell_data: Best matched shell account data from Salesforce
        match_scores: Computed matching scores from FuzzyMatchingService
    Returns:
        Dict with success status, confidence score, explanation bullets, and raw response
    """
    try:
        # Format data according to system prompt specification
        formatted_data = format_match_data_for_openai(customer_data, shell_data, match_scores)
        
        # Get system prompt
        system_prompt = get_system_prompt()

        # Create user prompt with formatted data
        user_prompt = f"Please assess this customer-to-shell account match recommendation:\n\n{json.dumps(formatted_data, indent=2)}"
        
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

def get_ai_match_assessments_batch(match_pairs: list, batch_size: int = 10, delay_between_calls: float = 1.0) -> list:
    """
    Process multiple AI assessments with rate limiting and batch processing
    Args:
        match_pairs: List of dicts with 'customer_account', 'shell_account', and 'match_scores'
        batch_size: Number of concurrent requests (default 10 to respect rate limits)
        delay_between_calls: Delay in seconds between API calls (default 1.0)
    Returns:
        List of AI assessment results in same order as input
    """
    def process_single_assessment(pair_data):
        """Process a single assessment with error handling"""
        try:
            customer = pair_data['customer_account']
            shell = pair_data['shell_account'] 
            scores = pair_data['match_scores']
            
            # Add small delay to respect rate limits
            time.sleep(delay_between_calls)
            
            return get_ai_match_assessment(customer, shell, scores)
        except Exception as e:
            return {
                'success': False,
                'error': f"Batch processing error: {str(e)}"
            }
    
    # Process in batches to manage memory and rate limits
    all_results = []
    total_batches = (len(match_pairs) + batch_size - 1) // batch_size
    
    print(f"🤖 Processing {len(match_pairs)} AI assessments in {total_batches} batches...")
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(match_pairs))
        batch_pairs = match_pairs[start_idx:end_idx]
        
        # Use ThreadPoolExecutor for controlled concurrency
        with ThreadPoolExecutor(max_workers=min(batch_size, len(batch_pairs))) as executor:
            batch_results = list(executor.map(process_single_assessment, batch_pairs))
        
        all_results.extend(batch_results)
        
        # Log progress for large datasets
        if total_batches > 1:
            print(f"✅ Processed AI batch {batch_num + 1}/{total_batches} ({len(batch_pairs)} assessments)")
        
        # Add delay between batches for rate limiting
        if batch_num < total_batches - 1:  # Don't delay after last batch
            time.sleep(delay_between_calls * 2)  # Longer delay between batches
    
    return all_results

def test_openai_connection():
    """Test OpenAI connection by listing available models"""
    try:
        models = client.models.list()
        model_list = list(models)
        
        if len(model_list) > 0:
            return True, f"OpenAI connection successful - Found {len(model_list)} available models"
        else:
            return False, "OpenAI connection failed - No models available"
            
    except Exception as e:
        return False, f"OpenAI connection failed: {str(e)}"

def test_openai_completion(prompt="Hello! Please respond with 'OpenAI connection test successful.'"):
    """Test OpenAI completion generation"""
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        
        return completion.choices[0].message.content, "OpenAI completion test successful"
        
    except Exception as e:
        return None, f"OpenAI completion test failed: {str(e)}"

def ask_openai(openai_client, system_prompt, user_prompt):
    """
    Calls OpenAI with proper error handling and response validation
    Returns a valid JSON string or raises an exception with a clear error message
    """
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        
        response = completion.choices[0].message.content
        
        # Debug logging
        print(f"OpenAI Raw Response: {response}")
        
        # Validate that we got a response
        if not response or not response.strip():
            raise ValueError("Empty response from OpenAI")
            
        # Try to extract JSON from response (in case there's extra text)
        import json
        import re
        
        try:
            # First try to parse the entire response as JSON
            parsed = json.loads(response)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON object from the response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                except json.JSONDecodeError as e:
                    print(f"JSON Parse Error (extracted): {str(e)}")
                    print(f"Extracted JSON: {json_match.group(0)}")
                    raise ValueError(f"Invalid JSON in extracted response: {str(e)}")
            else:
                print("No JSON object found in response")
                raise ValueError("No valid JSON found in response")
        
        # Validate required fields
        if 'confidence_score' not in parsed:
            raise ValueError("Missing required field: confidence_score")
        if 'explanation_bullets' not in parsed:
            raise ValueError("Missing required field: explanation_bullets")
        if not isinstance(parsed['explanation_bullets'], list):
            raise ValueError("explanation_bullets must be a list")
        
        # Return the valid JSON string
        return json.dumps(parsed, indent=2)
        
    except Exception as e:
        error_msg = str(e)
        print(f"OpenAI Error: {error_msg}")
        # Return a valid JSON string with error information
        return json.dumps({
            "confidence_score": 0,
            "explanation_bullets": [
                f"❌ Error: {error_msg}",
                "⚠️ Using computed scores only due to AI service error",
                "✅ Basic relationship checks still performed"
            ]
        }, indent=2)

def get_openai_config():
    """Get OpenAI configuration information"""
    return {
        "model": Config.OPENAI_MODEL,
        "max_tokens": Config.OPENAI_MAX_TOKENS,
        "api_key_configured": bool(Config.OPENAI_API_KEY)
    }