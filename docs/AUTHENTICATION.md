# Authentication API Documentation

This document describes the authentication system implemented with Supabase Auth.

## Overview

The authentication system provides secure user registration, login, token refresh, and password management using Supabase as the authentication provider.

## Authentication Flow

1. **Sign Up**: Register new users with email and password
2. **Login**: Authenticate users and receive JWT tokens
3. **Token Verification**: Validate tokens for protected routes
4. **Token Refresh**: Get new access tokens using refresh tokens
5. **Logout**: Invalidate user sessions

## API Endpoints

### Base URL
All authentication endpoints are prefixed with `/auth`

---

### 1. Sign Up (Register)

**Endpoint:** `POST /auth/signup`

**Description:** Create a new user account

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "expires_in": 3600,
  "expires_at": 1704067200
}
```

**Error Responses:**
- `400 Bad Request`: Invalid email format or password too short
- `409 Conflict`: Email already registered
- `500 Internal Server Error`: Server error

**Password Requirements:**
- Minimum 6 characters

**Email Validation:**
- Must be valid email format

---

### 2. Login (Sign In)

**Endpoint:** `POST /auth/login`

**Description:** Authenticate existing user

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "expires_in": 3600,
  "expires_at": 1704067200
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials or email not confirmed
- `500 Internal Server Error`: Server error

---

### 3. Get Current User

**Endpoint:** `GET /auth/me`

**Description:** Get authenticated user information

**Headers Required:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token

---

### 4. Logout

**Endpoint:** `POST /auth/logout`

**Description:** Logout current user and invalidate session

**Headers Required:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token
- `500 Internal Server Error`: Server error

---

### 5. Refresh Token

**Endpoint:** `POST /auth/refresh`

**Description:** Get new access token using refresh token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "expires_in": 3600,
  "expires_at": 1704067200
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid refresh token

---

### 6. Request Password Reset

**Endpoint:** `POST /auth/password-reset`

**Description:** Send password reset email to user

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200 OK):**
```json
{
  "message": "If an account exists with this email, you will receive a password reset link"
}
```

**Note:** This endpoint always returns success to prevent email enumeration attacks.

---

### 7. Update Password

**Endpoint:** `POST /auth/password-update`

**Description:** Update password for authenticated user

**Headers Required:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "password": "newsecurepassword123"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Password updated successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Password too short (must be at least 6 characters)
- `401 Unauthorized`: Invalid or expired token
- `500 Internal Server Error`: Server error

---

### 8. Verify Token

**Endpoint:** `POST /auth/verify-token`

**Description:** Verify if token is valid and return user info

**Headers Required:**
```
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or expired token

---

## Using Protected Routes

To access protected routes in your application, include the JWT access token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Example with cURL:

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Example with JavaScript (fetch):

```javascript
const response = await fetch('http://localhost:8000/auth/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json',
  },
});

const userData = await response.json();
```

### Example with Python (requests):

```python
import requests

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
}

response = requests.get('http://localhost:8000/auth/me', headers=headers)
user_data = response.json()
```

---

## Token Management

### Access Tokens
- **Lifetime:** 3600 seconds (1 hour) by default
- **Purpose:** Used to authenticate API requests
- **Storage:** Store securely (e.g., secure storage in mobile apps, httpOnly cookies for web)

### Refresh Tokens
- **Lifetime:** Longer than access tokens (typically 30 days)
- **Purpose:** Used to obtain new access tokens without re-authentication
- **Storage:** Store securely and separately from access tokens

### Token Refresh Flow

1. Client makes request with expired access token
2. Server returns 401 Unauthorized
3. Client uses refresh token to get new access token via `/auth/refresh`
4. Client retries original request with new access token

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication failed or token invalid
- `409 Conflict`: Resource conflict (e.g., email already exists)
- `500 Internal Server Error`: Server error

---

## Security Best Practices

1. **HTTPS Only**: Always use HTTPS in production
2. **Secure Storage**: Store tokens securely on client side
3. **Token Expiration**: Implement automatic token refresh
4. **Password Strength**: Enforce strong password requirements
5. **Rate Limiting**: Implement rate limiting on authentication endpoints
6. **Email Verification**: Consider requiring email verification before full access

---

## Environment Variables

Required environment variables for authentication:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_anon_key
```

---

## Testing the API

You can test the authentication endpoints using the interactive API documentation:

1. Start the server: `python main.py` or `uvicorn main:app --reload`
2. Navigate to: `http://localhost:8000/docs`
3. Use the Swagger UI to test endpoints interactively

---

## Integration with Frontend

### React Native Example (with Tanstack React Query)

```typescript
import { useMutation } from '@tanstack/react-query';

interface LoginCredentials {
  email: string;
  password: string;
}

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
    created_at: string;
  };
  token_type: string;
  expires_in: number;
}

const useLogin = () => {
  return useMutation({
    mutationFn: async (credentials: LoginCredentials) => {
      const response = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Login failed');
      }
      
      return response.json() as Promise<AuthResponse>;
    },
    onSuccess: (data) => {
      // Store tokens securely
      // Navigate to authenticated screen
    },
  });
};

// Usage
const { mutate: login, isPending, error } = useLogin();

const handleLogin = () => {
  login({
    email: 'user@example.com',
    password: 'password123',
  });
};
```

---

## Troubleshooting

### Common Issues

1. **"Invalid authentication credentials"**
   - Check that the token is correctly formatted in the Authorization header
   - Verify the token hasn't expired
   - Ensure SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY are correctly set

2. **"Email already registered"**
   - User exists, use login endpoint instead
   - Or implement "forgot password" flow

3. **"Invalid email or password"**
   - Verify credentials are correct
   - Check if email confirmation is required

4. **CORS errors**
   - Update CORS_ORIGINS in config.py for production
   - Ensure proper headers are set in requests

---

## Next Steps

- Implement email verification flow
- Add social authentication (Google, Apple, etc.)
- Implement role-based access control (RBAC)
- Add two-factor authentication (2FA)
- Set up password complexity requirements
- Implement account deletion


