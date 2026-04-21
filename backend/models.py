"""
models.py — Database Table Definitions
=======================================

This file defines what our database tables look like using Python classes.

KEY CONCEPT: What is a "model"?
    In web development, a "model" is a Python class that represents a database table.
    Each instance (object) of the class represents one ROW in that table.
    Each attribute of the class represents one COLUMN in that table.

    For example, our Task model below maps to a "tasks" table in Postgres:
        - The class Task        →  the "tasks" TABLE
        - A Task(name="Buy milk") object  →  one ROW in that table
        - Task.name             →  the "name" COLUMN

KEY CONCEPT: Why define tables in Python instead of just using SQL?
    You COULD create tables directly in pgAdmin with SQL:
        CREATE TABLE tasks (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            due_date DATE
        );
    But by defining them as Python classes, SQLAlchemy can:
    1. Automatically create the tables for you when the app starts
    2. Give you Python objects to work with instead of raw data
    3. Keep your table structure in version control (Git) alongside your code
"""

from datetime import date, datetime
from typing import Optional
from sqlalchemy import Integer, String, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


# ---------------------------------------------------------------------------
# The Task Model
# ---------------------------------------------------------------------------
# This class defines the "tasks" table in our database.
#
# It inherits from Base (defined in database.py), which is how SQLAlchemy
# knows this is a database table and not just a regular Python class.
#
# __tablename__ tells SQLAlchemy what to name the actual table in Postgres.
# Convention is to use lowercase, plural names (e.g., "tasks" not "Task").
# ---------------------------------------------------------------------------
class Task(Base):
    __tablename__ = "tasks"

    # -----------------------------------------------------------------------
    # Columns
    # -----------------------------------------------------------------------
    # Each line below defines a column in the "tasks" table.
    #
    # The type hint (e.g., Mapped[int]) tells Python what type to expect.
    # The mapped_column() call tells SQLAlchemy how to configure the column
    # in the actual database.
    #
    # id: The primary key — a unique identifier for each task.
    #     - Integer: stored as a whole number in Postgres
    #     - primary_key=True: makes this the unique ID for each row
    #     - autoincrement=True: Postgres will automatically assign 1, 2, 3...
    #       so you never have to provide an ID yourself when creating a task
    #
    # name: The task's name/title.
    #     - String(255): a text column with a max length of 255 characters
    #     - nullable=False: this column is REQUIRED (can't be left blank)
    #       If someone tries to create a task without a name, the database
    #       will reject it
    #
    # due_date: When the task is due.
    #     - Date: stored as a date (year-month-day) in Postgres
    #     - Optional[date] + nullable=True (the default): this column is
    #       OPTIONAL — not every task needs a due date
    # -----------------------------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # -----------------------------------------------------------------------
    # Timestamps: created_at and updated_at
    # -----------------------------------------------------------------------
    # Almost every real-world database table has these two columns. They let
    # you answer questions like "when was this task created?" or "sort tasks
    # by most recently edited" without having to write that logic yourself.
    #
    # DateTime(timezone=True):
    #   Stores a full timestamp (year, month, day, hour, minute, second)
    #   INCLUDING timezone info. Always use timezone-aware timestamps in a
    #   real app — otherwise you'll eventually hit bugs where a user in
    #   New York sees a time that was actually recorded in UTC.
    #
    # server_default=func.now():
    #   "When a new row is inserted, ask the DATABASE for the current time
    #   and use it as the default."
    #   func.now() becomes SQL's NOW() function — so Postgres itself fills
    #   in the value. This is better than filling it in from Python because:
    #     1. Every row gets a consistent time from one clock (the DB's)
    #     2. You can't forget to set it — the DB enforces it for you
    #
    # onupdate=func.now() (on updated_at only):
    #   "Every time this row is UPDATED via SQLAlchemy, set this column to
    #   the current time." This is what makes updated_at automatically
    #   refresh whenever we edit a task. You don't have to remember to
    #   update it yourself in your endpoint code.
    #
    # nullable=False:
    #   These columns are never empty. The database enforces that.
    #
    # IMPORTANT — EXISTING DATABASES:
    #   Since this project uses Base.metadata.create_all() (which only
    #   CREATES tables, it doesn't ALTER existing ones), adding these
    #   columns won't automatically show up if your "tasks" table already
    #   exists. You'll either need to:
    #     (a) Drop the tasks table in pgAdmin so the app recreates it, OR
    #     (b) Run this SQL in pgAdmin to add the columns manually:
    #         ALTER TABLE tasks
    #           ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    #           ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
    #   Later you'll learn about Alembic, which handles these "migrations"
    #   automatically.
    # -----------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
