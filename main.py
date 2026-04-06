from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from database import SessionLocal, TaskDB

app = FastAPI()

# Pydantic model for API requests/responses
class Task(BaseModel):
    id: int
    title: str
    description: str = ""
    status: str = "to do..."
    category: str = "uncategorized..."

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# WELCOME ENDPOINT
@app.get("/")
def root():
    return {"message": "Hello and welcome, from The Festiva Project Tracker!"}

# GET /tasks -- list all tasks
@app.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(TaskDB).all()
    return {"tasks": tasks}

# POST /tasks -- add a new task
@app.post("/tasks")
def create_task(task: Task, db: Session = Depends(get_db)):
    # Check if task with this ID already exists
    existing = db.query(TaskDB).filter(TaskDB.id == task.id).first()
    if existing:
        return {"error": f"Task with id {task.id} already exists."}
    db_task = TaskDB(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        category=task.category
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return {"message": f"Task {task_id} has been created.", "Task:": task}

# PUT /tasks/{task_id} -- update an existing task
@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: Task, db: Session = Depends(get_db)):
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not db_task:
        return {"error": "Task not found."}
    db_task.title = updated_task.title
    db_task.description = updated_task.description
    db_task.status = updated_task.status
    db_task.category = updated_task.category
    db.commit()
    db.refresh(db_task)
    return {"message": f"Task {task_id} has been updated.", "Task:": updated_task}

# DELETE /tasks/{task_id} -- delete a task by ID
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if not db_task:
        return {"error": "Task not found"}
    db.delete(db_task)
    db.commit()
    return {"message": f"Task {task_id} has been deleted."}
