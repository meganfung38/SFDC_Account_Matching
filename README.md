# 🎯 Customer-to-Shell Account Matching System

An intelligent AI-powered system that matches customer accounts to their most suitable parent shell accounts in Salesforce. Upload two Excel files and get comprehensive matching results with confidence scoring and detailed explanations.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Demo Video](#🎥-demo-video)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Data Fields](#data-fields)
- [Batch Processing & Performance](#-batch-processing--performance)
- [Matching Algorithm](#matching-algorithm)
- [Excel Export Format](#excel-export-format)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Overview

The Customer-to-Shell Account Matching System revolutionizes how organizations manage their account hierarchies in Salesforce. Instead of manual relationship assessment, this system uses advanced fuzzy matching algorithms and AI-powered analysis to intelligently match customer accounts to their optimal parent shell accounts.

### 🎥 Demo Video
**Watch the system in action:** [Demo Walkthrough](https://drive.google.com/file/d/1gAKrTDIhgsVqMadivsJlcFw1PXiS2IBO/view?usp=sharing)

### Key Capabilities

- **Dual-File Processing**: Upload customer and shell account Excel files
- **Intelligent Matching**: Advanced two-stage retrieval algorithm with fuzzy matching
- **AI-Powered Scoring**: OpenAI integration for confidence assessment and explanations
- **Data Quality Filtering**: Automatic bad domain detection and exclusion
- **Invalid ID Handling**: Graceful processing with invalid IDs excluded but tracked
- **High-Performance Batching**: Configurable batch processing for datasets of any size
- **Comprehensive Results**: One row per customer with complete metadata and match details
- **Professional Export**: Multi-worksheet Excel reports with summary metrics ([view sample](https://docs.google.com/spreadsheets/d/1eXpxC7F79lLkkgTNtVCuXvzZSCkGwSzF/edit?usp=sharing&ouid=113726783832302437979&rtpof=true&sd=true))

## ✨ Features

### 🚀 Core Functionality

- **Step-by-Step Workflow**: Intuitive 4-step process with visual progress indicators
- **Real-Time Validation**: Salesforce ID validation with immediate feedback on invalid IDs
- **Smart Filtering**: Automatic exclusion of accounts with bad domains (Gmail, Yahoo, etc.)
- **Fuzzy Matching**: Website, name, and address similarity scoring
- **AI Integration**: Confidence scoring and plain-language explanations
- **Batch Processing**: Handle thousands of accounts with intelligent batching and rate limiting

### 🎨 User Experience

- **Modern UI**: Beautiful RingCentral-themed interface
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Progress Tracking**: Real-time status updates and progress indicators
- **Error Handling**: Clear, actionable error messages
- **Global Notifications**: Auto-hiding status messages

### 📊 Data & Export

- **Flexible Input**: Any Excel file format with user-specified columns (handles invalid IDs gracefully)
- **Complete Metadata**: Full customer and shell account information
- **Multi-Sheet Export**: Organized results with summary metrics
- **Status Tracking**: MATCHED/UNMATCHED/FLAGGED/INVALID classifications
- **Confidence Metrics**: Multiple scoring dimensions with explanations

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │   Flask API      │    │   Salesforce    │
│                 │◄──►│                  │◄──►│      API        │
│ • Step-by-step  │    │ • Route handlers │    │ • Account data  │
│ • File uploads  │    │ • Validation     │    │ • ID validation │
│ • Results view  │    │ • Processing     │    │ • Field queries │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────┴────────┐
                       │                 │
            ┌──────────▼─────────┐    ┌──▼─────────────┐
            │   Core Services    │    │   OpenAI API   │
            │                    │    │                │
            │ • Fuzzy Matching   │    │ • Confidence   │
            │ • Excel Processing │    │ • Explanations │
            │ • Bad Domains      │    │ • Assessment   │
            └────────────────────┘    └────────────────┘
```

### Core Services

1. **SalesforceService**: Data extraction, validation, filtering
2. **FuzzyMatchingService**: Two-stage matching algorithm
3. **OpenAI_Service**: AI confidence scoring and explanations
4. **ExcelService**: File parsing and export generation
5. **BadDomainService**: Domain quality filtering

## 📋 Prerequisites

- **Python 3.8+**
- **Salesforce Account** with API access
- **OpenAI API Key** for AI-powered analysis
- **Excel Files** with customer and shell account IDs

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SFDC_Account_Matching
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r config/requirements.txt
```

### 4. Configure Environment

Copy the environment template and configure your credentials:

```bash
cp config/env.example .env
```

Edit `.env` with your credentials:

```env
# Salesforce Configuration
SF_USERNAME=your_salesforce_username
SF_PASSWORD=your_salesforce_password
SF_SECURITY_TOKEN=your_security_token
SF_DOMAIN=login  # or your custom domain

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=1000

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=true

# Batch Processing Configuration (Optional - defaults provided)
SALESFORCE_BATCH_SIZE=200          # SOQL query batch size (max ~1000)
OPENAI_BATCH_SIZE=10               # Concurrent OpenAI API calls
OPENAI_RATE_LIMIT_DELAY=0.5        # Seconds between OpenAI calls
```

## ⚙️ Configuration

### Salesforce Setup

1. **API Access**: Ensure your Salesforce user has API access
2. **Security Token**: Generate a security token from Salesforce Setup
3. **Custom Fields**: Verify ZI fields exist on Account object:
   - `ZI_Company_Name__c`
   - `ZI_Website__c`
   - `ZI_Company_City__c`
   - `ZI_Company_State__c`
   - `ZI_Company_Country__c`
   - `ZI_Company_Postal_Code__c`

### OpenAI Setup

1. **API Key**: Obtain from [OpenAI Platform](https://platform.openai.com/)
2. **Model Access**: Ensure access to GPT-4 or desired model
3. **Rate Limits**: Consider usage limits for batch processing

## 📖 Usage

### 1. Start the Application

```bash
source venv/bin/activate
python app.py
```

Access the UI at: `http://localhost:5000`

**💡 New to the system?** [Watch the demo walkthrough](https://drive.google.com/file/d/1gAKrTDIhgsVqMadivsJlcFw1PXiS2IBO/view?usp=sharing) to see the complete process in action.

### 2. Step-by-Step Process

#### Step 1: Upload Customer Accounts
- Select Excel file containing customer account IDs
- Choose sheet and column containing the IDs
- System validates all IDs with Salesforce
- **Invalid IDs are identified and excluded from matching**

#### Step 2: Upload Shell Accounts
- Select Excel file containing shell account IDs
- Choose sheet and column containing the IDs
- System validates all IDs and checks ZI data quality
- **Invalid IDs are identified and excluded from matching**

#### Step 3: Process Matching
- Review summary of accounts to be processed
- Click "Start Matching Process"
- System performs intelligent matching with AI analysis
- Progress indicator shows real-time status

#### Step 4: Results & Export
- View summary metrics and success rates
- Browse detailed results table
- Export comprehensive Excel report
- Option to reset and start new process

### 3. Excel File Requirements

#### Input Files
- **Format**: `.xlsx` or `.xls`
- **Structure**: Any layout with identifiable Account ID column
- **IDs**: Valid 15 or 18-character Salesforce Account IDs

#### Example Customer File
| Account Name | Account ID | Region |
|--------------|------------|--------|
| Acme Corp    | 0018c00002ABC123 | West |
| Tech Inc     | 0018c00002DEF456 | East |

#### Example Shell File
| Shell Account | Shell ID | Category |
|---------------|----------|----------|
| Acme Corporation | 0018c00002XYZ789 | Enterprise |
| Technology Inc   | 0018c00002UVW012 | SMB |

## 🔌 API Documentation

### Core Endpoints

#### POST `/excel/parse-customer-file`
Upload and validate customer account Excel file.

**Parameters:**
- `file`: Excel file upload
- `sheet_name`: Sheet name containing data
- `account_id_column`: Column name with Account IDs

**Response:**
```json
{
  "status": "success",
  "message": "Validation complete: 48 valid, 2 invalid customer account IDs. Invalid IDs: [unknown, bad]. Invalid IDs will be excluded from matching.",
  "data": {
    "validation_summary": {
      "valid_account_ids": ["0018c00002ABC123", "..."],
      "invalid_account_ids": ["unknown", "bad"],
      "total_from_excel": 50
    }
  }
}
```

#### POST `/excel/parse-shell-file`
Upload and validate shell account Excel file.

#### POST `/matching/process-batch`
Process dual-file matching algorithm.

**Request:**
```json
{
  "customer_account_ids": ["0018c00002ABC123", "..."],
  "shell_account_ids": ["0018c00002XYZ789", "..."],
  "invalid_customer_ids": ["unknown", "bad"],
  "invalid_shell_ids": []
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "summary": {
      "total_customer_accounts": 50,
      "matched_pairs": 45,
      "unmatched_customers": 3,
              "flagged_customer_accounts": 2,
        "invalid_customer_accounts": 1,
        "execution_time": "2.34s"
      },
      "matched_pairs": [...],
      "unmatched_customers": [...],
      "flagged_customers": [...],
      "invalid_customers": [...]
  }
}
```

#### POST `/export/matching-results`
Generate Excel export of matching results.

### Testing Endpoints

- `GET /health`: System health check
- `GET /test-salesforce-connection`: Validate Salesforce connectivity
- `GET /test-openai-connection`: Validate OpenAI API access

## 📊 Data Fields

### Customer Account Fields (Extracted)
- `Id`: Salesforce Account ID
- `Name`: Account name
- `Website`: Company website
- `BillingCity`: Billing city
- `BillingState`: Billing state/province
- `BillingCountry`: Billing country
- `BillingPostalCode`: Billing postal code

### Shell Account Fields (Extracted)
- `Id`: Salesforce Account ID
- `ZI_Id__c`: ZoomInfo company ID
- `ZI_Company_Name__c`: ZoomInfo company name
- `ZI_Website__c`: ZoomInfo website
- `ZI_Company_City__c`: ZoomInfo company city
- `ZI_Company_State__c`: ZoomInfo company state
- `ZI_Company_Country__c`: ZoomInfo company country
- `ZI_Company_Postal_Code__c`: ZoomInfo postal code

## ⚡ Batch Processing & Performance

### 🚀 Intelligent Batch Processing

The system is designed to handle large datasets efficiently through intelligent batch processing that automatically optimizes performance while maintaining all functionality.

#### 📊 Performance Capabilities

| Dataset Size | Processing Time | Salesforce Queries | OpenAI Calls | Status |
|--------------|----------------|-------------------|--------------|--------|
| **50-100 accounts** | 30-60 seconds | 1 batch | 1 batch | ✅ Optimal |
| **200-500 accounts** | 2-5 minutes | 2-3 batches | 5-10 batches | ✅ Fast |
| **500-1000 accounts** | 5-10 minutes | 3-5 batches | 10-20 batches | ✅ Efficient |
| **1000-2000 accounts** | 10-20 minutes | 5-10 batches | 20-40 batches | ✅ Scalable |
| **2000+ accounts** | 20+ minutes | 10+ batches | 40+ batches | ✅ Enterprise-ready |

#### 🔧 Two-Phase Processing Architecture

**Phase 1: Fast Fuzzy Matching**
- Process all customer accounts through fuzzy matching algorithms
- No external API calls - pure algorithmic processing
- Identifies matched vs unmatched customers quickly

**Phase 2: Batch AI Assessment**
- Collects all matched pairs from Phase 1
- Processes OpenAI assessments in parallel batches with rate limiting
- Adds AI confidence scores and explanations to results

#### ⚙️ Configurable Batch Settings

The system provides three key configuration parameters to optimize performance for your environment:

```env
# Batch Processing Configuration
SALESFORCE_BATCH_SIZE=200          # SOQL query batch size (default: 200)
OPENAI_BATCH_SIZE=10               # Concurrent OpenAI API calls (default: 10)
OPENAI_RATE_LIMIT_DELAY=0.5        # Seconds between OpenAI calls (default: 0.5)
```

**Configuration Guidelines:**

| Parameter | Recommended Range | Purpose | Impact |
|-----------|------------------|---------|---------|
| `SALESFORCE_BATCH_SIZE` | 100-500 | Prevents SOQL query limits | Higher = fewer queries, but risk of timeout |
| `OPENAI_BATCH_SIZE` | 5-20 | Controls concurrent API calls | Higher = faster, but may hit rate limits |
| `OPENAI_RATE_LIMIT_DELAY` | 0.2-2.0 | Prevents rate limiting | Lower = faster, but higher risk of rate limits |

#### 🔍 Progress Monitoring

For large datasets, the system provides real-time progress updates:

```
🔍 Processing fuzzy matching for 1000 customer accounts...
✅ Processed customer batch 1/5 (200 IDs)
✅ Processed customer batch 2/5 (200 IDs)
✅ Processed shell batch 1/3 (200 IDs)
✅ Fuzzy matching complete: 850 matched, 150 unmatched
🤖 Starting batch AI assessment for 850 matches...
🤖 Processing 850 AI assessments in 85 batches...
✅ Processed AI batch 1/85 (10 assessments)
✅ Processed AI batch 25/85 (10 assessments)
...
```

#### 🛡️ Built-in Safeguards

- **SOQL Limit Protection**: Automatically chunks large ID lists to prevent query failures
- **Rate Limit Compliance**: Intelligent delays between API calls to respect OpenAI limits
- **Memory Management**: Processes data in chunks to prevent memory exhaustion
- **Error Isolation**: Individual batch failures don't stop the entire process
- **Timeout Prevention**: Progress updates keep UI responsive during long operations

#### 🎯 Optimization Tips

**For Large Customer Lists (1000+):**
- Increase `SALESFORCE_BATCH_SIZE` to 300-400 for fewer Salesforce queries
- Keep `OPENAI_BATCH_SIZE` at 10-15 to respect rate limits
- Use `OPENAI_RATE_LIMIT_DELAY` of 0.3-0.5 for optimal throughput

**For High OpenAI Rate Limits:**
- Increase `OPENAI_BATCH_SIZE` to 15-20 for faster processing
- Decrease `OPENAI_RATE_LIMIT_DELAY` to 0.2-0.3 for minimal delays

**For Conservative Processing:**
- Keep `SALESFORCE_BATCH_SIZE` at 100-200 for stability
- Use `OPENAI_BATCH_SIZE` of 5-8 for conservative rate limiting
- Set `OPENAI_RATE_LIMIT_DELAY` to 1.0+ for maximum safety

## 🔍 Matching Algorithm

### Two-Stage Retrieval Process

#### Stage 1: Fast Filtering
1. **Website Domain Matching**: Hash buckets by domain
2. **Name-Based Filtering**: Normalized company names
3. **Candidate Reduction**: Narrow to most promising matches

#### Stage 2: Comprehensive Scoring
1. **Website Match**: Domain and URL similarity
2. **Name Match**: Fuzzy string matching with variations
3. **Address Consistency**: Geographic alignment scoring
4. **Overall Confidence**: Weighted combination of signals

### Scoring Dimensions

#### Website Match (0-100%)
- Exact domain match: 100%
- Subdomain match: 80%
- Similar domains: 60%
- No match: 0%

#### Name Match (0-100%)
- Exact match: 100%
- High similarity: 80-99%
- Moderate similarity: 50-79%
- Low similarity: 20-49%
- No match: 0-19%

#### Address Consistency (0-100 points)
- Country match: +30 points
- State match: +30 points
- City match: +30 points
- Postal code match: +10 points

### Data Precedence Rules
1. **Website > Name**: Website domain takes priority for entity identity
2. **Name > Address**: Company name more important than location
3. **Combined Signals**: All factors contribute to final confidence

## 📈 Excel Export Format

### 📄 Sample Export
**View a complete sample export:** [Sample Excel Export Results](https://docs.google.com/spreadsheets/d/1eXpxC7F79lLkkgTNtVCuXvzZSCkGwSzF/edit?usp=sharing&ouid=113726783832302437979&rtpof=true&sd=true)

### Sheet 1: "Customer Match Results"
Complete results with one row per customer account:

| Column | Description |
|--------|-------------|
| Customer ID | Salesforce Account ID |
| Customer Name | Account name |
| Customer Website | Company website |
| Customer Billing Address | Full billing address |
| Match Status | MATCHED/UNMATCHED/FLAGGED/INVALID |
| Match Reason | Explanation of status |
| Recommended Shell ID | Best match shell ID (if any) |
| Shell Name | Shell account name (if matched) |
| Shell ZI ID | ZoomInfo company ID (if matched) |
| Shell Website | Shell website (if matched) |
| Shell Billing Address | Shell address (if matched) |
| Overall Match Confidence | Combined confidence percentage |
| Website Match Score | Website similarity score |
| Name Match Score | Name similarity score |
| Address Consistency Score | Address alignment score |
| AI Confidence Score | OpenAI assessment score |
| AI Explanation | Detailed AI reasoning |
| Candidate Count | Number of shells evaluated |
| Processing Notes | Technical details |

### Sheet 2: "Summary Metrics"
Processing statistics and success rates:

| Metric | Description |
|--------|-------------|
| Total Customer Accounts Processed | Input count |
| Successfully Matched | Matched pairs |
| Unable to Match | No suitable shells found |
| Flagged (Bad Domains) | Excluded accounts |
| Invalid Account IDs | Invalid or non-existent IDs |
| Total Shell Accounts Available | Shell universe size |
| Processing Time | Execution duration |
| Match Success Rate | Percentage matched |

## 🔧 Troubleshooting

### Common Issues

#### Salesforce Connection Errors
```
Error: Invalid credentials or security token
```
**Solution**: 
1. Verify username/password in `.env`
2. Reset Salesforce security token
3. Check domain configuration

#### OpenAI API Errors
```
Error: Invalid API key
```
**Solution**:
1. Verify API key in `.env`
2. Check OpenAI account billing status
3. Confirm model access permissions

#### Excel Parsing Errors
```
Error: Column 'Account_ID' not found in sheet 'Sheet1'
```
**Solution**:
1. Verify sheet name exactly matches
2. Check column header spelling
3. Ensure column contains Account IDs

#### Invalid Account IDs
```
Validation complete: 48 valid, 2 invalid customer account IDs. 
Invalid IDs: [unknown, bad]. Invalid IDs will be excluded from matching.
```
**Note**: Invalid IDs are automatically handled:
1. Format validation catches non-Salesforce ID formats
2. Salesforce validation identifies non-existent IDs  
3. Invalid IDs are excluded from matching but included in final export
4. Process continues with valid IDs only

### Performance Optimization

#### Large File Processing
- **Automatic Batching**: System handles 2000+ accounts efficiently with intelligent batching
- **Configurable Settings**: Adjust `SALESFORCE_BATCH_SIZE`, `OPENAI_BATCH_SIZE`, and `OPENAI_RATE_LIMIT_DELAY` in `.env`
- **Memory Management**: Chunked processing prevents memory exhaustion
- **Progress Monitoring**: Real-time batch progress updates for large datasets

#### API Rate Limits
- **Salesforce Batching**: Automatic SOQL query chunking (configurable batch size)
- **OpenAI Rate Limiting**: Built-in delays and concurrent call limits (configurable)
- **Error Isolation**: Individual batch failures don't stop entire process
- **Retry Logic**: Built-in for transient failures

#### Optimization Guidelines
- **See [Batch Processing & Performance](#-batch-processing--performance)** section for detailed configuration guidance
- **Monitor Console Output**: Watch batch progress for performance insights
- **Adjust Settings**: Tune batch sizes based on your API limits and performance requirements

### Logging and Debugging

#### Enable Debug Mode
```bash
export FLASK_DEBUG=true
python app.py
```

#### Log Locations
- **Application**: Console output
- **Salesforce**: API call details
- **OpenAI**: Request/response logging

## 🤝 Contributing

### Development Setup

1. **Fork Repository**: Create your feature branch
2. **Virtual Environment**: Use isolated development environment
3. **Dependencies**: Install development requirements
4. **Testing**: Run test suite before committing

### Code Style

- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use consistent formatting
- **Comments**: Document complex logic
- **Error Handling**: Comprehensive error management

### Pull Request Process

1. **Feature Branch**: Create from `main` branch
2. **Testing**: Ensure all tests pass
3. **Documentation**: Update README if needed
4. **Review**: Submit PR with clear description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

1. **Documentation**: Check this README first
2. **Issues**: Create GitHub issue with details
3. **Logs**: Include relevant error messages
4. **Environment**: Specify Python/OS versions

---

## 🚀 Quick Start Summary

```bash
# 1. Setup
git clone <repo-url> && cd SFDC_Account_Matching
python -m venv venv && source venv/bin/activate
pip install -r config/requirements.txt

# 2. Configure
cp config/env.example .env
# Edit .env with your credentials

# 3. Run
python app.py
# Open http://localhost:5000

# 4. Use
# Upload customer Excel → Upload shell Excel → Process matching → Export results

# 5. View Sample Results
# See sample export: https://docs.google.com/spreadsheets/d/1eXpxC7F79lLkkgTNtVCuXvzZSCkGwSzF/edit

# 6. Watch Demo
# See demo video: https://drive.google.com/file/d/1gAKrTDIhgsVqMadivsJlcFw1PXiS2IBO/view
```

**Your intelligent customer-to-shell account matching system is ready! 🎯**
