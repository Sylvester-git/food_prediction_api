from pydantic import BaseModel
from typing import List

class UserSignUp(BaseModel):
    email: str
    password: str
    liked_food_ids: List[str]

class UserLogin(BaseModel):
    email: str
    password: str

