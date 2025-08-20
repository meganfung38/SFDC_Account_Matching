## **Project 4– SFDC Account Matching** 

### **SFDC Account Hierarchy** 

* RC uses a structured Salesforce account hierarchy to model organizational relationships. This system groups customer records under a unified corporate identity for better data hygiene and strategic visibility   
* Parent Account (Record Type: ZI Customer Shell Account)  
  * Represents the top-level corporate identity (e.g., headquarters or holding company)   
  * Links together all associated customer accounts  
* Child Account (Record Type: Customer Account)  
  * Represents a transacting business unit (local branch, regional office, individual, department, or subsidiary of the shell/ parent company)   
  * The actual entity buying or using RC products/ services 

### **Problem Statement**

* Many customer accounts are not currently assigned to a shell account, even though they should be. This gap prevents us from fully unifying customer level records under their parent corporate identity. As a result, the organization lacks complete strategic visibility into corporate relationships and risks degraded data quality in Salesforce. 

### **Solution**

* Build an automated system that, given two Excel inputs:   
  * A list of customer accounts (to be parent-ed)  
  * A list of ZI shell accounts (authorized shell universe)

  Finds the best parent shell for each customer and produces: 

  * A best match recommendation (best shell candidate– Id \+ Name)   
  * AI Confidence score (0-100)  
  * AI plain language explanation (which fields matched, which rules fired, why the score was assigned)   
  * Transparent rationale and flags to speed up human review  
* Steps:    
1. Salesforce Data Extraction  
* Customer Account data (non ZI fields):  

| Field  | Description | API Name |
| :---- | :---- | :---- |
| *Id*  | 18 Character SFDC Id | Id |
| *Account Name*  | Company/ Organization/ Personal Name | Name |
| *Website*  | Associated Website | Website |
| *Billing Address*  | Location  |  BillingCity, BillingState, BillingCountry, BillingPostalCode |

* Shell Account data (ZI fields only): 

| Field  | Description | API Name |
| :---- | :---- | :---- |
| *Id*  | 18 Character SFDC Id | Id |
| *ZI ID* | 9 Digit ZI Id  | ZI\_Id\_\_c |
| *ZI Account Name*  | ZoomInfo Enriched Company/ Organization/ Personal Name | ZI\_Company\_Name\_\_c |
| *ZI Website* | ZoomInfo Enriched Associated Website | ZI\_Website\_\_c  |
| *ZI Billing Address*  | ZoomInfo Enriched Location  | ZI\_Company\_City\_\_c, ZI\_Company\_State\_\_c, ZI\_Company\_Country\_\_c, ZI\_Company\_Postal\_Code\_\_c |

* Flags: 

| Flags  | Data Type | Meaning  |
| :---- | :---- | :---- |
| Bad\_Domain  | Boolean (True/ False) | Whether the website has a bad domain. If TRUE, skip further analysis.  |

2. Bad Domains  
* Accounts flagged with Bad\_Domain indicate that the account uses a free or invalid website domain. These accounts will be excluded from further analysis.  
3. Matching Algorithm  
* Build comparable representations for input customer and shell records:   
  * Name tokens (normalized, de-noised, legal suffix handling)   
  * Website/ domain (registered domain; handle redirects/ aliases if known)   
  * Geo signals (city/ state/ country/ postal as categorical or proximity)   
* Data precedence:   
  * Website \> Account Name for entity identity   
  * If website and name conflict, website wins  
  * If website is null, fall back to exact/ near name match (to ZI name)   
  * If both website and name null, use address signals (city/ state/ country/ postal)   
* For each customer account, compute similarity against all shell accounts using:   
  * Cosine similarity/ distance   
  * K-nearest neighbors (kNN)  
  * Two stage retrieval:   
    * Fast filter by website/ name hash buckets   
    * Re-rank with richer similarity   
* Scoring signals: 

| Signal  | Data Type  | Meaning |
| :---- | :---- | :---- |
| Website\_Match  | Fuzzy Match Score (0-100)  | How similar the customer and shell account websites are |
| Name\_Match | Fuzzy Match Score (0-100) | How similar the customer and shell account names are |
| Address\_Consistency  | Score (0-100)  | Country match (+30)  State match (+30)  City match (+30)  Postal code match (+10)  |

4. Confidence Score Generation  
* Design a hybrid model that uses fuzzy logic, contextual analysis, and LLM prompts to evaluate the validity of each account-to-shell relationship  
  * **Signal verification**: Leverage Website\_Match, Name\_Match, and Address\_Consistency similarity scores as signals   
1. **Customer to Shell Coherence**: Compare account name and website to those of its parent shell (use Website\_Match and Name\_Match scores)  
   * **External sourcing**: using external data sources (e.g., ZoomInfo, public directories), determine if the customer account is:   
     * A known local branch, regional office, individual, department, or subsidiary of the shell  
       * What does the Customer\_Shell\_Coherence score say about the relationship between the customer account and its parent shell account?   
       * Do external sources agree that the customer account has some corporate relationship to its parent shell account?	  
     * **Address Consistency**: evaluate billing address alignment and interpret address coherence based on regional vs global presence (use Address\_Consistency)   
2. **Weighting Scoring**: assign tunable weights to each factor  
   * **Customer to Shell Account Coherence**: does the relationship with the parent shell account make sense?   
     * **Address Consistency**: do the locations suggest a valid relationship?   
3. **Edge Case**: use AI to normalize noisy names, determine domain affliction, evaluate overall relationship coherence across fields  
4. **Output:** a confidence score (%) indicating the likelihood of a correct account-to-shell match

   

5. Explainability   
* Plain language rationale describing:  
  * Which fields matched or diverged  
  * How strong alignment was (without showing internal calculations)  
  * Why the system believes a relationship is valid, unclear, or mismatched  
* Explanation should help:   
  * Build trust and transparency in the model  
  * Enable informed decision making and manual review when necessary 