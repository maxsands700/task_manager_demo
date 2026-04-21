"""
schemas.py — Request & Response Shapes (Pydantic Schemas)
==========================================================

This file defines the "shape" of data that flows in and out of our API.

KEY CONCEPT: Why do we need BOTH models.py AND schemas.py?
    This is one of the most common questions beginners have, and it's a great one.

    - models.py (SQLAlchemy models) define what the DATABASE tables look like.
      They handle storing and retrieving data from Postgres.

    - schemas.py (Pydantic schemas) define what the API REQUEST and RESPONSE
      data looks like. They handle validating incoming data and formatting
      outgoing data.

    WHY SEPARATE THEM? Because the data you send to/from the API is often
    different from what's stored in the database:

    Example — Creating a task:
        What the client SENDS (request):  {"name": "Buy milk", "due_date": "2026-04-20"}
        What the DATABASE stores:          id=1, name="Buy milk", due_date=2026-04-20
        What the client GETS BACK (response): {"id": 1, "name": "Buy milk", "due_date": "2026-04-20"}

    Notice the client never sends an "id" — the database generates it. But the
    client DOES get an "id" back in the response. So we need different schemas
    for the request vs. the response.

KEY CONCEPT: What is Pydantic?
    Pydantic is a data validation library. When someone sends a request to your
    API, Pydantic automatically:
    1. Checks that all required fields are present
    2. Checks that each field is the correct type (e.g., "name" is a string)
    3. Returns a clear error message if anything is wrong

    Without Pydantic, you'd have to write all that validation code yourself.
    FastAPI uses Pydantic under the hood — they're designed to work together.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# TaskCreate — The shape of data when CREATING or UPDATING a task
# ---------------------------------------------------------------------------
# This is what the client sends in the request body (as JSON).
# Notice there's no "id" field — the database assigns that automatically.
#
# Fields:
#   name:     Required — every task needs a name
#   due_date: Optional — defaults to None if not provided
# ---------------------------------------------------------------------------
class TaskCreate(BaseModel):
    name: str
    due_date: Optional[date] = None


# ---------------------------------------------------------------------------
# TaskUpdate — The shape of data when PARTIALLY UPDATING a task (PATCH)
# ---------------------------------------------------------------------------
# This schema looks almost identical to TaskCreate, but EVERY field is
# optional. That's the whole point of PATCH: the client only sends the
# fields they want to change, and leaves the rest alone.
#
# KEY CONCEPT: PUT vs PATCH
#   PUT   = "Replace the whole resource." Client must send ALL fields.
#           If they forget one, it gets wiped (or fails validation).
#   PATCH = "Change only these specific fields." Client sends just the
#           fields they want to update. Everything else stays as-is.
#
#   Example — a task currently has name="Buy milk", due_date="2026-04-20":
#     PATCH body {"name": "Buy oat milk"}
#       → name becomes "Buy oat milk", due_date stays "2026-04-20"
#     PUT body {"name": "Buy oat milk"}
#       → name becomes "Buy oat milk", due_date gets wiped to None
#         (because the client didn't include it)
#
# Why the fields default to None:
#   If a client omits a field from the JSON body, Pydantic uses the default
#   (None). In the endpoint we'll use .model_dump(exclude_unset=True) to
#   tell the difference between "client sent null on purpose" and "client
#   didn't send this field at all."
# ---------------------------------------------------------------------------
class TaskUpdate(BaseModel):
    name: Optional[str] = None
    due_date: Optional[date] = None


# ---------------------------------------------------------------------------
# TaskResponse — The shape of data we SEND BACK to the client
# ---------------------------------------------------------------------------
# This includes the "id" field because once a task exists in the database,
# the client needs to know its ID (to update or delete it later).
#
# It also includes created_at and updated_at so the client can see WHEN a
# task was made and last changed. These come straight from the database —
# we never accept them in a request body; they're server-generated.
#
# model_config = ConfigDict(from_attributes=True)
#   This is a Pydantic setting that tells it: "When converting a SQLAlchemy
#   model object into this schema, read the data from the object's attributes."
#
#   Without this, Pydantic wouldn't know how to convert a SQLAlchemy Task
#   object into a TaskResponse — it would expect a plain dictionary.
#   With this setting, it can read task.id, task.name, task.due_date directly
#   from the SQLAlchemy object.
# ---------------------------------------------------------------------------
class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    due_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
