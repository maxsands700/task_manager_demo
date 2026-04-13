"""
main.py — Application Entry Point
===================================

This is the starting point of our FastAPI application. When you run the server,
this is the file that gets executed.

Think of it like the front door of a restaurant:
    - main.py is the front door and host stand (receives all incoming requests)
    - routers are the different sections of the menu (tasks, users, etc.)
    - models are the recipes (how data is structured)
    - database.py is the kitchen's connection to the pantry (database)

HOW TO RUN THIS APP:
    From the backend/ directory, with your virtual environment activated:
        uvicorn main:app --reload

    Breaking that down:
        uvicorn     →  the web server that runs our FastAPI app
        main        →  this file (main.py)
        app         →  the FastAPI instance we create below
        --reload    →  auto-restart when you change code (development only!)

    Once running, visit:
        http://localhost:8000/docs  →  interactive API documentation (Swagger UI)
        http://localhost:8000       →  the API itself
"""

from fastapi import FastAPI
from database import engine, Base
from routers import tasks

# ---------------------------------------------------------------------------
# Step 1: Create the FastAPI application
# ---------------------------------------------------------------------------
# This creates our web application. FastAPI is a "framework" — it provides
# all the plumbing for handling HTTP requests, validating data, generating
# docs, etc. We just tell it what our endpoints are and what they do.
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Task Manager API",
    description="A simple CRUD API for managing tasks — built for learning!",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# Step 2: Create all database tables
# ---------------------------------------------------------------------------
# This line looks at all the models that inherit from Base (our Task model)
# and creates the corresponding tables in Postgres IF they don't already exist.
#
# It's equivalent to running this SQL in pgAdmin:
#   CREATE TABLE IF NOT EXISTS tasks (
#       id SERIAL PRIMARY KEY,
#       name VARCHAR(255) NOT NULL,
#       due_date DATE
#   );
#
# This runs once when the application starts up.
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Step 3: Register the routers
# ---------------------------------------------------------------------------
# This tells our FastAPI app: "include all the endpoints defined in the
# tasks router." Without this line, FastAPI wouldn't know those endpoints
# exist.
#
# If we later add a users router, we'd add another line:
#   app.include_router(users.router)
# ---------------------------------------------------------------------------
app.include_router(tasks.router)


# ---------------------------------------------------------------------------
# A simple root endpoint
# ---------------------------------------------------------------------------
# This gives us something to see when we visit http://localhost:8000/
# It's not required, but it's a nice way to verify the server is running.
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Task Manager API is running!"}
