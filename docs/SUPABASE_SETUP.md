# Supabase Dashboard Setup Guide

Step-by-step guide to configure Supabase for authentication.

## Prerequisites

- Supabase project created
- Project URL and keys added to `.env` file

---

## 1. Email Authentication Setup

### Enable Email Provider

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Authentication** → **Providers**
4. Find **Email** section
5. Enable the following:
   - ✅ **Enable email provider**
   - ✅ **Confirm email** (users must verify email before login)
6. Click **Save**

### Configure Email Templates

1. Navigate to **Authentication** → **Email Templates**
2. Select **Confirm signup** template
3. Edit the template to include your branding:

```html
<h2>Welcome to CuiStudio Recipe App!</h2>

<p>Please confirm your email address to get started.</p>

<p>
  <a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=email&next=/dashboard">
    Confirm your email
  </a>
</p>

<p>If you didn't create an account, you can safely ignore this email.</p>
```

4. Customize other templates as needed:
   - Magic Link
   - Change Email Address
   - Reset Password

---

## 2. Phone Authentication Setup (Twilio)

### Prerequisites
- Twilio account (sign up at [twilio.com](https://www.twilio.com))
- Twilio phone number purchased
- Account SID and Auth Token

### Configure Twilio in Supabase

1. Navigate to **Authentication** → **Providers**
2. Find **Phone** section
3. Enable **Phone provider**
4. Select **Twilio** as SMS provider
5. Enter your Twilio credentials:
   ```
   Account SID: AC********************************
   Auth Token: ********************************
   Twilio Phone Number: +1234567890
   ```
6. **Optional**: Configure SMS template:
   ```
   Your CuiStudio verification code is: {{ .Code }}
   ```
7. Click **Save**

### Test Phone Authentication

1. Use the Swagger docs at `http://localhost:8000/api/docs`
2. Try the `/auth/signup-phone` endpoint with your phone number
3. You should receive an SMS with OTP code

---

## 3. Google OAuth Setup

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing one
3. Navigate to **APIs & Services** → **Credentials**
4. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
5. If prompted, configure OAuth consent screen:
   - User Type: **External**
   - App name: **CuiStudio Recipe App**
   - User support email: Your email
   - Developer contact: Your email
   - Save and continue through all steps
6. Create OAuth client ID:
   - Application type: **Web application**
   - Name: **CuiStudio Recipe App**
   - Authorized redirect URIs:
     ```
     https://<your-project-ref>.supabase.co/auth/v1/callback
     ```
   - Click **Create**
7. Copy the **Client ID** and **Client Secret**

### Step 2: Configure Google in Supabase

1. In Supabase Dashboard, navigate to **Authentication** → **Providers**
2. Find **Google** section
3. Enable **Google enabled**
4. Enter credentials:
   ```
   Client ID: <your-client-id>.apps.googleusercontent.com
   Client Secret: <your-client-secret>
   ```
5. Click **Save**

### Step 3: Test Google OAuth

1. Call `GET http://localhost:8000/api/v1/auth/oauth/google`
2. You'll receive an OAuth URL
3. Visit that URL in browser
4. You should see Google sign-in screen

---

## 4. Apple OAuth Setup

### Step 1: Create Apple Sign In Credentials

**Prerequisites:**
- Apple Developer account ($99/year)
- Enrolled in Apple Developer Program

**Steps:**

1. Go to [Apple Developer](https://developer.apple.com/account)
2. Navigate to **Certificates, Identifiers & Profiles**

3. **Create an App ID:**
   - Click **Identifiers** → **+**
   - Select **App IDs** → Continue
   - Description: **CuiStudio Recipe App**
   - Bundle ID: `com.cuistudio.recipeapp`
   - Enable **Sign in with Apple**
   - Click **Continue** → **Register**

4. **Create a Services ID:**
   - Click **Identifiers** → **+**
   - Select **Services IDs** → Continue
   - Description: **CuiStudio Recipe App Web**
   - Identifier: `com.cuistudio.recipeapp.web`
   - Enable **Sign in with Apple**
   - Click **Configure**:
     - Primary App ID: Select your App ID from step 3
     - Domains and Subdomains: `<your-project-ref>.supabase.co`
     - Return URLs: `https://<your-project-ref>.supabase.co/auth/v1/callback`
   - Click **Continue** → **Register**

5. **Create a Key:**
   - Click **Keys** → **+**
   - Key Name: **CuiStudio Apple Sign In Key**
   - Enable **Sign in with Apple**
   - Click **Configure** → Select your Primary App ID
   - Click **Continue** → **Register**
   - **Download the .p8 key file** (you can only download once!)
   - Note the **Key ID** shown

6. **Get Team ID:**
   - Go to **Membership** section
   - Copy your **Team ID**

### Step 2: Configure Apple in Supabase

1. In Supabase Dashboard, navigate to **Authentication** → **Providers**
2. Find **Apple** section
3. Enable **Apple enabled**
4. Enter credentials:
   ```
   Services ID: com.cuistudio.recipeapp.web
   Team ID: <your-team-id>
   Key ID: <your-key-id>
   ```
5. Upload the **.p8 private key file**
6. Click **Save**

### Step 3: Test Apple OAuth

1. Call `GET http://localhost:8000/api/v1/auth/oauth/apple`
2. You'll receive an OAuth URL
3. Visit that URL in browser
4. You should see Apple Sign In screen

---

## 5. URL Configuration

### Configure Redirect URLs

1. Navigate to **Authentication** → **URL Configuration**
2. Set **Site URL**:
   ```
   http://localhost:3000
   ```
   _(Change to your production URL when deploying)_

3. Add **Redirect URLs**:
   ```
   http://localhost:3000/*
   http://localhost:3000/auth/callback
   http://localhost:3000/auth/verify-email
   http://localhost:3000/dashboard
   ```

4. For production, add:
   ```
   https://yourdomain.com/*
   https://yourdomain.com/auth/callback
   ```

5. Click **Save**

---

## 6. Rate Limits Configuration

### Adjust Rate Limits

1. Navigate to **Authentication** → **Rate Limits**
2. Configure limits:

   **Email:**
   - Email sent per hour: `10`
   - Email OTP expiry: `3600` seconds (1 hour)

   **SMS:**
   - SMS sent per hour: `5`
   - SMS OTP expiry: `60` seconds

   **Sign-ups:**
   - Per hour: `50`

3. Click **Save**

**Note:** Adjust these based on your app's needs and to prevent abuse.

---

## 7. Security Settings

### Enable Additional Security Features

1. Navigate to **Authentication** → **Policies**
2. Consider enabling:
   - **Email rate limiting**: Prevents spam signups
   - **Password strength**: Require minimum password strength
   - **Session timeout**: Configure session duration

3. Navigate to **Authentication** → **Providers** → **Email**
4. Optional settings:
   - **Secure email change**: Require confirmation from both old and new email
   - **Double confirm email change**: Extra security for email changes

---

## 8. Testing Your Setup

### Test Checklist

- [ ] Email signup works and sends confirmation email
- [ ] Email verification link works
- [ ] Email login works after verification
- [ ] Phone signup sends SMS
- [ ] Phone OTP verification works
- [ ] Phone login works
- [ ] Google OAuth redirects correctly
- [ ] Google OAuth callback completes authentication
- [ ] Apple OAuth redirects correctly (if configured)
- [ ] Apple OAuth callback completes authentication (if configured)
- [ ] Password reset email works
- [ ] Refresh token works
- [ ] Logout works

### Test with API Documentation

1. Start your server: `python main.py`
2. Open Swagger docs: `http://localhost:8000/api/docs`
3. Test each endpoint manually
4. Check responses and error handling

### Monitor Logs

1. Navigate to **Authentication** → **Logs** in Supabase Dashboard
2. Monitor authentication events
3. Check for errors or suspicious activity

---

## 9. Production Deployment Checklist

Before deploying to production:

### Supabase Settings
- [ ] Update Site URL to production domain
- [ ] Add production redirect URLs
- [ ] Update email templates with production URLs
- [ ] Verify OAuth redirect URIs in Google/Apple consoles
- [ ] Enable email confirmations (if not already)
- [ ] Set appropriate rate limits
- [ ] Review and enable RLS policies on all tables
- [ ] Enable database backups

### Application Settings
- [ ] Update `.env` with production values:
  ```env
  SUPABASE_URL=https://your-project.supabase.co
  OAUTH_REDIRECT_URL=https://yourdomain.com/auth/callback
  SITE_URL=https://yourdomain.com
  CORS_ORIGINS=https://yourdomain.com
  APP_ENV=production
  DEBUG=false
  ```
- [ ] Use HTTPS for all URLs
- [ ] Configure proper CORS origins
- [ ] Set up monitoring and logging
- [ ] Enable rate limiting at application level
- [ ] Set up error tracking (Sentry, etc.)

### OAuth Providers
- [ ] Update Google OAuth redirect URIs for production
- [ ] Update Apple OAuth return URLs for production
- [ ] Test OAuth flows in production environment
- [ ] Verify OAuth consent screens are production-ready

---

## Troubleshooting

### Common Issues

**Email confirmation not sending:**
- Check Supabase email settings
- Verify email templates are saved
- Check spam folder
- For hosted projects, Supabase provides SMTP by default
- For self-hosted, configure custom SMTP

**Phone OTP not received:**
- Verify Twilio account has credits
- Check Twilio phone number is verified
- Check phone number format (must be E.164: +1234567890)
- Review Twilio logs for delivery issues
- Ensure Twilio account is not in trial mode restrictions

**OAuth redirect not working:**
- Verify redirect URL matches exactly in provider console
- Check that URL is whitelisted in Supabase
- Ensure protocol (http/https) matches
- Clear browser cache and cookies
- Check browser console for CORS errors

**Token expired errors:**
- Access tokens expire after 1 hour by default
- Implement refresh token flow in frontend
- Check system clock is synchronized

**Rate limit errors:**
- Adjust rate limits in Supabase dashboard
- Implement exponential backoff in client
- Cache tokens properly to avoid excessive requests

---

## Additional Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Twilio Documentation](https://www.twilio.com/docs)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Apple Sign In Documentation](https://developer.apple.com/sign-in-with-apple/)

---

## Support

If you encounter issues:

1. Check Supabase Dashboard → Authentication → Logs
2. Check your application logs
3. Review this documentation
4. Check the main [AUTHENTICATION.md](./AUTHENTICATION.md) file
5. Contact Supabase support for platform issues
