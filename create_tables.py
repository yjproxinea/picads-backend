#!/usr/bin/env python3
"""
Script to drop all tables and recreate them with the correct schema
CAUTION: This will delete all data in your database!
"""

# Load environment first
import argparse
import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text

# Set up argument parser
parser = argparse.ArgumentParser(description='Create database tables with specified env file')
parser.add_argument('--env', type=str, help='Path to environment file', default='.env')
parser.add_argument('--enable-rls', action='store_true', help='Enable Row Level Security policies')
parser.add_argument('--no-env-file', action='store_true', help='Skip loading env file (use system env vars)')
args = parser.parse_args()

# Load environment variables
if args.no_env_file:
    print("🔧 Using system environment variables (no .env file)")
else:
    env_path = args.env
    if not os.path.exists(env_path):
        print(f"⚠️  Environment file {env_path} not found - falling back to system environment variables")
        print("   (This is normal for cloud deployments like Render)")
    else:
        print(f"📄 Loading environment from {env_path}")
        load_dotenv(env_path)

# Import after loading env
from app.config import settings
from app.database import Base, engine
from app.models import Credits, Profile, UsageLog, UserAds, UserAssets, UserKeys


def mask_password(url):
    """Mask password in URL for logging"""
    if not url:
        return "Not set"
    try:
        parts = url.split('@')
        if len(parts) > 1:
            user_pass = parts[0].split('//')[-1]
            if ':' in user_pass:
                user, password = user_pass.split(':', 1)
                masked = f"postgresql+asyncpg://{user}:****@{parts[1]}"
                return masked
        return url[:30] + "..."
    except:
        return "URL configured but format unclear"


async def test_connection():
    """Test database connection step by step"""
    print("🔍 Step 1: Testing configuration...")
    
    # Check environment variables
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'Not set')}")
    print(f"   Schema: {os.getenv('DATABASE_SCHEMA', 'Not set')}")
    print(f"   USER: {os.getenv('DB_USER', 'Not set')}")
    print(f"   PASSWORD: {'****' if os.getenv('DB_PASSWORD') else 'Not set'}")
    print(f"   HOST: {os.getenv('DB_HOST', 'Not set')}")
    print(f"   PORT: {os.getenv('DB_PORT', 'Not set')}")
    print(f"   DBNAME: {os.getenv('DB_NAME', 'Not set')}")
    
    # Check settings object
    print(f"\n🔍 Step 2: Testing settings object...")
    print(f"   Settings USER: {settings.DB_USER}")
    print(f"   Settings PASSWORD: {'****' if settings.DB_PASSWORD else 'Not set'}")
    print(f"   Settings HOST: {settings.DB_HOST}")
    print(f"   Settings PORT: {settings.DB_PORT}")
    print(f"   Settings DBNAME: {settings.DB_NAME}")
    
    # Check DATABASE_URL construction
    print(f"\n🔍 Step 3: Testing DATABASE_URL construction...")
    db_url = settings.DATABASE_URL
    print(f"   Constructed URL: {mask_password(db_url)}")
    
    if not db_url:
        print("   ❌ DATABASE_URL is None - missing required components")
        return False
    
    # Check if engine exists
    print(f"\n🔍 Step 4: Testing engine...")
    if not engine:
        print("   ❌ Engine is None - database not configured")
        return False
    
    print(f"   ✅ Engine created successfully")
    print(f"   Engine URL: {mask_password(str(engine.url))}")
    
    # Test connection
    print(f"\n🔍 Step 5: Testing actual connection...")
    try:
        async with engine.connect() as conn:
            print("   ✅ Connection successful!")
            
            # Test a simple query
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            print(f"   ✅ Query test successful: {test_value}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False
    
    finally:
        print("   🔧 Disposing engine...")
        await engine.dispose()


async def setup_rls_policies(conn, schema: str):
    """Setup Row Level Security policies for all tables"""
    print("🔐 Setting up Row Level Security (RLS) policies...")
    
    # Define table configurations for RLS
    rls_tables = [
        {
            'name': 'profiles',
            'user_column': 'user_id',
            'description': 'User profiles - users can only access their own profile'
        },
        {
            'name': 'credits', 
            'user_column': 'user_id',
            'description': 'User credits - users can only access their own credits'
        },
        {
            'name': 'usage_logs',
            'user_column': 'user_id', 
            'description': 'Usage logs - users can only access their own usage history'
        },
        {
            'name': 'user_ads',
            'user_column': 'user_id',
            'description': 'User ads - users can only access their own generated ads'
        },
        {
            'name': 'user_assets',
            'user_column': 'user_id',
            'description': 'User assets - users can only access their own uploaded assets'
        },
        {
            'name': 'brand_identities',
            'user_column': 'user_id',
            'description': 'Brand identities - users can only access their own brand identities'
        },
        {
            'name': 'user_keys',
            'user_column': 'user_id',
            'description': 'User API keys - users can only access their own API keys'
        }
    ]
    
    for table_config in rls_tables:
        table_name = table_config['name']
        user_column = table_config['user_column']
        description = table_config['description']
        
        print(f"   🔍 Setting up RLS for {table_name}...")
        
        try:
            # Full table name with schema
            full_table_name = f"{schema}.{table_name}" if schema != 'public' else table_name
            
            # 1. Enable RLS on the table
            enable_rls_query = f"ALTER TABLE {full_table_name} ENABLE ROW LEVEL SECURITY;"
            print(f"      🔍 Executing: {enable_rls_query}")
            await conn.execute(text(enable_rls_query))
            print(f"      ✅ RLS enabled for {table_name}")
            
            # 2. Drop existing policies (in case of re-runs)
            policies_to_drop = [
                f"policy_select_{table_name}",
                f"policy_insert_{table_name}", 
                f"policy_update_{table_name}",
                f"policy_delete_{table_name}"
            ]
            
            for policy_name in policies_to_drop:
                try:
                    drop_policy_query = f"DROP POLICY IF EXISTS {policy_name} ON {full_table_name};"
                    await conn.execute(text(drop_policy_query))
                except Exception as e:
                    # It's okay if policy doesn't exist
                    pass
            
            # 3. Create comprehensive RLS policies
            
            # SELECT policy - users can read their own data
            select_policy = f"""
            CREATE POLICY policy_select_{table_name} ON {full_table_name}
                FOR SELECT 
                USING ((SELECT auth.uid()) = {user_column});
            """
            await conn.execute(text(select_policy))

            # INSERT policy - users can insert their own data
            insert_policy = f"""
            CREATE POLICY policy_insert_{table_name} ON {full_table_name}
                FOR INSERT 
                WITH CHECK ((SELECT auth.uid()) = {user_column});
            """
            await conn.execute(text(insert_policy))

            # UPDATE policy - users can update their own data
            update_policy = f"""
            CREATE POLICY policy_update_{table_name} ON {full_table_name}
                FOR UPDATE 
                USING ((SELECT auth.uid()) = {user_column})
                WITH CHECK ((SELECT auth.uid()) = {user_column});
            """
            await conn.execute(text(update_policy))

            # DELETE policy - users can delete their own data
            delete_policy = f"""
            CREATE POLICY policy_delete_{table_name} ON {full_table_name}
                FOR DELETE 
                USING ((SELECT auth.uid()) = {user_column});
            """
            print(f"      🔍 Creating DELETE policy for {table_name}")
            await conn.execute(text(delete_policy))
            print(f"      ✅ DELETE policy created for {table_name}")
            
            print(f"   ✅ RLS fully configured for {table_name} - {description}")
            
        except Exception as e:
            print(f"   ❌ Error setting up RLS for {table_name}: {e}")
            import traceback
            traceback.print_exc()
            
    print("🔐 Row Level Security setup complete!")
    print("   📋 Summary of RLS policies created:")
    for table_config in rls_tables:
        table_name = table_config['name']
        print(f"      - {table_name}: SELECT, INSERT, UPDATE, DELETE policies based on user_id")
    
    print("\n   ⚠️  Important RLS Notes:")
    print("      - All policies use auth.uid() which requires Supabase authentication")
    print("      - Users can only access data where their auth.uid() matches the user_id column")
    print("      - Service role bypasses RLS policies for admin operations")
    print("      - Test RLS policies thoroughly in your application")


async def reset_database():
    """Drop all tables and recreate them"""
    print("🔍 Step 6: Starting database reset...")
    
    if not engine:
        print("❌ Database engine not configured. Please check your DATABASE_URL environment variable.")
        return
    
    # Get schema name
    schema = os.getenv('DATABASE_SCHEMA', 'public')
    
    print(f"🔄 Resetting database schema: {schema}")
    print("⚠️  This will delete ALL data in your database!")
    
    try:
        print("🔍 Step 7: Creating transaction...")
        async with engine.begin() as conn:
            print("   ✅ Transaction created successfully")
            
            print("🗑️  Dropping existing tables...")
            
            # Drop tables in reverse order to handle dependencies
            tables_to_drop = [
                'user_keys',
                'user_assets',
                'user_ads',
                'usage_logs', 
                'credits',
                'profiles',
                'brand_identities'
            ]
            
            for table in tables_to_drop:
                try:
                    if schema != 'public':
                        query = f'DROP TABLE IF EXISTS {schema}.{table} CASCADE'
                    else:
                        query = f'DROP TABLE IF EXISTS {table} CASCADE'
                    
                    print(f"   🔍 Executing: {query}")
                    await conn.execute(text(query))
                    print(f"   ✅ Dropped {table}")
                except Exception as e:
                    print(f"   ⚠️  Could not drop {table}: {e}")
            
            print("🏗️  Creating new tables...")
            print("   🔍 Running Base.metadata.create_all...")
            
            # Create all tables from models
            await conn.run_sync(Base.metadata.create_all)
            
            print("✅ Successfully recreated all database tables:")
            print(f"   - profiles (schema: {schema})")
            print(f"   - credits (schema: {schema})")
            print(f"   - usage_logs (schema: {schema})")
            print(f"   - user_ads (schema: {schema})")
            print(f"   - user_assets (schema: {schema})")
            print(f"   - brand_identities (schema: {schema})")
            print(f"   - user_keys (schema: {schema})")
            # Setup RLS if requested
            if args.enable_rls:
                print("\n" + "=" * 60)
                await setup_rls_policies(conn, schema)
            else:
                print("\n⚠️  RLS policies not enabled. Use --enable-rls flag to enable Row Level Security.")
            
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Close the engine
        print("🔧 Disposing engine...")
        await engine.dispose()


if __name__ == "__main__":
    print("🚀 Database Reset Script with Enhanced Debugging and RLS Support")
    print("=" * 60)
    
    if args.enable_rls:
        print("🔐 Row Level Security (RLS) will be enabled on all tables")
    else:
        print("ℹ️  RLS will NOT be enabled. Use --enable-rls to enable Row Level Security")
    
    print("=" * 60)
    
    # Test connection first
    print("Testing connection before reset...")
    connection_ok = asyncio.run(test_connection())
    
    if not connection_ok:
        print("\n❌ Connection test failed. Please fix the connection issues before proceeding.")
        exit(1)
    
    print("\n" + "=" * 60)
    print("Connection test passed! Proceeding with reset...")
    
    # Run the reset
    asyncio.run(reset_database())
    
    print("\n🎉 Database reset complete!")
    
    if args.enable_rls:
        print("✅ Row Level Security policies have been applied to all tables")
        print("⚠️  Make sure your application uses authenticated requests with proper JWT tokens")
    
    print("You can now start your application with: python main.py")