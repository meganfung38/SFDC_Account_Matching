// Global state for dual-file matching workflow
let workflowState = {
    currentStep: 1,
    customerData: {
        file: null,
        accountIds: [],
        validation: null
    },
    shellData: {
        file: null,
        accountIds: [],
        validation: null
    },
    matchingResults: null
};

// Initialize event handlers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDualFileWorkflow();
    updateGlobalStatus('Ready to upload customer account Excel file', 'ℹ️');
});

function initializeDualFileWorkflow() {
    // Step 1: Customer file handlers
    document.getElementById('customerFile').addEventListener('change', handleCustomerFileChange);
    document.getElementById('parseCustomerBtn').addEventListener('click', handleParseCustomerFile);
    document.getElementById('validateCustomerBtn').addEventListener('click', handleValidateCustomerIds);
    
    // Step 2: Shell file handlers
    document.getElementById('shellFile').addEventListener('change', handleShellFileChange);
    document.getElementById('parseShellBtn').addEventListener('click', handleParseShellFile);
    document.getElementById('validateShellBtn').addEventListener('click', handleValidateShellIds);
    
    // Step 3: Matching process handlers
    document.getElementById('processMatchingBtn').addEventListener('click', handleProcessMatching);
    
    // Step 4: Results handlers
    document.getElementById('viewResultsBtn').addEventListener('click', handleViewResults);
    document.getElementById('exportResultsBtn').addEventListener('click', handleExportResults);
    document.getElementById('resetProcessBtn').addEventListener('click', handleResetProcess);
}

// STEP MANAGEMENT
function updateProgressStep(stepNumber, status = 'active') {
    console.log('🔍 updateProgressStep called with stepNumber:', stepNumber);
    
    // Update step indicators
    const indicators = document.querySelectorAll('.step');
    indicators.forEach((indicator, index) => {
        const step = index + 1;
        if (step < stepNumber) {
            indicator.className = 'step completed';
        } else if (step === stepNumber) {
            indicator.className = `step ${status}`;
        } else {
            indicator.className = 'step';
        }
    });
    
    // Enable/disable sections (only the step content sections, not progress indicators)
    const sections = document.querySelectorAll('[id$="-section"]'); // Only step1-section, step2-section, etc.
    console.log('🔍 Found step sections:', sections.length);
    sections.forEach((section, index) => {
        const step = index + 1;
        console.log(`🔍 Processing step section ${step} (${section.id}):`, section.className);
        if (step <= stepNumber) {
            // Remove disabled state and add enabled
            section.classList.remove('disabled-section');
            section.classList.add('enabled');
            console.log(`🔍 Enabled step section ${step}, new classes:`, section.className);
        } else {
            section.classList.add('disabled-section');
            section.classList.remove('enabled');
            console.log(`🔍 Disabled step section ${step}, new classes:`, section.className);
        }
    });
    
    workflowState.currentStep = stepNumber;
}

function updateGlobalStatus(message, icon = 'ℹ️') {
    const statusElement = document.getElementById('globalStatus');
    const messageElement = statusElement.querySelector('.status-message');
    const iconElement = statusElement.querySelector('.status-icon');
    
    messageElement.textContent = message;
    iconElement.textContent = icon;
    statusElement.style.display = 'block';
    
    // Auto-hide after 5 seconds for non-error messages
    if (icon !== '❌') {
        setTimeout(() => {
            statusElement.style.display = 'none';
        }, 5000);
    }
}

// STEP 1: CUSTOMER FILE HANDLERS
function handleCustomerFileChange() {
    const fileInput = document.getElementById('customerFile');
    const parseBtn = document.getElementById('parseCustomerBtn');
    const configSection = document.getElementById('customerConfig');
    
    if (fileInput.files.length > 0) {
        parseBtn.disabled = false;
        configSection.style.display = 'none';
        document.getElementById('validateCustomerBtn').disabled = true;
        
        // Reset subsequent steps
        resetShellSection();
        resetMatchingSection();
        resetResultsSection();
        
        updateGlobalStatus(`Customer file "${fileInput.files[0].name}" selected. Click Parse to analyze.`, '📄');
    }
}

async function handleParseCustomerFile() {
    const fileInput = document.getElementById('customerFile');
    const configSection = document.getElementById('customerConfig');
    const responseDiv = document.getElementById('customerResponse');
    
    if (!fileInput.files[0]) {
        showError(responseDiv, 'Please select a customer Excel file first.');
        return;
    }
    
    try {
        showLoading(responseDiv, 'Parsing customer Excel file...');
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        const response = await fetch('/excel/parse', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Populate sheet and column dropdowns
            populateDropdown('customerSheetSelect', result.data.sheet_names);
            populateDropdown('customerAccountIdColumn', result.data.headers[result.data.sheet_names[0]] || []);
            
            // Show configuration section
            configSection.style.display = 'block';
            document.getElementById('validateCustomerBtn').disabled = false;
            
            workflowState.customerData.file = result.data;
            
            showSuccess(responseDiv, `File parsed successfully! Found ${result.data.sheet_names.length} sheet(s). Please select the sheet and column containing customer account IDs.`);
            updateGlobalStatus('Customer file parsed. Please configure sheet and column settings.', '⚙️');
            
            // Handle sheet change to update columns
            document.getElementById('customerSheetSelect').addEventListener('change', function() {
                const selectedSheet = this.value;
                const headers = result.data.headers[selectedSheet] || [];
                populateDropdown('customerAccountIdColumn', headers);
            });
            
        } else {
            showError(responseDiv, `Failed to parse file: ${result.message}`);
            updateGlobalStatus('Failed to parse customer file', '❌');
        }
        
    } catch (error) {
        showError(responseDiv, `Error parsing file: ${error.message}`);
        updateGlobalStatus('Error parsing customer file', '❌');
    }
}

async function handleValidateCustomerIds() {
    const sheetSelect = document.getElementById('customerSheetSelect');
    const columnSelect = document.getElementById('customerAccountIdColumn');
    const responseDiv = document.getElementById('customerResponse');
    const fileInput = document.getElementById('customerFile');
    
    if (!sheetSelect.value || !columnSelect.value) {
        showError(responseDiv, 'Please select both sheet and account ID column.');
        return;
    }
    
    try {
        showLoading(responseDiv, 'Validating customer account IDs with Salesforce...');
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('sheet_name', sheetSelect.value);
        formData.append('account_id_column', columnSelect.value);
        
        const response = await fetch('/excel/parse-customer-file', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            workflowState.customerData.accountIds = result.data.validation_summary.valid_account_ids;
            workflowState.customerData.validation = result.data.validation_summary;
            
            showSuccess(responseDiv, `${result.message} Ready to proceed to shell accounts.`);
            
            // Enable next step
            console.log('🔍 Customer validation successful, enabling shell section...');
            enableShellSection();
            updateProgressStep(2);
            updateGlobalStatus(`${result.data.validation_summary.valid_account_ids.length} customer accounts ready. Upload shell accounts file.`, '✅');
            
        } else {
            showError(responseDiv, result.message);
            updateGlobalStatus('Customer account validation failed', '❌');
        }
        
    } catch (error) {
        showError(responseDiv, `Error validating customer accounts: ${error.message}`);
        updateGlobalStatus('Error validating customer accounts', '❌');
    }
}

// STEP 2: SHELL FILE HANDLERS
function enableShellSection() {
    console.log('🔍 enableShellSection called');
    const shellFile = document.getElementById('shellFile');
    const step2Section = document.getElementById('step2-section');
    
    console.log('🔍 Before changes:');
    console.log('  shellFile.disabled:', shellFile ? shellFile.disabled : 'NOT FOUND');
    console.log('  step2Section.className:', step2Section ? step2Section.className : 'NOT FOUND');
    
    if (shellFile) shellFile.disabled = false;
    if (step2Section) {
        // Try both approaches to ensure it works
        step2Section.classList.remove('disabled-section');
        step2Section.classList.add('enabled');
    }
    
    console.log('🔍 After changes:');
    console.log('  shellFile.disabled:', shellFile ? shellFile.disabled : 'NOT FOUND');
    console.log('  step2Section.className:', step2Section ? step2Section.className : 'NOT FOUND');
}

function resetShellSection() {
    document.getElementById('shellFile').disabled = true;
    document.getElementById('parseShellBtn').disabled = true;
    document.getElementById('validateShellBtn').disabled = true;
    document.getElementById('shellConfig').style.display = 'none';
    document.getElementById('shellResponse').style.display = 'none';
    workflowState.shellData = { file: null, accountIds: [], validation: null };
}

function handleShellFileChange() {
    const fileInput = document.getElementById('shellFile');
    const parseBtn = document.getElementById('parseShellBtn');
    const configSection = document.getElementById('shellConfig');
    
    if (fileInput.files.length > 0) {
        parseBtn.disabled = false;
        configSection.style.display = 'none';
        document.getElementById('validateShellBtn').disabled = true;
        
        // Reset subsequent steps
        resetMatchingSection();
        resetResultsSection();
        
        updateGlobalStatus(`Shell file "${fileInput.files[0].name}" selected. Click Parse to analyze.`, '📄');
    }
}

async function handleParseShellFile() {
    const fileInput = document.getElementById('shellFile');
    const configSection = document.getElementById('shellConfig');
    const responseDiv = document.getElementById('shellResponse');
    
    if (!fileInput.files[0]) {
        showError(responseDiv, 'Please select a shell Excel file first.');
        return;
    }
    
    try {
        showLoading(responseDiv, 'Parsing shell Excel file...');
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        const response = await fetch('/excel/parse', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Populate sheet and column dropdowns
            populateDropdown('shellSheetSelect', result.data.sheet_names);
            populateDropdown('shellAccountIdColumn', result.data.headers[result.data.sheet_names[0]] || []);
            
            // Show configuration section
            configSection.style.display = 'block';
            document.getElementById('validateShellBtn').disabled = false;
            
            workflowState.shellData.file = result.data;
            
            showSuccess(responseDiv, `File parsed successfully! Found ${result.data.sheet_names.length} sheet(s). Please select the sheet and column containing shell account IDs.`);
            updateGlobalStatus('Shell file parsed. Please configure sheet and column settings.', '⚙️');
            
            // Handle sheet change to update columns
            document.getElementById('shellSheetSelect').addEventListener('change', function() {
                const selectedSheet = this.value;
                const headers = result.data.headers[selectedSheet] || [];
                populateDropdown('shellAccountIdColumn', headers);
            });
            
        } else {
            showError(responseDiv, `Failed to parse file: ${result.message}`);
            updateGlobalStatus('Failed to parse shell file', '❌');
        }
        
    } catch (error) {
        showError(responseDiv, `Error parsing file: ${error.message}`);
        updateGlobalStatus('Error parsing shell file', '❌');
    }
}

async function handleValidateShellIds() {
    const sheetSelect = document.getElementById('shellSheetSelect');
    const columnSelect = document.getElementById('shellAccountIdColumn');
    const responseDiv = document.getElementById('shellResponse');
    const fileInput = document.getElementById('shellFile');
    
    if (!sheetSelect.value || !columnSelect.value) {
        showError(responseDiv, 'Please select both sheet and account ID column.');
        return;
    }
    
    try {
        showLoading(responseDiv, 'Validating shell account IDs with Salesforce...');
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
        formData.append('sheet_name', sheetSelect.value);
        formData.append('account_id_column', columnSelect.value);
        
        const response = await fetch('/excel/parse-shell-file', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            workflowState.shellData.accountIds = result.data.validation_summary.valid_account_ids;
            workflowState.shellData.validation = result.data.validation_summary;
            
            showSuccess(responseDiv, `${result.message} Ready to process matching.`);
            
            // Enable next step
            enableMatchingSection();
            updateProgressStep(3);
            updateMatchingSummary();
            updateGlobalStatus('Both files validated. Ready to start matching process.', '🎯');
            
        } else {
            showError(responseDiv, result.message);
            updateGlobalStatus('Shell account validation failed', '❌');
        }
        
    } catch (error) {
        showError(responseDiv, `Error validating shell accounts: ${error.message}`);
        updateGlobalStatus('Error validating shell accounts', '❌');
    }
}

// STEP 3: MATCHING PROCESS
function enableMatchingSection() {
    document.getElementById('processMatchingBtn').disabled = false;
    const step3Section = document.getElementById('step3-section');
    if (step3Section) {
        step3Section.classList.remove('disabled-section');
        step3Section.classList.add('enabled');
    }
}

function resetMatchingSection() {
    document.getElementById('processMatchingBtn').disabled = true;
    document.getElementById('matchingProgress').style.display = 'none';
    document.getElementById('matchingSummary').style.display = 'none';
    document.getElementById('matchingResponse').style.display = 'none';
}

function updateMatchingSummary() {
    const summaryDiv = document.getElementById('matchingSummary');
    const customerCount = document.getElementById('customerCount');
    const shellCount = document.getElementById('shellCount');
    
    customerCount.textContent = workflowState.customerData.accountIds.length;
    shellCount.textContent = workflowState.shellData.accountIds.length;
    
    summaryDiv.style.display = 'block';
}

async function handleProcessMatching() {
    const responseDiv = document.getElementById('matchingResponse');
    const progressDiv = document.getElementById('matchingProgress');
    const processBtn = document.getElementById('processMatchingBtn');
    
    try {
        // Show progress indicator
        progressDiv.style.display = 'flex';
        processBtn.disabled = true;
        showLoading(responseDiv, 'Starting intelligent matching process...');
        updateGlobalStatus('Processing matches... This may take a few moments.', '⚙️');
        
        const requestData = {
            customer_account_ids: workflowState.customerData.accountIds,
            shell_account_ids: workflowState.shellData.accountIds,
            invalid_customer_ids: workflowState.customerData.validation?.invalid_account_ids || [],
            invalid_shell_ids: workflowState.shellData.validation?.invalid_account_ids || []
        };
        
        const response = await fetch('/matching/process-batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            workflowState.matchingResults = result.data;
            
            progressDiv.style.display = 'none';
            showSuccess(responseDiv, `🎉 Matching completed successfully! Found ${result.data.summary.matched_pairs} matches out of ${result.data.summary.clean_customer_accounts} eligible customers in ${result.data.summary.execution_time}.`);
            
            // Enable results step
            enableResultsSection();
            updateProgressStep(4);
            updateResultsSummary(result.data.summary);
            updateGlobalStatus('Matching complete! View results and export to Excel.', '🎉');
            
        } else {
            progressDiv.style.display = 'none';
            processBtn.disabled = false;
            showError(responseDiv, `Matching failed: ${result.message}`);
            updateGlobalStatus('Matching process failed', '❌');
        }
        
    } catch (error) {
        progressDiv.style.display = 'none';
        processBtn.disabled = false;
        showError(responseDiv, `Error processing matches: ${error.message}`);
        updateGlobalStatus('Error processing matches', '❌');
    }
}

// STEP 4: RESULTS AND EXPORT
function enableResultsSection() {
    document.getElementById('viewResultsBtn').disabled = false;
    document.getElementById('exportResultsBtn').disabled = false;
    document.getElementById('resetProcessBtn').style.display = 'inline-block';
    const step4Section = document.getElementById('step4-section');
    if (step4Section) {
        step4Section.classList.remove('disabled-section');
        step4Section.classList.add('enabled');
    }
}

function resetResultsSection() {
    document.getElementById('viewResultsBtn').disabled = true;
    document.getElementById('exportResultsBtn').disabled = true;
    document.getElementById('resetProcessBtn').style.display = 'none';
    document.getElementById('resultsSummary').style.display = 'none';
    document.getElementById('detailedResults').style.display = 'none';
    document.getElementById('resultsResponse').style.display = 'none';
}

function updateResultsSummary(summary) {
    const summaryDiv = document.getElementById('resultsSummary');
    
    document.getElementById('matchedCount').textContent = summary.matched_pairs;
    document.getElementById('unmatchedCount').textContent = summary.unmatched_customers;
    document.getElementById('flaggedCount').textContent = summary.flagged_customer_accounts;
    document.getElementById('invalidCount').textContent = summary.invalid_customer_accounts || 0;
    
    const successRate = summary.clean_customer_accounts > 0 
        ? Math.round((summary.matched_pairs / summary.clean_customer_accounts) * 100)
        : 0;
    document.getElementById('successRate').textContent = `${successRate}%`;
    
    summaryDiv.style.display = 'block';
}

function handleViewResults() {
    const resultsDiv = document.getElementById('detailedResults');
    const tableBody = document.querySelector('#resultsTable tbody');
    
    if (!workflowState.matchingResults) {
        updateGlobalStatus('No results to display', '❌');
        return;
    }
    
    // Clear existing results
    tableBody.innerHTML = '';
    
    const allResults = [
        ...workflowState.matchingResults.matched_pairs.map(pair => ({
            type: 'matched',
            customer: pair.customer_account,
            shell: pair.recommended_shell,
            confidence: pair.match_confidence,
                            ai_explanation: pair.ai_assessment?.explanation_bullets?.join('<br>') || 'No explanation available'
        })),
        ...workflowState.matchingResults.unmatched_customers.map(unmatched => ({
            type: 'unmatched',
            customer: unmatched.customer_account,
            shell: null,
            confidence: 0,
            ai_explanation: unmatched.reason || 'No suitable match found'
        })),
        ...workflowState.matchingResults.flagged_customers.map(flagged => ({
            type: 'flagged',
            customer: flagged,
            shell: null,
            confidence: 0,
            ai_explanation: flagged.Bad_Domain?.explanation || 'Bad domain detected'
        })),
        ...(workflowState.matchingResults.invalid_customers || []).map(invalid_id => ({
            type: 'invalid',
            customer: {Id: invalid_id, Name: 'INVALID ACCOUNT ID', Website: '', BillingCity: '', BillingState: '', BillingCountry: '', BillingPostalCode: ''},
            shell: null,
            confidence: 0,
            ai_explanation: 'Invalid Account ID - does not exist in Salesforce'
        }))
    ];
    
    // Sort by customer name
    allResults.sort((a, b) => (a.customer.Name || '').localeCompare(b.customer.Name || ''));
    
    // Populate table
    allResults.forEach(result => {
        const row = document.createElement('tr');
        
        const statusBadge = `<span class="status-badge status-${result.type}">${result.type.toUpperCase()}</span>`;
        const customerInfo = `<strong>${result.customer.Name || 'N/A'}</strong><br/><small>${result.customer.Id || 'N/A'}</small>`;
        const shellInfo = result.shell 
            ? `<strong>${result.shell.ZI_Company_Name__c || 'N/A'}</strong><br/><small>${result.shell.Id || 'N/A'}</small>`
            : '<em>No match</em>';
        const confidenceInfo = result.confidence > 0 ? `${result.confidence.toFixed(1)}%` : '-';
        
        row.innerHTML = `
            <td>${customerInfo}</td>
            <td>${statusBadge}</td>
            <td>${shellInfo}</td>
            <td>${confidenceInfo}</td>
                            <td><div style="font-size: 0.9em; line-height: 1.5; white-space: normal;">${result.ai_explanation}</div></td>
        `;
        
        tableBody.appendChild(row);
    });
    
    resultsDiv.style.display = 'block';
    updateGlobalStatus(`Displaying ${allResults.length} customer results`, 'ℹ️');
}

async function handleExportResults() {
    if (!workflowState.matchingResults) {
        updateGlobalStatus('No results to export', '❌');
        return;
    }
    
    try {
        updateGlobalStatus('Generating Excel export...', '📊');
        
        const response = await fetch('/export/matching-results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(workflowState.matchingResults)
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `customer_shell_matching_results_${new Date().toISOString().slice(0,10)}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            updateGlobalStatus('Excel file downloaded successfully!', '✅');
        } else {
            const errorResult = await response.json();
            updateGlobalStatus(`Export failed: ${errorResult.message}`, '❌');
        }
        
    } catch (error) {
        updateGlobalStatus(`Export error: ${error.message}`, '❌');
    }
}

function handleResetProcess() {
    if (confirm('Are you sure you want to start a new matching process? This will clear all current results.')) {
        // Reset all state
        workflowState = {
            currentStep: 1,
            customerData: { file: null, accountIds: [], validation: null },
            shellData: { file: null, accountIds: [], validation: null },
            matchingResults: null
        };
        
        // Reset UI
        document.getElementById('customerFile').value = '';
        document.getElementById('shellFile').value = '';
        resetShellSection();
        resetMatchingSection();
        resetResultsSection();
        
        // Reset all form sections
        document.querySelectorAll('.excel-config').forEach(section => {
            section.style.display = 'none';
        });
        document.querySelectorAll('.response').forEach(div => {
            div.style.display = 'none';
        });
        
        // Reset buttons
        document.getElementById('parseCustomerBtn').disabled = true;
        document.getElementById('parseShellBtn').disabled = true;
        
        // Reset progress
        updateProgressStep(1);
        updateGlobalStatus('Process reset. Ready to upload customer account Excel file.', '🔄');
    }
}

// UTILITY FUNCTIONS
function populateDropdown(selectId, options) {
    const select = document.getElementById(selectId);
    select.innerHTML = '';
    
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        select.appendChild(optionElement);
    });
}

function showLoading(element, message) {
    element.style.display = 'block';
    element.className = 'response loading';
    element.innerHTML = `<div class="spinner"></div> ${message}`;
}

function showSuccess(element, message) {
    element.style.display = 'block';
    element.className = 'response success';
    element.innerHTML = `✅ ${message}`;
}

function showError(element, message) {
    element.style.display = 'block';
    element.className = 'response error';
    element.innerHTML = `❌ ${message}`;
}