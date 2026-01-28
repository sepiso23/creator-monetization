# Authentication & Multi-Frontend Architecture

This document describes the JWT authentication system and multi-frontend API architecture implemented in this project.

## User Types

The system supports three types of users:

### 1. Creator
- **Self-registration**: Can register via the public `/api/auth/register/` endpoint
- **Frontend**: Accesses the creator frontend application
- **Permissions**: Cannot be staff or admin, cannot access admin dashboard
- **Model**: Extends `CustomUser` with a `CreatorProfile` for additional metadata
- **Database Fields**: `user_type='creator'`, `is_staff=False`, `is_superuser=False`

### 2. Staff
- **Creation**: Created by admin via admin dashboard or management command
- **Frontend**: Can access the admin dashboard
- **Permissions**: Can perform staff-level operations
- **Database Fields**: `user_type='staff'`, `is_staff=True`, `is_superuser=False`

### 3. Admin
- **Creation**: Created via `createsuperuser` command
- **Frontend**: Can access the admin dashboard
- **Permissions**: Full access to all system operations
- **Database Fields**: `user_type='admin'`, `is_staff=True`, `is_superuser=True`

## Registration Endpoint

The `/api/auth/register/` endpoint:
- **Permissions**: `AllowAny` - no authentication required
- **User Type**: All self-registered users are created as `creator` type
- **Request Body**:
  ```json
  {
    "email": "creator@example.com",
    "username": "creator_username",
    "password": "SecurePassword123!",
    "password2": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```
- **Response**: Returns user data and JWT tokens (access & refresh)

## JWT Authentication

### Token Endpoints

- **Obtain Token**: `POST /api/auth/token/`
  - Authenticates with email and password
  - Returns access and refresh tokens
  - Custom claims included: `user_type`, `email`, `username`, `is_staff`

- **Refresh Token**: `POST /api/auth/token/refresh/`
  - Refresh access token using refresh token
  - Required when access token expires (15 minutes)

### Token Configuration

- **Access Token Lifetime**: 15 minutes
- **Refresh Token Lifetime**: 7 days
- **Rotation**: Refresh tokens rotate on each refresh
- **Blacklist**: Old refresh tokens are blacklisted

## Multi-Frontend Support

### API Client Model

The `APIClient` model manages different frontend applications:

**Fields**:
- `id`: UUID - Unique identifier
- `name`: String - Client name (e.g., "Creator Web App", "Admin Dashboard")
- `client_type`: Choice - Type of client (web, mobile, internal, partner)
- `api_key`: String - Unique API key for client identification
- `rate_limit`: Integer - Requests per hour allowed
- `is_active`: Boolean - Enable/disable client access

### Client Identification

Clients can be identified in two ways:

#### 1. API Key Header
```http
GET /api/auth/profile/ HTTP/1.1
X-API-Key: sk_xxxxxxxxxxxxx
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### 2. Client ID Header
```http
GET /api/auth/profile/ HTTP/1.1
X-Client-ID: 550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Accessing Client Information

In views, the client information is available via:
```python
def some_view(request):
    if hasattr(request, 'client'):
        client = request.client
        print(f"Request from: {client.name}")
```

### CORS Configuration

Frontend URLs are configured via environment variables:

```env
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://app.example.com
```

## Rate Limiting

The API implements throttling:
- **Anonymous Users**: 100 requests/hour
- **Authenticated Users**: 1000 requests/hour
- **Per Client**: Enforced based on `APIClient.rate_limit`

## API Versioning

Currently using namespace-based versioning:
- Future versions can be accessed via: `/api/v1/`, `/api/v2/`, etc.
- Configured in `REST_FRAMEWORK['DEFAULT_VERSIONING_CLASS']`

## Custom Permissions

Import from `utils.permissions`:

### IsCreator
Allows only users with `user_type='creator'`

```python
from utils.permissions import IsCreator

class CreatorOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsCreator]
```

### IsAdminUser
Allows only staff or admin users

```python
from utils.permissions import IsAdminUser

class AdminOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
```

### IsStaffUser
Allows only staff or superusers

```python
from utils.permissions import IsStaffUser

class StaffOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]
```

### IsOwnerOrAdmin
Allows only object owner or admin users

```python
from utils.permissions import IsOwnerOrAdmin

class OwnerOrAdminView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
```

## Authentication Methods

The API supports multiple authentication methods (tried in order):

1. **API Key Authentication** - Via `X-API-Key` header (for client identification)
2. **JWT Authentication** - Via `Authorization: Bearer <token>` header

## API Endpoints

### Authentication

- `POST /api/auth/register/` - Register new creator
- `POST /api/auth/token/` - Obtain JWT tokens
- `POST /api/auth/token/refresh/` - Refresh access token
- `POST /api/auth/logout/` - Logout (requires auth)

### User Profile

- `GET /api/auth/profile/` - Get current user profile (requires auth)
- `PUT /api/auth/profile/` - Update profile (full update, requires auth)
- `PATCH /api/auth/profile/` - Update profile (partial update, requires auth)

### Password Management

- `POST /api/auth/change-password/` - Change password (requires auth)

## Environment Variables

Add to `.env` file:

```env
# Authentication
SECRET_KEY=your-secret-key-here
DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,https://app.example.com
```

## Database Migrations

After implementing these changes, run:

```bash
python manage.py makemigrations customauth creators
python manage.py migrate
```

## Creating Admin/Staff Users

### Create Superuser (via CLI)
```bash
python manage.py createsuperuser
```

### Create Staff User (via Admin Dashboard)
1. Login to `/admin/`
2. Navigate to Users
3. Create new user with `user_type='staff'` and `is_staff=True`

## Security Notes

- API Keys should be treated like passwords and rotated regularly
- JWT tokens are short-lived (15 minutes) for security
- Refresh tokens should be stored securely on the client
- CORS should only allow trusted domains in production
- Use HTTPS in production to prevent token interception

## Scaling Considerations

This architecture is designed to scale:

1. **Multiple Frontends**: Register each frontend as an `APIClient`
2. **Rate Limiting**: Adjust per-client rate limits based on needs
3. **API Versioning**: Versions can be added without breaking existing clients
4. **Authentication**: Extensible to add OAuth, social login, etc.
5. **Monitoring**: Client identification enables per-client analytics

## Future Enhancements

- OAuth 2.0 / OpenID Connect support
- Social login (Google, Facebook, etc.)
- Two-factor authentication
- API usage analytics per client
- Webhook support for real-time events
- GraphQL support alongside REST
