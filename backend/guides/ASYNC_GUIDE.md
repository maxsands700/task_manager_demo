# Async vs. Sync in FastAPI — A Beginner's Guide

This guide explains one of the most important ideas in modern backend development: the difference between **synchronous** and **asynchronous** code, and why FastAPI is designed around the async model.

We'll look at the task manager we've built so far (which is currently fully synchronous), and rewrite it to take advantage of FastAPI's async capabilities. Along the way, we'll explain what actually changes, why it matters, and when it doesn't.

---

## Table of Contents

1. [The one-sentence version](#the-one-sentence-version)
2. [A real-world analogy: the coffee shop](#a-real-world-analogy-the-coffee-shop)
3. [What is "blocking" code?](#what-is-blocking-code)
4. [How FastAPI actually handles requests](#how-fastapi-actually-handles-requests)
5. [Before: our current synchronous codebase](#before-our-current-synchronous-codebase)
6. [After: the async version of the same code](#after-the-async-version-of-the-same-code)
7. [Side-by-side diffs](#side-by-side-diffs)
8. [Why it matters: a concrete example](#why-it-matters-a-concrete-example)
9. [The rules of async](#the-rules-of-async)
10. [When NOT to use async](#when-not-to-use-async)
11. [Glossary](#glossary)

---

## The one-sentence version

> **Synchronous code does one thing at a time. Asynchronous code can pause a slow operation (like waiting on the database) and work on other requests while it waits.**

FastAPI is called "Fast" because it's built on an **async** foundation — but if you write your endpoints as regular (synchronous) functions, you don't get the speed benefits. Our current codebase is a perfectly functional FastAPI app, but it is synchronous top-to-bottom. Let's see what that means and how to change it.

---

## A real-world analogy: the coffee shop

Imagine you're a barista. You have a line of 10 customers.

### Synchronous barista (our current code)

You take Customer 1's order: a latte.
You put milk on the steamer. The steamer takes **40 seconds**.

You stand there. You stare at the steamer. You do nothing for 40 seconds.

The steamer beeps. You finish the latte. Customer 1 leaves.
You start on Customer 2. Repeat.

Total time for 10 customers: **~7 minutes**, most of which is you standing still.

### Asynchronous barista (FastAPI async)

You take Customer 1's order. You start the steamer. Instead of staring at it, you say "I'll come back when it beeps."

You take Customer 2's order. You start their espresso shot. That takes 25 seconds — you start it and say "I'll come back when it's ready."

Customer 1's steamer beeps. You go back, finish the latte, hand it off.
Customer 2's shot is done. You go back, finish that drink.
Take Customer 3's order. And so on.

You were never doing two things *at the exact same moment* — you were just never idle.

Total time for 10 customers: **~2 minutes.**

**Key insight:** the barista didn't get faster. The _drinks_ didn't get faster. What got faster was how quickly the queue cleared, because the barista stopped wasting time waiting.

That is exactly what async does for a web server.

---

## What is "blocking" code?

A line of code is called **blocking** if the program can't do anything else while that line runs.

In our current `tasks.py`, this is a blocking line:

```python
task = db.query(Task).filter(Task.id == task_id).first()
```

When Python hits this line, it:

1. Opens a network connection to Postgres
2. Sends a SQL query over the wire
3. **Waits** for Postgres to execute the query
4. **Waits** for the results to come back
5. Parses them into a Python object

Steps 3 and 4 are the slow parts. They might take 5–50 milliseconds. While they're happening, Python is just sitting there waiting. The CPU is idle. _Other incoming requests_ are stuck in line.

That's the "standing at the steamer" moment. Async is what lets the Python process step away and handle another request during that wait.

---

## How FastAPI actually handles requests

FastAPI runs on top of an async server called **Uvicorn**. Uvicorn has a single thing called an **event loop** — think of it as the barista in the analogy above.

```
           ┌──────────────────────────────────────────┐
           │         Uvicorn event loop               │
           │  (one thread, handles many requests)     │
           └──────────────┬───────────────────────────┘
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
   request A          request B          request C
  (GET /tasks/1)   (POST /tasks)      (GET /tasks/2)
```

The event loop is _single-threaded_. There is literally one worker. But because it can **pause** a request at any `await` point and pick up another one, it can juggle hundreds or thousands of requests at once — provided each request spends most of its time waiting on something (a database, an API, a file).

### What happens when your endpoint is `def` (synchronous)

FastAPI sees a regular `def` function and thinks: "uh oh, this might block the event loop." So it quietly hands the function off to a **thread pool** — a small pool of background workers (by default, 40). Your function runs on one of those workers, and the event loop is free to keep working.

This is why our current synchronous code _works_. FastAPI protects you. But:

- The thread pool is limited. Once all 40 workers are busy, new requests queue up.
- Threads are more expensive than event-loop switches (memory, context switching).
- You lose the whole "handle thousands of concurrent connections" superpower.

### What happens when your endpoint is `async def`

FastAPI runs the function directly on the event loop. As long as every slow operation in the function is `await`ed, the event loop can freely jump between requests during those waits.

**But there's a catch:** if you put blocking code inside an `async def` function without awaiting it, you freeze the entire server. The single-threaded event loop has nothing else to do but sit and wait for your blocking call. _Every other request is stuck._

This is the biggest rule of async:

> Inside an `async def` function, every slow operation must be awaited. If you call a synchronous database library inside an async endpoint, you've made things _worse_, not better.

That's why upgrading a synchronous codebase to async is not just "add `async` in front of your functions." You have to swap out the libraries too.

---

## Before: our current synchronous codebase

Let's look at exactly what is synchronous today.

### `database.py` (current)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- `create_engine` is the **synchronous** engine factory.
- `Session` is the **synchronous** session class.
- The connection uses the `psycopg2` driver (implied by `postgresql://`), which is synchronous.
- `get_db` is a regular generator function.

### `routers/tasks.py` (current)

```python
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

- `def`, not `async def`.
- `db.query(...).first()` blocks until Postgres responds.
- FastAPI runs this on a worker thread.

Everything works. It's just not taking advantage of the event loop.

---

## After: the async version of the same code

To go async, we change three things:

1. **The Postgres driver.** Swap `psycopg2-binary` for `asyncpg` (async-native driver).
2. **The SQLAlchemy engine and session.** Swap `create_engine`/`Session` for `create_async_engine`/`AsyncSession`.
3. **The endpoints.** Add `async`/`await` in all the right places.

### `requirements.txt` (after)

```
fastapi
uvicorn[standard]
sqlalchemy
asyncpg           # was: psycopg2-binary
python-dotenv
```

### `database.py` (after)

```python
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DATABASE = os.getenv("PG_DATABASE")

# Notice the "+asyncpg" in the URL — that tells SQLAlchemy to use the
# async driver instead of the default (synchronous) psycopg2.
DATABASE_URL = (
    f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}"
    f"@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
)

# create_async_engine replaces create_engine.
engine = create_async_engine(DATABASE_URL)

# async_sessionmaker replaces sessionmaker. expire_on_commit=False is a
# common async best practice — it prevents SQLAlchemy from silently making
# another (now-invalidated) trip to the DB when you access attributes on
# an object after commit().
SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


# get_db is now an ASYNC generator. Notice:
#   - `async def`
#   - `async with` (the session itself is an async context manager)
#   - `yield` works the same way, but the dependency is awaited internally
#     by FastAPI.
async def get_db():
    async with SessionLocal() as db:
        yield db
```

### `main.py` (after)

The startup logic changes because `Base.metadata.create_all(bind=engine)` only works on a sync engine. With an async engine, we need a small async helper that runs it over a connection.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import engine, Base
from routers import tasks


# A "lifespan" is FastAPI's way of running startup/shutdown code. Anything
# before the `yield` runs at startup; anything after runs at shutdown.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup.
    async with engine.begin() as conn:
        # run_sync() lets us call synchronous SQLAlchemy metadata operations
        # inside the async engine's connection. It's the one place we have
        # to bridge the two worlds.
        await conn.run_sync(Base.metadata.create_all)
    yield
    # (No shutdown logic needed for now.)


app = FastAPI(
    title="Task Manager API",
    description="Async version of the task manager.",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(tasks.router)


@app.get("/")
async def root():
    return {"message": "Task Manager API is running!"}
```

### `routers/tasks.py` (after)

The biggest syntactic difference is that we stop using the old query style (`db.query(Model).filter(...).first()`) and use the modern SQLAlchemy 2.0 style (`select(Model).where(...)` + `await db.execute(...)`). This is what async SQLAlchemy expects.

```python
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Task
from schemas import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=list[TaskResponse])
async def get_all_tasks(
    db: AsyncSession = Depends(get_db),
    min_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Literal["id", "name", "due_date", "created_at", "updated_at"] = Query("id"),
    order: Literal["asc", "desc"] = Query("asc"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    # Build the SELECT statement. `select(Task)` replaces `db.query(Task)`.
    stmt = select(Task)

    if min_date is not None:
        stmt = stmt.where(Task.due_date >= min_date)
    if search is not None:
        stmt = stmt.where(Task.name.ilike(f"%{search}%"))

    sort_column = getattr(Task, sort_by)
    stmt = stmt.order_by(sort_column.asc() if order == "asc" else sort_column.desc())
    stmt = stmt.offset(offset).limit(limit)

    # This is the actual database round-trip. `await` pauses the function
    # here and lets the event loop handle OTHER requests until Postgres
    # responds.
    result = await db.execute(stmt)

    # .scalars().all() extracts the Task objects from the Result wrapper.
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    # db.get() is a convenient shortcut for "SELECT by primary key".
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(task_data: TaskCreate, db: AsyncSession = Depends(get_db)):
    new_task = Task(**task_data.model_dump())
    db.add(new_task)          # in-memory, not a DB call — no await needed
    await db.commit()         # actual DB call — must await
    await db.refresh(new_task)
    return new_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_data: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in task_data.model_dump().items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def patch_task(task_id: int, task_data: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await db.delete(task)
    await db.commit()
```

`models.py` and `schemas.py` do **not** change. Models describe table structure; schemas describe API data shapes. Neither of them actually does any I/O, so there's nothing to make async.

---

## Side-by-side diffs

Here's the minimum set of changes, by file:

| File                | Before                           | After                                          |
| ------------------- | -------------------------------- | ---------------------------------------------- |
| `requirements.txt`  | `psycopg2-binary`                | `asyncpg`                                      |
| `database.py`       | `create_engine`                  | `create_async_engine`                          |
| `database.py`       | `sessionmaker` + `Session`       | `async_sessionmaker` + `AsyncSession`          |
| `database.py`       | `postgresql://...`               | `postgresql+asyncpg://...`                     |
| `database.py`       | `def get_db(): ... yield db`     | `async def get_db(): async with ...: yield db` |
| `main.py`           | `Base.metadata.create_all(...)`  | `lifespan` + `await conn.run_sync(...)`        |
| `routers/tasks.py`  | `def endpoint(...)`              | `async def endpoint(...)`                      |
| `routers/tasks.py`  | `db.query(Task).filter(...)`     | `select(Task).where(...)`                      |
| `routers/tasks.py`  | `query.first()` / `query.all()`  | `await db.execute(stmt)` + `.scalar_one...()`  |
| `routers/tasks.py`  | `db.commit()`, `db.refresh(...)` | `await db.commit()`, `await db.refresh(...)`   |
| `models.py`         | (no changes)                     | (no changes)                                   |
| `schemas.py`        | (no changes)                     | (no changes)                                   |

---

## Why it matters: a concrete example

Let's say every database query takes 20 ms, and we have a single worker handling 100 simultaneous `GET /tasks/{id}` requests.

### Sync throughput

Each request spends ~20 ms waiting on the DB, during which the worker is idle. FastAPI moves these to its thread pool (40 threads by default). With 100 simultaneous requests, 60 of them queue up waiting for a free thread. The last 60 are effectively sequential-ish. Wall-clock time for all 100: roughly **50–60 ms** (assuming threads scale cleanly, which they don't always).

### Async throughput

All 100 requests hit the event loop. Each one reaches its `await db.execute(stmt)` call and immediately yields control. The event loop zips through all 100 in microseconds, firing off all the queries. Then it waits for Postgres to respond. As responses trickle back, the event loop resumes each request, serializes the response, and returns it. Wall-clock time for all 100: roughly **~20–30 ms** — essentially just the cost of one DB round trip plus processing.

Those numbers are illustrative, not benchmarks — but the shape is right. Async shines under **concurrent I/O-bound load**. If your app has 5 users, you'll never notice the difference. If it has 5,000 users hammering an API that talks to a slow external service, async is the difference between "works fine" and "falls over."

---

## The rules of async

Async in Python has a few strict rules. Breaking them either crashes your program or silently kills its performance.

1. **You can only `await` inside an `async def` function.** Writing `await` inside a regular `def` is a syntax error.
2. **Calling an async function without `await` does _not_ run it.** It returns a "coroutine object" — a recipe for work, not the work itself. This is a common bug. If `await db.commit()` becomes `db.commit()`, the commit just... doesn't happen.
3. **Never call blocking code inside an `async def`.** Things like `time.sleep(5)`, `requests.get(...)` (the old HTTP library), or a synchronous SQLAlchemy query will freeze the entire event loop. Use `await asyncio.sleep(5)`, `httpx.AsyncClient`, or the async SQLAlchemy session instead.
4. **Mixing sync and async is allowed — but be careful.** FastAPI lets you have some endpoints as `def` and some as `async def`. You'd typically reserve `def` for CPU-bound work (image processing, heavy computation) that would block the event loop anyway — FastAPI sends those to the thread pool for you.

A helpful mental model: **`async def` is a promise that your function will never stall the barista.** If you can keep that promise, put `async` on it. If you can't (because you're using a library that only comes in sync form), keep it as `def` and let FastAPI's thread pool handle it.

---

## When NOT to use async

Async isn't free. It makes code harder to reason about (every `await` is a potential context switch), and it forces you into an entire ecosystem of async-native libraries. Sometimes sync is the right choice:

- **Your app has very low traffic.** If you're serving tens of requests per minute, the sync version is simpler and indistinguishable in performance.
- **You don't do much I/O.** If your endpoint mostly does CPU work (like number-crunching), `async` actively _hurts_ because you'd block the event loop. Use a regular `def` endpoint and let FastAPI's thread pool handle it, or push the work into a background task queue.
- **Your ecosystem isn't async.** If the only database driver for your obscure database is synchronous, forcing async buys you nothing.
- **You're still learning.** There's no shame in shipping a synchronous FastAPI app while you learn the basics. That's exactly what this project is. You can always upgrade later — and now you know how.

---

## Glossary

| Term                 | Meaning                                                                                                                                            |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Synchronous**      | Code that runs one step at a time. Each line must finish before the next starts.                                                                   |
| **Asynchronous**     | Code that can pause at specific points (`await`), let other code run, and resume later.                                                            |
| **Blocking**         | A piece of code that forces the program to sit and wait — the CPU is idle, no other work can happen on that thread.                                |
| **Non-blocking**     | A piece of code that returns control to the caller right away; the wait happens somewhere it won't stall other work.                               |
| **Event loop**       | The single-threaded scheduler at the core of async Python. It's what decides which coroutine runs next when something awaits.                      |
| **Coroutine**        | The value an `async def` function returns when you _call_ it without `await`. It's a pending unit of work the event loop can run.                  |
| **`await`**          | "Pause here, let the event loop do other things, and come back when this is done." Only legal inside `async def`.                                  |
| **ASGI**             | Asynchronous Server Gateway Interface. The async successor to Python's older WSGI web standard. FastAPI speaks ASGI; Uvicorn is the ASGI server.   |
| **Uvicorn**          | The async web server that actually receives HTTP requests and hands them to FastAPI.                                                               |
| **Thread pool**      | The pool of background threads FastAPI uses to run your `def` (non-async) endpoints so they don't block the event loop. Default size: 40.          |
| **I/O-bound**        | A task whose time is mostly spent waiting on input/output (database, network, disk). Async helps a lot here.                                       |
| **CPU-bound**        | A task whose time is mostly spent doing computation (math, image processing). Async does NOT help here; use threads, processes, or a task queue.   |
| **`asyncpg`**        | A native-async Postgres driver for Python. Faster and more correct for async use than putting `psycopg2` behind a thread.                          |
| **`AsyncSession`**   | SQLAlchemy's async-aware version of `Session`. Every DB-touching method returns a coroutine and must be awaited.                                   |
