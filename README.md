# Picads Backend

A FastAPI backend with Supabase authentication and PostgreSQL database integration using SQLAlchemy ORM. **Fully integrated with the Picads frontend** for seamless user profile management and credits system.

## 🔗 Frontend Integration

This backend is specifically designed to work with the **Picads.ai frontend** (`picadsv2/`):

- **JWT Authentication**: Uses Supabase JWT tokens from frontend authentication
- **Smart Profile Management**: Optimized GET/POST pattern for signin/signup flows
- **Credits System**: Provides 1000 default credits for new users
- **CORS Configured**: Ready for frontend development on localhost:5173/5174
- **Graceful Fallback**: Frontend works even if backend is temporarily unavailable

### Integration Patterns

```mermaid
graph LR
    A[Frontend Auth] --> B[Supabase JWT]
    B --> C[Backend API]
    C --> D[PostgreSQL]
    D --> E[Profile Data]
    E --> F[Frontend Dashboard]
```

**Smart API Flow:**

- **Existing Users**: Frontend calls `GET /profile` → Returns data
- **New Users**: Frontend calls `GET /profile` → 404 → `POST /profile` → Creates profile
- **Single Fetch**: Profiles fetched once per session (performance optimized)

## Architecture Overview

This FastAPI backend provides user authentication through Supabase and uses SQLAlchemy ORM for database operations:

```

backend/
├── main.py                   # FastAPI application entry point with CORS
├── Dockerfile                # Docker configuration
├── .gitignore               # Git ignore patterns
├── environment.yml          # Conda environment file
├── README.md                # This file
├── test_profile_flow.py     # Test suite for profile management
├── verify_db_connection.py  # Database connection verification script
└── app/
    ├── __init__.py          # Package initialization
    ├── auth.py              # JWT authentication utilities
    ├── config.py            # Configuration settings with CORS origins
    ├── database.py          # SQLAlchemy async engine and session setup
    ├── models.py            # SQLAlchemy ORM models
    ├── routes.py            # API route handlers
    ├── schemas.py           # Pydantic models for API validation
    └── services.py          # Business logic services (get_or_create_profile)
```

## Features

- ✅ **FastAPI**: Modern, fast web framework
- ✅ **Supabase Auth**: User registration and JWT authentication
- ✅ **SQLAlchemy ORM**: Async database operations
- ✅ **PostgreSQL**: Database with connection pooling
- ✅ **Smart Profile Management**: `get_or_create_profile` pattern
- ✅ **Credits System**: 1000 default credits for new users
- ✅ **CORS**: Configured for frontend development and production
- ✅ **Pydantic**: Request/response validation
- ✅ **Auto Documentation**: Swagger UI at `/docs`
- ✅ **Async/Await**: Full async support throughout
- ✅ **Frontend Integration**: Optimized for Picads.ai frontend

## API Endpoints

### Public Endpoints

- `GET /` - Welcome message
- `GET /public-data` - Public data (works with or without auth)

### Authentication Required (Frontend Integration)

- `GET /profile` - Get current user's profile (for existing users)
- `POST /profile` - Create or get user profile (for new users)
- `PUT /profile` - Update user profile
- `GET /dashboard` - Protected dashboard with user info

### Profile Management Flow

The backend uses a smart `get_or_create_profile` pattern optimized for the frontend:

1. **Frontend Signin**: Calls `GET /profile` to fetch existing profile
2. **Frontend Signup**: Calls `GET /profile` → 404 → `POST /profile` to create new profile
3. **Automatic Credits**: New profiles get 1000 credits by default
4. **JWT Validation**: All requests authenticated via Supabase JWT tokens

## Database Schema

### Profile Model

```python
class Profile(Base):
    __tablename__ = "profiles"
  
    id = Column(UUID, primary_key=True)  # Matches Supabase auth.users.id
    full_name = Column(String)
    credits = Column(Integer, default=1000)  # Updated from 100 to 1000
    stripe_customer_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

**Key Changes:**

- ✅ Default credits increased to **1000** (from 100)
- ✅ Optimized for frontend integration patterns
- ✅ UUID primary key matches Supabase user IDs

## Setup Instructions

### 1. Environment Setup (Conda - Recommended)

```bash
# Navigate to backend directory
cd backend

# Create conda environment from environment.yml
conda env create -f environment.yml

# Activate the environment
conda activate picads-backend
```

### Alternative: Environment Setup (pip/venv)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Copy `env.example` to `.env` and fill in your credentials:

```bash
cp env.example .env
```

Edit `.env` with your actual values:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret

# Database Configuration (PostgreSQL connection string)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# Alternative: Individual database components
USER=your_db_user
PASSWORD=your_db_password
HOST=your_db_host
PORT=5432
DBNAME=your_db_name
```

#### Getting Supabase Credentials:

1. Go to your Supabase project dashboard
2. **URL & Keys**: Settings > API > Project URL and anon public key
3. **JWT Secret**: Settings > API > JWT Settings > JWT Secret
4. **Database URL**: Settings > Database > Connection string (use the async version with `asyncpg`)

### 3. Database Setup

The application uses Supabase PostgreSQL. The database tables will be created automatically when you first run the application.

**Important**: The application uses `NullPool` to avoid event loop conflicts during testing. This is automatically configured.

### 4. Run the Application

```bash
# Make sure your conda environment is activated
conda activate picads-backend

# Run the development server
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

**Frontend Integration:**

- The backend is configured with CORS to work with frontend on localhost:5173/5174
- Frontend will automatically connect to backend for profile management

### 5. Testing

Run the test suite to verify everything is working:

```bash
python test_profile_flow.py
```

This will test:

- Public endpoints accessibility
- Authentication flow with JWT tokens
- Profile creation and management (1000 default credits)
- Smart `get_or_create_profile` functionality
- Database operations

## Usage Examples

### Authentication Flow

1. **Sign up with Supabase** (using Supabase client SDK in frontend)
2. **Get the access token** from Supabase session
3. **Frontend automatically uses the token** to access backend endpoints

### API Usage with Frontend Integration

The frontend automatically handles these API calls:

```bash
# Smart profile fetching (frontend handles this automatically)
# First attempt: GET /profile
curl -X GET "http://localhost:8000/profile" \
     -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN"

# If 404, frontend automatically creates profile: POST /profile
curl -X POST "http://localhost:8000/profile" \
     -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"full_name": "John Doe"}'
```

### Manual API Testing

For testing without the frontend:

```bash
# Get public data (no auth required)
curl -X GET "http://localhost:8000/public-data"

# Create/get profile (requires auth token)
curl -X POST "http://localhost:8000/profile" \
     -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"full_name": "John Doe"}'

# Get profile
curl -X GET "http://localhost:8000/profile" \
     -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN"

# Update profile
curl -X PUT "http://localhost:8000/profile" \
     -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"full_name": "Jane Doe", "credits": 1500}'

# Dashboard
curl -X GET "http://localhost:8000/dashboard" \
     -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN"
```

## Project Structure Explanation

### `app/database.py`

- Async SQLAlchemy engine setup
- Database session management
- Connection pooling configuration (NullPool for testing compatibility)

### `app/models.py`

- SQLAlchemy ORM models
- Database table definitions
- Relationships and constraints

### `app/schemas.py`

- Pydantic models for API validation
- Request/response serialization
- Data transformation

### `app/services.py`

- Business logic layer
- Database operations
- Profile management services

### `app/routes.py`

- API endpoint definitions
- Request handling
- Authentication integration

### `app/auth.py`

- JWT token validation
- Supabase integration
- User authentication utilities

## Key Technical Decisions

### Async Database Operations

The backend uses SQLAlchemy with async/await for non-blocking database operations:

```python
# Example service method
async def get_profile(db: AsyncSession, user_id: str) -> Optional[Profile]:
    result = await db.execute(select(Profile).filter(Profile.id == user_uuid))
    return result.scalar_one_or_none()
```

### Connection Pool Configuration

Uses `NullPool` to prevent event loop conflicts, especially important for testing:

```python
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Prevents "Future attached to a different loop" errors
    echo=False
)
```

### Authentication Integration

Seamlessly integrates with Supabase Auth while maintaining custom database models:

```python
# User ID from Supabase JWT is used as foreign key
class Profile(Base):
    id = Column(UUID, primary_key=True)  # Matches auth.users.id
```

## Development Workflow

### Adding New Features

1. **Database Model**: Add to `app/models.py`
2. **Pydantic Schema**: Add to `app/schemas.py`
3. **Service Logic**: Add to `app/services.py`
4. **API Routes**: Add to `app/routes.py`
5. **Tests**: Update `test_profile_flow.py`

### Database Migrations

For schema changes, you can:

1. Update models in `app/models.py`
2. Use Alembic for migrations (optional, for production)
3. Or recreate tables for development

## Production Deployment

### Environment Configuration

- Set proper DATABASE_URL for production PostgreSQL
- Configure proper CORS origins
- Use production-grade connection pooling (remove NullPool)
- Set up proper logging and monitoring

### Database Considerations

- Use connection pooling in production (remove `poolclass=NullPool`)
- Set up database migrations with Alembic
- Configure proper database backup and recovery
- Monitor database performance

### Security

- Rotate JWT secrets regularly
- Use HTTPS in production
- Configure Supabase RLS (Row Level Security) policies
- Validate and sanitize all inputs

## Docker Support

```bash
# Build the image
docker build -t picads-backend .

# Run the container
docker run -p 8000:8000 --env-file .env picads-backend
```

## Troubleshooting

### Database Connection Issues

```bash
# Verify DATABASE_URL format
postgresql+asyncpg://user:password@host:port/database

# Check Supabase connection string in project settings
# Make sure to use the "async" version with asyncpg
```

### Event Loop Errors

The application uses `NullPool` to prevent "Future attached to a different loop" errors during testing. If you encounter these errors:

1. Ensure `poolclass=NullPool` is set in `database.py`
2. For production, consider using proper pooling with event loop management

### Authentication Issues

1. Verify JWT secret matches Supabase project settings
2. Check token expiration
3. Ensure user exists in Supabase auth.users table

### Conda Environment Issues

```bash
# Clean and recreate environment
conda clean --all
conda env remove -n picads-backend
conda env create -f environment.yml
```

## 🚀 Frontend-Backend Integration Workflow

### Complete Development Setup

1. **Start Backend** (Terminal 1):

   ```bash
   cd backend
   conda activate picads-backend
   python main.py
   ```
2. **Start Frontend** (Terminal 2):

   ```bash
   cd picadsv2
   bun run dev  # or npm run dev
   ```
3. **Test Integration**:

   - Visit frontend at http://localhost:5173
   - Sign up with Google OAuth or email/password
   - Check dashboard for credits display (should show 1000 for new users)
   - Monitor backend logs for API calls

### API Integration Examples

The backend is optimized for the frontend's specific patterns:

**New User Signup Flow:**

```
Frontend → Supabase Auth → Get JWT Token
Frontend → GET /profile (with JWT) → 404 Not Found  
Frontend → POST /profile (with JWT) → Creates profile with 1000 credits
Frontend → Displays credits in dashboard
```

**Existing User Signin Flow:**

```
Frontend → Supabase Auth → Get JWT Token
Frontend → GET /profile (with JWT) → Returns existing profile data
Frontend → Displays credits in dashboard
```

## Supabase Real-time Configuration

For the signup completion flow to work with real-time notifications, you need to enable real-time on the profiles table:

### 1. Enable Real-time for Profiles Table

In your Supabase dashboard:
1. Go to Database → Publications
2. Create a new publication or edit the default `supabase_realtime`
3. Add the `profiles` table to the publication
4. Enable `INSERT` events

Or run this SQL in the Supabase SQL editor:
```sql
-- Enable real-time for profiles table
ALTER PUBLICATION supabase_realtime ADD TABLE profiles;
```

### 2. Row Level Security (RLS) for Real-time

Make sure users can only listen to their own profile changes:
```sql
-- Enable RLS on profiles table (if not already enabled)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Allow users to read their own profiles
CREATE POLICY "Users can read own profile" ON profiles
  FOR SELECT USING (auth.uid() = user_id);

-- Allow real-time subscriptions for own profile
CREATE POLICY "Users can subscribe to own profile" ON profiles
  FOR SELECT USING (auth.uid() = user_id);
```

### 3. Test Real-time Subscription

You can test the real-time subscription in the browser console:
```javascript
// Subscribe to profile changes
const subscription = supabase
  .channel('test-profile')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public', 
    table: 'profiles',
    filter: 'user_id=eq.YOUR_USER_ID'
  }, (payload) => {
    console.log('Profile created:', payload);
  })
  .subscribe();
```

This replaces the polling approach with instant notifications when the webhook creates the profile.

# Picads Backend - Poetry & pyproject.toml Guide

## 🚀 Overview

This backend uses **Poetry** for dependency management instead of traditional `requirements.txt`. Poetry provides better dependency resolution, virtual environment management, and modern Python packaging.

## 📦 Why Poetry + pyproject.toml?

### **Key Benefits:**

| Feature | pip + requirements.txt | Poetry + pyproject.toml |
|---------|------------------------|--------------------------|
| **Dependency Resolution** | Manual conflict resolution | Automatic dependency solving |
| **Lock Files** | None (versions can drift) | `poetry.lock` ensures exact versions |
| **Virtual Environments** | Manual `venv` management | Automatic creation/activation |
| **Dev Dependencies** | Mixed with production | Separate `[tool.poetry.group.dev]` |
| **Version Conflicts** | Runtime errors | Resolved at install time |
| **Build System** | Legacy `setup.py` | Modern `pyproject.toml` standard |
| **Scripts** | Manual | Built-in `[tool.poetry.scripts]` |

### **Poetry Workflow:**
```bash
# Traditional way
pip install fastapi==0.104.1
pip install pydantic==2.5.0
pip freeze > requirements.txt

# Poetry way
poetry add fastapi@0.104.1
poetry add pydantic@2.5.0
# Poetry automatically resolves compatible versions and updates pyproject.toml + poetry.lock
```

---

## 🔧 Installation & Setup

### **1. Install Poetry**
```bash
# Method 1: Official installer (recommended)
curl -sSL https://install.python-poetry.org | python3 -

# Method 2: Via pip
pip install poetry

# Method 3: Via pipx
pipx install poetry

# Verify installation
poetry --version
```

### **2. Initialize Project**
```bash
# Navigate to backend directory
cd backend

# Install dependencies (reads pyproject.toml)
poetry install

# This creates:
# - Virtual environment (.venv/)
# - poetry.lock file (exact versions)
```

### **3. Activate Environment**
```bash
# Method 1: Enter poetry shell
poetry shell

# Method 2: Run commands with poetry
poetry run python main.py
poetry run uvicorn main:app --reload
```

---

## 📋 pyproject.toml Structure

Our `pyproject.toml` is organized into several sections:

### **1. Project Metadata**
```toml
[tool.poetry]
name = "picads-backend"              # Project name
version = "1.0.0"                    # Semantic versioning
description = "Backend API for..."   # Project description
authors = ["Picads Team <...>"]      # Authors list
readme = "README.md"                 # README file
packages = [{include = "app"}]       # Python packages to include
```

### **2. Production Dependencies**
```toml
[tool.poetry.dependencies]
python = "^3.11"                     # Python version constraint
fastapi = "^0.104.1"                # ^0.104.1 means >=0.104.1, <0.105.0
uvicorn = {extras = ["standard"], version = "^0.24.0"}  # With extras
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
```

**Version Constraint Operators:**
- `^1.2.3` - Compatible release (>=1.2.3, <2.0.0)
- `~1.2.3` - Reasonably close (>=1.2.3, <1.3.0)
- `>=1.2.3` - Greater than or equal
- `==1.2.3` - Exact version
- `*` - Any version

### **3. Development Dependencies**
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"          # Testing framework
black = "^23.0.0"           # Code formatter
isort = "^5.12.0"           # Import sorter
flake8 = "^6.0.0"           # Linter
mypy = "^1.5.0"             # Type checker
pytest-cov = "^4.1.0"      # Test coverage
```

### **4. Build System**
```toml
[build-system]
requires = ["poetry-core"]           # Build requirements
build-backend = "poetry.core.masonry.api"  # Build backend
```

### **5. Custom Scripts**
```toml
[tool.poetry.scripts]
start = "uvicorn main:app --host 0.0.0.0 --port 8000"
dev = "uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
test = "pytest tests/ -v"
lint = "black . && isort . && flake8 ."
type-check = "mypy ."
```

**Usage:**
```bash
poetry run start      # Start production server
poetry run dev        # Start development server
poetry run test       # Run tests
poetry run lint       # Format and lint code
poetry run type-check # Type checking
```

### **6. Tool Configuration**
```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true
```

---

## 🛠️ Common Poetry Commands

### **Environment Management**
```bash
# Install all dependencies (prod + dev)
poetry install

# Install only production dependencies
poetry install --only=main

# Install without development dependencies
poetry install --no-dev

# Show virtual environment info
poetry env info

# Show virtual environment path
poetry env info --path

# Activate shell
poetry shell

# Deactivate (when in poetry shell)
exit
```

### **Dependency Management**
```bash
# Add production dependency
poetry add fastapi
poetry add "fastapi>=0.100.0"
poetry add fastapi@0.104.1

# Add development dependency
poetry add --group dev pytest
poetry add --group dev black

# Add with extras
poetry add "uvicorn[standard]"
poetry add redis

# Remove dependency
poetry remove fastapi
poetry remove --group dev pytest

# Update dependencies
poetry update              # Update all
poetry update fastapi      # Update specific package
poetry update --dry-run    # Show what would be updated
```

### **Information & Analysis**
```bash
# List installed packages
poetry show

# Show dependency tree
poetry show --tree

# Show specific package info
poetry show fastapi

# Show outdated packages
poetry show --outdated

# Check for security vulnerabilities
poetry audit
```

### **Lock File Management**
```bash
# Update lock file without upgrading packages
poetry lock

# Update lock file and upgrade packages
poetry lock --no-update

# Export to requirements.txt (for compatibility)
poetry export -f requirements.txt --output requirements.txt
poetry export --only=main --output requirements.txt  # Prod only
poetry export --only=dev --output requirements-dev.txt  # Dev only
```

### **Version Management**
```bash
# Show current version
poetry version

# Bump version
poetry version patch    # 1.0.0 -> 1.0.1
poetry version minor    # 1.0.0 -> 1.1.0
poetry version major    # 1.0.0 -> 2.0.0

# Set specific version
poetry version 2.0.0-alpha.1
```

---

## 🔄 Migration from requirements.txt

### **Step 1: Backup Existing Setup**
```bash
# Backup current requirements
cp requirements.txt requirements.txt.backup
```

### **Step 2: Import from requirements.txt**
```bash
# Create pyproject.toml from requirements.txt
poetry init

# Or import dependencies manually
poetry add $(cat requirements.txt | grep -v "^#" | tr '\n' ' ')
```

### **Step 3: Separate Dev Dependencies**
```bash
# Move dev-only packages to dev group
poetry add --group dev pytest httpx black isort flake8 mypy
poetry remove pytest httpx black isort flake8 mypy
```

### **Step 4: Clean Up**
```bash
# Remove old requirements.txt
rm requirements.txt

# Verify everything works
poetry install
poetry run python main.py
```

---

## 🏗️ Development Workflow

### **Daily Development**
```bash
# 1. Start your day
cd backend
poetry shell  # or use poetry run for each command

# 2. Install any new dependencies
poetry install

# 3. Start development server
poetry run dev  # or: uvicorn main:app --reload

# 4. Add new dependency when needed
poetry add redis

# 5. Run tests before committing
poetry run test
poetry run lint
poetry run type-check

# 6. Commit changes (includes poetry.lock)
git add pyproject.toml poetry.lock
git commit -m "Add Redis caching"
```

### **Adding New Features**
```bash
# 1. Need a new library?
poetry add requests

# 2. Need a dev tool?
poetry add --group dev pytest-mock

# 3. Check what changed
poetry show --tree

# 4. Test everything still works
poetry run test
```

### **Code Quality Workflow**
```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Check for issues
poetry run flake8 .

# Type checking
poetry run mypy .

# Or run all at once
poetry run lint
```

---

## 🐳 Docker Integration

Our `Dockerfile` is optimized for Poetry:

```dockerfile
# Install Poetry
RUN pip install poetry

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry for Docker
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Benefits:
# - No virtual environment needed in container
# - Only production dependencies
# - Reproducible builds with poetry.lock
```

---

## 🚀 Production Deployment

### **Render Configuration**
```bash
# Build command
pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# Start command
poetry run gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

### **Environment Variables**
```bash
# Poetry configuration for production
POETRY_NO_INTERACTION=1
POETRY_VENV_IN_PROJECT=1
```

---

## 🔍 Troubleshooting

### **Common Issues**

#### **"Poetry not found"**
```bash
# Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall
curl -sSL https://install.python-poetry.org | python3 -
```

#### **"Virtual environment not found"**
```bash
# Recreate virtual environment
poetry env remove python
poetry install
```

#### **"Dependency conflicts"**
```bash
# Clear cache and reinstall
poetry cache clear pypi --all
poetry lock
poetry install
```

#### **"Import errors after adding dependencies"**
```bash
# Make sure you're in poetry environment
poetry shell
# or
poetry run python your_script.py
```

### **Performance Tips**

#### **Faster Installs**
```bash
# Configure Poetry for speed
poetry config installer.parallel true
poetry config installer.max-workers 10

# Use system keyring for credentials
poetry config keyring.enabled true
```

#### **Cache Management**
```bash
# Clear all caches
poetry cache clear pypi --all

# List cache info
poetry cache list

# Cache directory
poetry config cache-dir
```

---

## 📚 Further Resources

### **Official Documentation**
- [Poetry Documentation](https://python-poetry.org/docs/)
- [pyproject.toml Specification](https://peps.python.org/pep-0621/)
- [Dependency Specification](https://python-poetry.org/docs/dependency-specification/)

### **Best Practices**
- Always commit `poetry.lock` with `pyproject.toml`
- Use `^` for most dependencies to get compatible updates
- Separate development and production dependencies
- Use `poetry export` for systems that need `requirements.txt`
- Regular `poetry update` to get security fixes

### **Integration Examples**
- [Poetry with Docker](https://python-poetry.org/docs/basic-usage/#poetry-and-pep-517)
- [Poetry with CI/CD](https://python-poetry.org/docs/basic-usage/#installing-dependencies)
- [Poetry with IDEs](https://python-poetry.org/docs/basic-usage/#activating-the-virtual-environment)

---

## 🎯 Quick Reference

### **Essential Commands**
```bash
poetry install           # Install dependencies
poetry add package       # Add dependency
poetry remove package    # Remove dependency
poetry update           # Update dependencies
poetry run command      # Run command in environment
poetry shell           # Activate environment
poetry show            # List packages
poetry version         # Show/bump version
```

### **File Structure**
```
backend/
├── pyproject.toml      # Project configuration
├── poetry.lock         # Locked versions (commit this!)
├── app/               # Your application code
├── tests/             # Test files
└── .venv/             # Virtual environment (don't commit)
```

**🎉 You're now ready to use Poetry for modern Python dependency management!**
