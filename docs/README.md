# CrackDSA Backend Documentation

## 📚 Documentation Index

This directory contains comprehensive documentation for the CrackDSA API backend, with a focus on the new Supabase integration and authentication system.

### Core Documentation

#### 1. [Supabase Integration Guide](supabase-integration.md)
**Complete setup and implementation guide for Supabase**

- Overview of Supabase architecture (database + auth)
- Step-by-step setup instructions for Supabase projects
- Google OAuth configuration
- Environment variable setup
- Database connection management
- API usage examples
- Startup verification process
- Performance considerations
- Deployment checklist

**When to read**: Setting up Supabase for the first time, understanding how database connections work

---

#### 2. [Health Endpoint API Documentation](health-endpoint-api.md)
**Detailed API reference for the `/health` healthcheck endpoint**

- Endpoint specification (`GET /health`)
- Response formats (success, degraded, error)
- HTTP status codes
- Usage examples (cURL, Python, JavaScript, Bash)
- Monitoring integrations (Kubernetes, AWS Load Balancer, Datadog, Grafana)
- Performance metrics
- Debugging techniques
- FAQ

**When to read**: Setting up monitoring, integrating with load balancers, troubleshooting health checks

---

#### 3. [Authentication & Authorization Guide](authentication-guide.md)
**Comprehensive guide to implementing authentication and protecting routes**

- Quick start for Google OAuth setup
- Getting JWT tokens for testing
- Protecting routes with `Depends(get_current_user)`
- Common implementation patterns
- Role-based access control
- Error handling
- Testing protected endpoints
- JWT token flow diagram
- Security best practices
- Troubleshooting authentication issues

**When to read**: Protecting API endpoints, implementing role-based access, testing auth flows

---

#### 5. [OAuth Integration Frontend Guide](oauth-integration-frontend.md)
**Step-by-step guide for integrating Supabase Google OAuth from frontend to backend**

- Overall OAuth architecture and flow diagram
- Backend API endpoints (`/auth/callback`, `/auth/validate`)
- Complete frontend implementation using React + Supabase JS client
- Google login button component
- Auth callback page handler
- Protected route wrapper
- Session restoration on page reload
- Making authenticated API calls from frontend
- Environment variable setup (frontend & backend)
- Complete end-to-end workflow walkthrough
- Troubleshooting common OAuth issues
- Security best practices

**When to read**: Implementing Google login on frontend, integrating with backend auth endpoints, handling OAuth callbacks

---

#### 6. [Frontend OAuth Task - For AI Agent](FRONTEND_OAUTH_TASK.md)
**Concise, actionable task description for giving to AI agents or contractors on frontend**

- Quick overview of what needs to be built (10 components)
- Backend API contract with request/response formats
- Exact file structure to create
- Complete data flow diagram
- Critical do's and don'ts
- Testing checklist
- Environment variables needed
- Phase-by-phase breakdown
- Start-here guide

**When to read**: Copy this and paste as a task to an AI agent - concise version suitable for automation

---

#### 6a. [OAuth Flow - How It Works](OAUTH_FLOW_EXPLANATION.md)
**Step-by-step explanation of what happens during OAuth login (no implementation)**

- 10-step flow description of user login process
- What user sees at each step
- What backend does at each step
- Security checkpoints explained
- Session lifecycle diagram
- Data flow between frontend/backend/Supabase/Google
- Key security features explained
- Timeline of events
- Session expiration process
- Comparison of old vs new approach

**When to read**: Understanding the OAuth flow without implementation details, explaining to others how it works

---

#### 6b. [Backend-Driven OAuth Flow - Architecture](BACKEND_OAUTH_FLOW.md)
**Complete architecture and implementation details for secure backend-driven OAuth**

- Why backend-driven OAuth is more secure
- System architecture diagram and flow
- Detailed step-by-step flow explanation
- Component breakdown (OAuth service, routes)
- Security features (CSRF, session management)
- Configuration guide
- Error handling
- Testing procedures
- Production deployment requirements
- Troubleshooting guide

**When to read**: Understanding backend OAuth implementation, planning production deployment, implementing session management

---

#### 6c. [Callback Handler - Updated for Backend Flow](CALLBACK_HANDLER_ONLY.md)
**Simplified frontend OAuth implementation guide (backend-driven approach)**

- Login button implementation
- No callback handling needed (backend automatic)
- Session validation from frontend
- Logout implementation
- Backend endpoint reference
- Error handling
- Development setup

**When to read**: Implementing frontend OAuth with backend-driven flow - much simpler than traditional approach

---

#### 7. [Frontend OAuth Implementation Guide](FRONTEND_OAUTH_PROMPT.md)
**Detailed comprehensive guide for frontend developers (more thorough than FRONTEND_OAUTH_TASK.md)**

- All 8 implementation phases with detailed requirements
- Backend API endpoints full specification
- Critical implementation details
- File structure with descriptions
- Complete user journey flow walkthrough
- Testing checklist with verification steps
- Security best practices
- Common error scenarios
- Don's and don'ts
- Success criteria
- Clarification questions

**When to read**: Detailed implementation guidance for human developers - reference guide with all details

---
**Existing API documentation for the roadmap generation endpoint**

- Original endpoint specifications
- Request/response formats
- Example usage

---

## 🚀 Quick Start Paths

### For Backend Developers

1. **First Time Setup**:
   - [Supabase Integration Guide](supabase-integration.md) → Setup Instructions section
   - [Authentication & Authorization Guide](authentication-guide.md) → Quick Start section

2. **Implementing New Endpoints**:
   - [Authentication & Authorization Guide](authentication-guide.md) → Common Patterns section
   - [Supabase Integration Guide](supabase-integration.md) → Database Operations section

3. **Protecting Routes**:
   - [Authentication & Authorization Guide](authentication-guide.md) → Protected Routes section
   - [Authentication & Authorization Guide](authentication-guide.md) → Common Patterns section

### For DevOps/Operations

1. **Setting Up Monitoring**:
   - [Health Endpoint API Documentation](health-endpoint-api.md) → Usage Examples section
   - [Health Endpoint API Documentation](health-endpoint-api.md) → Monitoring Integrations section

2. **Deployment**:
   - [Supabase Integration Guide](supabase-integration.md) → Deployment Checklist section
   - [Health Endpoint API Documentation](health-endpoint-api.md) → Monitoring Integrations section

### For Frontend Developers

**If using AI Agent/Contractor**:

**Option A** (Everything needs to be built):
1. Copy & send [Frontend OAuth Task - For AI Agent](FRONTEND_OAUTH_TASK.md) as task description
2. Link to [Frontend OAuth Implementation Guide](FRONTEND_OAUTH_PROMPT.md) as reference

**Option B** (Only callback handler needed):
1. Copy & send [Callback Handler Only - Simple Task](CALLBACK_HANDLER_ONLY.md) as task
2. Reference backend API in that doc - no additional links needed

**If implementing yourself**:
1. **Getting Started with Google OAuth**:
   - [Frontend OAuth Implementation Guide](FRONTEND_OAUTH_PROMPT.md) → Phase 1-2
   - [OAuth Integration Frontend Guide](oauth-integration-frontend.md) → Architecture section

2. **Architecture & Planning**:
   - [Frontend OAuth Task - For AI Agent](FRONTEND_OAUTH_TASK.md) → Data Flow section
   - [Frontend OAuth Implementation Guide](FRONTEND_OAUTH_PROMPT.md) → Complete User Flow

3. **Just Callback Handler**:
   - [Callback Handler Only - Simple Task](CALLBACK_HANDLER_ONLY.md) → Complete template

4. **Code Examples & Patterns**:
   - [OAuth Integration Frontend Guide](oauth-integration-frontend.md) → Step 3-7 (code examples)
   - [Authentication & Authorization Guide](authentication-guide.md) → Common Patterns

5. **Testing & Verification**:
   - [Frontend OAuth Task - For AI Agent](FRONTEND_OAUTH_TASK.md) → Testing Checklist
   - [OAuth Integration Frontend Guide](oauth-integration-frontend.md) → Troubleshooting

---

## 📋 What Was Implemented

### ✅ Supabase Integration
- Replaced SQLAlchemy + PostgreSQL/SQLite with Supabase
- Implemented Supabase client connection pooling
- Created lazy-initialized singleton for database access
- Added database connectivity verification

### ✅ Health Check Endpoint
- **Endpoint**: `GET /health`
- Reports application status and database connectivity
- Returns HTTP 200 (healthy) or 503 (unhealthy)
- Includes UTC timestamp
- Public access (no authentication required)

### ✅ JWT Authentication
- Implemented Supabase JWT verification middleware
- Created `get_current_user()` dependency for protected routes
- Added `get_current_user_optional()` for conditional authentication
- Full error handling and 401 Unauthorized responses

### ✅ OAuth Token Validation
- Created auth service to validate tokens from frontend
- Implemented `/api/v1/auth/callback` endpoint for OAuth callback handling
- Implemented `/api/v1/auth/validate` endpoint for session restoration
- Extracts user details from Supabase JWT tokens
- Optional automatic user record creation/sync to database

### ✅ Configuration Management
- Added Supabase credentials to environment variables
- Pydantic-based configuration with validation
- `.env.example` template with all required variables

---

## 🔧 Key Files

| File | Purpose |
|------|---------|
| `app/database.py` | Supabase client initialization and connection management |
| `app/config.py` | Configuration settings with Pydantic validation |
| `app/middleware/auth.py` | JWT authentication middleware and dependencies |
| `app/services/auth_service.py` | Token validation and user data retrieval service |
| `app/routes/auth_routes.py` | OAuth callback and token validation endpoints |
| `app/main.py` | FastAPI app with startup verification and health endpoint |
| `.env.example` | Template for environment variables |
| `requirements.txt` | Python dependencies (includes `supabase`) |
| `docs/oauth-integration-frontend.md` | Frontend OAuth integration guide |

---

## 🔗 Related Files

- **[MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md)** — Transitioning from SQLAlchemy to Supabase, data migration strategies
- **[requirements.txt](../requirements.txt)** — Python dependencies including new Supabase client
- **[.env.example](../.env.example)** — Environment variable template

---

## 🆘 Troubleshooting

### Health Check Issues

See [Health Endpoint API Documentation → Troubleshooting](health-endpoint-api.md#troubleshooting)

### Authentication Failures

See [Authentication & Authorization Guide → Troubleshooting](authentication-guide.md#troubleshooting)

### Database Connection Problems

See [Supabase Integration Guide → Error Handling](supabase-integration.md#error-handling)

---

## 📞 Getting Help

### Common Questions

**Q: Where do I get my Supabase credentials?**  
A: See [Supabase Integration Guide → Setup Instructions](supabase-integration.md#setup-instructions)

**Q: How do I protect an endpoint with authentication?**  
A: See [Authentication & Authorization Guide → Protected Routes](authentication-guide.md#protected-routes)

**Q: How do I set up monitoring for the API?**  
A: See [Health Endpoint API Documentation → Monitoring Integrations](health-endpoint-api.md#monitoring-integrations)

**Q: How do I test authentication locally?**  
A: See [Authentication & Authorization Guide → Testing Protected Endpoints](authentication-guide.md#testing-protected-endpoints)

---

## 📝 Documentation Standards

All documentation follows these standards:
- **Format**: Markdown
- **Code Examples**: Language-specific where applicable (Python, JavaScript, Bash)
- **API Responses**: JSON format
- **Timestamps**: UTC ISO 8601 format
- **Status Codes**: HTTP standard codes

---

## 🔄 Keeping Documentation Updated

When making changes to:
- **Authentication**: Update [Authentication & Authorization Guide](authentication-guide.md)
- **Database operations**: Update [Supabase Integration Guide](supabase-integration.md)
- **Health endpoint**: Update [Health Endpoint API Documentation](health-endpoint-api.md)
- **Setup/configuration**: Update [Supabase Integration Guide](supabase-integration.md#setup-instructions)

---

## 📅 Last Updated

- **2025-03-30**: OAuth callback and token validation endpoints added
  - New auth service for token validation
  - Frontend-backend OAuth integration guide
  - API endpoints for `/auth/callback` and `/auth/validate`
- **2025-03-29**: Initial Supabase integration documentation
  - Core endpoints documented
  - Authentication patterns documented
  - Monitoring integration examples added

---

## 📖 Additional Resources

- [Supabase Official Docs](https://supabase.com/docs)
- [FastAPI Security Guide](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT (JSON Web Tokens)](https://jwt.io)
- [HTTP Status Codes](https://httpwg.org/specs/rfc7231.html#status.codes)

---

**Next**: Choose a documentation file above to learn more about a specific feature.
