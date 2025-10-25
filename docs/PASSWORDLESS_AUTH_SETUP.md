# Passwordless Authentication Setup Guide

Complete guide for setting up passwordless authentication (Email Magic Link + Phone OTP) with Supabase.

---

## Overview

The authentication system now uses **fully passwordless authentication** with two methods:

1. **Email Magic Link** - One-time use links sent to user's email
2. **Phone OTP** - 6-digit codes sent via SMS

Both methods automatically handle user registration and login in a unified flow.

---

## API Endpoints

### Email Magic Link Authentication

#### 1. Request Magic Link
```http
POST /api/v1/auth/email
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "Check your email! We've sent you a magic link to sign in."
}
```

#### 2. Verify Magic Link (PKCE Flow)
```http
POST /api/v1/auth/email/verify
Content-Type: application/json

{
  "token_hash": "<token_from_email_link>",
  "type": "email"
}
```

**Response:**
```json
{
  "access_token": "<JWT_TOKEN>",
  "refresh_token": "<REFRESH_TOKEN>",
  "token_type": "bearer",
  "expires_in": 3600,
  "expires_at": 1234567890,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "phone": null,
    "created_at": "2024-01-01T00:00:00Z",
    "user_metadata": {},
    "is_new_user": true
  }
}
```

### Phone OTP Authentication

#### 1. Request OTP
```http
POST /api/v1/auth/phone
Content-Type: application/json

{
  "phone": "+13334445555"
}
```

**Response:**
```json
{
  "message": "OTP sent to your phone number. Please verify to continue."
}
```

#### 2. Verify OTP
```http
POST /api/v1/auth/phone/verify
Content-Type: application/json

{
  "phone": "+13334445555",
  "token": "123456"
}
```

**Response:** Same as email verify response above.

### Profile Completion (New Users)

When `is_new_user` is `true` in the auth response, the user must complete their profile:

```http
POST /api/v1/auth/profile/complete
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "John Doe",
  "username": "johndoe",
  "date_of_birth": "1990-01-01",
  "bio": "Optional bio text"
}
```

### Other Endpoints

- `GET /api/v1/auth/me` - Get current user info
- `PATCH /api/v1/auth/profile` - Update profile
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout

---

## Supabase Configuration

### 1. Enable Email Magic Link

1. Go to **Supabase Dashboard** → **Authentication** → **Providers**
2. Enable **Email** provider
3. Navigate to **Authentication** → **Email Templates**
4. Edit the **Magic Link** template:

```html
<h2>Magic Link</h2>
<p>Follow this link to login:</p>
<p><a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email">Log In</a></p>
```

**Important:** Use `{{ .TokenHash }}` for PKCE flow (recommended for security).

### 2. Configure URL Settings

1. Navigate to **Authentication** → **URL Configuration**
2. Set **Site URL**: `http://localhost:3000` (or your production URL)
3. Add **Redirect URLs**:
   ```
   http://localhost:3000/*
   http://localhost:3000/auth/callback
   http://localhost:3000/auth/confirm
   ```

### 3. Enable Phone OTP

#### Choose an SMS Provider

Supabase supports multiple SMS providers:
- **Twilio** (recommended, most widely used)
- **MessageBird**
- **Vonage**
- **Textlocal** (community-supported)

#### Configure Twilio (Recommended)

1. **Create Twilio Account:**
   - Sign up at [twilio.com](https://www.twilio.com)
   - Purchase a phone number
   - Get your Account SID and Auth Token

2. **Configure in Supabase:**
   - Go to **Authentication** → **Providers**
   - Enable **Phone** provider
   - Select **Twilio** as SMS provider
   - Enter credentials:
     ```
     Account SID: AC********************************
     Auth Token: ********************************
     Twilio Phone Number: +1234567890
     ```

3. **Customize SMS Template (Optional):**
   ```
   Your CuiStudio verification code is: {{ .Code }}
   ```

4. Click **Save**

### 4. Rate Limits Configuration

1. Navigate to **Authentication** → **Rate Limits**
2. Configure limits to prevent abuse:

   **Email:**
   - Email sent per hour: `10`
   - Email OTP expiry: `3600` seconds (1 hour)

   **SMS:**
   - SMS sent per hour: `5`
   - SMS OTP expiry: `60` seconds

   **Sign-ups:**
   - Per hour: `50`

3. Click **Save**

### 5. Disable Password Authentication (Optional)

If you want to enforce passwordless only:
1. Go to **Authentication** → **Providers**
2. Disable **Email (Password)** authentication
3. Keep only **Email (OTP)** and **Phone** enabled

---

## Database Schema (Optional)

If you want to store user profiles in a separate table:

```sql
-- Create users table
CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  date_of_birth DATE NOT NULL,
  bio TEXT,
  email TEXT,
  phone TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can read all profiles
CREATE POLICY "Users can view all profiles"
  ON users FOR SELECT
  USING (true);

-- Users can only update their own profile
CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  USING (auth.uid() = id);

-- Users can insert their own profile
CREATE POLICY "Users can insert own profile"
  ON users FOR INSERT
  WITH CHECK (auth.uid() = id);

-- Create username index for fast lookups
CREATE INDEX users_username_idx ON users(username);

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
```

---

## Frontend Integration Guide

### 1. Email Magic Link Flow

```typescript
// Step 1: Request magic link
async function loginWithEmail(email: string) {
  const response = await fetch('/api/v1/auth/email', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });

  const data = await response.json();
  // Show message: "Check your email!"
}

// Step 2: Handle callback from email link
// User clicks link in email → redirected to /auth/confirm?token_hash=xxx&type=email
async function handleMagicLinkCallback() {
  const params = new URLSearchParams(window.location.search);
  const tokenHash = params.get('token_hash');
  const type = params.get('type');

  if (!tokenHash || !type) return;

  const response = await fetch('/api/v1/auth/email/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token_hash: tokenHash, type })
  });

  const data = await response.json();

  // Save tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  // Check if new user
  if (data.user.is_new_user) {
    // Redirect to profile completion
    router.push('/onboarding/complete-profile');
  } else {
    // Redirect to dashboard
    router.push('/dashboard');
  }
}
```

### 2. Phone OTP Flow

```typescript
// Step 1: Request OTP
async function loginWithPhone(phone: string) {
  const response = await fetch('/api/v1/auth/phone', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone })
  });

  // Show OTP input form
}

// Step 2: Verify OTP
async function verifyPhoneOTP(phone: string, token: string) {
  const response = await fetch('/api/v1/auth/phone/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, token })
  });

  const data = await response.json();

  // Save tokens
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);

  // Check if new user
  if (data.user.is_new_user) {
    router.push('/onboarding/complete-profile');
  } else {
    router.push('/dashboard');
  }
}
```

### 3. Profile Completion Flow

```typescript
async function completeProfile(profileData: {
  name: string;
  username: string;
  date_of_birth: string; // YYYY-MM-DD
  bio?: string;
}) {
  const accessToken = localStorage.getItem('access_token');

  const response = await fetch('/api/v1/auth/profile/complete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify(profileData)
  });

  if (response.ok) {
    router.push('/dashboard');
  } else {
    const error = await response.json();
    // Handle error (e.g., username taken)
  }
}
```

### 4. Using Access Token

```typescript
async function makeAuthenticatedRequest(endpoint: string) {
  const accessToken = localStorage.getItem('access_token');

  const response = await fetch(endpoint, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  if (response.status === 401) {
    // Token expired, refresh it
    await refreshAccessToken();
    // Retry request
  }

  return response.json();
}

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token');

  const response = await fetch('/api/v1/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
}
```

---

## Testing Checklist

### Email Magic Link
- [ ] Request magic link for new email
- [ ] Receive email with magic link
- [ ] Click link and verify redirect works
- [ ] Check `is_new_user` is `true` for new users
- [ ] Complete profile for new users
- [ ] Request magic link for existing user
- [ ] Check `is_new_user` is `false` for existing users
- [ ] Verify link expires after 1 hour
- [ ] Verify link is one-time use only

### Phone OTP
- [ ] Request OTP for new phone number
- [ ] Receive SMS with 6-digit code
- [ ] Verify OTP within 60 seconds
- [ ] Check `is_new_user` is `true` for new users
- [ ] Complete profile for new users
- [ ] Request OTP for existing user
- [ ] Check `is_new_user` is `false` for existing users
- [ ] Verify OTP expires after 60 seconds
- [ ] Test invalid OTP code
- [ ] Test rate limiting (max 5 SMS per hour)

### Profile Management
- [ ] Complete profile with valid data
- [ ] Test username uniqueness validation
- [ ] Update profile for existing user
- [ ] Verify profile data in user metadata
- [ ] Verify profile data in users table (if exists)

### Session Management
- [ ] Get current user info
- [ ] Refresh access token
- [ ] Logout user
- [ ] Verify token expiration (1 hour)

---

## Security Best Practices

1. **Rate Limiting:**
   - Configure appropriate rate limits in Supabase
   - Implement CAPTCHA for production (see Supabase docs)
   - Monitor for abuse patterns

2. **Token Management:**
   - Store tokens securely (httpOnly cookies recommended for web)
   - Implement token refresh flow
   - Clear tokens on logout

3. **Phone Numbers:**
   - Validate E.164 format: `+[country_code][number]`
   - Follow country-specific regulations (e.g., India's TRAI DLT)
   - Keep Twilio costs under control with rate limits

4. **Email Security:**
   - Use PKCE flow (token_hash) instead of implicit flow
   - Configure proper redirect URLs
   - Verify email domains if needed

5. **User Privacy:**
   - Don't expose if email/phone exists (generic messages)
   - Implement proper error handling
   - Log authentication attempts for monitoring

---

## Troubleshooting

### Magic Link Not Received
- Check spam/junk folder
- Verify email provider settings in Supabase
- Check Supabase logs for email delivery status
- Verify email template is configured correctly

### SMS Not Received
- Verify Twilio account has credits
- Check phone number format (E.164: +1234567890)
- Review Twilio logs for delivery issues
- Ensure Twilio account is not in trial mode restrictions
- Check if phone number is verified in Twilio

### Token Expired Errors
- Access tokens expire after 1 hour by default
- Implement refresh token flow
- Check system clock is synchronized

### Redirect Not Working
- Verify redirect URL is whitelisted in Supabase
- Check Site URL configuration
- Ensure protocol (http/https) matches
- Clear browser cache and cookies

### Username Already Taken
- Usernames must be unique
- Check if user already has a profile
- Implement username availability check in frontend

---

## Production Deployment

### Environment Variables

Update `.env` for production:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_publishable_key
SUPABASE_SECRET_KEY=your_secret_key

# Auth Redirects
SITE_URL=https://yourdomain.com
OAUTH_REDIRECT_URL=https://yourdomain.com/auth/callback

# CORS
CORS_ORIGINS=https://yourdomain.com

# Application
APP_ENV=production
DEBUG=false
```

### Supabase Dashboard

1. Update **Site URL** to production domain
2. Add production **Redirect URLs**
3. Update **Email Templates** with production URLs
4. Review and adjust **Rate Limits**
5. Enable **Row Level Security (RLS)** on all tables
6. Set up **Database Backups**
7. Monitor **Authentication Logs**

### SMS Provider

- Ensure Twilio account is upgraded (not trial mode)
- Add sufficient credits
- Configure production phone number
- Test SMS delivery in production environment

---

## Support Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Magic Link Guide](https://supabase.com/docs/guides/auth/auth-magic-link)
- [Phone Auth Guide](https://supabase.com/docs/guides/auth/phone-login)
- [Twilio Documentation](https://www.twilio.com/docs)

---

## Migration from Password-Based Auth

If you're migrating from password-based authentication:

1. **Keep old endpoints temporarily** (for backward compatibility)
2. **Notify users** about the new passwordless system
3. **Provide migration path:**
   - Allow users to link their email/phone to existing account
   - Send magic link/OTP to verify ownership
   - Migrate user data to new system
4. **Deprecate password endpoints** after migration period
5. **Disable password auth** in Supabase dashboard

---

Last updated: 2024
