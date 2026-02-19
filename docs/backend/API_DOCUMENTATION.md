# Authentication API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

---

## Auth Endpoints

### 1. Register Candidate

**Endpoint:** `POST /auth/register/candidate`

**Description:** Register a new candidate user with profile information.

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john.doe@example.com",
  "password": "securePassword123",
  "role": "candidate",
  "profile": {
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+91-9876543210",
    "resume_id": null,
    "experience_years": 3,
    "skills": ["Python", "Machine Learning", "FastAPI"]
  }
}
```

**Required Fields:**
- `username` (string) - Unique username
- `email` (string) - Valid email address
- `password` (string) - User password
- `role` (string) - Must be "candidate"
- `profile` (object) - Candidate profile with:
  - `first_name` (string, optional)
  - `last_name` (string, optional)
  - `phone` (string, optional)
  - `resume_id` (string, optional) - ObjectId reference to resume
  - `experience_years` (number, optional)
  - `skills` (array of strings, optional)

**Success Response (200):**
```json
{
  "access_token": "mock_token_john_doe",
  "token_type": "bearer",
  "username": "john_doe",
  "role": "candidate"
}
```

**Error Responses:**

- **400 Bad Request** - Username already exists or wrong role
```json
{
  "detail": "Username already registered"
}
```
or
```json
{
  "detail": "This endpoint is for candidate registration only"
}
```

- **422 Unprocessable Entity** - Missing required fields
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required"
    }
  ]
}
```

---

### 2. Register Admin

**Endpoint:** `POST /auth/register/admin`

**Description:** Register a new admin user with profile information.

**Request Body:**
```json
{
  "username": "hr_manager",
  "email": "hr.manager@company.com",
  "password": "adminPassword123",
  "role": "admin",
  "profile": {
    "first_name": "HR",
    "last_name": "Manager",
    "department": "Data Science Hiring",
    "designation": "Lead Recruiter"
  }
}
```

**Required Fields:**
- `username` (string) - Unique username
- `email` (string) - Valid email address
- `password` (string) - User password
- `role` (string) - Must be "admin"
- `profile` (object) - Admin profile with:
  - `first_name` (string, optional)
  - `last_name` (string, optional)
  - `department` (string, optional)
  - `designation` (string, optional)

**Success Response (200):**
```json
{
  "access_token": "mock_token_hr_manager",
  "token_type": "bearer",
  "username": "hr_manager",
  "role": "admin"
}
```

**Error Responses:**
Same as candidate registration endpoint.

---

### 3. Login Candidate

**Endpoint:** `POST /auth/login/candidate`

**Description:** Authenticate a candidate user.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "securePassword123"
}
```

**Required Fields:**
- `username` (string)
- `password` (string)

**Success Response (200):**
```json
{
  "access_token": "mock_token_john_doe",
  "token_type": "bearer",
  "username": "john_doe",
  "role": "candidate"
}
```

**Error Responses:**

- **401 Unauthorized** - Invalid credentials
```json
{
  "detail": "Incorrect candidate credentials"
}
```

- **403 Forbidden** - User is not a candidate or login is disabled.
```json
{
  "detail": "User is not a candidate"
}
```

---

### 4. Login Admin

**Endpoint:** `POST /auth/login/admin`

**Description:** Authenticate an admin user.

**Request Body:**
```json
{
  "username": "hr_manager",
  "password": "adminPassword123"
}
```

**Required Fields:**
- `username` (string)
- `password` (string)

**Success Response (200):**
```json
{
  "access_token": "mock_token_hr_manager",
  "token_type": "bearer",
  "username": "hr_manager",
  "role": "admin"
}
```

**Error Responses:**

- **401 Unauthorized** - Invalid credentials
```json
{
  "detail": "Incorrect admin credentials"
}
```

- **403 Forbidden** - User is not an admin
```json
{
  "detail": "User is not an admin"
}
```

---

### 5. Get Current User

**Endpoint:** `GET /auth/me`

**Description:** Get the profile of the currently logged-in user.

**Headers:**
- `Authorization`: `Bearer <token>`

**Success Response (200):**
Returns the full user object including profile details.
```json
{
  "_id": "65d4...",
  "username": "john_doe",
  "email": "john.doe@example.com",
  "role": "candidate",
  "is_active": true,
  "profile": { ... },
  "created_at": "2024-02-17T..."
}
```

---

### 6. Logout

**Endpoint:** `POST /auth/logout`

**Description:** Logs out the user (client-side token removal expected).

**Success Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

## Admin Features

### 1. Register Candidate (Admin)

**Endpoint:** `POST /auth/admin/register-candidate`

**Description:** Admin creates a new candidate and triggers an email invitation.

**Headers:**
- `Authorization`: `Bearer <admin_token>`
- `Content-Type`: `multipart/form-data`

**Form Data:**
- `candidate_name` (string)
- `candidate_email` (string)
- `job_description` (string)
- `resume` (file)

**Success Response (201):**
```json
{
  "id": "65d4...",
  "username": "john",
  "email": "john@example.com",
  "is_active": true,
  "login_disabled": false,
  "created_at": "...",
  "job_description": "..."
}
```

---

### 2. Get All Candidates

**Endpoint:** `GET /auth/admin/candidates`

**Description:** Retrieve a list of all registered candidates.

**Headers:**
- `Authorization`: `Bearer <admin_token>`

**Success Response (200):**
```json
[
  {
    "id": "65d4...",
    "username": "john",
    "email": "john@example.com",
    "is_active": true,
    "login_disabled": false,
    "created_at": "..."
  },
  ...
]
```

---

### 3. Toggle Candidate Login

**Endpoint:** `POST /auth/admin/candidates/{candidate_id}/toggle-login`

**Description:** Enable or disable a candidate's ability to login.

**Headers:**
- `Authorization`: `Bearer <admin_token>`

**Path Parameters:**
- `candidate_id`: ID of the candidate.

**Success Response (200):**
```json
{
  "message": "Candidate login has been disabled",
  "candidate_id": "65d4...",
  "email": "john@example.com",
  "login_disabled": true
}
```

---

## Dashboard Endpoints

### 1. Get Dashboard Stats

**Endpoint:** `GET /dashboard/stats`

**Description:** Get aggregated statistics for the dashboard.

**Success Response (200):**
```json
{
  "total_interviews": 24,
  "completed": 15,
  "pending": 7,
  "flagged": 2
}
```

---

## Frontend Integration Guide

### TypeScript Types

```typescript
// Profile types
interface CandidateProfile {
  first_name?: string;
  last_name?: string;
  phone?: string;
  resume_id?: string;
  experience_years?: number;
  skills?: string[];
}

interface AdminProfile {
  first_name?: string;
  last_name?: string;
  department?: string;
  designation?: string;
}

// Registration types
interface CandidateRegistration {
  username: string;
  email: string;
  password: string;
  role: "candidate";
  profile: CandidateProfile;
}

interface AdminRegistration {
  username: string;
  email: string;
  password: string;
  role: "admin";
  profile: AdminProfile;
}

// Login types
interface LoginRequest {
  username: string;
  password: string;
}

// Response type
interface AuthResponse {
  access_token: string;
  token_type: string;
  username: string;
  role: "admin" | "candidate";
}

// Candidate Management
interface CandidateResponse {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  login_disabled: boolean;
  created_at: string;
  job_description?: string;
}

interface DashboardStats {
  total_interviews: number;
  completed: number;
  pending: number;
  flagged: number;
}
```

### Example Usage (React/Next.js)

```typescript
// Register Candidate
async function registerCandidate(data: CandidateRegistration): Promise<AuthResponse> {
  const response = await fetch('http://localhost:8000/api/v1/auth/register/candidate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Registration failed');
  }

  return response.json();
}

// Login Candidate
async function loginCandidate(credentials: LoginRequest): Promise<AuthResponse> {
  const response = await fetch('http://localhost:8000/api/v1/auth/login/candidate', {
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

  return response.json();
}

// Usage in component
const handleCandidateRegistration = async (formData: CandidateRegistration) => {
  try {
    const result = await registerCandidate(formData);
    // Store token
    localStorage.setItem('access_token', result.access_token);
    localStorage.setItem('role', result.role);
    // Redirect to dashboard
    router.push('/candidate/dashboard');
  } catch (error) {
    console.error('Registration error:', error);
    // Show error to user
  }
};
```

---

## Validation Rules

### Email
- Must be a valid email format
- Required field

### Username
- Must be unique
- Required field

### Password
- Required field
- No specific format enforced (implement your own validation on frontend)

### Role
- Must match the endpoint ("candidate" for `/register/candidate`, "admin" for `/register/admin`)
- Required field

### Profile
- Required field
- Must match role type:
  - Candidate role → CandidateProfile structure
  - Admin role → AdminProfile structure

---

## CORS Configuration

The backend is configured with CORS to allow requests from:
- `http://localhost:3000` (Next.js default)

If using a different port, update the CORS configuration in `app/main.py`.

---

## Notes for Frontend Team

1. **Token Storage**: Store the `access_token` securely (localStorage or httpOnly cookies)
2. **Role-Based Routing**: Use the `role` field to redirect users to appropriate dashboards
3. **Error Handling**: Handle 400, 401, 403, and 422 status codes appropriately
4. **Form Validation**: Validate email format and required fields on frontend before submission
5. **Profile Fields**: All profile fields are optional, but the profile object itself is required
6. **Skills Array**: For candidates, skills should be an array of strings (can be empty)
