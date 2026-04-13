"""
database.py — Database Connection Setup
========================================

This file is responsible for connecting our Python application to our Postgres database.
Think of it as the "bridge" between your Python code and your database.

KEY CONCEPT: Why do we need this file?
    Your FastAPI app (Python) and your Postgres database are two completely separate programs.
    They don't automatically know about each other. This file sets up the connection between
    them using a library called SQLAlchemy.

KEY CONCEPT: What is SQLAlchemy?
    SQLAlchemy is an ORM (Object-Relational Mapper). Instead of writing raw SQL like:
        SELECT * FROM tasks WHERE id = 1;
    You write Python code like:
        db.query(Task).filter(Task.id == 1).first()

    The ORM translates your Python code into SQL behind the scenes. This is nice because:
    1. You get to stay in Python-land (no switching between languages)
    2. You get autocompletion and type checking from your editor
    3. It helps prevent SQL injection attacks (a common security vulnerability)
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ---------------------------------------------------------------------------
# Step 1: Load environment variables from the .env file
# ---------------------------------------------------------------------------
# We keep sensitive info (passwords, hostnames) in a .env file rather than
# hardcoding them. This is a security best practice — you never want database
# passwords committed to Git where anyone can see them.
# The load_dotenv() function reads the .env file and makes those values
# available via os.getenv().
# ---------------------------------------------------------------------------
load_dotenv()

PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DATABASE = os.getenv("PG_DATABASE")

# ---------------------------------------------------------------------------
# Step 2: Build the database URL
# ---------------------------------------------------------------------------
# SQLAlchemy needs a "connection string" (also called a database URL) to know
# where and how to connect. The format is:
#   postgresql://username:password@host:port/database_name
#
# This is the same info you'd type into pgAdmin when setting up a connection —
# just formatted as a single string.
# ---------------------------------------------------------------------------
DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"

# ---------------------------------------------------------------------------
# Step 3: Create the Engine
# ---------------------------------------------------------------------------
# The "engine" is SQLAlchemy's core connection to the database. Think of it
# like a phone line between your app and Postgres — it manages the actual
# network connection and sends SQL statements over it.
#
# You typically create ONE engine for your entire application and reuse it.
# ---------------------------------------------------------------------------
engine = create_engine(DATABASE_URL)

# ---------------------------------------------------------------------------
# Step 4: Create a Session Factory
# ---------------------------------------------------------------------------
# A "session" is a temporary workspace for talking to the database. Each time
# your API handles a request, it opens a session, does its database work
# (read, create, update, delete), and then closes the session.
#
# sessionmaker() doesn't create a session right away — it creates a "factory"
# (a function) that will produce new sessions whenever we call it.
#
# autocommit=False: We want to control when changes are saved (committed).
# autoflush=False:  We want to control when pending changes are sent to the DB.
# bind=engine:      Tells sessions to use our engine (our database connection).
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Step 5: Create a Base class for our models
# ---------------------------------------------------------------------------
# Every database table we define in Python will be a class that inherits from
# this Base class. It's how SQLAlchemy knows "this class represents a database
# table" vs. a regular Python class.
#
# We'll use this in models.py when defining our Task table.
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Step 6: Create a dependency that provides a database session
# ---------------------------------------------------------------------------
# This function is a "dependency" — a concept in FastAPI where you can
# automatically provide something (like a database session) to your endpoint
# functions without them having to create it themselves.
#
# HOW IT WORKS:
#   1. When an API request comes in, FastAPI calls get_db()
#   2. get_db() creates a new database session
#   3. "yield" pauses the function and hands the session to your endpoint
#   4. Your endpoint does its work with the session
#   5. After your endpoint finishes, execution resumes AFTER the yield
#   6. The "finally" block runs, closing the session and freeing resources
#
# WHY "yield" INSTEAD OF "return"?
#   "return" would end the function immediately — we'd never get to close
#   the session. "yield" lets us run cleanup code AFTER the endpoint is done.
#   The "finally" block guarantees the session closes even if an error occurs.
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
