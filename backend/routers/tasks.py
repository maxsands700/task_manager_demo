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

from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Task
from schemas import TaskCreate, TaskResponse, TaskUpdate

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
#
# KEY CONCEPT: Query parameters
#   A "query parameter" is a filter you tack onto the end of a URL after a "?".
#   Multiple parameters are separated by "&". For example:
#       GET /tasks?min_date=2026-05-01
#       GET /tasks?min_date=2026-05-01&something_else=foo
#
#   Unlike path parameters ({task_id}), query parameters are OPTIONAL by
#   default when you give them a default value (like None below).
#
#   FastAPI reads the function argument "min_date: Optional[date] = None"
#   and automatically:
#     1. Looks for "min_date" in the URL's query string
#     2. If present, parses it as a date (e.g., "2026-05-01" → date(2026, 5, 1))
#     3. If the value isn't a valid date, returns a 422 error automatically
#     4. If absent, uses None — meaning "don't filter by date"
#
#   Query(None, description=...) is optional — it just adds a helpful
#   description to the auto-generated docs at /docs.
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[TaskResponse])
def get_all_tasks(
    db: Session = Depends(get_db),
    min_date: Optional[date] = Query(
        None,
        description="Only return tasks with a due_date on or after this date (YYYY-MM-DD).",
    ),
    search: Optional[str] = Query(
        None,
        description="Only return tasks whose name contains this text (case-insensitive).",
    ),
    # -----------------------------------------------------------------------
    # Sorting parameters
    # -----------------------------------------------------------------------
    # sort_by: which column to sort on. We use typing.Literal to restrict
    #   the allowed values — FastAPI will automatically reject anything
    #   that isn't one of these names with a clear 422 error.
    #
    #   WHY RESTRICT THE VALUES? If we let the client pass ANY string and
    #   then did getattr(Task, sort_by), they could sneak in attribute
    #   names we didn't intend (like internal SQLAlchemy methods). Always
    #   whitelist when you're turning user input into column references.
    #
    # order: "asc" (ascending: A→Z, 1→9, oldest→newest) or
    #        "desc" (descending: Z→A, 9→1, newest→oldest).
    # -----------------------------------------------------------------------
    sort_by: Literal["id", "name", "due_date", "created_at", "updated_at"] = Query(
        "id",
        description="Which column to sort by.",
    ),
    order: Literal["asc", "desc"] = Query(
        "asc",
        description="Sort direction — 'asc' (ascending) or 'desc' (descending).",
    ),
    # -----------------------------------------------------------------------
    # Pagination parameters
    # -----------------------------------------------------------------------
    # KEY CONCEPT: What is pagination?
    #   If your database has 10,000 tasks, you don't want to send all of
    #   them back in a single response — it would be slow and use a lot of
    #   memory on both server and client. Pagination lets the client ask
    #   for one "page" at a time.
    #
    # limit: the MAXIMUM number of tasks to return in one response.
    #   e.g., limit=20 means "give me at most 20 tasks".
    #
    # offset: how many tasks to SKIP before starting to return results.
    #   This is how you get "the next page." To get:
    #     Page 1 (tasks 1–20):   limit=20, offset=0
    #     Page 2 (tasks 21–40):  limit=20, offset=20
    #     Page 3 (tasks 41–60):  limit=20, offset=40
    #   General formula: offset = (page_number - 1) * limit
    #
    # ge=0 / ge=1 / le=100:
    #   FastAPI validates these at the edges. "ge" = "greater than or
    #   equal to", "le" = "less than or equal to". So limit must be
    #   between 1 and 100, and offset can't be negative. If a client
    #   sends limit=9999, they get a 422 error instead of crashing our DB.
    # -----------------------------------------------------------------------
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Maximum number of tasks to return (1–100).",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of tasks to skip before returning results.",
    ),
):
    """Return tasks from the database, with optional filtering, sorting, and pagination."""
    query = db.query(Task)

    # If the client provided min_date, add a WHERE clause to filter the results.
    # Task.due_date >= min_date becomes SQL like: WHERE due_date >= '2026-05-01'
    # Tasks with a NULL due_date are excluded by this comparison (SQL NULLs
    # never match a >= comparison), which is the behavior we want here.
    if min_date is not None:
        query = query.filter(Task.due_date >= min_date)

    # If the client provided a search term, add a case-insensitive
    # "contains" filter on the task name. ilike() is SQL's case-insensitive
    # LIKE operator, and the "%" characters are wildcards meaning "any
    # characters." So ilike("%milk%") matches "Buy milk", "MILK run",
    # "almond milk", etc.
    if search is not None:
        query = query.filter(Task.name.ilike(f"%{search}%"))

    # -----------------------------------------------------------------------
    # Apply sorting
    # -----------------------------------------------------------------------
    # getattr(Task, "name") is the same as writing Task.name — it just lets
    # us choose the column dynamically based on the string the client sent.
    # Because we restricted sort_by to a Literal above, we know it's always
    # a valid column name and this is safe.
    #
    # .asc() / .desc() are SQLAlchemy methods that turn a column into a
    # sort expression. query.order_by(Task.name.asc()) becomes SQL like:
    #   ORDER BY name ASC
    # -----------------------------------------------------------------------
    sort_column = getattr(Task, sort_by)
    sort_expression = sort_column.asc() if order == "asc" else sort_column.desc()
    query = query.order_by(sort_expression)

    # -----------------------------------------------------------------------
    # Apply pagination
    # -----------------------------------------------------------------------
    # .offset() and .limit() translate directly to SQL's OFFSET and LIMIT
    # clauses. They must come AFTER order_by() so the "page" you get back
    # is consistent — otherwise the database could return rows in any order
    # and "page 2" wouldn't mean anything.
    # -----------------------------------------------------------------------
    query = query.offset(offset).limit(limit)

    return query.all()


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
# PATCH /tasks/{task_id} — Partially update an existing task
# ---------------------------------------------------------------------------
# PATCH is PUT's more surgical sibling. Instead of requiring the client to
# send the WHOLE task, PATCH lets them send only the fields they want to
# change.
#
# Compare the two:
#   PUT   /tasks/5  body: {"name": "Buy oat milk", "due_date": "2026-04-22"}
#                   → replaces the whole task (must include every field)
#   PATCH /tasks/5  body: {"name": "Buy oat milk"}
#                   → only updates "name", leaves "due_date" unchanged
#
# The key trick below is model_dump(exclude_unset=True):
#   - model_dump() normally returns a dict of ALL fields in the schema,
#     filling in defaults for any the client didn't send.
#   - exclude_unset=True tells Pydantic: "only include fields the client
#     ACTUALLY sent in the JSON body."
#   That's exactly what we want for PATCH — if the client didn't mention
#   "due_date", we don't want to touch it.
# ---------------------------------------------------------------------------
@router.patch("/{task_id}", response_model=TaskResponse)
def patch_task(task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db)):
    """Partially update an existing task — only the fields the client sends will change."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get only the fields the client actually provided in the request body.
    # If they sent {"name": "New"}, update_data will be {"name": "New"} —
    # "due_date" is NOT in the dict, so we won't touch it.
    update_data = task_data.model_dump(exclude_unset=True)

    # Same setattr loop as PUT, but now it only iterates over fields the
    # client sent. Untouched fields on the existing task keep their values.
    for field, value in update_data.items():
        setattr(task, field, value)

    # Note: we don't need to manually set updated_at here — the model has
    # onupdate=func.now() on that column, so SQLAlchemy updates it for us
    # automatically when we commit.
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
