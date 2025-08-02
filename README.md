# 💳 M-Pesa Flask Integration

A robust, production-ready Flask application for integrating M-Pesa STK Push payments with real-time transaction status tracking.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![M-Pesa](https://img.shields.io/badge/M--Pesa-STK%20Push-orange.svg)](https://developer.safaricom.co.ke)

## 🌟 Features

- **STK Push Integration** - Seamless M-Pesa payment initiation
- **Real-time Status Tracking** - Live transaction status updates
- **Smart Phone Number Validation** - Handles multiple Kenyan phone number formats
- **Token Caching** - Efficient API token management with automatic refresh
- **Retry Logic** - Robust error handling with automatic retries
- **Modern UI** - Responsive design with real-time feedback
- **Test Mode** - Built-in testing capabilities for development
- **Comprehensive Logging** - Detailed logging for debugging and monitoring
- **Production Ready** - Built with security and scalability in mind

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- M-Pesa Developer Account ([Register here](https://developer.safaricom.co.ke))
- ngrok (for local testing) - [Download here](https://ngrok.com/download)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Denniskaninu/mpesa-push-stk.git
   cd mpesa-flask-integration
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your M-Pesa credentials
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open http://localhost:5000 in your browser
   - Use the test mode for immediate testing

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# M-Pesa API Credentials
CONSUMER_KEY=your_consumer_key_here
CONSUMER_SECRET=your_consumer_secret_here
BUSINESS_SHORT_CODE=your_business_shortcode
PASSKEY=your_passkey_here
CALLBACK_URL=https://yourdomain.com/callback

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=True
```

### M-Pesa Credentials Setup

1. **Register at Safaricom Developer Portal**
   - Visit [developer.safaricom.co.ke](https://developer.safaricom.co.ke)
   - Create an account and new app

2. **Get Sandbox Credentials**
   - Consumer Key
   - Consumer Secret
   - Business Shortcode (use `174379` for sandbox)
   - Passkey (provided in sandbox)

3. **Set Callback URL**
   - For local development, use ngrok: `https://abc123.ngrok.io/callback`
   - For production, use your domain: `https://yourdomain.com/callback`

## 📱 Phone Number Formats

The application automatically handles various Kenyan phone number formats:

- `254712345678` - International format
- `0712345678` - Local format with leading zero
- `712345678` - Without country code
- `+254 712 345 678` - With spaces and symbols

## 🔧 API Endpoints

### Payment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main payment interface |
| `POST` | `/pay` | Initiate STK Push |
| `POST` | `/callback` | M-Pesa callback handler |
| `GET` | `/transaction-status/<id>` | Check transaction status |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health check |
| `GET` | `/debug/transactions` | View all transactions (dev only) |
| `GET/POST` | `/test-callback` | Test callback simulation |

## 💻 Usage Examples

### Basic Payment Request

```javascript
// Frontend JavaScript
const response = await fetch('/pay', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        phone: '254712345678',
        amount: 100
    })
});

const data = await response.json();
if (data.success) {
    // Start checking transaction status
    checkTransactionStatus(data.checkout_request_id);
}
```

### Python Backend Usage

```python
from your_app import lipa_na_mpesa_online

# Initiate payment
result = lipa_na_mpesa_online('254712345678', 100)

if result['success']:
    checkout_request_id = result['checkout_request_id']
    # Store and track this ID
```

## 🧪 Testing

### Test Mode

Enable test mode in the UI to simulate the entire payment flow without calling M-Pesa APIs:

1. Check the "🧪 Test Mode" box in the interface
2. Enter any phone number and amount
3. The system will simulate success/failure responses

### Manual Testing

1. **Test Callback Simulation**
   ```bash
   curl -X POST http://localhost:5000/test-callback \
        -d "checkout_request_id=test-123&result_code=0"
   ```

2. **Check Transaction Status**
   ```bash
   curl http://localhost:5000/transaction-status/test-123
   ```

### Local Development with ngrok

```bash
# Terminal 1: Start Flask app
python app.py

# Terminal 2: Expose locally
ngrok http 5000

# Update .env with ngrok URL
CALLBACK_URL=https://abc123.ngrok.io/callback
```
### Development
- ✅ Use sandbox credentials
- ✅ Test with small amounts
- ✅ Use ngrok for secure callbacks
- ✅ Never commit `.env` files

### Production
- 🔐 Use production M-Pesa credentials
- 🔐 Implement HTTPS everywhere
- 🔐 Validate callback signatures
- 🔐 Use environment variables for secrets
- 🔐 Implement rate limiting
- 🔐 Set up proper logging and monitoring
- 🔐 Use a production database (PostgreSQL/MySQL)
- 🔐 Implement proper authentication

## 📊 Monitoring and Logging

The application provides comprehensive logging:

```python
# Log levels
logger.info("STK push initiated successfully")
logger.warning("Failed payment attempt")
logger.error("API connection failed")
```

### Log Locations
- Console output during development
- `logs/` directory for file logging
- Configure external logging services for production
```

### Environment Variables for Production

```bash
# Set production environment variables
export CONSUMER_KEY="your_production_consumer_key"
export CONSUMER_SECRET="your_production_consumer_secret"
export BUSINESS_SHORT_CODE="your_production_shortcode"
export PASSKEY="your_production_passkey"
export CALLBACK_URL="https://yourdomain.com/callback"
export FLASK_ENV="production"
```

## 🐛 Troubleshooting

### Common Issues

**1. "Enter your M-Pesa PIN..." stuck indefinitely**
- **Cause**: Callback URL not reachable
- **Solution**: Use ngrok for local testing or check firewall settings

**2. "Transaction not found" error**
- **Cause**: Transaction storage issue
- **Solution**: Check if transaction was properly stored, restart application

**3. Authentication failures**
- **Cause**: Wrong credentials or expired tokens
- **Solution**: Verify credentials in `.env`, check token caching

**4. Phone number format errors**
- **Cause**: Invalid phone number format
- **Solution**: Use supported formats (254XXXXXXXXX, 0XXXXXXXXX, XXXXXXXXX)

### Debug Commands

```bash
# Check application health
curl http://localhost:5000/health

# View all transactions
curl http://localhost:5000/debug/transactions

# Test callback manually
curl -X POST http://localhost:5000/test-callback \
     -d "checkout_request_id=YOUR_ID&result_code=0"
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Ensure security best practices

## 📝 API Response Examples

### Successful STK Push
```json
{
    "success": true,
    "message": "STK push sent successfully",
    "checkout_request_id": "ws_CO_123456789",
    "merchant_request_id": "16740-34861180-1",
    "response_code": "0",
    "response_description": "Success. Request accepted for processing"
}
```

### Transaction Status - Success
```json
{
    "success": true,
    "status": "success",
    "result_code": 0,
    "result_desc": "The service request is processed successfully.",
    "transaction_details": {
        "amount": 100,
        "receipt_number": "NLJ7RT61SV",
        "transaction_date": "20231201143022",
        "phone_number": "254712345678"
    }
}
```

### Transaction Status - Failed
```json
{
    "success": true,
    "status": "failed",
    "result_code": 1032,
    "result_desc": "Request cancelled by user"
}
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Safaricom Developer Portal](https://developer.safaricom.co.ke)
- **Issues**: Create an issue in this repository
- **Email**: your-email@domain.com

## 🙏 Acknowledgments

- [Safaricom](https://safaricom.co.ke) for the M-Pesa API
- [Flask](https://flask.palletsprojects.com) team for the amazing framework
- [Tailwind CSS](https://tailwindcss.com) for the UI components

