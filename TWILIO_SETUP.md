# Twilio Setup Guide for Jarvis Phone AI Assistant

This guide will help you set up Twilio as your primary telephony provider for Jarvis Phone.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   ```bash
   cp env.example .env
   # Edit .env with your Twilio credentials
   ```

3. **Test Configuration**
   ```bash
   python test_twilio_setup.py
   ```

## 📋 Prerequisites

- Twilio account (sign up at [twilio.com](https://twilio.com))
- Twilio phone number with SMS and Voice capabilities
- Python 3.8+ installed

## 🔑 Required Environment Variables

Add these to your `.env` file:

```bash
# Twilio Configuration (Primary)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567
TWILIO_WEBHOOK_SECRET=your_webhook_secret_here

# Telephony Provider
PROVIDER=twilio
PHONE_NUMBER=+15551234567
```

## 📱 Getting Your Twilio Credentials

### 1. Account SID and Auth Token
1. Log into [Twilio Console](https://console.twilio.com/)
2. Go to Dashboard → Account Info
3. Copy your Account SID and Auth Token

### 2. Phone Number
1. In Twilio Console, go to Phone Numbers → Manage → Active numbers
2. Buy a new number or use existing one
3. Ensure it has SMS and Voice capabilities enabled

### 3. Webhook Secret (Optional but Recommended)
1. Generate a random string (32+ characters)
2. Use this to validate incoming webhooks

## 🌐 Webhook Configuration

### SMS Webhook
Set your SMS webhook URL in Twilio Console:
```
https://your-domain.com/api/v1/sms/webhook
```

### Voice Webhook  
Set your Voice webhook URL in Twilio Console:
```
https://your-domain.com/api/v1/voice/webhook
```

## 🧪 Testing Your Setup

Run the test script to verify everything is working:

```bash
python test_twilio_setup.py
```

This will test:
- ✅ Configuration validation
- ✅ Service creation
- ✅ Telephony manager
- ✅ Webhook validation

## 📞 Testing SMS

Send a test SMS to your Twilio number:

```python
from telephony.telephony_manager import TelephonyManager
from config import settings

# Create manager
config = {
    "PROVIDER": "twilio",
    "PHONE_NUMBER": settings.TWILIO_PHONE_NUMBER,
    "twilio_account_sid": settings.TWILIO_ACCOUNT_SID,
    "twilio_auth_token": settings.TWILIO_AUTH_TOKEN,
    "twilio_phone_number": settings.TWILIO_PHONE_NUMBER,
    "twilio_webhook_secret": settings.TWILIO_WEBHOOK_SECRET
}

manager = TelephonyManager(config)

# Send test SMS
await manager.send_sms(
    to="+15551234567",
    body="Hello from Jarvis Phone! 🤖",
    user_id=1
)
```

## 🎯 Testing Voice Calls

Make a test voice call:

```python
# Make test call
await manager.make_call(
    to="+15551234567",
    script="Hello! This is a test call from Jarvis Phone.",
    user_id=1,
    call_type="test"
)
```

## 🔧 Troubleshooting

### Common Issues

1. **"Twilio is not properly configured"**
   - Check your `.env` file has all required variables
   - Verify credentials are correct
   - Ensure no extra spaces in values

2. **"Failed to create Twilio service"**
   - Verify Account SID and Auth Token
   - Check internet connection
   - Ensure Twilio account is active

3. **"SMS failed to send"**
   - Verify phone number format (+1XXXXXXXXXX)
   - Check Twilio account balance
   - Verify phone number has SMS capability

4. **"Call failed to initiate"**
   - Verify phone number has Voice capability
   - Check Twilio account balance
   - Ensure phone number is verified (for trial accounts)

### Debug Mode

Enable debug logging in your `.env`:

```bash
LOG_LEVEL=DEBUG
```

### Check Twilio Console

- Monitor SMS logs: Console → SMS → Logs
- Monitor call logs: Console → Voice → Logs
- Check account status: Console → Dashboard

## 📊 Monitoring and Analytics

### Twilio Console
- Real-time SMS and call logs
- Usage analytics
- Error reports
- Cost tracking

### Jarvis Phone Logs
- Application-level telephony logs
- Webhook processing logs
- Error tracking

## 🔒 Security Best Practices

1. **Never commit credentials to version control**
2. **Use webhook signature validation**
3. **Rotate Auth Token regularly**
4. **Monitor for unusual activity**
5. **Use environment variables for all secrets**

## 💰 Cost Optimization

- **SMS**: $0.0079 per message (US)
- **Voice**: $0.0085 per minute (US)
- **Webhook**: Free
- **Phone Number**: $1/month

### Tips to Reduce Costs
- Use webhooks instead of polling
- Implement rate limiting
- Monitor usage patterns
- Use trial credits for testing

## 🚀 Production Deployment

1. **Update webhook URLs** to your production domain
2. **Set webhook secret** for security
3. **Monitor logs** for errors
4. **Set up alerts** for failures
5. **Test thoroughly** before going live

## 📚 Additional Resources

- [Twilio Python SDK Documentation](https://www.twilio.com/docs/libraries/python)
- [Twilio Webhook Security](https://www.twilio.com/docs/usage/webhooks/webhooks-security)
- [Twilio Best Practices](https://www.twilio.com/docs/usage/best-practices)
- [Jarvis Phone Documentation](./README.md)

## 🆘 Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review Twilio Console logs
3. Check Jarvis Phone application logs
4. Verify environment variables
5. Test with the provided test script

For additional support, check the main project documentation or create an issue in the repository.
