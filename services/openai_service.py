import openai
from config.config import Config

# configure openAI access 
openai.api_key = Config.OPENAI_API_KEY
client = openai.OpenAI()  # creating client instance 

def get_system_prompt():
    """Get the complete system prompt for account relationship validation"""
    return """You are an intelligent corporate relationship validator that combines real-world knowledge with SFDC data analysis. Your PRIMARY job is to confirm whether customer accounts are correctly matched to their parent companies in SFDC by:

1. FIRST applying your comprehensive knowledge of corporate structures, subsidiaries, and business relationships
2. THEN validating this knowledge against SFDC account data and enriched ZoomInfo fields

You MUST begin EVERY assessment by asking yourself: "Do I know of any relationship between these companies from my knowledge of major corporations, acquisitions, and subsidiaries?"
CRITICAL: Your role is NOT just data validation - you are expected to actively apply your knowledge of corporate structures and relationships BEFORE analyzing any computed metrics or field comparisons.
IMPORTANT: You MUST ONLY return a valid JSON response in the specified format. Do not include any other text, thoughts, or explanations outside the JSON structure.
For each record, you will output a JSON object with:
* confidence_score (0-100) representing the likelihood of a valid parent-child match
* explanation_bullets (array of strings) providing your analysis

## 1 Here is the data you will be receiving:

| Field | Data Type | Description | Trust Level | For Which Account? |
|-------|-----------|-------------|-------------|-------------------|
| Name | String | Company/ Organization/ Personal Name | Trusted | Customer Parent |
| ParentId | String (18 character SFDC ID) | SFDC ID linking customer to its shell | Trusted | Customer |
| Website | String | Website owned by the account | Trusted | Customer Parent |
| Billing_Address | String | State, Country, Postal Code | Trusted | Customer Parent |
| ZI_Company_Name__c | String | ZoomInfo enriched company/ organization name | Semi-reliable (enriched data– could be inaccurate) | Customer Parent |
| ZI_Website__c | String | ZoomInfo enriched website | Semi-reliable (enriched data– could be inaccurate) | Customer Parent |
| ZI_Billing_Address | String | ZoomInfo enriched State, Country, Postal Code | Semi-reliable (enriched data– could be inaccurate) | Customer Parent |
| Has_Shell | Boolean | TRUE if the account rolls up to a shell account | Trusted | Customer |
| Customer_Consistency | Score (0-100) and Explanation (String) | Attempt to determine level of internal account data coherence– fuzzy match score between account name and website | Computed (determine its significance based on contextual analysis) | Customer |
| Customer_Shell_Coherence | Score (0-100) and Explanation (String) | Attempt to measure how well a customer account's metadata aligns with its parent shell account– fuzzy match score between customer v shell account | Computed (determine its significance based on contextual analysis) | Customer |
| Address_Consistency | Boolean and Explanation (String) | TRUE if customer and shell account addresses match using precedence: Customer Billing_Address vs Parent ZI_Billing_Address (with fallbacks) | Computed (determine its significance based on contextual analysis) | Customer |

## 2 Validation– Is This a Valid Shell Relationship?

Apply a layered validation process. You are required to use your world knowledge and assume access to trusted external data sources when evaluating relationships. Fuzzy string comparisons alone are not sufficient:

* Customer metadata coherence: you must validate whether the customer's website and billing address logically belong to the claimed account name using real-world information
  * What does the Customer_Consistency score say about the customer metadata?
  * Normalize noisy values (e.g., Carlos Reyes vs carlosreyes.zumba.com)
  * Accepted branded subdomains and personal instructor URLs if clearly affiliated
* ONLY IF Has_Shell is TRUE →
  * Shell relationship coherence: you must evaluate the relationship the customer account and parent shell using known corporate structures, branding conventions, and public company knowledge
    * You must determine whether the customer is a known subsidiary, franchise, individual representative, department, regional office, or branch of the shell using external validation and world knowledge:
    * What does the Customer_Shell_Coherence score say about the relationship between the customer and parent shell account?
    * Do external sources agree that the customer account has some corporate relationship to its parent shell account?
  * Billing address match: compare addresses using precedence (Customer Billing vs Parent ZI, with fallbacks)
    * What does Address_Consistency say about the relationship between the customer and parent shell account?
    * The explanation will specify which exact address fields were compared (e.g., Customer Billing_Address vs Parent ZI_Billing_Address)
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

Evaluate each account-to-shell relationship based on three weighted pillars. Each is scored then summed and clamped to a maximum of 100. Use contextual judgment, not fixed thresholds.

| Pillar | Description |
|--------|-------------|
| Customer Metadata Coherence (0-30) | Does the customer account's name align with its website domain? Is the account's own field logically consistent? |
| Shell Relationship Coherence (0-50) | Does the customer logically roll up to the shell? Do their names/ websites indicate affiliation? Use real-world brand knowledge if needed? |
| Billing Address Coherence (0-20) | Are the customer and shell addresses close enough to suggest affiliation? If they differ, is that expected (e.g. remote rep, franchise)? |

For shell accounts (Has_Shell = False) only evaluate Customer Metadata Coherence and whether the account plausibly represents a corporate identity.

Assign lower scores for:
* Weak brand/ domain alignment
* Vague, noisy, or inconsistent naming
* Address mismatch with no logical explanation

Assign higher scores for:
* Clear domain-to-name coherence
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

## 7 Output Format (Strict JSON)

{
  "confidence_score": <int 0–100>,
  "explanation_bullets": [
    "✅ explanation 1",
    "⚠️ explanation 2",
    "❌ explanation 3"
  ]
}"""

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