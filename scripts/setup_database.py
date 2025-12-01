#!/usr/bin/env python3
"""
Setup script - Initialize database and create tables

Usage:
    python setup_database.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from backend.core.database import engine, test_connection, init_db
from backend.models.db_models import Base
from sqlalchemy import text


def setup():
    """Setup database and create tables"""
    print("=" * 80)
    print("DATABASE SETUP")
    print("=" * 80)
    
    # Test connection
    print("\n1. Testing database connection...")
    if not test_connection():
        print("❌ Cannot connect to database. Please check:")
        print("   - PostgreSQL is running")
        print("   - DATABASE_URL in .env is correct")
        print("   - Database 'real_estate_risk' exists")
        print("\nTo create the database, run:")
        print("   psql -U postgres -c 'CREATE DATABASE real_estate_risk;'")
        sys.exit(1)
    
    # Create tables
    print("\n2. Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
        
        # Show created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            print(f"\n📊 Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
    
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)
    
    # Create indexes
    print("\n3. Creating indexes...")
    try:
        with engine.connect() as conn:
            # Additional indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_fecha_year ON transactions(year_radica, fecha_radicacion);",
                "CREATE INDEX IF NOT EXISTS idx_valor_range ON transactions(valor_acto) WHERE valor_acto IS NOT NULL;",
            ]
            for idx_sql in indexes:
                conn.execute(text(idx_sql))
            conn.commit()
        
        print("✅ Indexes created successfully")
    
    except Exception as e:
        print(f"⚠️  Warning creating indexes: {e}")
    
    print("\n" + "=" * 80)
    print("✅ DATABASE SETUP COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run ETL pipeline:")
    print("   python data/etl_pipeline.py --input path/to/your/8gb-file.csv")
    print("\n2. Train ML models:")
    print("   python ml/train_from_db.py --sample-size 100000")
    print("\n3. Start backend:")
    print("   cd backend && uvicorn main_simple:app --reload")
    print("=" * 80)


if __name__ == "__main__":
    setup()
