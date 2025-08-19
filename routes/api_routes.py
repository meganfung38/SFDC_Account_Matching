from flask import Blueprint, jsonify, request, send_file
from services.salesforce_service import SalesforceService
from services.openai_service import test_openai_connection, test_openai_completion, get_openai_config
from services.excel_service import ExcelService
from config.config import Config

# Create blueprint for API routes
api_bp = Blueprint('api', __name__)

# Initialize services
sf_service = SalesforceService()
excel_service = ExcelService()

@api_bp.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        "message": "Account to Shell Account Assessment API",
        "version": "1.0.0",
        "status": "running",
        "web_ui": "/",
        "endpoints": {
            "health": "/health",
            "debug_config": "/debug-config",
            "salesforce_test": "/test-salesforce-connection",
            "openai_test": "/test-openai-connection",
            "openai_completion": "/test-openai-completion",
            "get_account": "/account/<account_id>",
            "query_accounts": "/accounts",
            "analyze_query": "/accounts/analyze-query",
            "get_accounts_data": "/accounts/get-data"
        }
    })

@api_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Account to Shell Account Assessment API"
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

@api_bp.route('/account/<account_id>', methods=['GET', 'POST'])
def get_account(account_id):
    """Get specific Account data by Account ID"""
    try:
        result, message = sf_service.get_account_by_id(account_id)
        
        if result:
            return jsonify({
                "status": "success",
                "message": message,
                "data": result
            })
        else:
            return jsonify({
                "status": "error",
                "message": message
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500

@api_bp.route('/accounts', methods=['GET'])
def query_accounts():
    """Query accounts with optional filters"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        where_clause = request.args.get('where')
        
        # Query accounts using the service
        result, message = sf_service.query_accounts(where_clause, limit)
        
        if result is None:
            return jsonify({
                'status': 'error',
                'message': message
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': message,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error querying accounts: {str(e)}'
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

@api_bp.route('/accounts/analyze-query', methods=['POST'])
def analyze_accounts_query():
    """Get Account IDs from a custom SOQL query that returns Account IDs only"""
    try:
        # Get JSON data from request
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'soql_query' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: soql_query'
            }), 400
        
        soql_query = data['soql_query']
        max_ids = data.get('max_ids', '')
        
        # Handle optional max_ids parameter
        if max_ids == '' or max_ids is None:
            max_ids = None  # No limit
        else:
            try:
                max_ids = int(max_ids)
                if max_ids < 1 or max_ids > 500:
                    return jsonify({
                        'status': 'error',
                        'message': 'max_ids must be an integer between 1 and 500, or leave blank for all results'
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    'status': 'error',
                    'message': 'max_ids must be a valid number, or leave blank for all results'
                }), 400
        
        # Get Account IDs from query
        result, message = sf_service.get_account_ids_from_query(soql_query, max_ids)
        
        if result is None:
            # Check if it's a validation error or just no results
            if "Invalid" in message or "Error" in message:
                return jsonify({
                    'status': 'error',
                    'message': message
                }), 400
            else:
                # No results is not an error
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'data': {
                        'account_ids': [],
                        'summary': {
                            'total_found': 0,
                            'execution_time': '0.00s',
                            'effective_limit': max_ids
                        }
                    }
                })
        
        # Success with results
        return jsonify({
            'status': 'success',
            'message': message,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/accounts/get-data', methods=['POST'])
def get_accounts_data():
    """Get full Account data for a list of Account IDs"""
    try:
        # Get JSON data from request
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'account_ids' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: account_ids'
            }), 400
        
        account_ids = data['account_ids']
        
        # Validate account_ids is a list
        if not isinstance(account_ids, list):
            return jsonify({
                'status': 'error',
                'message': 'account_ids must be a list'
            }), 400
        
        # Validate not too many IDs
        if len(account_ids) > 500:
            return jsonify({
                'status': 'error',
                'message': 'Cannot request data for more than 500 accounts at once'
            }), 400
        
        # Get full Account data
        result, message = sf_service.get_accounts_data_by_ids(account_ids)
        
        if result is None:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
        
        return jsonify({
            'status': 'success',
            'message': message,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error getting Account data: {str(e)}'
        }), 500

@api_bp.route('/excel/parse', methods=['POST'])
def parse_excel_file():
    """Parse uploaded Excel file and return sheet names and preview data"""
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
        
        # Validate file extension
        filename = file.filename
        if not filename or not filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({
                'status': 'error',
                'message': 'File must be an Excel file (.xlsx or .xls)'
            }), 400
        
        # Read file content
        file_content = file.read()
        
        # Parse the Excel file
        result = excel_service.parse_excel_file(file_content)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Excel file parsed successfully',
                'data': {
                    'sheet_names': result['sheet_names'],
                    'headers': result['headers'],
                    'preview_data': result['preview_data'],
                    'total_rows': result['total_rows']
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result['error']
            }), 400
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error parsing Excel file: {str(e)}'
        }), 500

@api_bp.route('/excel/validate-account-ids', methods=['POST'])
def validate_excel_account_ids():
    """Validate Account IDs from Excel file upload and return Account data"""
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
        validation_result, validation_message = sf_service.validate_account_ids(account_ids)
        
        if validation_result is None:
            return jsonify({
                'status': 'error',
                'message': validation_message
            }), 500
        
        # Check if any Account IDs are invalid
        invalid_account_ids = validation_result.get('invalid_account_ids', [])
        if invalid_account_ids:
            return jsonify({
                'status': 'error',
                'message': f'Invalid Account IDs found: {", ".join(invalid_account_ids)}. All Account IDs must be valid to proceed with analysis.',
                'data': {
                    'invalid_account_ids': invalid_account_ids,
                    'valid_account_ids': validation_result.get('valid_account_ids', []),
                    'total_from_excel': len(account_ids)
                }
            }), 400
        
        # All Account IDs are valid - now get the Account data
        valid_account_ids = validation_result['valid_account_ids']
        
        # Get full Account data for the valid IDs
        account_data_result, account_data_message = sf_service.get_accounts_data_by_ids(valid_account_ids)
        
        if account_data_result is None:
            return jsonify({
                'status': 'error',
                'message': f'Account IDs validated successfully, but failed to retrieve Account data: {account_data_message}'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully validated and retrieved data for {len(valid_account_ids)} accounts from Excel file',
            'data': {
                'validation_summary': {
                    'total_ids_from_excel': len(account_ids),
                    'valid_account_ids': len(valid_account_ids),
                    'invalid_account_ids': 0,
                    'original_data_rows': extraction_result['total_rows']
                },
                'accounts': account_data_result['accounts'],
                'original_excel_data': extraction_result['original_data'],  # Add original Excel data
                'execution_time': account_data_result['execution_time'],
                'excel_info': {
                    'sheet_name': sheet_name,
                    'account_id_column': account_id_column,
                    'file_name': file.filename
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing Excel file: {str(e)}'
        }), 500

@api_bp.route('/export/soql-analysis', methods=['POST'])
def export_soql_analysis():
    """Export SOQL analysis results to Excel"""
    try:
        data = request.get_json()
        if not data or 'accounts' not in data:
            return jsonify({
                "status": "error",
                "message": "No analysis data provided for export"
            }), 400
        
        accounts = data['accounts']
        summary = data.get('summary', {})
        
        # Create Excel export
        excel_service = ExcelService()
        export_result = excel_service.create_analysis_export(
            accounts=accounts,
            summary=summary,
            export_type="soql_analysis"
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

@api_bp.route('/export/single-account', methods=['POST'])
def export_single_account():
    """Export single account analysis to Excel"""
    try:
        data = request.get_json()
        if not data or 'account' not in data:
            return jsonify({
                "status": "error",
                "message": "No account data provided for export"
            }), 400
        
        account = data['account']
        
        # Create Excel export
        excel_service = ExcelService()
        export_result = excel_service.create_analysis_export(
            accounts=[account],
            summary={'total_requested': 1, 'accounts_retrieved': 1},
            export_type="single_account"
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

@api_bp.route('/export/excel-analysis', methods=['POST'])
def export_excel_analysis():
    """Export Excel analysis results with original data"""
    try:
        data = request.get_json()
        if not data or 'accounts' not in data or 'original_data' not in data:
            return jsonify({
                "status": "error",
                "message": "No analysis data or original Excel data provided for export"
            }), 400
        
        accounts = data['accounts']
        original_data = data['original_data']
        excel_info = data.get('excel_info', {})
        
        # Create Excel export
        excel_service = ExcelService()
        export_result = excel_service.create_excel_analysis_export(
            accounts=accounts,
            original_data=original_data,
            excel_info=excel_info
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