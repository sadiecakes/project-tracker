from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# In memory storage (we'll replace this with a database later)
tasks_db = []

# Task model -- defines what a task looks like
class Task(BaseModel):
	id: int
	title: str
	description: str = ""
	status: str = "todo"

# WELCOME ENDPOINT
@app.get("/")
def root():
	return {"message": "Hello from the Festiva Project Tracker!"}

# GET /tasks -- list all tasks
@app.get("/tasks")
def list_tasks():
	return {"tasks": tasks_db}

# POST /tasks -- add a new task
@app.post("/tasks")
def create_task(task: Task):
	tasks_db.append(task)
	return {"message": "Task created", "task": task}
