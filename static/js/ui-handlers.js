// Global variables to store analysis results for export
let analysisResults = null;
let singleAccountResults = null;
let excelValidationResults = null;
let excelOriginalData = null;
let excelInfo = null;

// Global variables for Excel upload functionality
let excelFileData = null;
let excelPreviewData = null;
let excelAnalysisResults = null;



// Initialize event handlers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // SOQL Query Analysis
    document.getElementById('queryForm').addEventListener('submit', handleQueryFormSubmit);
    document.getElementById('getAccountDataBtn').addEventListener('click', handleGetAccountData);
    document.getElementById('exportBtn').addEventListener('click', handleExportToExcel);
    
    // Single Account Analysis
    document.getElementById('accountForm').addEventListener('submit', handleAccountFormSubmit);
    document.getElementById('exportAccountBtn').addEventListener('click', handleExportAccountToExcel);
    
    // Excel Analysis
    document.getElementById('excelForm').addEventListener('submit', handleExcelSubmit);
    document.getElementById('parseExcelBtn').addEventListener('click', handleExcelSubmit);
    document.getElementById('validateAccountIdsBtn').addEventListener('click', handleValidateAccountIds);
    document.getElementById('analyzeExcelBtn').addEventListener('click', handleAnalyzeExcelAccounts);
    document.getElementById('exportExcelBtn').addEventListener('click', handleExportExcelToExcel);
    
    // File input change handler
    document.getElementById('excelFile').addEventListener('change', function() {
        const fileInput = this;
        const parseBtn = document.getElementById('parseExcelBtn');
        const excelConfig = document.getElementById('excelConfig');
        
        console.log('File input change detected');
        console.log('Files length:', fileInput.files.length);
        console.log('Parse button found:', parseBtn);
        
        if (fileInput.files.length > 0) {
            console.log('Enabling parse button');
            parseBtn.disabled = false;
            excelConfig.style.display = 'none';
            // Reset other buttons
            document.getElementById('validateAccountIdsBtn').disabled = true;
            document.getElementById('analyzeExcelBtn').disabled = true;
            document.getElementById('exportExcelBtn').disabled = true;
        } else {
            console.log('Disabling parse button');
            parseBtn.disabled = true;
            excelConfig.style.display = 'none';
        }
    });
    
    // Clear stored results when inputs change
    document.getElementById('accountId').addEventListener('input', function() {
        singleAccountResults = null;
        document.getElementById('exportAccountBtn').disabled = true;
    });
    
    document.getElementById('soqlQuery').addEventListener('input', function() {
        analysisResults = null;
        // Reset button states
        document.getElementById('getAccountDataBtn').disabled = true;
        document.getElementById('exportBtn').disabled = true;
    });
    
    document.getElementById('maxAnalyze').addEventListener('input', function() {
        analysisResults = null;
        // Reset button states  
        document.getElementById('getAccountDataBtn').disabled = true;
        document.getElementById('exportBtn').disabled = true;
    });
});



async function handleQueryFormSubmit(e) {
    e.preventDefault();
    
    const responseDiv = document.getElementById('queryResponse');
    const button = document.getElementById('analyzeBtn');
    const getDataBtn = document.getElementById('getAccountDataBtn');
    const exportBtn = document.getElementById('exportBtn');
    
    // Get form values
    const soqlQuery = document.getElementById('soqlQuery').value.trim();
    const maxAnalyzeInput = document.getElementById('maxAnalyze').value.trim();
    const maxAnalyze = maxAnalyzeInput === '' ? '' : parseInt(maxAnalyzeInput);
    
    // Validate inputs
    if (maxAnalyze !== '' && (isNaN(maxAnalyze) || maxAnalyze < 1 || maxAnalyze > 500)) {
        responseDiv.innerHTML = '<pre class="error">❌ Error: Max accounts to analyze must be a number between 1 and 500, or leave blank for all results.</pre>';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        getDataBtn.disabled = true;
        return;
    }
    
    // Validate SOQL query - must be a full query, not empty or partial
    if (!soqlQuery) {
        responseDiv.innerHTML = '<pre class="error">❌ Error: Please enter a complete SOQL query that returns Account IDs.</pre>';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        getDataBtn.disabled = true;
        return;
    }
    
    // Must start with SELECT (full query required)
    if (!soqlQuery.toUpperCase().startsWith('SELECT')) {
        responseDiv.innerHTML = '<pre class="error">❌ Error: Please enter a complete SOQL query starting with SELECT. WHERE/LIMIT clauses alone are not accepted.</pre>';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        getDataBtn.disabled = true;
        return;
    }
    
    // Show loading state and disable buttons
    button.disabled = true;
    button.textContent = 'Validating...';
    getDataBtn.disabled = true;
    exportBtn.disabled = true;
    responseDiv.innerHTML = 'Validating SOQL query and getting Account IDs...';
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const response = await fetch('/accounts/analyze-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                soql_query: soqlQuery,
                max_ids: maxAnalyze === '' ? '' : parseInt(maxAnalyze)
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            // Store the complete result for later use
            analysisResults = result;
            
            // Format data for display
            displayQueryResults({
                success: true,
                data: result.data,
                message: result.message
            });
            
            responseDiv.className = 'response success';
        } else {
            // Clear stored results
            analysisResults = null;
            
            // Display error
            const errorMessage = result.message || 'Unknown error occurred';
            responseDiv.innerHTML = `<pre class="error">❌ Error: ${errorMessage}</pre>`;
            responseDiv.className = 'response error';
            getDataBtn.disabled = true;
            exportBtn.disabled = true;
        }
        
    } catch (error) {
        // Clear stored results
        analysisResults = null;
        
        // Display error
        responseDiv.innerHTML = `<pre class="error">❌ Network Error: ${error.message}</pre>`;
        responseDiv.className = 'response error';
        getDataBtn.disabled = true;
        exportBtn.disabled = true;
    } finally {
        // Restore button state
        button.disabled = false;
        button.textContent = 'Validate Account IDs';
        responseDiv.style.display = 'block';
    }
}

async function handleGetAccountData(e) {
    e.preventDefault();
    
    if (!analysisResults || !analysisResults.data.account_ids) {
        alert('Please validate Account IDs first.');
        return;
    }
    
    const responseDiv = document.getElementById('queryResponse');
    const button = document.getElementById('getAccountDataBtn');
    const exportBtn = document.getElementById('exportBtn');
    const accountIds = analysisResults.data.account_ids;
    
    try {
        // Show loading state
        button.disabled = true;
        button.textContent = 'Analyzing...';
        exportBtn.disabled = true;
        responseDiv.innerHTML = 'Analyzing accounts...';
        responseDiv.className = 'response loading';
        
        const response = await fetch('/accounts/get-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                account_ids: accountIds
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success' && data.data && data.data.accounts) {
            const accounts = data.data.accounts;
            const summary = data.data.summary;
            
            // Store results for export
            analysisResults = {
                accounts: accounts,
                summary: summary
            };
            
            let output = `✅ Account Analysis Complete!\n\n`;
            
            // Summary Section
            output += `<details>
<summary>📊 Summary</summary>
- Total accounts requested: ${summary.total_requested}
- Accounts retrieved: ${summary.accounts_retrieved}
- Execution time: ${data.data.execution_time}
</details>

`;
            
            // Account Analysis Section
            output += `Account Analysis(s):\n==================================================\n\n`;
            
            accounts.forEach((account, index) => {
                // Add bold account header
                output += `<strong>${index + 1}. ${account.Name} (${account.Id})</strong>\n\n`;
                // Add account details with collapsible sections
                output += formatAccountOutput(account);
            });
            
            responseDiv.innerHTML = `<pre>${output}</pre>`;
            responseDiv.className = 'response success';
            
            // Enable export button
            exportBtn.disabled = false;
        } else {
            const errorMsg = data.message || 'Failed to analyze accounts';
            responseDiv.innerHTML = `<pre class="error">❌ Error: ${errorMsg}</pre>`;
            responseDiv.className = 'response error';
            exportBtn.disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `<pre class="error">❌ Network Error: ${error.message}</pre>`;
        responseDiv.className = 'response error';
        exportBtn.disabled = true;
    } finally {
        button.disabled = false;
        button.textContent = 'Analyze Accounts';
    }
}

async function handleAccountFormSubmit(e) {
    e.preventDefault();
    
    const accountId = document.getElementById('accountId').value.trim();
    const responseDiv = document.getElementById('accountResponse');
    const exportBtn = document.getElementById('exportAccountBtn');
    
    if (!accountId) {
        responseDiv.innerHTML = '<pre class="error">❌ Please enter an Account ID</pre>';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        return;
    }
    
    try {
        // Show loading state
        exportBtn.disabled = true;
        responseDiv.innerHTML = 'Analyzing account...';
        responseDiv.className = 'response loading';
        responseDiv.style.display = 'block';
        
        const response = await fetch(`/account/${accountId}`, {
            method: 'GET'
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success' && data.data && data.data.accounts && data.data.accounts.length > 0) {
            const account = data.data.accounts[0];
            
            // Store results for export
            singleAccountResults = {
                account: account
            };
            
            let output = `✅ Account Analysis Complete!\n\n`;
            
            // Add bold account header
            output += `<strong>${account.Name} (${account.Id})</strong>\n\n`;
            // Add account details with collapsible sections
            output += formatAccountOutput(account);
            
            responseDiv.innerHTML = `<pre>${output}</pre>`;
            responseDiv.className = 'response success';
            
            // Enable export button
            exportBtn.disabled = false;
        } else {
            const errorMsg = data.message || 'Failed to retrieve account';
            responseDiv.innerHTML = `<pre class="error">❌ Error: ${errorMsg}</pre>`;
            responseDiv.className = 'response error';
            exportBtn.disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `<pre class="error">❌ Network Error: ${error.message}</pre>`;
        responseDiv.className = 'response error';
        exportBtn.disabled = true;
    }
}

function formatBillingAddress(account) {
    const parts = [
        account.BillingState,
        account.BillingCountry,
        account.BillingPostalCode
    ].filter(part => part && part.trim());
    
    return parts.length > 0 ? parts.join(', ') : 'N/A';
}

function formatZIBillingAddress(account) {
    const parts = [
        account.ZI_Company_State__c,
        account.ZI_Company_Country__c,
        account.ZI_Company_Postal_Code__c
    ].filter(part => part && part.trim());
    
    return parts.length > 0 ? parts.join(', ') : 'N/A';
}

function formatAccountOutput(account) {
    let output = '';
    
    // Account Details Section
    output += `<details>
<summary>Account Details</summary>Record Type: ${account.RecordType?.Name || 'N/A'}
Website: ${account.Website || 'N/A'}
Billing Address: ${formatBillingAddress(account)}
ZI Company: ${account.ZI_Company_Name__c || 'N/A'}
ZI Website: ${account.ZI_Website__c || 'N/A'}
ZI Billing Address: ${formatZIBillingAddress(account)}
Contact Most Frequent Email: ${account.ContactMostFrequentEmail__c || 'N/A'}
Parent ID: ${account.ParentId || 'No parent linked'}
Parent: ${account.Parent?.Name || 'No parent linked'}
</details>`;

    // Relationship Assessment Flags Section
    output += `<details>
<summary>🔍 Relationship Assessment Flags</summary>`;

    // Check for Bad_Domain flag first - if present and true, show only this flag
    if (account.Bad_Domain && account.Bad_Domain.is_bad) {
        output += `Bad Domain: ❌ True
  └─ ${account.Bad_Domain.explanation}`;
    } else {
        // Show all other flags only if no bad domain detected
        output += `Bad Domain: ✅ False
${account.Has_Shell !== undefined ? `Has Shell: ${account.Has_Shell ? '✅ True' : '❌ False'}` : ''}
${account.Customer_Consistency ? `Customer Consistency: ${account.Customer_Consistency.score}/100
  └─ ${account.Customer_Consistency.explanation}` : ''}
${account.Customer_Shell_Coherence ? `Customer-Shell Coherence: ${account.Customer_Shell_Coherence.score}/100
  └─ ${account.Customer_Shell_Coherence.explanation}` : ''}
${account.Address_Consistency ? `Address Consistency: ${account.Address_Consistency.is_consistent ? '✅ True' : '❌ False'}
  └─ ${account.Address_Consistency.explanation}` : ''}`;
    }
    
    output += `</details>`;

    // Parent Shell Account Data Section
    if (account.Shell_Account_Data) {
        output += `<details>
<summary>📋 Parent Shell Account Data</summary>Shell ID: ${account.Shell_Account_Data.Id}
Shell Name: ${account.Shell_Account_Data.Name || 'N/A'}
Shell Website: ${account.Shell_Account_Data.Website || 'N/A'}
Shell Billing Address: ${formatBillingAddress(account.Shell_Account_Data)}
Shell ZI Company: ${account.Shell_Account_Data.ZI_Company_Name__c || 'N/A'}
Shell ZI Website: ${account.Shell_Account_Data.ZI_Website__c || 'N/A'}
Shell ZI Billing Address: ${formatZIBillingAddress(account.Shell_Account_Data)}
</details>`;
    }

    // AI Assessment Section - Open by default
    if (account.AI_Assessment) {
        output += `<details open>
<summary>🤖 AI-Powered Relationship Assessment</summary>`;
        if (account.AI_Assessment.success) {
            output += `Overall Confidence Score: ${account.AI_Assessment.confidence_score}/100\n\nAI Analysis:`;
            if (account.AI_Assessment.explanation_bullets && account.AI_Assessment.explanation_bullets.length > 0) {
                account.AI_Assessment.explanation_bullets.forEach(bullet => {
                    output += `\n  • ${bullet}`;
                });
            }
        } else {
            output += `❌ AI Assessment Failed: ${account.AI_Assessment.error || 'Unknown error'}`;
        }
        output += '\n</details>\n';
    }

    return output;
}



// Excel handling functions
async function handleExcelFileChange(e) {
    const file = e.target.files[0];
    const parseBtn = document.getElementById('parseExcelBtn');
    const configDiv = document.getElementById('excelConfig');
    const responseDiv = document.getElementById('excelResponse');
    const validateBtn = document.getElementById('validateAccountIdsBtn');
    const exportBtn = document.getElementById('exportExcelBtn');
    
    if (file) {
        excelFileData = file;
        parseBtn.disabled = false;
        configDiv.style.display = 'none';
        responseDiv.style.display = 'none';
        
        // Reset subsequent buttons
        validateBtn.disabled = true;
        exportBtn.disabled = true;
        
        // Clear previous data
        excelPreviewData = null;
        excelAnalysisResults = null;
    } else {
        excelFileData = null;
        parseBtn.disabled = true;
        configDiv.style.display = 'none';
        validateBtn.disabled = true;
        exportBtn.disabled = true;
    }
}

async function handleParseExcel(e) {
    e.preventDefault();
    
    if (!excelFileData) {
        alert('Please select an Excel file first.');
        return;
    }
    
    const button = e.target;
    const responseDiv = document.getElementById('excelResponse');
    const validateBtn = document.getElementById('validateAccountIdsBtn');
    const exportBtn = document.getElementById('exportExcelBtn');
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Parsing...';
    validateBtn.disabled = true;
    exportBtn.disabled = true;
    responseDiv.innerHTML = 'Parsing Excel file...';
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const formData = new FormData();
        formData.append('file', excelFileData);
        
        const response = await fetch('/excel/parse', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            excelPreviewData = data.data;
            populateExcelSelectors(data.data);
            responseDiv.innerHTML = `✅ File parsed successfully! Found ${data.data.total_rows} rows in ${data.data.sheet_names.length} sheet(s).\n\nSelect the sheet and Account ID column, then validate the Account IDs.`;
            responseDiv.className = 'response success';
            document.getElementById('excelConfig').style.display = 'block';
            validateBtn.disabled = false;
        } else {
            responseDiv.innerHTML = `❌ Parse failed: ${data.message}`;
            responseDiv.className = 'response error';
            document.getElementById('excelConfig').style.display = 'none';
            validateBtn.disabled = true;
            exportBtn.disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `❌ Network Error: ${error.message}`;
        responseDiv.className = 'response error';
        document.getElementById('excelConfig').style.display = 'none';
        validateBtn.disabled = true;
        exportBtn.disabled = true;
    } finally {
        button.disabled = false;
        button.textContent = '1. Parse File';
    }
}

function populateExcelSelectors(data) {
    const sheetSelect = document.getElementById('sheetSelect');
    const columnSelect = document.getElementById('accountIdColumn');
    
    // Populate sheet selector
    sheetSelect.innerHTML = '';
    data.sheet_names.forEach(sheetName => {
        const option = document.createElement('option');
        option.value = sheetName;
        option.textContent = sheetName;
        sheetSelect.appendChild(option);
    });
    
    // Populate column selector
    columnSelect.innerHTML = '<option value="">-- Select Account ID Column --</option>';
    data.headers.forEach(header => {
        const option = document.createElement('option');
        option.value = header;
        option.textContent = header;
        columnSelect.appendChild(option);
    });
}

async function handleValidateAccountIds() {
    const fileInput = document.getElementById('excelFile');
    const responseDiv = document.getElementById('excelResponse');
    const button = document.getElementById('validateAccountIdsBtn');
    const analyzeBtn = document.getElementById('analyzeExcelBtn');
    
    if (!fileInput.files.length) {
        responseDiv.innerHTML = '<pre class="error">❌ Please select an Excel file first</pre>';
        return;
    }
    
    const sheetName = document.getElementById('sheetSelect').value;
    const accountIdColumn = document.getElementById('accountIdColumn').value;
    
    if (!sheetName || !accountIdColumn) {
        responseDiv.innerHTML = '<pre class="error">❌ Please select both sheet and Account ID column</pre>';
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('sheet_name', sheetName);
    formData.append('account_id_column', accountIdColumn);
    
    try {
        button.disabled = true;
        button.textContent = 'Validating...';
        responseDiv.innerHTML = 'Validating Account IDs...';
        responseDiv.className = 'response loading';
        
        const response = await fetch('/excel/validate-account-ids', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            excelValidationResults = data.data;
            excelOriginalData = data.data.original_excel_data;  // Store original Excel data for export
            excelInfo = data.data.excel_info;  // Store Excel info for export
            
            let output = `✅ Account IDs Validated Successfully!\n\n`;
            
            // Summary Section
            output += `<details>
<summary>📊 Validation Summary</summary>
- Total IDs from Excel: ${data.data.validation_summary.total_ids_from_excel}
- Valid Account IDs: ${data.data.validation_summary.valid_account_ids}
- Invalid Account IDs: ${data.data.validation_summary.invalid_account_ids}
- Execution time: ${data.data.execution_time}
</details>

`;
            
            // Excel File Info Section
            output += `<details>
<summary>📁 Excel File Info</summary>
- File: ${data.data.excel_info.file_name}
- Sheet: ${data.data.excel_info.sheet_name}
- Account ID Column: ${data.data.excel_info.account_id_column}
</details>

`;
            
            if (data.data.validation_summary.valid_account_ids > 0) {
                output += `\n✅ **${data.data.validation_summary.valid_account_ids} valid Account IDs found.** Click "Analyze Accounts" to proceed with analysis.\n`;
                analyzeBtn.disabled = false;
            } else {
                output += `\n❌ **No valid Account IDs found.** Please check your Excel file and try again.\n`;
                analyzeBtn.disabled = true;
            }
            
            responseDiv.innerHTML = `<pre>${output}</pre>`;
            responseDiv.className = 'response success';
        } else {
            responseDiv.innerHTML = `<pre class="error">❌ Error: ${data.message}</pre>`;
            responseDiv.className = 'response error';
            analyzeBtn.disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `<pre class="error">❌ Network Error: ${error.message}</pre>`;
        responseDiv.className = 'response error';
        analyzeBtn.disabled = true;
    } finally {
        button.disabled = false;
        button.textContent = 'Validate Account IDs';
    }
}

function displayQueryResults(result) {
    const responseDiv = document.getElementById('queryResponse');
    const getDataBtn = document.getElementById('getAccountDataBtn');
    
    if (!result.success) {
        const errorMessage = result.message || result.error || 'Unknown error occurred';
        responseDiv.innerHTML = `<pre class="error">❌ Error: ${errorMessage}</pre>`;
        getDataBtn.disabled = true;
        return;
    }
    
    const data = result.data;
    if (!data || !data.account_ids) {
        responseDiv.innerHTML = '<pre class="warning">⚠️ No Account IDs found matching the query criteria.</pre>';
        getDataBtn.disabled = true;
        return;
    }
    
    // If we have account IDs, show the results
    if (data.account_ids.length === 0) {
        responseDiv.innerHTML = '<pre class="warning">⚠️ No Account IDs found matching the query criteria.</pre>';
        getDataBtn.disabled = true;
        return;
    }
    
    let output = '✅ SOQL Query Valid - Account IDs Retrieved!\n\n';
    
    // Summary section
    output += '📊 Summary:\n';
    output += `- Account IDs found: ${data.summary.total_found}\n`;
    output += `- Execution time: ${data.summary.execution_time}\n`;
    output += `- Effective limit: ${data.summary.effective_limit}\n\n`;
    
    // Account IDs section
    output += 'Account IDs:\n';
    output += '==================================================\n';
    data.account_ids.forEach((id, index) => {
        output += `${index + 1}. ${id}\n`;
    });
    
    responseDiv.innerHTML = `<pre>${output}</pre>`;
    
    // Only enable the Analyze button if we have account IDs
    getDataBtn.disabled = false;
}

async function handleSingleAccountSubmit(e) {
    e.preventDefault();
    const accountId = document.getElementById('accountId').value.trim();
    const responseDiv = document.getElementById('accountResponse');
    const button = e.target.querySelector('button');
    
    if (!accountId) {
        responseDiv.innerHTML = '<pre class="error">❌ Please enter an Account ID</pre>';
        responseDiv.style.display = 'block';
        return;
    }
    
    try {
        button.disabled = true;
        button.textContent = 'Analyzing...';
        responseDiv.innerHTML = 'Analyzing account...';
        responseDiv.style.display = 'block';
        responseDiv.className = 'response loading';
        
        const response = await fetch(`/account/${accountId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        console.log('Response data:', data); // Debug log
        
        if (response.ok && data.status === 'success' && data.data && data.data.accounts && data.data.accounts.length > 0) {
            const account = data.data.accounts[0];
            console.log('Account data:', account); // Debug log
            
            if (!account || !account.Id) {
                throw new Error('Invalid account data received from server');
            }
            
            let output = `✅ Account Analysis Complete!\n\n`;
            
            // Summary Section
            output += `<details>
<summary>📊 Summary</summary>
- Account analyzed: ${accountId}
- Execution time: ${data.data.execution_time}
</details>

`;
            
            // Account Analysis Section
            output += `Account Analysis:\n==================================================\n\n`;
            
            // Add bold account header
            output += `<strong>${account.Name} (${account.Id})</strong>\n\n`;
            // Add account details with collapsible sections
            output += formatAccountOutput(account);
            
            responseDiv.innerHTML = `<pre>${output}</pre>`;
            responseDiv.className = 'response success';
        } else {
            const errorMsg = data.message || 'Failed to retrieve account data';
            responseDiv.innerHTML = `<pre class="error">❌ Error: ${errorMsg}</pre>`;
            responseDiv.className = 'response error';
        }
    } catch (error) {
        console.error('Error details:', error);
        console.error('Full error object:', error);
        responseDiv.innerHTML = `<pre class="error">❌ Network Error: ${error.message}</pre>`;
        responseDiv.className = 'response error';
    } finally {
        button.disabled = false;
        button.textContent = 'Analyze Account';
    }
}

async function handleExcelSubmit(e) {
    e.preventDefault();
    const fileInput = document.getElementById('excelFile');
    const responseDiv = document.getElementById('excelResponse');
    const button = e.target; // The button that was clicked
    
    if (!fileInput.files.length) {
        responseDiv.innerHTML = '<pre class="error">❌ Please select an Excel file</pre>';
        responseDiv.style.display = 'block';
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    try {
        button.disabled = true;
        button.textContent = 'Parsing...';
        responseDiv.innerHTML = 'Parsing Excel file...';
        responseDiv.style.display = 'block';
        responseDiv.className = 'response loading';
        
        const response = await fetch('/excel/parse', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            // Show Excel configuration options
            const excelConfig = document.getElementById('excelConfig');
            const sheetSelect = document.getElementById('sheetSelect');
            const accountIdColumn = document.getElementById('accountIdColumn');
            
            // Populate sheet dropdown
            sheetSelect.innerHTML = '';
            data.data.sheet_names.forEach(sheet => {
                const option = document.createElement('option');
                option.value = sheet;
                option.textContent = sheet;
                sheetSelect.appendChild(option);
            });
            
            // Populate column dropdown
            accountIdColumn.innerHTML = '';
            data.data.headers.forEach(header => {
                const option = document.createElement('option');
                option.value = header;
                option.textContent = header;
                accountIdColumn.appendChild(option);
            });
            
            excelConfig.style.display = 'block';
            responseDiv.innerHTML = '<pre class="success">✅ Excel file parsed successfully. Please select sheet and column, then validate Account IDs.</pre>';
            responseDiv.className = 'response success';
            
            // Enable the Validate Account IDs button
            document.getElementById('validateAccountIdsBtn').disabled = false;
        } else {
            responseDiv.innerHTML = `<pre class="error">❌ Error: ${data.message}</pre>`;
            responseDiv.className = 'response error';
        }
    } catch (error) {
        responseDiv.innerHTML = `<pre class="error">❌ Network Error: ${error.message}</pre>`;
        responseDiv.className = 'response error';
    } finally {
        button.disabled = false;
        button.textContent = 'Parse File';
    }
}

async function handleAnalyzeExcelAccounts() {
    const responseDiv = document.getElementById('excelResponse');
    const button = document.getElementById('analyzeExcelBtn');
    const exportBtn = document.getElementById('exportExcelBtn');
    
    if (!excelValidationResults || !excelValidationResults.accounts) {
        responseDiv.innerHTML = '<pre class="error">❌ No validated accounts found. Please validate Account IDs first.</pre>';
        return;
    }
    
    try {
        button.disabled = true;
        exportBtn.disabled = true;
        button.textContent = 'Analyzing...';
        responseDiv.innerHTML = 'Analyzing accounts...';
        responseDiv.className = 'response loading';
        
        // Extract account IDs from validated results
        const accountIds = excelValidationResults.accounts.map(account => account.Id);
        
        const response = await fetch('/accounts/get-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                account_ids: accountIds
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success' && data.data && data.data.accounts) {
            const accounts = data.data.accounts;
            const summary = data.data.summary;
            
            // Store results for export
            excelValidationResults.analysisResults = {
                accounts: accounts,
                summary: summary
            };
            
            let output = `✅ Account Analysis Complete!\n\n`;
            
            // Summary Section
            output += `<details>
<summary>📊 Summary</summary>
- Excel rows processed: ${excelValidationResults.validation_summary.total_ids_from_excel}
- Valid Account IDs found: ${excelValidationResults.validation_summary.valid_account_ids}
- Accounts analyzed: ${summary.accounts_retrieved}
- Execution time: ${data.data.execution_time}
</details>

`;
            
            // Account Analysis Section
            output += `Account Analysis(s):\n==================================================\n\n`;
            
            accounts.forEach((account, index) => {
                // Add bold account header
                output += `<strong>${index + 1}. ${account.Name} (${account.Id})</strong>\n\n`;
                // Add account details with collapsible sections
                output += formatAccountOutput(account);
            });
            
            responseDiv.innerHTML = `<pre>${output}</pre>`;
            responseDiv.className = 'response success';
            
            // Enable export button
            exportBtn.disabled = false;
        } else {
            const errorMsg = data.message || 'Failed to analyze accounts';
            responseDiv.innerHTML = `<pre class="error">❌ Error: ${errorMsg}</pre>`;
            responseDiv.className = 'response error';
            exportBtn.disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `<pre class="error">❌ Network Error: ${error.message}</pre>`;
        responseDiv.className = 'response error';
        exportBtn.disabled = true;
    } finally {
        button.disabled = false;
        button.textContent = 'Analyze Accounts';
    }
}

// Export functions
async function handleExportToExcel(e) {
    e.preventDefault();
    
    if (!analysisResults || !analysisResults.accounts) {
        alert('No analysis results to export. Please run analysis first.');
        return;
    }
    
    try {
        const response = await fetch('/export/soql-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                accounts: analysisResults.accounts,
                summary: analysisResults.summary
            })
        });
        
        if (response.ok) {
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `sfdc_analysis_soql_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const errorData = await response.json();
            alert(`Export failed: ${errorData.message}`);
        }
    } catch (error) {
        alert(`Export failed: ${error.message}`);
    }
}

async function handleExportAccountToExcel(e) {
    e.preventDefault();
    
    if (!singleAccountResults || !singleAccountResults.account) {
        alert('No account analysis to export. Please run analysis first.');
        return;
    }
    
    try {
        const response = await fetch('/export/single-account', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                account: singleAccountResults.account
            })
        });
        
        if (response.ok) {
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `sfdc_analysis_single_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const errorData = await response.json();
            alert(`Export failed: ${errorData.message}`);
        }
    } catch (error) {
        alert(`Export failed: ${error.message}`);
    }
}

async function handleExportExcelToExcel(e) {
    e.preventDefault();
    
    if (!excelValidationResults || !excelValidationResults.analysisResults || !excelOriginalData) {
        alert('No Excel analysis to export. Please run analysis first.');
        return;
    }
    
    try {
        const response = await fetch('/export/excel-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                accounts: excelValidationResults.analysisResults.accounts,
                original_data: excelOriginalData,
                excel_info: excelInfo
            })
        });
        
        if (response.ok) {
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `excel_analysis_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const errorData = await response.json();
            alert(`Export failed: ${errorData.message}`);
        }
    } catch (error) {
        alert(`Export failed: ${error.message}`);
    }
}