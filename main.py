# Import FastAPI Framework
from fastapi import FastAPI, HTTPException, Depends
#Import HTMLREsponse to return an HTML welcome page instead of plain JSON
from fastapi.responses import HTMLResponse
# Import Pydantic BaseModel for data validation
from pydantic import BaseModel
# Import SQLAlchemy ORM session
from sqlalchemy.orm import Session
# Import List and Optional for type hints
from typing import List, Optional
# Import database session and TaskDB model from database.py
from database import SessionLocal, TaskDB

# Create the FastAPI application instance
app = FastAPI()

# Pydantic model for task requests/returns
# Defines the shape of a task that API accepts and returns
class Task(BaseModel):
    id: int                     # Create a unique identifier
    title: str                  # Define task title (required)
    description: str = ""       # Define task description (optional, defaults to empty string)
    status: str = "to do..."    # Define status (to do..., in progress, completed; defaults to to do...)
    category: str = "uncategorized..."  # Define category for grouping tasks
    project: str = "default"    # Define which project a task belongs to
    phase: str = "0"            # Define the phase of a given task under each project (e.g. Phase 1, Phase 2, Research; defaults to 0)

# Creates a response model that excludes a phase when it is defined as "0"
class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    category: str
    project: str
    phase: Optional[str] = None   # Item will be omitted if None

    # If phase = "0", it is set to None (will not be serialized)
    @classmethod
    def from_task(cls, task: Task):
        data = task.dict()
        if data.get("phase") == "0":
            data["phase"] = None
        return cls(**data)

# Dependency: provides a database session for each request which closes automatically after the request finishes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# WELCOME ENDPOINT
@app.get("/", response_class=HTMLResponse)
def root():
    # Create an HTML string with navigation links to all key endpoints
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project Tracker API!</title>
        <style>
            body { font-family: sans-serif; max-width: 800px; margin: 1rem auto; padding: 1rem; }
            h1 { color: #2c3e50; }
            li { margin: 0.5rem 0; }
            a { text-decoration: none; color: #3498db; }
            a:hover { text-decoration: underline; }
            code { background: #f4f4f4; padding: 0.2rem 0.4rem; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>🃋 Project Tracker API</h1>
        <p>Welcome to your task management API. Use the links below to explore.</p>
        <ul>
            <li>List all tasks (supports filtering) 🔗 <a href="/tasks">/tasks</a></li>
            <li>List all categories                 🔗 <a href="/categories">/categories</a></li>
            <li>List all projects                   🔗 <a href="/projects">/projects</a></li>
            <li>Interact with the API               🔗 <a href="/docs">/docs</a></li>
        </ul>
        <hr>
        <p><small>Powered by FastAPI | <a href="https://github.com/sadiecakes/project-tracker">GitHub</a></small></p>
    </body>
    </html>
    """
    # Return the HTML string as a response which will be rendered in the browser
    return HTMLResponse(content=html_content)

# GET /tasks -- list all tasks with optional filters for project, phase, and category
@app.get("/tasks", response_model=List[TaskResponse])
def list_tasks(
    project: Optional[str] = None,
    phase: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TaskDB)
    if project:
        query = query.filter(TaskDB.project == project)
    if phase:
        query = query.filter(TaskDB.phase == phase)
    if category:
        query = query.filter(TaskDB.category == category)
    if status:
        query = query.filter(TaskDB.status == status)
    tasks = query.all()
    return [TaskResponse.from_task(Task(**t.__dict__)) for t in tasks]


# POST /tasks -- create a new task
@app.post("/tasks", response_model=TaskResponse)
def create_task(task: Task, db: Session = Depends(get_db)):
    # Check if task with this ID already exists
    existing = db.query(TaskDB).filter(TaskDB.id == task.id).first()
    if existing:
        # Find the maximum ID currently in use (global max)
        max_id = db.query(TaskDB).order_by(TaskDB.id.desc()).first()
        next_id = (max_id.id + 1) if max_id else 1
        raise HTTPException(
            status_code=409,  # Conflict
            detail=f"Task with id {task.id} already exists. The next available ID is {next_id}."
        )
    # Create a new TaskDB object from Pydantic Task model
    db_task = TaskDB(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        category=task.category,
        project=task.project,
        phase=task.phase
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return TaskResponse.from_task(task)


# PUT /tasks/{task_id} -- update an existing task
@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updated_task: Task, db: Session = Depends(get_db)):
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found.")
    db_task.title = updated_task.title
    db_task.description = updated_task.description
    db_task.status = updated_task.status
    db_task.category = updated_task.category
    db_task.project = updated_task.project
    db_task.phase = updated_task.phase
    db.commit()
    db.refresh(db_task)
    return TaskResponse.from_task(updated_task)


# DELETE /tasks/{task_id} -- delete a task by ID
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found.")
    db.delete(db_task)
    db.commit()
    return {"message": f"Task {task_id} has been deleted."}


# GET /categories -- list all unique category names with navigation links
@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    results = db.query(TaskDB.category).distinct().all()
    categories = [row[0] for row in results if row[0] is not None]
    links = {
        "self": "/categories",
        "all_tasks": "/tasks"
    }
    for cat in categories:
        links[f"tasks_in_{cat}"] = f"/tasks?category={cat}"
    return {"categories": categories, "links": links}


# GET /projects -- list all unique project names with navigation links
@app.get("/projects")
def get_projects(db: Session = Depends(get_db)):
    results = db.query(TaskDB.project).distinct().all()
    projects = [row[0] for row in results if row[0] is not None]
    links = {
        "self": "/projects",
        "all_tasks": "/tasks"
    }
    for proj in projects:
        links[f"tasks_in_{proj}"] = f"/tasks?project={proj}"
    return {"projects": projects, "links": links}


# GET /phases -- list all unique phase values for a given project
@app.get("/phases")
def get_phases(project: str, db: Session = Depends(get_db)):
    results = db.query(TaskDB.phase).filter(TaskDB.project == project).distinct().all()
    phases = [row[0] for row in results if row[0] is not None]
    return {"project": project, "phases": phases}
