#!/usr/bin/env python3
"""
Database creation script for Hospital Management System.
Run this script to create the MySQL database and tables.
"""

import pymysql
from sqlalchemy import create_engine
from config.config import config
import os

def create_database():
    """Create the MySQL database if it doesn't exist."""
    config_obj = config[os.environ.get('FLASK_ENV', 'development')]
    
    # Connection without database name
    connection_string = f"mysql+pymysql://{config_obj.DB_USER}:{config_obj.DB_PASSWORD}@{config_obj.DB_HOST}:{config_obj.DB_PORT}/"
    
    try:
        # Create engine without database
        engine = create_engine(connection_string)
        
        with engine.connect() as connection:
            # Create database
            connection.execute(f"CREATE DATABASE IF NOT EXISTS {config_obj.DB_NAME}")
            print(f"Database '{config_obj.DB_NAME}' created successfully!")
            
            # Grant privileges (adjust as needed)
            connection.execute(f"GRANT ALL PRIVILEGES ON {config_obj.DB_NAME}.* TO '{config_obj.DB_USER}'@'%'")
            connection.execute("FLUSH PRIVILEGES")
            print("Database privileges granted!")
        
        engine.dispose()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
    
    return True

def create_tables():
    """Create all tables using Flask-SQLAlchemy."""
    from app import create_app
    from app.models import db
    
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("All tables created successfully!")
            return True
        except Exception as e:
            print(f"Error creating tables: {e}")
            return False

def main():
    """Main function to set up the database."""
    print("Setting up Hospital Management System Database...")
    print("=" * 50)
    
    # Step 1: Create database
    print("Step 1: Creating database...")
    if not create_database():
        print("Failed to create database. Exiting.")
        return
    
    # Step 2: Create tables
    print("\nStep 2: Creating tables...")
    if not create_tables():
        print("Failed to create tables. Exiting.")
        return
    
    print("\n" + "=" * 50)
    print("Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Run 'python run.py seed_db' to add initial data")
    print("2. Start the application with 'python run.py'")

if __name__ == "__main__":
    main()