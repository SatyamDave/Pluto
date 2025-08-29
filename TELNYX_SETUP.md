# 🚀 Telnyx Setup Guide for Jarvis Phone

This guide will walk you through setting up Telnyx SMS + Voice for Jarvis Phone AI Assistant. **Telnyx is 30-70% cheaper than Twilio**, making it perfect for your 100-user beta!

## 💰 **Cost Comparison for 100 Beta Users**

**Monthly costs with typical usage:**
- **Twilio**: ~$45-65/month
- **Telnyx**: ~$25-35/month
- **Savings**: **$20-30/month** (40-50% cheaper!)

## 📋 Prerequisites

- [Telnyx Account](https://telnyx.com/sign-up) (free, no credit card required for signup)
- Credit card for phone number purchase
- Domain with HTTPS for webhooks (ngrok works for development)

## 🔑 Step 1: Create Telnyx Account

### 1.1 Sign Up
1. Go to [telnyx.com/sign-up](https://telnyx.com/sign-up)
2. Fill out the signup form
3. Verify your email address
4. Complete account setup

### 1.2 Get Your API Key
1. Go to [Telnyx Portal](https://portal.telnyx.com/)
2. Navigate to **Develop → API Keys**
3. Click **"Create API Key"**
4. Give it a name like "Jarvis Phone Production"
5. Copy the **API Key** (starts with `KEY...`)
6. **⚠️ Save this securely - you won't see it again!**

## 📞 Step 2: Buy a Phone Number

### 2.1 Purchase Steps
1. Go to **Portal → Phone Numbers → Buy Numbers**
2. Select your area code/region
3. Choose capabilities:
   - ✅ **Voice** (for calls)
   - ✅ **SMS** (for text messages)
4. Click **Buy** (typically $1/month + usage)

### 2.2 Number Types
- **Local Number** (Recommended):
  - Cost: $1/month + usage
  - No emergency address required
  - Works immediately
  
- **Toll-Free Number**:
  - Cost: $2/month + usage
  - **⚠️ REQUIRES emergency address within 30 days**
  - Number gets suspended if not provided

## ⚙️ Step 3: Configure Webhooks

### 3.1 Set Webhook URLs
1. Go to **Portal → Phone Numbers → Manage**
2. Click on your purchased number
3. Configure these webhook URLs:

```
Inbound SMS:
https://yourdomain.com/api/v1/sms/webhook
HTTP Method: POST

Inbound Voice:
https://yourdomain.com/api/v1/voice/webhook/incoming
HTTP Method: POST
```

### 3.2 Development with ngrok
If testing locally:
```bash
# Install ngrok
npm install -g ngrok

# Start your FastAPI app
python main.py

# In another terminal, expose your app
ngrok http 8000

# Use the ngrok URL for webhooks
# Example: https://abc123.ngrok.io/api/v1/sms/webhook
```

## 🔧 Step 4: Environment Configuration

### 4.1 Update .env File
```env
# Telnyx Configuration (Primary provider)
TELNYX_API_KEY=KEYxxxxxxxxxxxxxxxxxxxx
TELNYX_PHONE_NUMBER=+15551234567
TELNYX_WEBHOOK_SECRET=your_webhook_secret_here

# Set telephony provider to Telnyx
TELEPHONY_PROVIDER=telnyx

# Base URL for webhooks
BASE_URL=https://yourdomain.com
```

### 4.2 Verify Configuration
```python
# Test your setup
from config import is_telnyx_enabled
print(f"Telnyx enabled: {is_telnyx_enabled()}")
```

## 🧪 Step 5: Test Your Setup

### 5.1 Test SMS
1. Text your Telnyx number: "Hello Jarvis"
2. Check your FastAPI logs for webhook receipt
3. Verify Jarvis responds via SMS

### 5.2 Test Voice
1. Call your Telnyx number
2. Listen for Jarvis greeting
3. Speak a request and verify response

### 5.3 Test Outbound Operations
```python
# Send test SMS
from telephony.telnyx_handler import TelnyxHandler
handler = TelnyxHandler()
await handler.send_sms("+15551234567", "Test message from Jarvis!")

# Make test call
await handler.make_call("+15551234567", "This is a test call from Jarvis!")
```

## 📊 Step 6: Monitor Usage

### 6.1 Telnyx Portal
- **Portal → Phone Numbers**: Manage your numbers
- **Portal → Messaging**: View SMS logs and analytics
- **Portal → Call Control**: View call logs and analytics
- **Portal → Billing**: Track costs and usage

### 6.2 Your Application Logs
```bash
# Check FastAPI logs
tail -f logs/jarvis.log

# Monitor webhook endpoints
curl -X GET https://yourdomain.com/api/v1/sms/status
curl -X GET https://yourdomain.com/api/v1/voice/status
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Data
- ✅ Verify HTTPS (required for production)
- ✅ Check webhook URL spelling
- ✅ Ensure FastAPI is running
- ✅ Check firewall/network settings

#### 2. SMS Not Sending
- ✅ Verify API Key is correct
- ✅ Check account balance
- ✅ Verify phone number format (+1XXXXXXXXXX)
- ✅ Check Telnyx portal for error codes

#### 3. Voice Calls Not Working
- ✅ Verify Voice capability is enabled
- ✅ Check Call Control webhook configuration
- ✅ Ensure webhook returns valid JSON
- ✅ Check call logs in Telnyx portal

#### 4. Emergency Address Required (Toll-Free)
- ⚠️ **CRITICAL**: Provide emergency address within 30 days
- Go to **Portal → Phone Numbers → Emergency Addresses**
- Add your business address
- Verify with supporting documents

### Error Codes
- **400**: Bad request (check webhook payload)
- **401**: Unauthorized (check API key)
- **403**: Forbidden (check permissions)
- **404**: Not found (check phone number)

## 💰 Cost Management

### Pricing (US Numbers)
- **Local Number**: $1/month
- **Toll-Free Number**: $2/month
- **SMS**: $0.004 per message (vs Twilio's $0.0079)
- **Voice**: $0.002 per minute (vs Twilio's $0.0085)

### Cost Optimization
1. **Start with local number** (no emergency address needed)
2. **Use Telnyx's free tier** (first $50 free)
3. **Monitor usage** in Telnyx portal
4. **Set up billing alerts** for unexpected charges

## 🔒 Security Best Practices

### 1. Protect Credentials
- Never commit `.env` files to git
- Use environment variables in production
- Rotate API keys regularly

### 2. Webhook Security
- Use HTTPS in production
- Implement webhook signature validation
- Rate limit webhook endpoints

### 3. Phone Number Security
- Don't share your Telnyx number publicly during development
- Use ngrok for local testing
- Monitor for abuse/spam

## 🚀 Production Deployment

### 1. Domain Setup
- Use a real domain (not ngrok)
- Ensure HTTPS is enabled
- Set up proper DNS

### 2. Environment Variables
```bash
# Production .env
TELNYX_API_KEY=KEYxxxxxxxxxxxxxxxxxxxx
TELNYX_PHONE_NUMBER=+15551234567
TELNYX_WEBHOOK_SECRET=your_webhook_secret_here
TELEPHONY_PROVIDER=telnyx
BASE_URL=https://yourdomain.com
DEBUG=False
LOG_LEVEL=WARNING
```

### 3. Monitoring
- Set up Telnyx usage alerts
- Monitor webhook response times
- Track error rates and success rates

## 🐳 Docker Compose Setup

### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - TELNYX_API_KEY=${TELNYX_API_KEY}
      - TELNYX_PHONE_NUMBER=${TELNYX_PHONE_NUMBER}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=jarvis_phone
      - POSTGRES_USER=jarvis
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  ngrok:
    image: ngrok/ngrok:latest
    command: http app:8000
    ports:
      - "4040:4040"
    environment:
      - NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN}

volumes:
  postgres_data:
```

## 📱 Next Steps

Once Telnyx is working:

1. **Test all Jarvis features** via SMS and voice
2. **Set up proactive automation** (daily digests, wake-up calls)
3. **Implement outbound calling** (AI calling humans)
4. **Add monitoring and analytics**
5. **Scale to multiple numbers** if needed

## 🆘 Support

- **Telnyx Support**: [support.telnyx.com](https://support.telnyx.com)
- **Telnyx Docs**: [developers.telnyx.com](https://developers.telnyx.com)
- **Community**: [Stack Overflow](https://stackoverflow.com/questions/tagged/telnyx)

---

**🎯 You're now ready to launch Jarvis Phone with Telnyx!**

Users can simply save your number as "Jarvis" and start texting/calling for AI assistance. You'll save **30-70% on costs** compared to Twilio!
