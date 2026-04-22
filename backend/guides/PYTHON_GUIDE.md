# Python & Programming Basics — Beginner's Guide

This guide exists to fill in the Python and programming fundamentals you'll need to read and modify the code in this project. `GUIDE.md` explains **what** the system does and how the pieces talk to each other. This file explains the **language** those pieces are written in.

It assumes you understand basic logic (if/else, loops, functions as an idea) but are new to Python specifically and to **classes and inheritance** — which is where most of this project's "magic" lives.

---

## 1. What is Python?

Python is a **high-level, interpreted, dynamically-typed** programming language. Unpacking those words:

| Word | What it means |
| --- | --- |
| **High-level** | Hides the gnarly low-level details (memory, pointers, how the CPU works). You write ideas; Python figures out the mechanics. |
| **Interpreted** | You don't "compile" a Python file into a standalone executable ahead of time the way you would with Go or C++. Instead, a program called the **Python interpreter** reads your `.py` files and runs them line by line. |
| **Dynamically-typed** | You don't declare that a variable is an integer — Python figures it out from what you assign to it. `x = 5` makes `x` an integer; `x = "hi"` changes it to a string. (Type _hints_, which this project uses a lot, are a way to write down the intended type even though Python won't enforce it at runtime.) |

**Why Python for backend work?** It has a massive ecosystem of libraries (FastAPI, SQLAlchemy, Pydantic — all three are core to this project), reads almost like English, and is the default choice for a lot of web services, data work, and scripting.

---

## 2. How a Python Program Actually Runs

When you type:

```bash
uvicorn main:app --reload
```

…here's what happens in slow-motion:

1. `uvicorn` is a program that knows how to run a web server.
2. It opens `main.py`, hands the contents to the Python interpreter.
3. The interpreter starts at the top of the file and runs each line in order.
4. When it hits `from database import engine, Base`, it pauses, opens `database.py`, runs THAT file top-to-bottom, then comes back and continues `main.py`.
5. Eventually it reaches `app = FastAPI(...)` — this creates the web server object. `uvicorn` then tells that object to start listening for HTTP requests on port 8000.
6. From that moment on, Python doesn't exit — it sits in a loop, waiting for HTTP requests, and when one arrives, it runs the function for that endpoint.

**Important mental model:** a running Python program is just the interpreter holding a bunch of values in memory. When it hits the end of a file (or the server is stopped), those values disappear. That's why we use a **database** — it's where data lives after Python stops running.

---

## 3. Values, Variables, and Types

A **value** is a piece of data: `5`, `"hello"`, `True`, `None`.
A **variable** is a name that points to a value. `x = 5` means "make `x` refer to the value `5`."

Python's core built-in types you'll see in this project:

| Type | Example | What it's for |
| --- | --- | --- |
| `int` | `5`, `-12`, `0` | Whole numbers |
| `float` | `3.14`, `0.5` | Decimal numbers |
| `str` | `"Buy milk"` | Text |
| `bool` | `True`, `False` | True/false values |
| `None` | `None` | "No value" / "nothing here" |
| `list` | `[1, 2, 3]` | Ordered collection |
| `dict` | `{"name": "Buy milk"}` | Key/value pairs |
| `tuple` | `(1, 2)` | Like a list but can't be changed |

**From this project:**

```python
# routers/tasks.py
raise HTTPException(status_code=404, detail="Task not found")
#                                 ^int       ^str
```

```python
# schemas.py — model_dump() returns a dict
{"name": "Buy milk", "due_date": "2026-04-20"}
```

---

## 4. Strings

Strings are text wrapped in quotes. Single (`'hi'`) and double (`"hi"`) quotes are equivalent; triple quotes (`"""..."""`) let you span multiple lines and are how every file in this project starts its top-of-file docstring.

**f-strings** are the most important string feature you'll see. An `f` before the opening quote lets you drop variables and expressions into the string with `{...}`:

```python
# database.py
DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
```

If `PG_USER = "max"` and `PG_HOST = "localhost"`, this becomes `"postgresql://max:...@localhost:..."`. Much cleaner than gluing pieces together with `+`.

---

## 5. Lists, Dictionaries, and Tuples

### Lists

Ordered, changeable collections. Written with square brackets.

```python
tasks = ["Buy milk", "Walk dog", "Learn Python"]
tasks[0]           # "Buy milk"  — zero-indexed
tasks.append("Sleep")   # add to the end
len(tasks)         # 4
```

**From this project:**

```python
# routers/tasks.py
return query.all()   # returns a list of Task objects
```

### Dictionaries (dicts)

Unordered collections of key→value pairs. Written with curly braces.

```python
task = {"id": 1, "name": "Buy milk", "due_date": "2026-04-20"}
task["name"]              # "Buy milk"
task["name"] = "Buy oat milk"  # update
```

Dicts are how JSON is represented in Python — which means whenever your API receives a JSON request body, Python is working with it as a dict under the hood.

**From this project:**

```python
# routers/tasks.py
update_data = task_data.model_dump(exclude_unset=True)
# update_data is a dict like {"name": "Buy oat milk"}
for field, value in update_data.items():
    setattr(task, field, value)
```

### Tuples

Like lists, but **immutable** — once created, you can't change them. Written with parentheses. You'll see them less often but they sometimes pop up for "a fixed-size group of things."

```python
point = (3, 5)   # a 2D coordinate
```

---

## 6. `None`, `True`, `False`

- `None` is Python's "no value" / "empty." Comparable to `null` in JavaScript or SQL.
- `True` and `False` (capital T and F) are the two boolean values.

**From this project:**

```python
# routers/tasks.py
if min_date is not None:
    query = query.filter(Task.due_date >= min_date)
```

Note `is not None` — the preferred Python idiom for "does this variable hold an actual value or is it empty?". You _could_ write `if min_date != None`, but `is` is faster and more idiomatic because `None` is a singleton (there's only ever one `None` object in memory).

---

## 7. Control Flow

You already know the shape of these from other languages. Python quirks:

- **Indentation is syntax.** Python uses whitespace (4 spaces per level, by convention) where other languages use `{ }`. Inconsistent indentation is a syntax error.
- **No parentheses around conditions** (though they're allowed).
- **`elif`** instead of `else if`.

```python
if x > 0:
    print("positive")
elif x < 0:
    print("negative")
else:
    print("zero")
```

```python
# for-loop — iterates over any collection
for field, value in update_data.items():
    setattr(task, field, value)
```

```python
# while-loop — runs until the condition becomes False
while still_running:
    do_something()
```

### Truthiness

In a condition, Python treats these as "falsy": `False`, `None`, `0`, `""`, `[]`, `{}`. Everything else is "truthy." This is why you sometimes see:

```python
# routers/tasks.py
task = db.query(Task).filter(Task.id == task_id).first()
if not task:
    raise HTTPException(status_code=404, detail="Task not found")
```

`first()` returns either a `Task` object or `None`. `not None` is `True`, `not <Task object>` is `False`. So `if not task:` is "if the task wasn't found."

---

## 8. Functions

The `def` keyword defines a function:

```python
def add(a, b):
    return a + b

add(2, 3)   # 5
```

A few things the project uses that you should recognize:

### Default arguments

Values assigned in the signature are used if the caller leaves them out.

```python
# routers/tasks.py
def get_all_tasks(
    db: Session = Depends(get_db),
    min_date: Optional[date] = None,
    search: Optional[str] = None,
    ...
):
```

If the client doesn't include `?min_date=...` in the URL, `min_date` is `None`.

### Keyword arguments

You can call a function by naming the arguments. This is how most of this codebase passes arguments because it's vastly more readable than positional order:

```python
HTTPException(status_code=404, detail="Task not found")
#             ^^^^^^^^^^^^^^^  ^^^^^^^
#             keyword args — the names tell you what each value means
```

### Return values

`return <expression>` sends a value back to whoever called the function. A function with no `return` (or a bare `return`) returns `None`.

---

## 9. Type Hints

Type hints look like:

```python
def get_task(task_id: int, db: Session = Depends(get_db)):
```

`task_id: int` says "this parameter is expected to be an integer."

**Crucial fact:** Python does NOT enforce type hints at runtime. You can pass a string where an `int` is expected and Python won't complain — it'll just crash later when the string doesn't behave like an int. Type hints are for:

1. **Your editor / linter** — they catch mistakes before you run the code.
2. **FastAPI / Pydantic / SQLAlchemy** — these libraries actively READ the hints and use them to do work. FastAPI reads `task_id: int` and automatically converts `GET /tasks/5` into `task_id = 5`, validates the type, and returns a 422 error if the URL is `/tasks/abc`.
3. **Humans** — future-you reading the code will thank you.

Types you'll see a lot:

| Hint | Meaning |
| --- | --- |
| `int`, `str`, `bool`, `float` | Built-in types |
| `list[int]` | A list of ints |
| `dict[str, int]` | A dict where keys are strings and values are ints |
| `Optional[X]` | Either `X` or `None`. Same as `X \| None`. |
| `Literal["asc", "desc"]` | Must be one of those exact strings. |

**From this project:**

```python
# routers/tasks.py
sort_by: Literal["id", "name", "due_date", "created_at", "updated_at"] = Query("id", ...)
```

That `Literal[...]` hint is literally (ha) the reason FastAPI can auto-reject `?sort_by=drop_table` with a 422 error before it ever reaches our code.

---

## 10. Imports and Modules

Each `.py` file in Python is a **module**. The `import` statement pulls names from one module into another.

```python
# Two common forms:
import os                        # bring in the whole module; use as os.getenv(...)
from dotenv import load_dotenv   # bring in just one name; use as load_dotenv()
```

**From this project:**

```python
# routers/tasks.py
from database import get_db
from models import Task
from schemas import TaskCreate, TaskResponse, TaskUpdate
```

This file pulls in things from three other files in the project. Python finds them because of how the project is organized and how `uvicorn` is started (from the `backend/` directory, which becomes the root for imports).

Circular imports (A imports B, B imports A) can cause problems — one reason the project separates models and schemas rather than mashing them into one file.

---

## 11. Classes — The Big One

This is the section that matters most for reading this project.

### What problem do classes solve?

Imagine you have 100 tasks in your app. Each task has an `id`, a `name`, a `due_date`. Without classes, you might store each one as a dict:

```python
task1 = {"id": 1, "name": "Buy milk", "due_date": "2026-04-20"}
task2 = {"id": 2, "name": "Walk dog", "due_date": None}
```

Fine for a toy. But now you want functions that operate on tasks: `is_overdue(task)`, `mark_complete(task)`, `format_for_display(task)`. They're all tied to "task-ness" but they live in random places in your codebase, and you have to remember which dict keys exist.

A **class** bundles the data (`id`, `name`, `due_date`) AND the functions that operate on that data into one named thing. A **class** is the blueprint; an **instance** is one specific thing built from that blueprint.

Analogy: a class is "the idea of a car" (has wheels, has an engine, can accelerate). An instance is "that specific Honda Civic in your driveway, license plate ABC-123."

### Defining a class

```python
class Task:
    def __init__(self, id, name, due_date):
        self.id = id
        self.name = name
        self.due_date = due_date

    def is_overdue(self, today):
        if self.due_date is None:
            return False
        return self.due_date < today
```

Breaking that down:

- `class Task:` — "I am defining a new type called Task."
- `def __init__(self, id, name, due_date):` — the **constructor**. Python calls this automatically when you create a new instance. Its job is to set up the instance's starting data.
- `self` — the instance being built/operated on. It's the first parameter of every method. When you call `task.is_overdue(today)`, Python secretly passes `task` in as `self`. You never pass it explicitly.
- `self.id = id` — "store `id` as an attribute on this instance so we can get it back later as `task.id`."
- `is_overdue` — a **method**. A method is just a function that lives inside a class and takes `self` as its first argument.

### Creating and using an instance

```python
t = Task(id=1, name="Buy milk", due_date=date(2026, 4, 20))
# Python calls Task.__init__(self=<new instance>, id=1, name="Buy milk", due_date=...)

t.name              # "Buy milk"       — read an attribute
t.name = "Oat milk" # modify an attribute
t.is_overdue(date(2026, 5, 1))  # True  — call a method
```

Read this pattern carefully — it's the pattern you'll see everywhere in the project.

### "But where are the classes I actually see in this project?"

Good question, because you'll look at `models.py` and go "wait, there's no `__init__`."

```python
# models.py
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
```

Two things are happening:

1. **`class Task(Base):`** — the `(Base)` part is inheritance. We'll cover that next.
2. **No `__init__`** — because SQLAlchemy's `Base` class writes one for us. When you do `Task(name="Buy milk", due_date="2026-04-20")`, SQLAlchemy's machinery reads the keyword arguments and assigns them to attributes for you. Same idea, just automated.

And in `schemas.py`:

```python
class TaskCreate(BaseModel):
    name: str
    due_date: Optional[date] = None
```

Same story. `BaseModel` comes from Pydantic and handles `__init__` (plus a lot more — validation, conversion, error messages) for any class that inherits from it.

**The big realization:** most classes you'll define in a real Python project don't have custom `__init__` methods. They inherit one from a library.

---

## 12. Inheritance

Inheritance lets one class build on top of another. The child class gets everything the parent has, and can add or override things.

### The minimal example

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def describe(self):
        return f"{self.name} is an animal"

class Dog(Animal):         # Dog "inherits from" Animal
    def bark(self):
        return "Woof!"

d = Dog(name="Rex")
d.describe()   # "Rex is an animal"   — inherited from Animal
d.bark()       # "Woof!"              — defined on Dog itself
```

`Dog` automatically has `__init__` and `describe` because `Animal` had them. `Dog` adds `bark` on top.

### Why it matters for this project

Every model and schema in this codebase inherits from a library-provided parent class, and that parent is doing enormous amounts of work on your behalf.

```python
# database.py
class Base(DeclarativeBase):
    pass
```

`Base` inherits from SQLAlchemy's `DeclarativeBase`. `pass` is Python's "empty block" — it means "I'm not adding anything." So `Base` _is_ `DeclarativeBase` with a different name. Why bother? Because every model in the project inherits from `Base`, and SQLAlchemy uses that shared parent as a registry — it knows "every class that inherits from `Base` represents a database table."

```python
# models.py
class Task(Base):
    __tablename__ = "tasks"
    ...
```

When Python reaches this line, SQLAlchemy notices "a new class inherited from Base" and wires it up so that:

- You can query it with `db.query(Task)`.
- `Base.metadata.create_all(engine)` will create the `tasks` table.
- Instances of `Task` know how to save themselves to the database.

You didn't write any of that behavior. It came free with inheritance.

```python
# schemas.py
class TaskCreate(BaseModel):
    name: str
    due_date: Optional[date] = None
```

Same deal. `BaseModel` (from Pydantic) gives `TaskCreate` automatic validation, JSON conversion, `.model_dump()`, and clear error messages when the incoming JSON is wrong — all by inheritance.

### How to read the pattern

When you see `class Something(SomethingElse):`, ask two questions:

1. What is the parent (`SomethingElse`) — what library does it come from?
2. What does inheriting from that parent give me for free?

That's the whole mental model.

---

## 13. Decorators

A **decorator** is a special syntax (`@something` above a function) that wraps the function in extra behavior. You'll see them all over `routers/tasks.py`:

```python
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    ...
```

The `@router.get("/{task_id}", ...)` line is a decorator. What it does, in plain English: "Register this function as the handler for `GET /tasks/{task_id}` requests, and when FastAPI uses it, also format the return value using `TaskResponse`."

Without the decorator, `get_task` is just a regular function that does nothing special. With it, FastAPI knows to call this function whenever an HTTP GET request arrives at that URL.

You don't need to write decorators yourself to work with this project — just read them as "this function is special in the following way." The library provides the decorator, you just stick it above your function.

---

## 14. Exceptions and `try / except / finally`

When something goes wrong, Python **raises an exception** — a special object that interrupts normal execution and bubbles up until something handles it.

```python
# routers/tasks.py
if not task:
    raise HTTPException(status_code=404, detail="Task not found")
```

`raise` throws the exception. FastAPI catches `HTTPException` automatically and converts it into a proper HTTP response with the right status code — so from your endpoint's perspective, `raise` is basically "stop here and send this error to the client."

### `try / except / finally`

You use these to handle exceptions yourself:

```python
# database.py
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- `try:` — "attempt this code."
- `except ExceptionType:` — "if _that_ kind of error happens, run this instead." (Not used here, but common.)
- `finally:` — "whether or not an error happened, always run this at the end." This is how we guarantee the DB session gets closed, even if the endpoint crashed mid-request.

---

## 15. Generators and `yield` (a quick detour)

Most functions use `return` to hand back a value and exit. A few use `yield` instead — these are **generator functions**, and they have a very different lifecycle.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db          # hand `db` out, then PAUSE here
    finally:
        db.close()        # runs after whoever used `db` is done
```

The key idea: `yield` pauses the function, hands a value to the caller, and resumes _later_ when the caller is done. In FastAPI's dependency injection system, this is the exact pattern that lets us say "give the endpoint a fresh database session, and when the endpoint finishes, automatically close it."

You don't need to write generators often — but recognize this shape when you see it, especially in `get_db`.

---

## 16. Putting It All Together — Reading One Endpoint

Here's an annotated walkthrough of a real endpoint, using everything above:

```python
@router.get("/{task_id}", response_model=TaskResponse)          # 1
def get_task(task_id: int, db: Session = Depends(get_db)):      # 2
    task = db.query(Task).filter(Task.id == task_id).first()    # 3
    if not task:                                                # 4
        raise HTTPException(status_code=404, detail="Task not found")   # 5
    return task                                                 # 6
```

1. **Decorator.** Registers this function as the handler for `GET /tasks/{task_id}`. `response_model=TaskResponse` means the return value will be validated and formatted by the `TaskResponse` Pydantic class (which inherits from `BaseModel`).
2. **Function definition with type hints and a default argument.** `task_id: int` tells FastAPI to convert the URL segment to an int. `db: Session = Depends(get_db)` uses FastAPI's dependency injection to call `get_db()` (the generator) and hand us a database session as `db`.
3. **Method calls on an object.** `db.query(...)` is a method on the `Session` object. Each `.something()` returns another object, so you can chain them (`.filter(...)` on the result of `.query(...)`). This is a classic OOP pattern — the result of one method is another object that has its own methods.
4. **Truthiness check.** `first()` returned either a `Task` instance or `None`. `if not task:` means "if we got None."
5. **Raise an exception.** Exits the function, and FastAPI turns the `HTTPException` into a 404 response.
6. **Return a value.** FastAPI takes the `Task` SQLAlchemy object, feeds it into the `TaskResponse` Pydantic class (which reads the attributes thanks to `from_attributes=True`), and serializes it to JSON for the client.

Every endpoint in this project is a variation on this pattern.

---

## 17. Common Python Idioms You'll See in This Project

| Pattern | What it means |
| --- | --- |
| `from X import Y` | Pull `Y` from another file |
| `class Foo(Bar):` | `Foo` inherits from `Bar` |
| `self.x = y` | Store `y` as an attribute on the current instance |
| `@something` above a function | A decorator — adds behavior to the function |
| `x if condition else y` | The "ternary" — a one-line if/else that returns a value |
| `f"hello {name}"` | An f-string — drops the variable into the text |
| `is None` / `is not None` | The idiomatic way to check for emptiness |
| `for k, v in d.items():` | Loop over a dict's keys and values |
| `**some_dict` | "Unpack a dict as keyword arguments." `Task(**{"name": "x"})` is the same as `Task(name="x")`. |
| `list[int]`, `Optional[str]` | Type hints |

One last one — **`**` unpacking** is everywhere in this project:

```python
# routers/tasks.py
new_task = Task(**task_data.model_dump())
```

`task_data.model_dump()` produces `{"name": "Buy milk", "due_date": "2026-04-20"}`. The `**` spreads that dict into keyword arguments, so the line is equivalent to `Task(name="Buy milk", due_date="2026-04-20")`. Handy when you have a dict and want to pass its contents into a function or constructor.

---

## 18. What to Read Next

You now have enough Python to read this codebase end-to-end without being confused by the syntax. Good next topics to explore on your own, in rough order of usefulness for backend work:

1. **List comprehensions** (`[x * 2 for x in nums]`) — very Pythonic, used heavily in real code.
2. **`*args` and `**kwargs`** — how functions accept variable numbers of arguments.
3. **Context managers (`with` blocks)** — the other way (besides `try/finally`) to guarantee cleanup.
4. **Async / await** — Python's way of doing concurrency; FastAPI supports it natively for handling many requests at once.
5. **Virtual environments (`venv`)** — how Python projects isolate their dependencies, which is why every Python project has its own `.venv/` folder.

But for now, you know enough. Go read `routers/tasks.py` top to bottom and see how much more of it makes sense.
