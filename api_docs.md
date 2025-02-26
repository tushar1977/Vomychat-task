# API Documentation

---

## 1. Register a New User

Register a new user by providing an email, username, password, and an optional referral code.

### Endpoint

POST /api/register

### Request Body

```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "securepassword123",
  "referral_code": "optional_referral_code"
}

Response
Success (201 Created):

{
  "message": "User registered successfully",
  "user_id": "12345"
}
Error (400 Bad Request):

{
  "error": "Email or username already exists"
}
```

2. User Login
   Authenticate a user and return a JWT token for accessing protected endpoints.

Endpoint
POST /api/login

### Request Body

{
"identifier": "john_doe or user@example.com",
"password": "securepassword123"
}

Success (200 OK):

{
"message": "Login successful",
"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
Error (401 Unauthorized):

{
"error": "Invalid credentials"
}

3. Forgot Password
   Initiate a password recovery process by providing the user's email.

Endpoint
POST /api/forgot-password

Request Body
{
"email": "user@example.com"
}

Response
Success (200 OK):

{
"message": "Password reset link sent",
"reset_url": "/reset-password?token=reset_token_123"
}
Error (404 Not Found):

{
"error": "Email not found"
}

4. Reset Password
   Reset the user's password using the token received in the reset URL.

Endpoint
POST /api/reset-password?token=xxxx

Request Body
{
"new_password": "newsecurepassword123"
}
Response
Success (200 OK):

{
"message": "Password reset successful"
}
Error (400 Bad Request):

{
"error": "Invalid or expired token"
}

5. User Logout
   Log out the user and invalidate the JWT token.

Endpoint
POST /api/logout
Response
Success (200 OK):

{
"message": "Logout successful"
}

6. Fetch Referrals
   Fetch the list of users referred by the logged-in user.

Endpoint
GET /api/referrals
Response
Success (200 OK):

{
"referrals": [
{
"username": "jane_doe",
"email": "jane@example.com",
"signup_date": "2023-10-01"
},
{
"username": "alice_smith",
"email": "alice@example.com",
"signup_date": "2023-10-05"
}
]
}
Error (401 Unauthorized):

{
"error": "Unauthorized"
}

7. Referral Statistics
   Retrieve statistics related to the referral system, such as the number of successful sign-ups from the user's referrals.

Endpoint
GET /api/referral-stats

Success (200 OK):

{
"total_referrals": 5,
"successful_signups": 3,
"pending_referrals": 2
}
Error (401 Unauthorized):

{
"error": "Unauthorized"
}
