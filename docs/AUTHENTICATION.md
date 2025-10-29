# Authentication API Documentation

Complete guide to authentication in the Recipe App API.

## Overview

The Recipe App supports multiple authentication methods through Supabase Auth:

1. **Email + Password** (with email confirmation)
2. **Phone Number** (with SMS OTP)
3. **Google OAuth**
4. **Apple OAuth**

All authentication methods return a consistent JWT-based session format.

---

## Base URL

```
http://localhost:8000/api/v1/auth
```

---

## 1. Email + Password Authentication

### 1.1 Sign Up with Email

Create a new user account. Requires email verification.

**Endpoint:** `POST /auth/signup`

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**

```json
{
  "message": "Signup successful! Please check your email to verify your account."
}
```

**Notes:**

- User will receive a confirmation email with verification link
- User cannot login until email is verified
- Password must be at least 6 characters

---

### 1.2 Verify Email

Verify email address using the token from confirmation email.

**Endpoint:** `POST /auth/verify-email`

**Request Body:**

```json
{
  "token_hash": "hash_from_email_link",
  "type": "email"
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "expires_at": 1234567890,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "created_at": "2025-01-01T00:00:00Z",
    "user_metadata": {}
  }
}
```

---

### 1.3 Login with Email

Authenticate existing user with email and password.

**Endpoint:** `POST /auth/login`

**Request Body:**

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "expires_at": 1234567890,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "created_at": "2025-01-01T00:00:00Z",
    "user_metadata": {}
  }
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid email or password
- `400 Bad Request`: Email not verified

---

## 2. Phone Number Authentication

### 2.1 Sign Up with Phone

Sign up using phone number. Sends OTP via SMS.

**Endpoint:** `POST /auth/signup-phone`

**Request Body:**

```json
{
  "phone": "+1234567890"
}
```

**Response (200 OK):**

```json
{
  "message": "OTP sent to your phone number. Please verify to complete signup."
}
```

**Notes:**

- Phone number must be in E.164 format (+country_code + number)
- OTP valid for 60 seconds
- User can request new OTP after 60 seconds

---

### 2.2 Verify Phone OTP

Verify phone number with OTP code received via SMS.

**Endpoint:** `POST /auth/verify-phone-otp`

**Request Body:**

```json
{
  "phone": "+1234567890",
  "token": "123456"
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "expires_at": 1234567890,
  "user": {
    "id": "uuid",
    "email": null,
    "created_at": "2025-01-01T00:00:00Z",
    "user_metadata": {
      "phone": "+1234567890"
    }
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid or expired OTP

---

### 2.3 Login with Phone

Login using phone number. Sends OTP via SMS.

**Endpoint:** `POST /auth/login-phone`

**Request Body:**

```json
{
  "phone": "+1234567890"
}
```

**Response (200 OK):**

```json
{
  "message": "If a user exists with this phone number, an OTP has been sent."
}
```

**Notes:**

- For security, always returns success message even if phone doesn't exist
- After receiving OTP, use `/auth/verify-phone-otp` to complete login

---

## 3. Google OAuth

### 3.1 Initiate Google OAuth

Get Google OAuth authorization URL.

**Endpoint:** `GET /auth/oauth/google`

**Response (200 OK):**

```json
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...",
  "provider": "google"
}
```

**Frontend Flow:**

1. Call this endpoint to get OAuth URL
2. Redirect user to the returned URL
3. User authenticates with Google
4. Google redirects back to your `OAUTH_REDIRECT_URL`
5. Frontend receives auth code in URL parameters
6. Use `/auth/oauth/callback` to exchange code for session

---

### 3.2 Handle OAuth Callback

Exchange OAuth code for session (called automatically by Supabase redirect).

**Endpoint:** `GET /auth/oauth/callback?code={code}`

**Query Parameters:**

- `code` (required): Authorization code from OAuth provider
- `error` (optional): Error from OAuth provider
- `error_description` (optional): Error description

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "expires_at": 1234567890,
  "user": {
    "id": "uuid",
    "email": "user@gmail.com",
    "created_at": "2025-01-01T00:00:00Z",
    "user_metadata": {
      "avatar_url": "https://...",
      "full_name": "John Doe",
      "provider_id": "google_user_id"
    }
  }
}
```

---

## 4. Apple OAuth

### 4.1 Initiate Apple OAuth

Get Apple OAuth authorization URL.

**Endpoint:** `GET /auth/oauth/apple`

**Response (200 OK):**

```json
{
  "url": "https://appleid.apple.com/auth/authorize?client_id=...",
  "provider": "apple"
}
```

**Frontend Flow:**
Same as Google OAuth (see section 3.1)

---

## 5. Session Management

### 5.1 Get Current User

Get authenticated user information.

**Endpoint:** `GET /auth/me`

**Headers:**

```
Authorization: Bearer {access_token}
```

**Response (200 OK):**

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "created_at": "2025-01-01T00:00:00Z",
  "user_metadata": {}
}
```

**Error Responses:**

- `401 Unauthorized`: Invalid or expired token

---

### 5.2 Refresh Access Token

Refresh expired access token using refresh token.

**Endpoint:** `POST /auth/refresh`

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**

```json
{
  "access_token": "new_access_token",
  "refresh_token": "new_refresh_token",
  "token_type": "bearer",
  "expires_in": 3600,
  "expires_at": 1234567890,
  "user": {
    /* user object */
  }
}
```

---

### 5.3 Logout

Sign out current user.

**Endpoint:** `POST /auth/logout`

**Headers:**

```
Authorization: Bearer {access_token}
```

**Response (200 OK):**

```json
{
  "message": "Successfully logged out"
}
```

---

## 6. Password Management

### 6.1 Request Password Reset

Send password reset email.

**Endpoint:** `POST /auth/password-reset`

**Request Body:**

```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**

```json
{
  "message": "If an account exists with this email, you will receive a password reset link"
}
```

**Notes:**

- Always returns success to prevent email enumeration
- User receives email with reset link

---

### 6.2 Update Password

Update password for authenticated user.

**Endpoint:** `POST /auth/password-update`

**Headers:**

```
Authorization: Bearer {access_token}
```

**Request Body:**

```json
{
  "password": "newsecurepassword123"
}
```

**Response (200 OK):**

```json
{
  "message": "Password updated successfully"
}
```

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Insufficient permissions
- `409 Conflict`: Resource already exists (e.g., email already registered)
- `500 Internal Server Error`: Server error

---

## Authentication Flow Examples

### Complete Email Signup Flow

```bash
# 1. Sign up
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'

# Response: {"message": "Signup successful! Please check your email..."}

# 2. User clicks link in email, frontend extracts token_hash

# 3. Verify email
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "token_hash": "hash_from_email",
    "type": "email"
  }'

# Response: {access_token, refresh_token, user}
```

### Complete Phone Signup Flow

```bash
# 1. Request OTP
curl -X POST http://localhost:8000/api/v1/auth/signup-phone \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890"
  }'

# Response: {"message": "OTP sent to your phone number..."}

# 2. User receives SMS with OTP code

# 3. Verify OTP
curl -X POST http://localhost:8000/api/v1/auth/verify-phone-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "token": "123456"
  }'

# Response: {access_token, refresh_token, user}
```

### Google OAuth Flow

```bash
# 1. Frontend: Get OAuth URL
curl -X GET http://localhost:8000/api/v1/auth/oauth/google

# Response: {"url": "https://accounts.google.com/...", "provider": "google"}

# 2. Frontend: Redirect user to URL
window.location.href = response.url

# 3. User authenticates with Google

# 4. Google redirects to: http://localhost:3000/auth/callback?code=xyz

# 5. Supabase automatically handles callback and returns session
# Frontend receives session in URL or needs to extract code and call backend
```

---

## Supabase Dashboard Configuration

### Required Configurations

#### 1. Email Authentication

- Navigate to **Authentication > Providers > Email**
- Enable "Enable email provider"
- Enable "Confirm email"
- Configure email templates in **Authentication > Email Templates**

#### 2. Phone Authentication (Twilio)

- Navigate to **Authentication > Providers > Phone**
- Enable "Enable phone provider"
- Select provider: **Twilio**
- Enter Twilio credentials:
  - Account SID
  - Auth Token
  - Phone Number (sender)

#### 3. Google OAuth

- Create OAuth credentials in [Google Cloud Console](https://console.cloud.google.com)
- Navigate to **Authentication > Providers > Google**
- Enable "Google enabled"
- Add Client ID and Client Secret
- Authorized redirect URI: `https://<project-ref>.supabase.co/auth/v1/callback`

#### 4. Apple OAuth

- Set up Apple Sign In at [Apple Developer](https://developer.apple.com)
- Navigate to **Authentication > Providers > Apple**
- Enable "Apple enabled"
- Add Services ID, Team ID, Key ID
- Upload private key file
- Authorized redirect URI: `https://<project-ref>.supabase.co/auth/v1/callback`

#### 5. URL Configuration

- Navigate to **Authentication > URL Configuration**
- Set **Site URL**: `http://localhost:3000` (or your frontend URL)
- Add **Redirect URLs**:
  - `http://localhost:3000/auth/callback`
  - `http://localhost:3000/auth/verify-email`
  - Add production URLs when deploying

#### 6. Rate Limits

- Navigate to **Authentication > Rate Limits**
- Configure limits for:
  - Email OTP: 1 per 60 seconds
  - SMS OTP: 1 per 60 seconds
  - Signup: Adjust as needed

---

## Security Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (httpOnly cookies or secure storage)
3. **Implement token refresh** before access token expires
4. **Never expose refresh tokens** to client-side JavaScript
5. **Validate phone numbers** on frontend before submission
6. **Implement rate limiting** on your frontend
7. **Use environment variables** for all sensitive config
8. **Monitor failed login attempts** for security threats

---

## Frontend Integration Examples

### React/TypeScript Example

```typescript
// auth.service.ts
import axios from "axios";

const API_BASE = "http://localhost:8000/api/v1/auth";

export const authService = {
  // Email signup
  async signupEmail(email: string, password: string) {
    const { data } = await axios.post(`${API_BASE}/signup`, {
      email,
      password,
    });
    return data;
  },

  // Verify email
  async verifyEmail(tokenHash: string) {
    const { data } = await axios.post(`${API_BASE}/verify-email`, {
      token_hash: tokenHash,
      type: "email",
    });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return data;
  },

  // Email login
  async loginEmail(email: string, password: string) {
    const { data } = await axios.post(`${API_BASE}/login`, {
      email,
      password,
    });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return data;
  },

  // Phone signup
  async signupPhone(phone: string) {
    const { data } = await axios.post(`${API_BASE}/signup-phone`, {
      phone,
    });
    return data;
  },

  // Verify phone OTP
  async verifyPhoneOTP(phone: string, token: string) {
    const { data } = await axios.post(`${API_BASE}/verify-phone-otp`, {
      phone,
      token,
    });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    return data;
  },

  // Google OAuth
  async loginGoogle() {
    const { data } = await axios.get(`${API_BASE}/oauth/google`);
    window.location.href = data.url;
  },

  // Apple OAuth
  async loginApple() {
    const { data } = await axios.get(`${API_BASE}/oauth/apple`);
    window.location.href = data.url;
  },

  // Get current user
  async getCurrentUser() {
    const token = localStorage.getItem("access_token");
    const { data } = await axios.get(`${API_BASE}/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  },

  // Logout
  async logout() {
    const token = localStorage.getItem("access_token");
    await axios.post(
      `${API_BASE}/logout`,
      {},
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },
};
```

---

## Testing

### Manual Testing with cURL

See examples above for each endpoint.

### Automated Testing

```python
# test_auth.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_signup_email():
    response = client.post("/api/v1/auth/signup", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "message" in response.json()

def test_signup_phone():
    response = client.post("/api/v1/auth/signup-phone", json={
        "phone": "+1234567890"
    })
    assert response.status_code == 200
    assert "message" in response.json()

# Add more tests...
```

---

## Support & Troubleshooting

### Common Issues

**1. Email confirmation not working**

- Check email templates are configured in Supabase
- Verify SMTP settings (use Supabase's built-in SMTP for testing)
- Check spam folder
- Ensure redirect URLs are whitelisted

**2. Phone OTP not received**

- Verify Twilio credentials in Supabase dashboard
- Check Twilio account has sufficient credits
- Ensure phone number is in E.164 format
- Check Twilio logs for delivery issues

**3. OAuth redirect not working**

- Verify redirect URLs are whitelisted in Supabase
- Check OAuth credentials are correct
- Ensure callback URL matches configuration
- Check browser console for CORS errors

**4. Token expired errors**

- Implement token refresh flow
- Access tokens expire after 1 hour by default
- Use refresh tokens to get new access tokens

---

## API Reference Summary

| Method | Endpoint                 | Description            | Auth Required |
| ------ | ------------------------ | ---------------------- | ------------- |
| POST   | `/auth/signup`           | Email signup           | No            |
| POST   | `/auth/verify-email`     | Verify email           | No            |
| POST   | `/auth/login`            | Email login            | No            |
| POST   | `/auth/signup-phone`     | Phone signup           | No            |
| POST   | `/auth/verify-phone-otp` | Verify phone OTP       | No            |
| POST   | `/auth/login-phone`      | Phone login            | No            |
| GET    | `/auth/oauth/google`     | Google OAuth           | No            |
| GET    | `/auth/oauth/apple`      | Apple OAuth            | No            |
| GET    | `/auth/oauth/callback`   | OAuth callback         | No            |
| GET    | `/auth/me`               | Get current user       | Yes           |
| POST   | `/auth/refresh`          | Refresh token          | No            |
| POST   | `/auth/logout`           | Logout                 | Yes           |
| POST   | `/auth/password-reset`   | Request password reset | No            |
| POST   | `/auth/password-update`  | Update password        | Yes           |

---

## Version History

- **v1.0.0** (2025-01-25): Initial implementation with email, phone, Google, and Apple auth
