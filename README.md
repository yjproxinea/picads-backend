# Picads Backend

A FastAPI backend with Supabase authentication and PostgreSQL database integration using SQLAlchemy ORM.

## Architecture Overview

This FastAPI backend provides user authentication through Supabase and uses SQLAlchemy ORM for database operations:

```

backend/
├── main.py                   # FastAPI application entry point
├── Dockerfile                # Docker configuration
├── .gitignore               # Git ignore patterns
├── environment.yml          # Conda environment file
├── README.md                # This file
├── test_profile_flow.py     # Test suite for profile management
├── verify_db_connection.py  # Database connection verification script
└── app/
    ├── __init__.py          # Package initialization
    ├── auth.py              # JWT authentication utilities
    ├── config.py            # Configuration settings with database
    ├── database.py          # SQLAlchemy async engine and session setup
    ├── models.py            # SQLAlchemy ORM models
    ├── routes.py            # API route handlers
    ├── schemas.py           # Pydantic models for API validation
    └── services.py          # Business logic services
```

## Features

- ✅ **FastAPI**: Modern, fast web framework
- ✅ **Supabase Auth**: User registration and JWT authentication
- ✅ **SQLAlchemy ORM**: Async database operations
- ✅ **PostgreSQL**: Database with connection pooling
- ✅ **Profile Management**: User profiles with credits system
- ✅ **CORS**: Configured for frontend integration
- ✅ **Pydantic**: Request/response validation
- ✅ **Auto Documentation**: Swagger UI at `/docs`
- ✅ **Async/Await**: Full async support throughout

## API Endpoints

### Public Endpoints
- `GET /` - Welcome message
- `GET /public-data` - Public data (works with or without auth)

### Authentication Required
- `GET /profile` - Get current user's profile
- `POST /profile` - Create or get user profile  
- `PUT /profile` - Update user profile
- `GET /dashboard` - Protected dashboard with user info

## Database Schema

### Profile Model
```python
class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(UUID, primary_key=True)  # Matches Supabase auth.users.id
    full_name = Column(String)
    credits = Column(Integer, default=100)
    stripe_customer_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

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

### 5. Testing

Run the test suite to verify everything is working:

```bash
python test_profile_flow.py
```

This will test:
- Public endpoints accessibility
- Authentication flow
- Profile creation and management
- Database operations

## Usage Examples

### Authentication Flow

1. **Sign up with Supabase** (using Supabase client SDK in your frontend)
2. **Get the access token** from Supabase
3. **Use the token** to access protected endpoints

### API Usage with curl

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
     -d '{"full_name": "Jane Doe", "credits": 150}'

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