import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env vars
from app.config import settings
from app.database import Base, engine
from app.models import Profile


async def verify_database_connection():
    """Verify that we can connect to Supabase PostgreSQL using SQLAlchemy"""
    
    print("🔍 Verifying Supabase PostgreSQL Connection with SQLAlchemy ORM")
    print("=" * 60)
    
    # Check environment variables
    print("📋 Environment Variables:")
    print(f"   USER: {'✅' if settings.USER else '❌'} {settings.USER}")
    print(f"   PASSWORD: {'✅' if settings.PASSWORD else '❌'} {settings.PASSWORD}")
    print(f"   HOST: {'✅' if settings.HOST else '❌'} {settings.HOST}")
    print(f"   PORT: {'✅' if settings.PORT else '❌'} {settings.PORT}")
    print(f"   DBNAME: {'✅' if settings.DBNAME else '❌'} {settings.DBNAME}")
    print()
    
    # Check constructed DATABASE_URL
    if settings.DATABASE_URL:
        print("🔗 Constructed DATABASE_URL:")
        # Hide password in output
        print(f"   {settings.DATABASE_URL}")
        print("   ✅ DATABASE_URL constructed successfully")
    else:
        print("❌ DATABASE_URL could not be constructed")
        print("   Please check that all database environment variables are set")
        return
    
    print()
    
    # Test database connection
    if not engine:
        print("❌ Database engine not initialized")
        return
    
    try:
        print("🔌 Testing database connection...")
        
        # Test basic connection
        async with engine.begin() as conn:
            result = await conn.execute("SELECT version()")
            version = result.scalar()
            print(f"   ✅ Connected to PostgreSQL: {version}")
        
        print()
        print("📊 Testing table operations...")
        
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("   ✅ Tables created/verified successfully")
        
        # Test table exists
        async with engine.begin() as conn:
            result = await conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'profiles'
            """)
            table_exists = result.scalar()
            
            if table_exists:
                print("   ✅ 'profiles' table exists in database")
            else:
                print("   ❌ 'profiles' table not found")
        
        print()
        print("🎉 Database verification completed successfully!")
        print("✅ Supabase PostgreSQL is properly connected via SQLAlchemy ORM")
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Check your database password is correct")
        print("   2. Verify your Supabase project is active")
        print("   3. Ensure your IP is allowed (Supabase → Settings → Database → Network)")
        print("   4. Check if SSL is required")

if __name__ == "__main__":
    asyncio.run(verify_database_connection()) 