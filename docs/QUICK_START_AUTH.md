# Quick Start - Authentication Setup

**5-Minute Guide to Get Authentication Running**

## 1. Update Environment (30 seconds)

```bash
# Update .env file with OAuth URLs
OAUTH_REDIRECT_URL=http://localhost:3000/auth/callback
SITE_URL=http://localhost:3000
```

## 2. Configure Supabase Email (2 minutes)

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. **Authentication** → **Providers** → **Email**
3. ✅ Enable "Confirm email"
4. **Save**

5. **Authentication** → **Email Templates** → **Confirm signup**
6. Replace content with:
```html
<h2>Welcome to CuiStudio!</h2>
<p>Please confirm your email:</p>
<p><a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email">Confirm Email</a></p>
```

7. **Authentication** → **URL Configuration**
8. Set **Site URL**: `http://localhost:3000`
9. Add **Redirect URLs**: `http://localhost:3000/*`

## 3. Test Email Auth (1 minute)

```bash
# Start server
python main.py

# Open browser
open http://localhost:8000/api/docs

# Test signup endpoint:
POST /auth/signup
{
  "email": "test@example.com",
  "password": "test123"
}

# Check your email for confirmation link
```

## 4. Optional: Phone Auth Setup

### Prerequisites
- Twilio account with phone number

### Configuration (2 minutes)
1. **Authentication** → **Providers** → **Phone**
2. Enable, select **Twilio**
3. Add credentials:
   - Account SID
   - Auth Token
   - Phone Number
4. **Save**

### Test
```bash
POST /auth/signup-phone
{
  "phone": "+1234567890"
}

# You should receive SMS with OTP
```

## 5. Optional: Google OAuth Setup

### Prerequisites
- Google Cloud Console account

### Quick Setup (3 minutes)
1. [Google Cloud Console](https://console.cloud.google.com)
2. **APIs & Services** → **Credentials** → **Create OAuth Client ID**
3. Authorized redirect: `https://<your-project>.supabase.co/auth/v1/callback`
4. Copy **Client ID** and **Secret**

5. In Supabase:
   - **Authentication** → **Providers** → **Google**
   - Enable, add credentials
   - **Save**

### Test
```bash
GET /auth/oauth/google
# Returns: {"url": "https://accounts.google.com/..."}
# Visit URL to test OAuth flow
```

---

## Quick Test Commands

### Email Auth
```bash
# Signup
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Login (after email verification)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Phone Auth
```bash
# Signup
curl -X POST http://localhost:8000/api/v1/auth/signup-phone \
  -H "Content-Type: application/json" \
  -d '{"phone":"+1234567890"}'

# Verify OTP
curl -X POST http://localhost:8000/api/v1/auth/verify-phone-otp \
  -H "Content-Type: application/json" \
  -d '{"phone":"+1234567890","token":"123456"}'
```

### OAuth
```bash
# Get Google OAuth URL
curl http://localhost:8000/api/v1/auth/oauth/google
```

---

## Troubleshooting

**Email not sending?**
- Check spam folder
- Verify email template saved in Supabase
- Check Supabase email logs

**Phone OTP not received?**
- Verify Twilio credentials
- Check Twilio account credits
- Ensure phone format: +1234567890

**OAuth not working?**
- Verify redirect URL matches exactly
- Check OAuth credentials in Supabase
- Clear browser cache

---

## Full Documentation

For complete details, see:
- **[AUTHENTICATION.md](./AUTHENTICATION.md)** - API reference
- **[SUPABASE_SETUP.md](./SUPABASE_SETUP.md)** - Detailed setup
- **[AUTH_IMPLEMENTATION_SUMMARY.md](./AUTH_IMPLEMENTATION_SUMMARY.md)** - Implementation details

---

**Estimated Setup Time:**
- Email only: 3 minutes
- Email + Phone: 5 minutes
- Email + Phone + OAuth: 10 minutes

**Status:** ✅ All authentication methods implemented and ready to use!
