# WebRTC SIP Integration Setup Guide

This guide explains how to set up real telephone calls using SIP integration.

## Overview

The AI Voice Hostess Bot now supports real phone calls via:
- **Twilio** (recommended for quick setup)
- **Vonage (Nexmo)** (alternative cloud provider)
- **Custom SIP Server** (FreeSWITCH/Asterisk for advanced users)

## Quick Start with Twilio

### 1. Create Twilio Account

1. Sign up at [https://www.twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Get a phone number in Console → Phone Numbers
3. Find your credentials in Console → Account → API Keys

### 2. Configure Environment Variables

Add to `.env`:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# Webhook URL (must be publicly accessible)
TWIML_WEBHOOK_URL=https://your-domain.com/api/webrtc-sip/webhooks/twilio/voice
WEBRTC_WS_URL=wss://your-domain.com/api/vocode/ws
```

### 3. Expose Webhooks with ngrok (Development)

For testing, use ngrok to expose your local server:

```bash
# Install ngrok
npm install -g ngrok

# Expose port 8000
ngrok http 8000
```

Use the ngrok URL in your `.env`:
```bash
TWIML_WEBHOOK_URL=https://abc123.ngrok.io/api/webrtc-sip/webhooks/twilio/voice
WEBRTC_WS_URL=wss://abc123.ngrok.io/api/vocode/ws
```

### 4. Configure Twilio Phone Number

1. Go to Console → Phone Numbers → Manage → Active Numbers
2. Click on your phone number
3. Under "Voice & Fax":
   - **A CALL COMES IN**: Webhook → `https://your-domain.com/api/webrtc-sip/webhooks/twilio/voice`
   - **METHOD**: HTTP POST
   - **STATUS CALLBACK URL**: `https://your-domain.com/api/webrtc-sip/webhooks/twilio/status`

### 5. Test Incoming Call

Call your Twilio number from your phone. The AI assistant should answer!

### 6. Make Outbound Call

Use the API:

```bash
curl -X POST http://localhost:8000/api/webrtc-sip/call/outbound \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "+1234567890",
    "provider": "twilio"
  }'
```

---

## Setup with Vonage (Nexmo)

### 1. Create Vonage Account

1. Sign up at [https://dashboard.nexmo.com/sign-up](https://dashboard.nexmo.com/sign-up)
2. Buy a phone number
3. Get your API credentials

### 2. Configure Environment Variables

```bash
# Vonage Configuration
VONAGE_API_KEY=your_api_key
VONAGE_API_SECRET=your_api_secret
VONAGE_WEBHOOK_URL=https://your-domain.com/api/webrtc-sip/webhooks/vonage/answer
```

### 3. Configure Webhook URLs

In Vonage Dashboard → Your Numbers → Edit:
- **Answer URL**: `https://your-domain.com/api/webrtc-sip/webhooks/vonage/answer`
- **Event URL**: `https://your-domain.com/api/webrtc-sip/webhooks/vonage/events`

---

## Custom SIP Server Setup (Advanced)

For full control, you can deploy your own SIP server.

### Option 1: FreeSWITCH

```bash
# Install FreeSWITCH (Ubuntu)
wget -O - https://files.freeswitch.org/repo/deb/debian-release/fsstretch-archive-keyring.asc | apt-key add -
echo "deb http://files.freeswitch.org/repo/deb/debian-release/ stretch main" > /etc/apt/sources.list.d/freeswitch.list
apt-get update
apt-get install -y freeswitch-meta-all
```

Configure in `.env`:
```bash
SIP_SERVER_URL=sip:your-freeswitch-server.com
SIP_USERNAME=your_username
SIP_PASSWORD=your_password
```

### Option 2: Asterisk

```bash
# Install Asterisk (Ubuntu)
apt-get install -y asterisk
```

Configure Asterisk REST Interface (ARI) and update `.env`.

---

## Testing

### Check Provider Status

```bash
curl http://localhost:8000/api/webrtc-sip/providers
```

Response:
```json
{
  "twilio": {
    "configured": true,
    "phone_number": "+1234567890"
  },
  "vonage": {
    "configured": false
  },
  "custom_sip": {
    "configured": false,
    "server": null
  }
}
```

### Check Call Status

```bash
curl http://localhost:8000/api/webrtc-sip/call/status/CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?provider=twilio
```

### End Call

```bash
curl -X POST http://localhost:8000/api/webrtc-sip/call/end/CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?provider=twilio
```

---

## Production Deployment

### Requirements

1. **Public HTTPS endpoint** for webhooks
2. **SSL certificates** (Let's Encrypt)
3. **STUN/TURN servers** for NAT traversal
4. **Load balancing** for high availability
5. **Monitoring** (call quality, latency)

### Recommended Stack

```
┌─────────────────┐
│   Phone Network │
└────────┬────────┘
         │ SIP
┌────────▼────────┐
│  Twilio/Vonage  │ (or your SIP server)
└────────┬────────┘
         │ WebRTC
┌────────▼────────┐
│  NGINX (SSL)    │
└────────┬────────┘
         │ HTTPS/WSS
┌────────▼────────┐
│  FastAPI App    │ (AI Hostess Bot)
└────────┬────────┘
         │
┌────────▼────────┐
│  PostgreSQL     │
│  Redis          │
│  ChromaDB       │
└─────────────────┘
```

### SSL Configuration (nginx)

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # WebSocket for Vocode
    location /api/vocode/ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # REST API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Troubleshooting

### Call doesn't connect

1. Check webhook URLs are publicly accessible
2. Verify SSL certificates are valid
3. Check logs: `docker-compose logs -f backend`
4. Test webhook manually with curl

### No audio

1. Verify sample rate (16kHz)
2. Check audio codec (LINEAR16)
3. Ensure TURN server is configured for NAT
4. Check firewall rules for WebRTC ports

### High latency

1. Use streaming TTS (enabled by default)
2. Deploy closer to users (regional servers)
3. Optimize LLM response time
4. Use CDN for audio delivery

---

## Cost Optimization

### Twilio Pricing
- Incoming calls: ~$0.0085/min
- Outgoing calls: ~$0.013/min
- Phone number: $1/month

### Tips
1. Use voice activity detection (VAD) to reduce transcription
2. Cache LLM responses for common queries
3. Implement call time limits
4. Monitor usage with rate limiting

---

## Security Best Practices

1. **Validate webhooks** - Verify Twilio/Vonage signatures
2. **Rate limiting** - Already implemented ✅
3. **Input validation** - Sanitize all phone numbers
4. **Secrets management** - Use environment variables, never commit
5. **Logging** - Monitor for suspicious activity
6. **Authentication** - Require auth for outbound calls

---

## Support

For issues or questions:
- Check logs: `docker-compose logs -f backend`
- Twilio docs: https://www.twilio.com/docs/voice
- Vonage docs: https://developer.vonage.com/voice
- GitHub Issues: https://github.com/your-repo/issues
