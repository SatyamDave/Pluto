# 🚀 Twilio Setup Guide for Jarvis Phone

This guide will walk you through setting up Twilio SMS + Voice for Jarvis Phone AI Assistant.

## 📋 Prerequisites

- [Twilio Account](https://www.twilio.com/try-twilio) (free trial available)
- Credit card for verification (required for trial)
- Domain with HTTPS for webhooks (ngrok works for development)

## 🔑 Step 1: Get Twilio Credentials

### 1.1 Sign Up for Twilio
1. Go to [twilio.com](https://www.twilio.com/try-twilio)
2. Fill out the signup form
3. Verify your email and phone number
4. Complete account verification

### 1.2 Get Your Credentials
1. Go to [Twilio Console](https://console.twilio.com/)
2. Copy your **Account SID** and **Auth Token**
3. Keep these secure - they're your API keys!

## 📞 Step 2: Buy a Phone Number

### 2.1 Choose Number Type
- **Local Number** (Recommended for MVP):
  - Cost: $1/month + usage
  - No emergency address required
  - Works immediately
  
- **Toll-Free Number**:
  - Cost: $2/month + usage
  - **⚠️ REQUIRES emergency address within 30 days**
  - Number gets suspended if not provided

### 2.2 Purchase Steps
1. Go to **Console → Phone Numbers → Manage → Buy a number**
2. Select your area code/region
3. Choose capabilities:
   - ✅ **Voice** (for calls)
   - ✅ **SMS** (for text messages)
   - ✅ **MMS** (optional, for media)
4. Click **Buy** and confirm

## ⚙️ Step 3: Configure Webhooks

### 3.1 Set Webhook URLs
1. Go to **Console → Phone Numbers → Manage**
2. Click on your purchased number
3. Configure these webhook URLs:

```
A Call Comes In:
https://yourdomain.com/api/v1/voice/webhook/incoming
HTTP Method: POST

A Message Comes In:
https://yourdomain.com/api/v1/sms/webhook
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
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=yyyyyyyyyyyyyyyyyyyy
TWILIO_PHONE_NUMBER=+15551234567

# Set telephony provider to Twilio
TELEPHONY_PROVIDER=twilio
```

### 4.2 Verify Configuration
```python
# Test your setup
from config import is_twilio_enabled
print(f"Twilio enabled: {is_twilio_enabled()}")
```

## 🧪 Step 5: Test Your Setup

### 5.1 Test SMS
1. Text your Twilio number: "Hello Jarvis"
2. Check your FastAPI logs for webhook receipt
3. Verify Jarvis responds via SMS

### 5.2 Test Voice
1. Call your Twilio number
2. Listen for Jarvis greeting
3. Speak a request and verify response

### 5.3 Test Outbound Operations
```python
# Send test SMS
from telephony.twilio_handler import TwilioHandler
handler = TwilioHandler()
await handler.send_sms("+15551234567", "Test message from Jarvis!")

# Make test call
await handler.make_call("+15551234567", "This is a test call from Jarvis!")
```

## 📊 Step 6: Monitor Usage

### 6.1 Twilio Console
- **Console → Monitor → Logs**: View all SMS and calls
- **Console → Monitor → Usage**: Track costs and usage
- **Console → Phone Numbers**: Manage your numbers

### 6.2 Your Application Logs
```bash
# Check FastAPI logs
tail -f logs/jarvis.log

# Monitor webhook endpoints
curl -X POST https://yourdomain.com/api/v1/sms/status
curl -X POST https://yourdomain.com/api/v1/voice/status
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Data
- ✅ Verify HTTPS (required for production)
- ✅ Check webhook URL spelling
- ✅ Ensure FastAPI is running
- ✅ Check firewall/network settings

#### 2. SMS Not Sending
- ✅ Verify Account SID and Auth Token
- ✅ Check account balance
- ✅ Verify phone number format (+1XXXXXXXXXX)
- ✅ Check Twilio console for error codes

#### 3. Voice Calls Not Working
- ✅ Verify Voice capability is enabled
- ✅ Check TwiML syntax
- ✅ Ensure webhook returns valid XML
- ✅ Check call logs in Twilio console

#### 4. Emergency Address Required (Toll-Free)
- ⚠️ **CRITICAL**: Provide emergency address within 30 days
- Go to **Console → Phone Numbers → Emergency Addresses**
- Add your business address
- Verify with supporting documents

### Error Codes
- **21211**: Invalid phone number
- **21214**: Invalid 'from' phone number
- **21608**: Account not active
- **21610**: Account suspended

## 💰 Cost Management

### Pricing (US Numbers)
- **Local Number**: $1/month
- **Toll-Free Number**: $2/month
- **SMS**: $0.0079 per message (US)
- **Voice**: $0.0085 per minute (US)

### Cost Optimization
1. **Start with local number** (no emergency address needed)
2. **Use free trial credits** ($15-20 free credit)
3. **Monitor usage** in Twilio console
4. **Set up billing alerts** for unexpected charges

## 🔒 Security Best Practices

### 1. Protect Credentials
- Never commit `.env` files to git
- Use environment variables in production
- Rotate Auth Token regularly

### 2. Webhook Security
- Use HTTPS in production
- Implement webhook signature validation
- Rate limit webhook endpoints

### 3. Phone Number Security
- Don't share your Twilio number publicly during development
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
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=yyyyyyyyyyyyyyyyyyyy
TWILIO_PHONE_NUMBER=+15551234567
TELEPHONY_PROVIDER=twilio
DEBUG=False
LOG_LEVEL=WARNING
```

### 3. Monitoring
- Set up Twilio usage alerts
- Monitor webhook response times
- Track error rates and success rates

## 📱 Next Steps

Once Twilio is working:

1. **Test all Jarvis features** via SMS and voice
2. **Set up proactive automation** (daily digests, wake-up calls)
3. **Implement outbound calling** (AI calling humans)
4. **Add monitoring and analytics**
5. **Scale to multiple numbers** if needed

## 🆘 Support

- **Twilio Support**: [support.twilio.com](https://support.twilio.com)
- **Twilio Docs**: [twilio.com/docs](https://www.twilio.com/docs)
- **Community**: [Stack Overflow](https://stackoverflow.com/questions/tagged/twilio)

---

**🎯 You're now ready to launch Jarvis Phone with Twilio!**

Users can simply save your number as "Jarvis" and start texting/calling for AI assistance.
