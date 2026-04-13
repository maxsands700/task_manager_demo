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

from datetime import date
from typing import Optional
from sqlalchemy import Integer, String, Date
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
