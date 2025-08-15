# Email Alerts Setup Guide for DigitalOcean

## The Problem
DigitalOcean blocks SMTP ports (25, 465, 587) for new accounts to prevent spam. This means Gmail SMTP won't work directly from your droplet.

## The Solution
Use SendGrid, which DigitalOcean recommends and has partnered with. SendGrid uses HTTP API instead of SMTP ports.

## Setup Steps

### 1. Create SendGrid Account

**Option A: Direct SignUp**
- Go to https://sendgrid.com/
- Sign up for free account (100 emails/day limit)

**Option B: DigitalOcean Marketplace (Recommended)**
- In your DigitalOcean dashboard, go to Marketplace
- Search for "SendGrid Email API"
- This may provide better integration and billing

### 2. Get SendGrid API Key

1. Login to SendGrid dashboard
2. Go to **Settings** → **API Keys**
3. Click **Create API Key**
4. Choose **Full Access** or create restricted key with **Mail Send** permissions
5. **IMPORTANT**: Copy the API key immediately (you won't see it again!)

### 3. Configure Domain Authentication (Recommended)

1. Go to **Settings** → **Sender Authentication**
2. **Authenticate Your Domain** or **Single Sender Verification**
3. Follow the DNS setup instructions
4. This greatly improves email deliverability

### 4. Install and Configure on Your Server

```bash
# SSH to your droplet
ssh root@your-droplet-ip

# Navigate to project
cd /root/trading_analysis/email_alerts

# Install SendGrid library
source /root/trading_venv/bin/activate
pip install sendgrid

# Run setup script
python setup_sendgrid.py
```

### 5. Configuration File

Your `.env` file should contain:
```
# Gmail credentials (backup method)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# SendGrid credentials (primary method)
SENDGRID_API_KEY=SG.your-api-key-here
FROM_EMAIL=your-verified-email@yourdomain.com
```

### 6. Test the System

```bash
# Test SendGrid specifically
python setup_sendgrid.py
# Choose option 3: Test SendGrid configuration

# Test hybrid email service
python test_hybrid_email.py

# Test full trading alerts
python hourly_trading_alerts.py --test
```

## Email Method Priority

The hybrid email service tries methods in this order:

1. **SendGrid API** (recommended for DigitalOcean)
   - Uses HTTP API, bypasses SMTP port blocks
   - Most reliable for droplets
   - Better deliverability with domain authentication

2. **Gmail SMTP** (fallback for local development)
   - Will work on local machines
   - Blocked on most VPS providers

3. **System sendmail** (last resort)
   - Uses local mail server
   - Requires proper mail server setup
   - May end up in spam folders

## Troubleshooting

### SendGrid API Key Issues
- Make sure you copied the full API key
- Check that key has Mail Send permissions
- Verify FROM_EMAIL is authenticated in SendGrid

### Email Deliverability
- Authenticate your domain in SendGrid
- Use a professional email address as FROM_EMAIL
- Avoid spammy subject lines
- Don't send too frequently (respect rate limits)

### Testing Connection
```bash
# Test SendGrid API directly
curl -i --request POST \
--url https://api.sendgrid.com/v3/mail/send \
--header "authorization: Bearer YOUR_API_KEY" \
--header "content-type: application/json" \
--data '{
  "personalizations": [{"to": [{"email": "test@example.com"}]}],
  "from": {"email": "your-email@yourdomain.com"},
  "subject": "Test",
  "content": [{"type": "text/plain", "value": "Test email"}]
}'
```

## Rate Limits

**SendGrid Free Tier:**
- 100 emails/day
- 40,000 emails first month

**For Higher Volume:**
- Upgrade to paid SendGrid plan
- Consider multiple email services
- Implement email throttling in the system

## Security Notes

- Keep your SendGrid API key secure
- Use environment variables, never hardcode keys
- Consider using restricted API keys with minimal permissions
- Regularly rotate API keys

## Alternative Services

If SendGrid doesn't work for you:

1. **Mailgun** - Similar API-based service
2. **Amazon SES** - If you're comfortable with AWS
3. **Postmark** - Good for transactional emails
4. **Local mail server** - More complex but full control

All of these use HTTP APIs instead of SMTP ports.
