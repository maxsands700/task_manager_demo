"""
routers/tasks.py — Task API Endpoints (CRUD)
=============================================

This file contains all the API endpoints (routes) for managing tasks.
Each endpoint handles one specific operation: Create, Read, Update, or Delete.

KEY CONCEPT: What is CRUD?
    CRUD stands for Create, Read, Update, Delete — the four basic operations
    you can perform on any data. Almost every app you use does CRUD:
    - Instagram: Create a post, Read your feed, Update your bio, Delete a photo
    - Notes app: Create a note, Read notes, Update a note, Delete a note
    - This app: Create a task, Read tasks, Update a task, Delete a task

KEY CONCEPT: What is REST?
    REST is a set of conventions for how to design your API URLs and HTTP methods.
    Instead of inventing random URLs, REST gives you a predictable pattern:

    HTTP Method  |  URL             |  What it does
    -------------|------------------|---------------------------
    GET          |  /tasks          |  Get ALL tasks
    GET          |  /tasks/5        |  Get ONE task (id=5)
    POST         |  /tasks          |  CREATE a new task
    PUT          |  /tasks/5        |  UPDATE task with id=5
    DELETE       |  /tasks/5        |  DELETE task with id=5

    Notice the pattern: the URL tells you WHAT (tasks), and the HTTP method
    tells you the ACTION (get, create, update, delete). This is what you'll
    see when you set up requests in Postman.

KEY CONCEPT: What is a Router?
    A router groups related endpoints together. We put all task-related
    endpoints in this one file/router. If we later add "users" or "projects",
    each would get their own router file. This keeps the code organized as
    the app grows.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Task
from schemas import TaskCreate, TaskResponse

# ---------------------------------------------------------------------------
# Create the Router
# ---------------------------------------------------------------------------
# prefix="/tasks" means all routes in this file start with /tasks.
# So a route defined as "/" below actually becomes "/tasks" in the full URL.
# And "/{task_id}" becomes "/tasks/5" (for example).
#
# tags=["Tasks"] is just for documentation — it groups these endpoints
# together in the auto-generated docs at http://localhost:8000/docs
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ---------------------------------------------------------------------------
# GET /tasks — List all tasks
# ---------------------------------------------------------------------------
# response_model=list[TaskResponse] tells FastAPI:
#   "The response will be a LIST of TaskResponse objects"
#   FastAPI uses this to automatically format the response as JSON.
#
# db: Session = Depends(get_db) is "dependency injection":
#   Instead of creating a database session ourselves, we tell FastAPI
#   "please run get_db() and give me the result as 'db'."
#   FastAPI handles creating the session before our function runs
#   and closing it after our function finishes.
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db)):
    """Return every task in the database."""
    tasks = db.query(Task).all()
    return tasks


# ---------------------------------------------------------------------------
# GET /tasks/{task_id} — Get one specific task
# ---------------------------------------------------------------------------
# {task_id} in the URL is a "path parameter" — it captures whatever value
# is in that position. So GET /tasks/3 means task_id=3.
#
# FastAPI automatically converts it to an int because of the type hint.
# If someone sends GET /tasks/abc, FastAPI returns a 422 error automatically.
#
# If no task is found, we raise an HTTPException with status 404 (Not Found).
# HTTP status codes are how the server tells the client what happened:
#   200 = OK (success)
#   201 = Created (something new was made)
#   204 = No Content (success, but nothing to send back — used for deletes)
#   404 = Not Found (the thing you asked for doesn't exist)
#   422 = Unprocessable Entity (the data you sent was invalid)
# ---------------------------------------------------------------------------
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Return a single task by its ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ---------------------------------------------------------------------------
# POST /tasks — Create a new task
# ---------------------------------------------------------------------------
# status_code=201 means "Created" — the standard response code when a new
# resource is successfully created.
#
# task_data: TaskCreate — FastAPI reads the JSON request body and
# automatically validates it against the TaskCreate schema. If the client
# forgets to include "name", Pydantic returns a clear error message.
#
# The flow:
#   1. Client sends JSON: {"name": "Buy milk", "due_date": "2026-04-20"}
#   2. FastAPI validates it with TaskCreate (Pydantic)
#   3. We create a SQLAlchemy Task object from that data
#   4. We add it to the session, commit (save) to the database
#   5. We refresh the object to get the auto-generated id
#   6. We return the task (now with its id) as the response
# ---------------------------------------------------------------------------
@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    # model_dump() converts the Pydantic schema into a plain dictionary:
    # {"name": "Buy milk", "due_date": "2026-04-20"}
    # The ** unpacks that dictionary into keyword arguments for Task():
    # Task(name="Buy milk", due_date="2026-04-20")
    new_task = Task(**task_data.model_dump())

    db.add(new_task)       # Stage the new task (like "git add")
    db.commit()            # Save to the database (like "git commit")
    db.refresh(new_task)   # Reload from DB to get the auto-generated id

    return new_task


# ---------------------------------------------------------------------------
# PUT /tasks/{task_id} — Update an existing task
# ---------------------------------------------------------------------------
# PUT replaces the entire resource with new data. The client sends the full
# updated task, and we overwrite the existing fields.
#
# Steps:
#   1. Find the task by ID (return 404 if not found)
#   2. Loop through the fields in the request body
#   3. Update each field on the existing task object using setattr()
#   4. Commit the changes to the database
# ---------------------------------------------------------------------------
@router.put("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_data: TaskCreate, db: Session = Depends(get_db)):
    """Update an existing task by its ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # setattr(task, "name", "New name") is the same as task.name = "New name"
    # We loop through each field so we don't have to write one line per field.
    for field, value in task_data.model_dump().items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


# ---------------------------------------------------------------------------
# DELETE /tasks/{task_id} — Delete a task
# ---------------------------------------------------------------------------
# status_code=204 means "No Content" — the standard response when something
# is successfully deleted. We don't need to send any data back because the
# resource no longer exists.
# ---------------------------------------------------------------------------
@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task by its ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
