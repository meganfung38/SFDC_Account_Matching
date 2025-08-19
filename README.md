# SFDC Account to Shell Account Relationship Assessment

## 🎯 **Project Overview**

This project provides an automated system to evaluate the validity of Salesforce account-to-shell-account relationships using field comparison, pattern analysis, and AI-powered confidence scoring. The goal is to identify misaligned parent-child relationships that cause poor data hygiene, misleading sales attribution, and operational inefficiencies.

### **Account Hierarchy Background**
RingCentral's Salesforce system uses a structured hierarchy:
- **Shell Accounts** (RecordType: "ZI Customer Shell Account"): ZoomInfo-enriched master entities representing business identities
- **Customer Accounts** (RecordType: "Customer Account"): Individual or departmental accounts that should roll up to appropriate shell accounts

### **Problem Statement**
Inconsistencies in data and incorrect associations have led to misaligned parent-child relationships, introducing:
- Poor data hygiene
- Misleading sales attribution  
- Fragmented customer insights
- Operational inefficiencies

---

## 🚀 **Current Implementation Status**

### ✅ **FULLY IMPLEMENTED: Complete Assessment System**

The system is **fully functional** with all core features implemented and operational:

#### **🎯 Core Assessment Features**
- **✅ Relationship Assessment Flags**: All 5 assessment flags implemented and computed
  - `Bad_Domain`: Boolean flag for filtering accounts with consumer/test email domains and websites
  - `Has_Shell`: Boolean flag indicating if account has a parent shell
  - `Customer_Consistency`: Fuzzy match score (0-100) for name/website alignment
  - `Customer_Shell_Coherence`: Fuzzy match score (0-100) for customer-shell metadata alignment
  - `Address_Consistency`: Boolean flag for billing address matching
- **✅ AI-Powered Confidence Scoring**: OpenAI GPT-4o integration with comprehensive system prompt
- **✅ Explainability**: Detailed AI-generated explanations with confidence scores and reasoning bullets
- **✅ Data Quality Filtering**: Automatic detection and filtering of bad domains to prevent analysis of low-quality accounts

#### **🌐 Web Interface & API Endpoints**
- **✅ Full-featured web UI** at `/` with three input methods:
  - **SOQL Query Analysis**: Validate queries and analyze returned accounts
  - **Single Account Analysis**: Direct account ID lookup and assessment
  - **Excel Upload Processing**: Batch processing with validation and analysis
- **✅ RESTful API** with comprehensive endpoints for all functionality
- **✅ Real-time validation** and error handling across all workflows

#### **📊 Account Data Retrieval (13 Fields)**
The system queries these fields for comprehensive account analysis:

**Standard Fields:**
- `Id` - Account's unique Salesforce ID
- `Name` - Account name
- `Website` - Account's website URL
- `RecordType.Name` - Account type (Shell vs Customer)

**Contact Information:**
- `ContactMostFrequentEmail__c` - Most frequently used contact email

**Address Fields:**
- `BillingState`, `BillingCountry`, `BillingPostalCode` - Billing address components
- `ZI_Company_State__c`, `ZI_Company_Country__c`, `ZI_Company_Postal_Code__c` - ZoomInfo address data

**ZoomInfo Enriched Fields:**
- `ZI_Company_Name__c`, `ZI_Website__c` - Enriched company data

**Parent Relationship Fields:**
- `ParentId` - Parent account ID via relationship
- `Parent.Name` - Parent account name via relationship

#### **🤖 AI Assessment System**
- **✅ OpenAI GPT-4o Integration**: Advanced AI-powered relationship validation
- **✅ External Knowledge Application**: AI leverages real-world corporate knowledge
- **✅ Comprehensive System Prompt**: Detailed instructions for consistent assessment
- **✅ Confidence Scoring**: 0-100 confidence scores with detailed explanations
- **✅ Error Handling**: Robust fallback when AI service is unavailable

#### **📁 Excel Processing & Export**
- **✅ Multi-step Workflow**: Parse → Validate → Analyze
- **✅ File Validation**: Sheet and column selection with real-time feedback
- **✅ Account ID Validation**: Pre-analysis validation to prevent errors
- **✅ Batch Processing**: Handle multiple accounts efficiently
- **✅ Excel Export**: Three export types with RingCentral theming
  - **SOQL/Single Account**: Full analysis with metadata, flags, and AI assessment
  - **Excel Input**: Original data + AI confidence score and explanation
  - **Summary Tables**: Processing statistics and confidence metrics

#### **🔧 Technical Infrastructure**
- **✅ Salesforce Integration**: Full API integration with connection management
- **✅ Fuzzy Matching Service**: Custom service for string similarity and domain analysis
- **✅ Error Handling**: Comprehensive error management and user feedback
- **✅ Performance Optimization**: Connection reuse and batch processing

---

## 🏗️ **Technical Architecture**

### **Core Technologies**
- **Backend**: Python Flask API
- **Data Layer**: Salesforce API integration via simple-salesforce
- **AI**: OpenAI GPT-4o integration
- **Frontend**: Responsive web interface with HTML/CSS/JavaScript
- **Data Processing**: pandas, openpyxl for Excel handling
- **Fuzzy Matching**: Custom service with domain extraction and name normalization

### **Service Layer Architecture**
```
services/
├── salesforce_service.py   # SOQL queries, account data retrieval, flag computation
├── openai_service.py       # AI prompt management and completion
├── excel_service.py        # File processing and validation
├── fuzzy_matching_service.py # String similarity and domain analysis
├── bad_domain_service.py   # Bad domain detection and filtering
```

### **Key Components**

#### **Flag Computation Engine**
- **Bad_Domain**: Detects consumer/test domains in email and website fields with intelligent pattern matching
- **Has_Shell**: Validates parent account relationships using `ParentId` field
- **Customer_Consistency**: Fuzzy matching between account name and website/ZI data
- **Customer_Shell_Coherence**: Multi-dimensional comparison with detailed field-level explanations
- **Address_Consistency**: Intelligent address comparison using field precedence (Customer Billing vs Parent ZI, with fallbacks)

#### **AI Assessment System**
- **System Prompt**: Comprehensive instructions for relationship validation
- **External Knowledge**: Leverages AI's understanding of corporate structures
- **Confidence Scoring**: 0-100 scores with detailed reasoning
- **Error Resilience**: Graceful fallback when AI service unavailable

#### **Web Interface**
- **Collapsible Output**: Organized display with toggleable sections
- **Real-time Validation**: Immediate feedback on inputs and errors
- **Consistent Formatting**: Unified output format across all workflows
- **Export Ready**: Infrastructure for future Excel export functionality

---

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.8+
- Salesforce org access with API enabled
- OpenAI API key
- Required Python packages (see `config/requirements.txt`)

### **Setup**
1. **Clone repository and install dependencies**:
   ```bash
   pip install -r config/requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp config/env.example .env
   # Edit .env with your Salesforce and OpenAI credentials
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access web interface**: http://localhost:5000

### **API Testing**
```bash
# Test Salesforce connection
curl http://localhost:5000/test-salesforce-connection

# Test OpenAI connection  
curl http://localhost:5000/test-openai-connection

# Get single account analysis
curl http://localhost:5000/account/0012H00001cH3WB
```

---

## 📊 **API Endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Web interface |
| `/account/{id}` | GET | Single account analysis |
| `/accounts/analyze-query` | POST | Validate SOQL queries, return Account IDs |
| `/accounts/get-data` | POST | Batch account data retrieval with full assessment |
| `/excel/parse` | POST | Parse Excel files, return structure |
| `/excel/validate-account-ids` | POST | Validate Account IDs from Excel |
| `/export/soql-analysis` | POST | Export SOQL analysis results to Excel |
| `/export/single-account` | POST | Export single account analysis to Excel |
| `/export/excel-analysis` | POST | Export Excel analysis results to Excel |
| `/test-salesforce-connection` | GET | Test Salesforce connectivity |
| `/test-openai-connection` | GET | Test OpenAI API connectivity |

---

## 🎯 **Usage Examples**

### **SOQL Query Analysis**
1. Enter complete SOQL query (e.g., `SELECT Id FROM Account WHERE Industry = 'Technology'`)
2. Click "Validate Account IDs" to get account list
3. Click "Analyze Accounts" for full assessment with flags and AI scoring
4. Click "📊 Export to Excel" to download comprehensive analysis results

### **Single Account Analysis**
1. Enter Salesforce Account ID (15 or 18 characters)
2. Click "Analyze Account" for immediate assessment
3. Click "📊 Export to Excel" to download analysis results

### **Excel Upload Analysis**
1. Upload Excel file with Account IDs
2. Click "Parse File" to extract structure
3. Select sheet and Account ID column
4. Click "Validate Account IDs" to verify with Salesforce
5. Click "Analyze Accounts" for full assessment
6. Click "📊 Export to Excel" to download original data + AI analysis

---

## 📈 **Output Format**

All workflows produce consistent, collapsible output with:

### **Summary Section**
- Processing statistics and execution time
- Validation results and account counts

### **Account Analysis**
- **Account Details**: All 12 Salesforce fields in collapsible section
- **Relationship Assessment Flags**: 4 computed flags with scores/explanations
- **Parent Shell Account Data**: Shell account information (when applicable)
- **AI-Powered Assessment**: Confidence score (0-100) with detailed reasoning bullets

### **AI Assessment Features**
- **External Knowledge**: Leverages AI's understanding of corporate relationships
- **Confidence Scoring**: 0-100 scores indicating relationship validity
- **Detailed Explanations**: Bullet-point reasoning for each assessment
- **Error Handling**: Graceful fallback when AI service unavailable

### **Excel Export Features**
- **SOQL/Single Account**: Account metadata, assessment flags, and AI analysis in organized tables with frozen panes
- **Excel Input**: Original Excel data + AI confidence score and explanation appended to the right
- **Summary Tables**: Processing statistics and confidence score metrics
- **RingCentral Theming**: Professional styling with corporate colors
- **Sample Export**: [View sample SOQL analysis export](https://docs.google.com/spreadsheets/d/1N_o4rBYNrakOTZS25jTi7mx8AzqezeW0/edit?usp=sharing&ouid=113726783832302437979&rtpof=true&sd=true)
- **Bad Domain Sample**: [View bad domain filtering example](https://docs.google.com/spreadsheets/d/1lR7YUN0i72QUC4spYk-xHTFDn-P3rk0p/edit?usp=sharing&ouid=113726783832302437979&rtpof=true&sd=true)
- **Demo Walkthrough**: [Watch demo walkthrough](https://drive.google.com/file/d/1Y5TNF1La23kzbGhlaSc8GCIp3Fu11Uwo/view?usp=sharing)
- **Latest Changes Demo**: [View recent feature updates](https://drive.google.com/file/d/1xoAItHK8u5FYcGWQhFZL8NRi3TYsIcb5/view?usp=sharing) 

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Salesforce Configuration
SF_USERNAME=your_salesforce_username
SF_PASSWORD=your_salesforce_password
SF_SECURITY_TOKEN=your_salesforce_security_token
SF_DOMAIN=login  # or test for sandbox

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=1000
```

### **Performance Settings**
- **Batch Processing**: Up to 500 accounts per request
- **Connection Timeout**: 1-hour Salesforce connection reuse
- **Query Limits**: Configurable SOQL query limits

---

## 📝 **Documentation**

- **[Project Breakdown](docs/project_breakdown.md)**: Complete project scope and requirements
- **[Data Interpretation Guide](docs/data_interpretation.md)**: AI system prompt and assessment logic
- **API Documentation**: Available at `/api` endpoint when running
- **Configuration Guide**: See `config/env.example` for setup details

---

## 🎯 **Project Goals Achievement**

This implementation **fully addresses** the project requirements outlined in [project_breakdown.md](docs/project_breakdown.md):

| Requirement | Status | Implementation |
|-------------|--------|---------------|
| **Data Extraction** | ✅ Complete | 12-field comprehensive account retrieval |
| **Input Flexibility** | ✅ Complete | SOQL queries, single IDs, Excel uploads |
| **Flag Computation** | ✅ Complete | All 4 flags implemented and computed |
| **AI Confidence Scoring** | ✅ Complete | OpenAI GPT-4o integration with external knowledge |
| **Explainability** | ✅ Complete | Detailed AI-generated explanations |
| **Web Interface** | ✅ Complete | Full-featured UI with all input methods |

---

## 🤝 **Contributing**

This project is production-ready with clear separation of concerns:
- **Core API**: Handle data retrieval and flag computation
- **AI Integration**: Advanced scoring and explanation generation
- **Web Interface**: User-friendly access to all functionality
- **Excel Processing**: Batch workflow with validation

Each component is fully implemented and tested, providing a complete solution for Salesforce account relationship assessment.