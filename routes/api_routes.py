from flask import Blueprint, jsonify, request, send_file
from services.salesforce_service import SalesforceService
from services.openai_service import test_openai_connection, test_openai_completion, get_openai_config
from services.excel_service import ExcelService
from services.fuzzy_matching_service import FuzzyMatchingService
from config.config import Config

# Create blueprint for API routes
api_bp = Blueprint('api', __name__)

# Initialize services
sf_service = SalesforceService()
excel_service = ExcelService()
fuzzy_matcher = FuzzyMatchingService()

@api_bp.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        "message": "Dual-File Account Matching API",
        "version": "2.0.0",
        "status": "running",
        "web_ui": "/",
        "endpoints": {
            "health": "/health",
            "debug_config": "/debug-config",
            "salesforce_test": "/test-salesforce-connection",
            "openai_test": "/test-openai-connection",
            "openai_completion": "/test-openai-completion",
            "parse_excel": "/excel/parse",
            "parse_customer_excel": "/excel/parse-customer-file",
            "parse_shell_excel": "/excel/parse-shell-file",
            "process_matching": "/matching/process-batch",
            "export_results": "/export/matching-results"
        }
    })

@api_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Dual-File Account Matching API"
    })

@api_bp.route('/debug-config')
def debug_config():
    """Debug endpoint to check configuration (for development only)"""
    try:
        return jsonify({
            "salesforce": {
                "username_present": bool(Config.SF_USERNAME),
                "password_present": bool(Config.SF_PASSWORD),
                "token_present": bool(Config.SF_SECURITY_TOKEN),
                "domain": Config.SF_DOMAIN
            },
            "openai": {
                "api_key_present": bool(Config.OPENAI_API_KEY),
                "api_key_length": len(Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else 0,
                "api_key_starts_with_sk": Config.OPENAI_API_KEY.startswith('sk-') if Config.OPENAI_API_KEY else False,
                "model": Config.OPENAI_MODEL,
                "max_tokens": Config.OPENAI_MAX_TOKENS
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Configuration error: {str(e)}"
        }), 500

@api_bp.route('/test-salesforce-connection')
def test_salesforce_connection():
    """Test endpoint to verify Salesforce connection"""
    try:
        is_connected, message = sf_service.test_connection()
        
        if is_connected:
            connection_info = sf_service.get_connection_info()
            return jsonify({
                "status": "success",
                "message": message,
                "connection_details": connection_info
            })
        else:
            return jsonify({
                "status": "error",
                "message": message
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500

@api_bp.route('/test-openai-connection')
def test_openai_connection_endpoint():
    """Test endpoint to verify OpenAI API connection"""
    try:
        is_connected, message = test_openai_connection()
        
        if is_connected:
            config_info = get_openai_config()
            return jsonify({
                "status": "success",
                "message": message,
                "configuration": config_info
            })
        else:
            return jsonify({
                "status": "error",
                "message": message,
                "debug_info": {
                    "api_key_present": bool(Config.OPENAI_API_KEY),
                    "api_key_length": len(Config.OPENAI_API_KEY) if Config.OPENAI_API_KEY else 0,
                    "api_key_starts_with_sk": Config.OPENAI_API_KEY.strip().startswith('sk-') if Config.OPENAI_API_KEY else False
                }
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500

@api_bp.route('/test-openai-completion')
def test_openai_completion_endpoint():
    """Test endpoint to verify OpenAI completion generation"""
    try:
        # Get optional prompt from query parameters
        prompt = request.args.get('prompt', 'Hello! Please respond with "OpenAI connection test successful."')
        
        completion, message = test_openai_completion(prompt)
        
        if completion:
            return jsonify({
                "status": "success",
                "message": message,
                "prompt": prompt,
                "completion": completion,
                "configuration": get_openai_config()
            })
        else:
            return jsonify({
                "status": "error",
                "message": message
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500

# NEW DUAL-FILE MATCHING ENDPOINTS

@api_bp.route('/excel/parse', methods=['POST'])
def parse_excel_file():
    """Parse Excel file to get sheet names and headers (structure only)"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Read file content
        file_content = file.read()
        
        # Parse the Excel file structure
        result = excel_service.parse_excel_file(file_content)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error parsing Excel file: {str(e)}'
        }), 500

@api_bp.route('/excel/parse-customer-file', methods=['POST'])
def parse_customer_excel():
    """Parse uploaded customer Excel file and validate account IDs"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Get form data
        sheet_name = request.form.get('sheet_name')
        account_id_column = request.form.get('account_id_column')
        
        # Validate parameters
        if not sheet_name:
            return jsonify({
                'status': 'error',
                'message': 'Sheet name is required'
            }), 400
        
        if not account_id_column:
            return jsonify({
                'status': 'error',
                'message': 'Account ID column is required'
            }), 400
        
        # Read file content
        file_content = file.read()
        
        # Extract Account IDs from Excel
        extraction_result = excel_service.extract_account_ids_from_excel(
            file_content, sheet_name, account_id_column
        )
        
        if not extraction_result['success']:
            return jsonify({
                'status': 'error',
                'message': extraction_result['error']
            }), 400
        
        account_ids = extraction_result['account_ids']
        
        if not account_ids:
            return jsonify({
                'status': 'error',
                'message': f'No valid Account IDs found in column "{account_id_column}"'
            }), 400
        
        # Validate Account IDs with Salesforce
        validation_result, validation_message = sf_service.validate_customer_account_ids(account_ids)
        
        if validation_result is None:
            return jsonify({
                'status': 'error',
                'message': validation_message
            }), 500
        
        # Include both valid and invalid IDs in response (no longer terminate on invalid IDs)
        invalid_account_ids = validation_result.get('invalid_account_ids', [])
        valid_count = len(validation_result.get('valid_account_ids', []))
        invalid_count = len(invalid_account_ids)
        
        if invalid_count > 0:
            invalid_ids_list = ', '.join(invalid_account_ids[:5])  # Show first 5 invalid IDs
            if invalid_count > 5:
                invalid_ids_list += f' (and {invalid_count - 5} more)'
            message = f'Validation complete: {valid_count} valid, {invalid_count} invalid customer account IDs. Invalid IDs: [{invalid_ids_list}]. Invalid IDs will be excluded from matching.'
        else:
            message = f'Successfully validated {valid_count} customer account IDs'
        
        return jsonify({
            'status': 'success',
            'message': message,
            'data': {
                'validation_summary': validation_result,
                'excel_info': {
                    'sheet_name': sheet_name,
                    'account_id_column': account_id_column,
                    'file_name': file.filename,
                    'total_rows': extraction_result['total_rows']
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing customer Excel file: {str(e)}'
        }), 500

@api_bp.route('/excel/parse-shell-file', methods=['POST'])
def parse_shell_excel():
    """Parse uploaded shell Excel file and validate account IDs"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400
        
        # Get form data
        sheet_name = request.form.get('sheet_name')
        account_id_column = request.form.get('account_id_column')
        
        # Validate parameters
        if not sheet_name:
            return jsonify({
                'status': 'error',
                'message': 'Sheet name is required'
            }), 400
        
        if not account_id_column:
            return jsonify({
                'status': 'error',
                'message': 'Account ID column is required'
            }), 400
        
        # Read file content
        file_content = file.read()
        
        # Extract Account IDs from Excel
        extraction_result = excel_service.extract_account_ids_from_excel(
            file_content, sheet_name, account_id_column
        )
        
        if not extraction_result['success']:
            return jsonify({
                'status': 'error',
                'message': extraction_result['error']
            }), 400
        
        account_ids = extraction_result['account_ids']
        
        if not account_ids:
            return jsonify({
                'status': 'error',
                'message': f'No valid Account IDs found in column "{account_id_column}"'
            }), 400
        
        # Validate shell Account IDs with Salesforce
        validation_result, validation_message = sf_service.validate_shell_account_ids(account_ids)
        
        if validation_result is None:
            return jsonify({
                'status': 'error',
                'message': validation_message
            }), 500
        
        # Include both valid and invalid IDs in response (no longer terminate on invalid IDs)
        invalid_account_ids = validation_result.get('invalid_account_ids', [])
        valid_count = len(validation_result.get('valid_account_ids', []))
        invalid_count = len(invalid_account_ids)
        
        if invalid_count > 0:
            invalid_ids_list = ', '.join(invalid_account_ids[:5])  # Show first 5 invalid IDs
            if invalid_count > 5:
                invalid_ids_list += f' (and {invalid_count - 5} more)'
            message = f'Validation complete: {valid_count} valid, {invalid_count} invalid shell account IDs. Invalid IDs: [{invalid_ids_list}]. Invalid IDs will be excluded from matching.'
        else:
            message = f'Successfully validated {valid_count} shell account IDs'
        
        return jsonify({
            'status': 'success',
            'message': message,
            'data': {
                'validation_summary': validation_result,
                'excel_info': {
                    'sheet_name': sheet_name,
                    'account_id_column': account_id_column,
                    'file_name': file.filename,
                    'total_rows': extraction_result['total_rows']
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing shell Excel file: {str(e)}'
        }), 500

@api_bp.route('/matching/process-batch', methods=['POST'])
def process_matching_batch():
    """Process dual-file matching between customer and shell accounts"""
    try:
        data = request.get_json()
        if not data or 'customer_account_ids' not in data or 'shell_account_ids' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: customer_account_ids and shell_account_ids"
            }), 400
        
        customer_account_ids = data['customer_account_ids']
        shell_account_ids = data['shell_account_ids']
        invalid_customer_ids = data.get('invalid_customer_ids', [])
        invalid_shell_ids = data.get('invalid_shell_ids', [])
        
        if not isinstance(customer_account_ids, list) or not isinstance(shell_account_ids, list):
            return jsonify({
                "status": "error",
                "message": "customer_account_ids and shell_account_ids must be lists"
            }), 400
        
        if len(customer_account_ids) == 0 or len(shell_account_ids) == 0:
            return jsonify({
                "status": "error",
                "message": "At least one customer and one shell account ID must be provided"
            }), 400
        
        # Get customer account data from Salesforce
        customer_data, customer_message = sf_service.get_customer_accounts_bulk(customer_account_ids)
        if customer_data is None:
            return jsonify({
                "status": "error",
                "message": f"Error retrieving customer account data: {customer_message}"
            }), 500
        
        # Get shell account data from Salesforce  
        shell_data, shell_message = sf_service.get_shell_accounts_bulk(shell_account_ids)
        if shell_data is None:
            return jsonify({
                "status": "error",
                "message": f"Error retrieving shell account data: {shell_message}"
            }), 500
        
        # Filter customer accounts by bad domains
        clean_customers, flagged_customers = sf_service.filter_customer_accounts_by_bad_domains(customer_data)
        
        # Process matching for clean customer accounts
        import time
        from services.openai_service import get_ai_match_assessment
        
        start_time = time.time()
        matched_pairs = []
        unmatched_customers = []
        
        for customer in clean_customers:
            # Find best shell match using fuzzy matching
            match_result = fuzzy_matcher.find_best_shell_match(customer, shell_data)
            
            if match_result['success']:
                best_match = match_result['best_match']
                
                # Get AI assessment for the match
                ai_assessment = get_ai_match_assessment(
                    customer, 
                    best_match['shell_account'], 
                    best_match
                )
                
                # Create match pair result
                match_pair = {
                    'customer_account': customer,
                    'recommended_shell': best_match['shell_account'],
                    'match_confidence': best_match['confidence_score'],
                    'website_match': best_match['website_match'],
                    'name_match': best_match['name_match'], 
                    'address_consistency': best_match['address_consistency'],
                    'explanations': best_match['explanations'],
                    'ai_assessment': {
                        'confidence_score': ai_assessment.get('confidence_score', 0),
                        'explanation_bullets': ai_assessment.get('explanation_bullets', []),
                        'success': ai_assessment.get('success', False)
                    },
                    'candidate_count': match_result['candidate_count'],
                    'total_shells': match_result['total_shells']
                }
                matched_pairs.append(match_pair)
            else:
                unmatched_customers.append({
                    'customer_account': customer,
                    'reason': match_result['message']
                })
        
        execution_time = time.time() - start_time
        
        return jsonify({
            "status": "success",
            "message": f"Matching completed successfully in {execution_time:.2f}s",
            "data": {
                "summary": {
                    "total_customer_accounts": len(customer_data) + len(invalid_customer_ids),
                    "clean_customer_accounts": len(clean_customers),
                    "flagged_customer_accounts": len(flagged_customers),
                    "invalid_customer_accounts": len(invalid_customer_ids),
                    "total_shell_accounts": len(shell_data) + len(invalid_shell_ids),
                    "invalid_shell_accounts": len(invalid_shell_ids),
                    "matched_pairs": len(matched_pairs),
                    "unmatched_customers": len(unmatched_customers),
                    "execution_time": f"{execution_time:.2f}s"
                },
                "matched_pairs": matched_pairs,
                "unmatched_customers": unmatched_customers,
                "flagged_customers": flagged_customers,
                "invalid_customers": invalid_customer_ids
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error processing matching batch: {str(e)}"
        }), 500

@api_bp.route('/export/matching-results', methods=['POST'])
def export_matching_results():
    """Export dual-file matching results to Excel"""
    try:
        data = request.get_json()
        if not data or 'matched_pairs' not in data:
            return jsonify({
                "status": "error",
                "message": "No matching results data provided for export"
            }), 400
        
        matched_pairs = data['matched_pairs']
        unmatched_customers = data.get('unmatched_customers', [])
        flagged_customers = data.get('flagged_customers', [])
        invalid_customers = data.get('invalid_customers', [])
        summary = data.get('summary', {})
        
        # Create Excel export
        export_result = excel_service.create_matching_results_export(
            matched_pairs=matched_pairs,
            unmatched_customers=unmatched_customers,
            flagged_customers=flagged_customers,
            invalid_customers=invalid_customers,
            summary=summary
        )
        
        if export_result['success']:
            return send_file(
                export_result['file_buffer'],
                as_attachment=True,
                download_name=export_result['filename'],
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({
                "status": "error",
                "message": export_result['error']
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Export failed: {str(e)}"
        }), 500