# 🚀 Pluto Telephony Setup Guide

This guide will help you connect Pluto to real phone numbers using either Telnyx or Twilio.

## 📋 Prerequisites

- ✅ Pluto AI Assistant running locally
- ✅ PostgreSQL and Redis running
- ✅ OpenRouter API key configured
- ✅ Phone number from Telnyx or Twilio

## 🔧 Configuration

### 1. Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Telephony Provider (choose one)
PROVIDER=telnyx  # or twilio
PHONE_NUMBER=+15551234567

# Telnyx Configuration (Recommended - 30-70% cheaper than Twilio)
TELNYX_API_KEY=your_telnyx_api_key_here
TELNYX_PHONE_NUMBER=+15551234567
TELNYX_WEBHOOK_SECRET=your_telnyx_webhook_secret_here

# Twilio Configuration (Alternative)
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567
TWILIO_WEBHOOK_SECRET=your_twilio_webhook_secret_here
```

### 2. Provider Selection

**Telnyx (Recommended):**
- ✅ 30-70% cheaper than Twilio
- ✅ Better international rates
- ✅ Modern API with better webhook handling
- ✅ Excellent developer experience

**Twilio (Alternative):**
- ✅ More established provider
- ✅ Extensive documentation
- ✅ More integrations available
- ✅ Higher costs

## 📱 Getting Phone Numbers

### Telnyx Setup

1. **Create Account:**
   - Visit [telnyx.com](https://telnyx.com)
   - Sign up for a free account
   - Add payment method

2. **Get Phone Number:**
   - Go to "Phone Numbers" → "Search & Order"
   - Search for available numbers in your area
   - Order a number (usually $1-3/month)

3. **Get API Key:**
   - Go to "Portal Settings" → "API Keys"
   - Create a new API key
   - Copy the key to your `.env` file

4. **Configure Webhooks:**
   - Go to "Phone Numbers" → Your Number → "Webhooks"
   - Set SMS webhook: `https://your-domain.com/api/v1/telephony/telnyx/sms`
   - Set Voice webhook: `https://your-domain.com/api/v1/telephony/telnyx/voice`

### Twilio Setup

1. **Create Account:**
   - Visit [twilio.com](https://twilio.com)
   - Sign up for a free account
   - Verify your phone number

2. **Get Phone Number:**
   - Go to "Phone Numbers" → "Manage" → "Buy a number"
   - Search for available numbers
   - Purchase a number (usually $1/month + usage)

3. **Get Credentials:**
   - Go to "Console" → "Settings" → "API Keys"
   - Copy Account SID and Auth Token
   - Add to your `.env` file

4. **Configure Webhooks:**
   - Go to "Phone Numbers" → Your Number → "Configuration"
   - Set SMS webhook: `https://your-domain.com/api/v1/telephony/twilio/sms`
   - Set Voice webhook: `https://your-domain.com/api/v1/telephony/twilio/voice`

## 🌐 Webhook Configuration

### Local Development

For local testing, use ngrok to expose your local server:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from ngrok.com

# Start Pluto
python main.py

# In another terminal, expose your local server
ngrok http 8000

# Use the ngrok URL for webhooks
# Example: https://abc123.ngrok.io/api/v1/telephony/telnyx/sms
```

### Production Deployment

For production, ensure your domain has HTTPS and configure webhooks:

```bash
# Example webhook URLs
SMS: https://pluto.yourdomain.com/api/v1/telephony/telnyx/sms
Voice: https://pluto.yourdomain.com/api/v1/telephony/telnyx/voice
```

## 🧪 Testing the Integration

### 1. Test Telephony Services

```bash
# Run telephony integration tests
python test_telephony_integration.py
```

### 2. Test Webhook Endpoints

```bash
# Check telephony status
curl http://localhost:8000/api/v1/telephony/status

# Get webhook URLs
curl http://localhost:8000/api/v1/telephony/webhook-urls
```

### 3. Test SMS Sending

```bash
# Send test SMS (replace with real phone number)
curl -X POST "http://localhost:8000/api/v1/telephony/send-sms" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "to=+1234567890&body=Hello from Pluto!&user_id=1"
```

### 4. Test Inbound SMS

1. Send an SMS to your configured phone number
2. Check Pluto's response
3. Verify the conversation is stored in the database

## 🔒 Security Considerations

### Webhook Signature Validation

Both Telnyx and Twilio support webhook signature validation:

```bash
# Telnyx
TELNYX_WEBHOOK_SECRET=your_secret_here

# Twilio
TWILIO_WEBHOOK_SECRET=your_secret_here
```

### Rate Limiting

Consider implementing rate limiting for webhook endpoints:

```python
# Example rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@limiter.limit("10/minute")
@router.post("/telnyx/sms")
async def telnyx_sms_webhook(request: Request):
    # ... webhook handling
```

## 📊 Monitoring & Debugging

### 1. Check Telephony Status

```bash
curl http://localhost:8000/api/v1/telephony/status
```

### 2. View Webhook Logs

Check your application logs for webhook processing:

```bash
# Tail logs
tail -f logs/pluto.log | grep telephony
```

### 3. Database Verification

Check that conversations are being stored:

```sql
-- Check user creation
SELECT * FROM users ORDER BY created_at DESC LIMIT 5;

-- Check message storage
SELECT * FROM user_memory ORDER BY timestamp DESC LIMIT 5;
```

## 🚨 Troubleshooting

### Common Issues

1. **Webhook Not Receiving:**
   - Verify webhook URLs are correct
   - Check firewall/security group settings
   - Ensure HTTPS is enabled for production

2. **Signature Validation Fails:**
   - Verify webhook secret is correct
   - Check timestamp synchronization
   - Ensure payload format matches provider expectations

3. **SMS Not Sending:**
   - Verify API keys are correct
   - Check account balance/credits
   - Verify phone number format (+1XXXXXXXXXX)

4. **Database Errors:**
   - Ensure PostgreSQL is running
   - Check database connection string
   - Verify tables are created

### Debug Mode

Enable debug logging in your `.env`:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## 💰 Cost Estimation

### Telnyx (Recommended)

**Monthly Costs:**
- Phone Number: $1-3/month
- SMS: $0.0039 per message (US)
- Voice: $0.0039 per minute (US)
- **Total for 100 users: $5-15/month**

### Twilio

**Monthly Costs:**
- Phone Number: $1/month
- SMS: $0.0079 per message (US)
- Voice: $0.0085 per minute (US)
- **Total for 100 users: $10-25/month**

## 🎯 Next Steps

1. **Test with Real Phone Numbers:**
   - Send SMS to your Pluto number
   - Verify AI responses
   - Check conversation storage

2. **Implement Voice Features:**
   - Add TTS (Text-to-Speech)
   - Implement voice response handling
   - Add call recording capabilities

3. **Add Advanced Features:**
   - Multi-language support
   - Voice recognition
   - Call analytics

4. **Scale Up:**
   - Add more phone numbers
   - Implement load balancing
   - Add monitoring and alerting

## 🆘 Support

If you encounter issues:

1. Check the logs for error messages
2. Verify configuration settings
3. Test with the provided test scripts
4. Check provider documentation (Telnyx/Twilio)

---

**🎉 Congratulations!** You now have Pluto connected to real phone numbers and ready to handle inbound/outbound SMS and voice calls!
