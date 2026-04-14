# Task Manager Backend — Beginner's Guide

## What Are We Building?

A **REST API** (backend server) that lets you Create, Read, Update, and Delete tasks. There is no user interface yet — we interact with the API using **Postman** (to send requests) and **pgAdmin** (to see the data in the database).

Think of it like this:

```
 Postman (Client)           FastAPI (Server)             Postgres (Database)
┌──────────────┐          ┌──────────────────┐          ┌──────────────────┐
│              │  HTTP    │                  │  SQL     │                  │
│ Send request ├─────────►│ Process request  ├─────────►│ Store/retrieve   │
│ See response │◄─────────┤ Return response  │◄─────────┤ data             │
│              │  JSON    │                  │          │                  │
└──────────────┘          └──────────────────┘          └──────────────────┘
```

Later, when we build a frontend (React, etc.), it will take Postman's place — sending the same HTTP requests, just from a web page instead of a tool.

---

## How the Code is Organized

```
backend/
├── .env              ← Database credentials (never commit this to Git!)
├── requirements.txt  ← List of Python packages this project needs
├── main.py           ← Entry point — starts the server, wires everything together
├── database.py       ← Database connection setup (engine, sessions)
├── models.py         ← Database table definitions (what columns exist)
├── schemas.py        ← Request/response validation (what data looks like in the API)
└── routers/
    └── tasks.py      ← The actual API endpoints (GET, POST, PUT, DELETE)
```

### Why so many files? Why not put everything in one file?

You _could_ put everything in one file, and it would work. But as an app grows, a single file becomes impossible to navigate. Splitting by responsibility is a pattern called **Separation of Concerns**:

| File               | Responsibility                                   |
| ------------------ | ------------------------------------------------ |
| `database.py`      | "How do I connect to the database?"              |
| `models.py`        | "What do my database tables look like?"          |
| `schemas.py`       | "What data does the API accept and return?"      |
| `routers/tasks.py` | "What can the user actually do?" (the endpoints) |
| `main.py`          | "Wire it all together and start the server"      |

Each file has ONE job. When something breaks, you know exactly where to look.

### How do the files connect to each other?

```
main.py
  ├── imports from database.py    (to create tables on startup)
  └── imports from routers/tasks.py (to register the API endpoints)
        ├── imports from database.py   (to get database sessions)
        ├── imports from models.py     (to query the Task table)
        └── imports from schemas.py    (to validate request/response data)

database.py
  └── imported by models.py        (models inherit from Base)
```

---

## Getting Started

### Prerequisites

- Python 3.12 installed
- Postgres installed and running
- pgAdmin4 installed
- Postman installed

### 1. Create the database

Open **pgAdmin4** and create a new database called `task_manager`:

1. In the left sidebar, right-click **Databases** → **Create** → **Database**
2. Name it `task_manager`
3. Click **Save**

(The tables will be created automatically when you start the server.)

### 2. Set up your environment variables

The `.env.example` file contains the template for your database credentials. Copy it to create your own `.env` file:

```bash
cp .env.example .env
```

Then open `.env` in your editor and fill in your actual Postgres password. The `.env` file is listed in `.gitignore` so it will never be committed to Git — this keeps your password private.

### 3. Install dependencies

Open a terminal, navigate to the `backend/` folder, activate the virtual environment, and install:

```bash
# On Mac/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Then install packages:
pip install -r requirements.txt
```

### 4. Start the server

```bash
uvicorn main:app --reload
```

You should see output like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### 5. Verify it works

Open your browser and go to: **http://localhost:8000**

You should see: `{"message": "Task Manager API is running!"}`

Also try: **http://localhost:8000/docs** — this is auto-generated interactive documentation where you can test your endpoints directly in the browser.

---

## Testing with Postman

Open Postman and try each of these requests. Make sure your server is running first.

### Create a task

```
Method: POST
URL:    http://localhost:8000/tasks/
Body:   raw → JSON

{
    "name": "Buy groceries",
    "due_date": "2026-04-20"
}
```

Expected response (status 201):

```json
{
  "id": 1,
  "name": "Buy groceries",
  "due_date": "2026-04-20"
}
```

### Create a task without a due date

```
Method: POST
URL:    http://localhost:8000/tasks/
Body:   raw → JSON

{
    "name": "Learn FastAPI"
}
```

Expected response (status 201):

```json
{
  "id": 2,
  "name": "Learn FastAPI",
  "due_date": null
}
```

### Get all tasks

```
Method: GET
URL:    http://localhost:8000/tasks/
```

Expected response (status 200):

```json
[
  {
    "id": 1,
    "name": "Buy groceries",
    "due_date": "2026-04-20"
  },
  {
    "id": 2,
    "name": "Learn FastAPI",
    "due_date": null
  }
]
```

### Get one task

```
Method: GET
URL:    http://localhost:8000/tasks/1
```

Expected response (status 200):

```json
{
  "id": 1,
  "name": "Buy groceries",
  "due_date": "2026-04-20"
}
```

### Get a task that doesn't exist

```
Method: GET
URL:    http://localhost:8000/tasks/999
```

Expected response (status 404):

```json
{
  "detail": "Task not found"
}
```

### Update a task

```
Method: PUT
URL:    http://localhost:8000/tasks/1
Body:   raw → JSON

{
    "name": "Buy groceries and cook dinner",
    "due_date": "2026-04-21"
}
```

Expected response (status 200):

```json
{
  "id": 1,
  "name": "Buy groceries and cook dinner",
  "due_date": "2026-04-21"
}
```

### Delete a task

```
Method: DELETE
URL:    http://localhost:8000/tasks/1
```

Expected response: status 204 (no body — the task is gone)

---

## Viewing Data in pgAdmin

After creating some tasks via Postman, you can see them directly in the database:

1. Open **pgAdmin4**
2. In the left sidebar, expand: **Servers** → **PostgreSQL** → **Databases** → **task_manager** → **Schemas** → **public** → **Tables**
3. Right-click on **tasks** → **View/Edit Data** → **All Rows**

You'll see your tasks in a spreadsheet-like view. This is the raw data that your API reads from and writes to. Any task you create in Postman will show up here, and vice versa.

---

## Key Concepts Glossary

| Term                     | What it means                                                                                               |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- |
| **API**                  | Application Programming Interface — a way for programs to talk to each other. Our FastAPI server is an API. |
| **REST**                 | A convention for designing APIs using HTTP methods (GET, POST, PUT, DELETE) and URLs.                       |
| **CRUD**                 | Create, Read, Update, Delete — the four basic data operations.                                              |
| **Endpoint**             | A specific URL + HTTP method combo that does something (e.g., `GET /tasks`).                                |
| **ORM**                  | Object-Relational Mapper — lets you use Python objects instead of writing raw SQL. SQLAlchemy is our ORM.   |
| **Model**                | A Python class that represents a database table (defined in `models.py`).                                   |
| **Schema**               | A Python class that defines the shape of API request/response data (defined in `schemas.py`).               |
| **Dependency Injection** | FastAPI's way of automatically providing things (like a DB session) to your endpoint functions.             |
| **Migration**            | A versioned change to your database schema (we'll learn this later with Alembic).                           |
