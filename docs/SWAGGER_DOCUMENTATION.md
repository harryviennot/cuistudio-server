# Swagger API Documentation

## Overview

The backend API now includes comprehensive OpenAPI/Swagger documentation for all passwordless authentication endpoints.

## Accessing Swagger UI

### Local Development
```
http://localhost:8000/docs
```

### Alternative ReDoc Format
```
http://localhost:8000/redoc
```

### OpenAPI JSON Schema
```
http://localhost:8000/openapi.json
```

---

## API Documentation Structure

### Authentication Endpoints

All authentication endpoints are now fully documented with:

#### **Email Magic Link Authentication**

**`POST /api/v1/auth/email`** - Request Email Magic Link
- **Summary**: Send a magic link to user's email for passwordless authentication
- **Description**: Unified endpoint for both login and signup
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response**: 200 OK with success message
- **Features**:
  - Automatic user creation
  - One-time use links
  - Expires in 1 hour
  - Rate limited
  - Email enumeration prevention

**`POST /api/v1/auth/email/verify`** - Verify Email Magic Link
- **Summary**: Verify the magic link token from email
- **Description**: Complete authentication and return JWT tokens
- **Request Body**:
  ```json
  {
    "token_hash": "abc123def456",
    "type": "email"
  }
  ```
- **Response**: 200 OK with access token, refresh token, and user data
- **Key Fields**:
  - `is_new_user`: Boolean flag indicating if profile completion is needed
  - `access_token`: JWT token for API requests
  - `refresh_token`: Long-lived token for refreshing access

---

#### **Phone OTP Authentication**

**`POST /api/v1/auth/phone`** - Request Phone OTP
- **Summary**: Send 6-digit OTP to user's phone
- **Description**: Unified endpoint for both login and signup via SMS
- **Request Body**:
  ```json
  {
    "phone": "+15551234567"
  }
  ```
- **Response**: 200 OK with success message
- **Features**:
  - E.164 phone format required
  - 6-digit OTP code
  - Expires in 60 seconds
  - Rate limited (5 SMS/hour)
  - Requires Twilio configuration

**`POST /api/v1/auth/phone/verify`** - Verify Phone OTP
- **Summary**: Verify the 6-digit OTP code
- **Description**: Complete authentication and return JWT tokens
- **Request Body**:
  ```json
  {
    "phone": "+15551234567",
    "token": "123456"
  }
  ```
- **Response**: 200 OK with access token, refresh token, and user data
- **Key Fields**:
  - `is_new_user`: Boolean flag for profile completion check

---

#### **Profile Management**

**`POST /api/v1/auth/profile/complete`** - Complete User Profile
- **Summary**: Complete profile for new users
- **Description**: Required when `is_new_user` is true
- **Authentication**: Required (Bearer token)
- **Request Body**:
  ```json
  {
    "name": "John Doe",
    "username": "johndoe",
    "date_of_birth": "1990-01-01",
    "bio": "Food enthusiast and recipe collector"
  }
  ```
- **Response**: 200 OK with success message
- **Validation**:
  - Username must be unique
  - Username: 3-30 chars, alphanumeric + underscore
  - Date format: YYYY-MM-DD
  - Bio: max 500 characters

**`PATCH /api/v1/auth/profile`** - Update User Profile
- **Summary**: Update profile for existing users
- **Description**: Update any profile field(s)
- **Authentication**: Required (Bearer token)
- **Request Body**: (all fields optional)
  ```json
  {
    "name": "John Doe",
    "username": "johndoe",
    "date_of_birth": "1990-01-01",
    "bio": "Updated bio"
  }
  ```
- **Response**: 200 OK with success message

---

#### **Session Management**

**`GET /api/v1/auth/me`** - Get Current User
- **Summary**: Retrieve current user information
- **Authentication**: Required (Bearer token)
- **Response**: 200 OK with user data including `is_new_user` flag
- **Example Response**:
  ```json
  {
    "id": "uuid-here",
    "email": "user@example.com",
    "phone": null,
    "created_at": "2024-01-01T00:00:00Z",
    "user_metadata": {
      "name": "John Doe",
      "username": "johndoe",
      "profile_completed": true
    },
    "is_new_user": false
  }
  ```

**`POST /api/v1/auth/logout`** - Logout User
- **Summary**: Logout and invalidate session
- **Authentication**: Required (Bearer token)
- **Response**: 200 OK with success message

**`POST /api/v1/auth/refresh`** - Refresh Access Token
- **Summary**: Get new access token using refresh token
- **Description**: Access tokens expire after 1 hour
- **Request Body**:
  ```json
  {
    "refresh_token": "v1.MR45tLN-Io..."
  }
  ```
- **Response**: 200 OK with new tokens and user data
- **Best Practices**:
  - Store refresh tokens securely
  - Auto-refresh on 401 errors
  - Never expose in URLs/logs

---

## Enhanced Documentation Features

### 1. **Interactive "Try it out" functionality**
- Every endpoint can be tested directly in Swagger UI
- Example request bodies pre-filled
- Response examples shown

### 2. **Comprehensive Examples**
- Request body examples for all endpoints
- Response examples for success and error cases
- E.164 phone format examples
- ISO date format examples

### 3. **Detailed Descriptions**
- Full markdown descriptions with formatting
- Key features listed
- Security considerations
- Authentication flow explanations
- Validation rules clearly stated

### 4. **Response Status Codes**
- 200: Success responses
- 400: Bad request / validation errors
- 401: Authentication required / invalid token
- 500: Server errors

### 5. **Schema Validation**
- Email format validation (EmailStr)
- Phone format validation (E.164 regex)
- Username pattern validation
- Length constraints
- Required vs optional fields

---

## Using the API Documentation

### For Developers

1. **Explore Endpoints**:
   - Navigate to http://localhost:8000/docs
   - Browse through the "Authentication" tag
   - Click any endpoint to see details

2. **Test Endpoints**:
   - Click "Try it out" button
   - Modify the example request body
   - Click "Execute" to test
   - View the response

3. **Generate Client Code**:
   - Download OpenAPI spec from `/openapi.json`
   - Use tools like OpenAPI Generator or Swagger Codegen
   - Generate client libraries for any language

### For API Consumers

1. **Authentication Flow**:
   ```
   Email Magic Link:
   POST /auth/email → User clicks link → POST /auth/email/verify

   Phone OTP:
   POST /auth/phone → User enters OTP → POST /auth/phone/verify
   ```

2. **Profile Completion** (if `is_new_user === true`):
   ```
   POST /auth/profile/complete (with Bearer token)
   ```

3. **Using Access Tokens**:
   ```
   Authorization: Bearer <access_token>
   ```

4. **Token Refresh** (when access token expires):
   ```
   POST /auth/refresh with refresh_token
   ```

---

## Swagger UI Customization

The API documentation includes:

- **Grouped endpoints** by functionality (Authentication, Profile, Session)
- **Clear naming conventions** for easy discovery
- **Detailed parameter descriptions** with examples
- **HTTP status code documentation**
- **Security scheme** (Bearer token authentication)

---

## Development Workflow

### Testing with Swagger UI

1. **Start your backend**:
   ```bash
   cd cuistudio-server
   python main.py
   ```

2. **Open Swagger UI**:
   ```
   http://localhost:8000/docs
   ```

3. **Test Email Magic Link**:
   - Expand `POST /api/v1/auth/email`
   - Click "Try it out"
   - Enter your email
   - Execute
   - Check your email for magic link

4. **Authorize Requests**:
   - After authentication, click "Authorize" button (🔒)
   - Enter your access token
   - All subsequent requests will include the token

---

## API Schema Export

### Download OpenAPI Specification

**JSON Format**:
```bash
curl http://localhost:8000/openapi.json > openapi.json
```

**Use with Postman**:
1. Open Postman
2. Import → Link
3. Enter: `http://localhost:8000/openapi.json`
4. Import collection

**Use with Insomnia**:
1. Open Insomnia
2. Import/Export → Import Data
3. Select From URL
4. Enter: `http://localhost:8000/openapi.json`

---

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **OpenAPI Specification**: https://swagger.io/specification/
- **ReDoc Documentation**: http://localhost:8000/redoc

---

## Notes

- All endpoints return JSON responses
- Authentication uses JWT Bearer tokens
- Rate limiting is configured in Supabase
- CORS is configured for frontend origins
- Comprehensive error messages with detail field

---

Last updated: 2024
