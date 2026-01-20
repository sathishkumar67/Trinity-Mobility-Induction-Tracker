from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI()


class User(BaseModel):
    name: str = Field(min_length=3)
    age: int = Field(ge=18)


users = []


@app.get("/")
def home():
    return {"msg": "API is running"}


@app.post("/users")
def create_user(user: User):
    users.append(user)
    return user


@app.get("/users")
def get_users():
    return users


@app.get("/users/{id}")
def get_user(id: int):
    if id >= len(users):
        raise HTTPException(404, "User not found")
    return users[id]


@app.delete("/users/{id}")
def delete_user(id: int):
    if id >= len(users):
        raise HTTPException(404, "User not found")
    users.pop(id)
    return {"msg": "User deleted"}