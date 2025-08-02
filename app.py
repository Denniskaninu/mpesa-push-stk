from flask import Flask, render_template, request, jsonify
import requests
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import re
import time
from functools import wraps

load_dotenv()

app = Flask(__name__)

# M-Pesa credentials
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
BUSINESS_SHORT_CODE = os.getenv("BUSINESS_SHORT_CODE")
PASSKEY = os.getenv("PASSKEY")
CALLBACK_URL = os.getenv("CALLBACK_URL")

# Configuration
SANDBOX_BASE_URL = "https://sandbox.safaricom.co.ke"
PRODUCTION_BASE_URL = "https://api.safaricom.co.ke"
BASE_URL = SANDBOX_BASE_URL  # Change to PRODUCTION_BASE_URL for live environment

# Token caching
access_token_cache = {
    'token': None,
    'expires_at': None
}

def retry_on_failure(max_retries=3, delay=1):
    """Decorator to retry function calls on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def validate_phone_number(phone):
    """Validate and standardize phone number to Kenyan format"""
    if not phone:
        raise ValueError("Phone number is required")
    
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', str(phone))
    
    # Handle different formats
    if phone.startswith('254'):
        # Already in correct format (254XXXXXXXXX)
        if len(phone) != 12:
            raise ValueError("Invalid phone number format")
        return phone
    elif phone.startswith('0'):
        # Kenyan format starting with 0 (0XXXXXXXXX)
        if len(phone) != 10:
            raise ValueError("Invalid phone number format")
        return '254' + phone[1:]
    elif phone.startswith('7') or phone.startswith('1'):
        # Without country code or leading zero (XXXXXXXXX)
        if len(phone) != 9:
            raise ValueError("Invalid phone number format")
        return '254' + phone
    else:
        raise ValueError("Unsupported phone number format")

def validate_amount(amount):
    """Validate transaction amount"""
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        if amount > 70000:  # M-Pesa daily limit
            raise ValueError("Amount exceeds daily transaction limit")
        return int(amount)  # M-Pesa expects integer amounts
    except (ValueError, TypeError):
        raise ValueError("Invalid amount format")

@retry_on_failure(max_retries=3, delay=2)
def get_access_token():
    """Get cached access token or fetch new one"""
    current_time = datetime.now()
    
    # Check if we have a valid cached token
    if (access_token_cache['token'] and 
        access_token_cache['expires_at'] and 
        current_time < access_token_cache['expires_at']):
        return access_token_cache['token']
    
    # Fetch new token
    try:
        api_url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(
            api_url, 
            auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET),
            timeout=30
        )
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data['access_token']
        expires_in = int(token_data.get('expires_in', 3600))  # Default 1 hour
        
        # Cache the token (expire 5 minutes early for safety)
        access_token_cache['token'] = access_token
        access_token_cache['expires_at'] = current_time + timedelta(seconds=expires_in - 300)
        
        return access_token
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Authentication failed: {str(e)}")
    except KeyError as e:
        raise Exception("Invalid authentication response")

@retry_on_failure(max_retries=2, delay=3)
def lipa_na_mpesa_online(phone_number, amount):
    """Initiate STK push with proper error handling"""
    try:
        # Validate inputs
        phone_number = validate_phone_number(phone_number)
        amount = validate_amount(amount)
        
        # Get access token
        access_token = get_access_token()
        
        # Prepare API call
        api_url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Generate timestamp and password
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{BUSINESS_SHORT_CODE}{PASSKEY}{timestamp}"
        password = base64.b64encode(password_string.encode('utf-8')).decode('utf-8')
        
        # Prepare payload
        payload = {
            "BusinessShortCode": BUSINESS_SHORT_CODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": BUSINESS_SHORT_CODE,
            "PhoneNumber": phone_number,
            "CallBackURL": CALLBACK_URL,
            "AccountReference": f"ORDER_{timestamp}",
            "TransactionDesc": f"Payment for order {timestamp}"
        }
        
        # Make API call
        response = requests.post(
            api_url, 
            json=payload, 
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Check if the request was successful
        if result.get('ResponseCode') == '0':
            return {
                'success': True,
                'message': 'STK push sent successfully',
                'checkout_request_id': result.get('CheckoutRequestID'),
                'merchant_request_id': result.get('MerchantRequestID'),
                'response_code': result.get('ResponseCode'),
                'response_description': result.get('ResponseDescription')
            }
        else:
            return {
                'success': False,
                'message': result.get('ResponseDescription', 'Transaction failed'),
                'response_code': result.get('ResponseCode')
            }
            
    except ValueError as e:
        return {'success': False, 'message': str(e)}
    except requests.exceptions.Timeout:
        return {'success': False, 'message': 'Request timeout. Please try again.'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'message': 'Payment service temporarily unavailable'}
    except Exception as e:
        return {'success': False, 'message': 'An unexpected error occurred'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pay', methods=['POST'])
def pay():
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        phone_number = data.get('phone', '').strip()
        amount = data.get('amount', '')
        
        # Basic validation
        if not phone_number:
            return jsonify({"success": False, "message": "Phone number is required"}), 400
        
        if not amount:
            return jsonify({"success": False, "message": "Amount is required"}), 400
        
        # Process payment
        result = lipa_na_mpesa_online(phone_number, amount)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": "Payment processing failed"
        }), 500

@app.route('/callback', methods=['POST'])
def callback():
    """Handle M-Pesa callback"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"ResultCode": 1, "ResultDesc": "Invalid data"}), 400
        
        # Extract relevant information
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        
        if result_code == 0:
            # Successful transaction
            callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            transaction_data = {}
            
            for item in callback_metadata:
                name = item.get('Name')
                value = item.get('Value')
                transaction_data[name] = value
            
        # Always return success to M-Pesa
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200
        
    except Exception as e:
        return jsonify({"ResultCode": 1, "ResultDesc": "Internal error"}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test if we can get an access token
        token = get_access_token()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "token_cached": bool(access_token_cache['token'])
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "Internal server error"}), 500

if __name__ == '__main__':
    # Validate required environment variables
    required_vars = ['CONSUMER_KEY', 'CONSUMER_SECRET', 'BUSINESS_SHORT_CODE', 'PASSKEY', 'CALLBACK_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=5000)