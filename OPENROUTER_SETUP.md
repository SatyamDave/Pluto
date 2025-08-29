# OpenRouter Integration Setup Guide

## Overview

OpenRouter provides unified access to hundreds of AI models through a single endpoint, with automatic fallbacks and cost optimization. This integration makes Jarvis Phone more reliable and cost-effective by automatically switching between different AI providers based on availability and cost.

## Features

- **Unified AI Access**: Single API key for multiple AI providers
- **Automatic Fallbacks**: Seamlessly switches between models if one fails
- **Cost Optimization**: Automatically selects cost-effective models
- **Provider Diversity**: Access to OpenAI, Anthropic, Google, Meta, and more
- **Real-time Monitoring**: Track usage, costs, and model performance
- **Health Checks**: Automatic monitoring of AI service availability

## Setup Steps

### 1. Get OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai)
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key (starts with `sk-or-`)

### 2. Configure Environment Variables

Add the following to your `.env` file:

```bash
# OpenRouter Configuration (Primary AI provider)
OPENROUTER_API_KEY=sk-or-your-api-key-here
OPENROUTER_PREFERRED_MODEL=openai/gpt-4o
OPENROUTER_FALLBACK_ENABLED=True
OPENROUTER_COST_OPTIMIZATION=True
```

### 3. Model Preferences

The system automatically tries models in this order for optimal performance and cost:

1. **openai/gpt-4o** - Best performance, higher cost
2. **openai/gpt-4o-mini** - Good performance, moderate cost  
3. **anthropic/claude-3-5-sonnet-20241022** - Alternative provider
4. **anthropic/claude-3-haiku-20240307** - Fast, cost-effective
5. **meta-llama/llama-3-1-8b-instruct** - Local fallback option
6. **google/gemini-pro-1.5** - Google's offering

### 4. Fallback Configuration

If OpenRouter is unavailable, the system automatically falls back to:
- OpenAI (if configured)
- Anthropic (if configured)
- Simple keyword-based analysis

## API Endpoints

### Health Check
```bash
GET /api/v1/ai/health
```
Check the health of all AI services.

### Available Models
```bash
GET /api/v1/ai/models
```
Get list of available AI models from OpenRouter.

### Usage Statistics
```bash
GET /api/v1/ai/usage
```
Get current AI usage statistics and cost tracking.

### Test AI Completion
```bash
POST /api/v1/ai/test
```
Test AI completion with a simple message.

### Model Information
```bash
GET /api/v1/ai/models/{model_id}
```
Get detailed information about a specific model.

### Credits
```bash
GET /api/v1/ai/credits
```
Get current credit balance and usage from OpenRouter.

## Usage Examples

### Basic Chat Completion

```python
from services.openrouter_service import OpenRouterService

# Initialize service
service = OpenRouterService()

# Send message
response = await service.chat_completion(
    messages=[
        {"role": "user", "content": "What's the weather like?"}
    ],
    temperature=0.3,
    max_tokens=100
)

print(response["content"])
```

### Intent Analysis

```python
from services.openrouter_service import analyze_intent_with_openrouter

# Analyze user intent
intent = await analyze_intent_with_openrouter(
    "Wake me up at 7 AM tomorrow"
)

print(f"Intent: {intent['intent']}")
print(f"Confidence: {intent['confidence']}")
```

### Time Extraction

```python
from services.openrouter_service import extract_time_info_with_openrouter

# Extract time information
time_info = await extract_time_info_with_openrouter(
    "Remind me in 2 hours"
)

print(f"Time: {time_info['readable_time']}")
print(f"Type: {time_info['type']}")
```

## Cost Optimization

### Automatic Model Selection

The system automatically selects models based on:
- **Performance requirements**: Use GPT-4o for complex tasks
- **Cost constraints**: Use GPT-4o-mini for routine tasks
- **Speed requirements**: Use Claude Haiku for fast responses
- **Provider availability**: Switch if one provider is down

### Usage Monitoring

Track costs and usage through:
- Real-time usage statistics
- Model-specific performance metrics
- Cost per request tracking
- Automatic cost alerts

## Troubleshooting

### Common Issues

1. **API Key Invalid**
   - Verify your OpenRouter API key is correct
   - Check if the key has sufficient credits
   - Ensure the key is active and not expired

2. **Model Unavailable**
   - The system automatically falls back to alternative models
   - Check the health endpoint for model status
   - Verify your OpenRouter account has access to the requested models

3. **Rate Limiting**
   - OpenRouter has rate limits based on your plan
   - Implement exponential backoff in your requests
   - Monitor usage through the credits endpoint

4. **Fallback Failures**
   - Ensure fallback providers (OpenAI/Anthropic) are configured
   - Check network connectivity to all AI services
   - Review logs for specific error messages

### Debug Mode

Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
```

### Health Checks

Regular health checks are available at:
```bash
GET /api/v1/ai/health
```

## Best Practices

### 1. Model Selection
- Use specific models for critical tasks
- Let the system auto-select for routine operations
- Monitor performance and adjust preferences

### 2. Error Handling
- Always implement fallback logic
- Log AI service failures for monitoring
- Use health checks before critical operations

### 3. Cost Management
- Set up usage alerts
- Monitor cost per request
- Use cost-effective models for high-volume tasks

### 4. Performance
- Cache responses when appropriate
- Use streaming for long responses
- Implement request batching for multiple queries

## Security Considerations

- **API Key Protection**: Never expose API keys in client-side code
- **Rate Limiting**: Implement proper rate limiting to prevent abuse
- **Input Validation**: Validate all user inputs before sending to AI services
- **Response Sanitization**: Sanitize AI responses before displaying to users
- **Audit Logging**: Log all AI interactions for security monitoring

## Monitoring and Analytics

### Metrics to Track
- Request success/failure rates
- Response times by model
- Cost per request
- Model usage distribution
- Fallback frequency

### Alerts
- Service unavailability
- High error rates
- Cost threshold exceeded
- Model performance degradation

## Support

For OpenRouter-specific issues:
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Discord](https://discord.gg/openrouter)
- [OpenRouter Status Page](https://status.openrouter.ai)

For Jarvis Phone integration issues:
- Check the application logs
- Review the health endpoints
- Verify configuration settings
- Test with the `/api/v1/ai/test` endpoint

## Migration from Direct Providers

If you're migrating from direct OpenAI/Anthropic usage:

1. **Keep existing keys** as fallbacks
2. **Test OpenRouter** with non-critical operations first
3. **Monitor performance** and adjust model preferences
4. **Gradually increase** OpenRouter usage
5. **Remove direct provider keys** once confident

## Performance Benchmarks

Typical response times by model:
- **GPT-4o**: 2-5 seconds
- **GPT-4o-mini**: 1-3 seconds  
- **Claude 3.5 Sonnet**: 2-4 seconds
- **Claude 3 Haiku**: 0.5-2 seconds
- **Llama 3.1**: 1-3 seconds

Cost comparison (approximate per 1K tokens):
- **GPT-4o**: $0.01-0.03
- **GPT-4o-mini**: $0.00015-0.0006
- **Claude 3.5 Sonnet**: $0.003-0.015
- **Claude 3 Haiku**: $0.00025-0.00125
- **Llama 3.1**: $0.0002-0.0008
