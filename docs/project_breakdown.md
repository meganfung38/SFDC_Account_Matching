## **Project 3– SFDC Shell Account Assessment**

### **SFDC Account Hierarchy** 

* RC uses a structured Salesforce account hierarchy to model organizational relationships. This system groups customer records under a unified corporate identity for better data hygiene and strategic visibility   
* Parent Account (Record Type: ZI Customer Shell Account)  
  * Represents the top-level corporate identity (e.g., headquarters or holding company)   
  * Links together all associated customer accounts  
* Child Account (Record Type: Customer Account)  
  * Represents a transacting business unit (local branch, regional office, individual, department, or subsidiary of the shell/ parent company)   
  * The actual entity buying or using RC products/ services 

### **Problem Statement**

* Shell accounts are designed to unify customer-level records under one corporate identity. However, inconsistencies in data and incorrect associations have led to misaligned parent-child relationships within SFDC. This introduces:   
  * Poor data hygiene   
  * Misleading sales attribution   
  * Fragmented customer insights   
  * Operational inefficiencies


### **Solution**

* Build an automated system to evaluate the validity of SFDC account-to-shell-account relationships using field comparison and pattern analysis.   
  * Inputs:   
    * list of SFDC account IDs (via SOQL query or excel upload)   
    * Single SFDC account ID   
    * Single SFDC shell account ID (to trigger batch evaluation of its child accounts)  
  * Output:   
    * Confidence scoring (%) for each account-shell pairing that reflects the likelihood of a correct match   
    * An explanation detailing why the score was assigned  
    * Flags and metadata indicators for further review

    

* Steps:    
1. Salesforce Data Extraction  
* Shell and Customer Account data: 

| Field  | Description | API Name |
| :---- | :---- | :---- |
| *Id*  | 18 Character SFDC Id | Id |
| *Account Name*  | Company/ Organization/ Personal Name | Name |
| *Parent Account ID*  | 18 Character SFDC Id | ParentId |
| *Parent Account Name*  | Shell Account Company/ Organization | Parent.Name |
| *Website*  | Associated Website | Website |
| *Contact Most Frequent Email*  | Associated Email | ContactMostFrequentEmail__c |
| *Billing Address*  | Location  | BillingState, BillingCountry, BillingPostalCode |
| *ZI Company Name*  | ZoomInfo Enriched Company Name | ZI\_Company\_Name\_\_c |
| *ZI Website* | ZoomInfo Enriched Company Name | ZI\_Website\_\_c  |
| *ZI Billing Address*  | Location  | ZI_Company_State, ZI_Company_Country__c, ZI_Company_Postal_Code__c |

* Flags: 

| Flags  | Data Type | Meaning  |
| :---- | :---- | :---- |
| Bad\_Domain  | Boolean (True/ False) | Whether ContactMostFrequentEmail__c or Website has a bad domain. If TRUE, skip further analysis. |
| Has\_Shell  | Boolean (True/ False) | Whether ParentId is null or points to itself |
| Customer\_Consistency   | Fuzzy Match Score (0-100) | Whether the account name and website align |
| Customer\_Shell\_Coherence  | Fuzzy Match Score (0-100) | Whether the customer account metadata aligns with its shell's metadata (name and website) ONLY compute if Has\_Shell is TRUE |
| Address\_Consistency | Boolean (True/ False) | Whether the customer billing address and shell ZI billing address match ONLY compute if Has\_Shell is TRUE |

3. Bad Domains 
* Accounts flagged with Bad_Domain indicate that the account uses a free or invalid email/ website domain. These accounts will be excluded from further analysis. 
 
2. Confidence Score Generation  
* Design a hybrid model that uses fuzzy logic, contextual analysis, and LLM prompts to evaluate the validity of each account-to-shell relationship  
  * **Flag verification**: Leverage Customer\_Consistency and Customer\_Shell\_Coherence similarity scores as signals   
1. **Customer Metadata Coherence**: evaluate whether the account’s website and name logically belong together (use Customer\_Consistency score)   
   * Does the account’s website and billing address belong to the claimed account name?   
2. **Customer to Shell Coherence (only if Has\_Shell is TRUE)**: Compare account name and website to those its parent shell (use Customer\_Shell\_Coherence score)  
   * **External sourcing**: using external data sources (e.g., ZoomInfo, public directories), determine if the customer account is:   
     * A known local branch, regional office, individual, department, or subsidiary of the shell  
       * What does the Customer\_Shell\_Coherence score say about the relationship between the customer account and its parent shell account?   
       * Do external sources agree that the customer account has some corporate relationship to its parent shell account?	  
     * **Address Consistency**: evaluate billing address alignment and interpret address coherence based on regional vs global presence (use Address\_Consistency)   
3. **Weighting Scoring**: assign tunable weights to each factor  
   * **Customer Metadata Coherence**: does the account data seem independently valid?   
     * **Customer to Shell Account Coherence**: does the relationship with the parent shell account make sense?   
     * **Address Consistency**: do the locations suggest a valid relationship?   
4. **Edge Case**: use AI to normalize noisy names, determine domain affliction, evaluate overall relationship coherence across fields  
5. **Output:** a confidence score (%) indicating the likelihood of a correct account-to-shell match

   

3. Explainability   
* Plain language rationale describing:  
  * Which fields matched or diverged  
  * How strong alignment was (without showing internal calculations)  
  * Why the system believes a relationship is valid, unclear, or mismatched  
* Explanation should help:   
  * Build trust and transparency in the model  
  * Enable informed decision making and manual review when necessary 