from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import pandas as pd
from dotenv import load_dotenv
import random
import os
from typing import Optional
from typing import List
import bcrypt
import jwt
from model import *
from datetime import datetime, timedelta


load_dotenv()

app = FastAPI()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRY_SECONDS = int(os.getenv("JWT_EXP_TIME", "86400"))
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()

# AUTH HELPERS
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(),  bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def genetate_token(user_id: str) -> str:
    expiry = datetime.utcnow() + timedelta(seconds=JWT_EXPIRY_SECONDS)
    payload = {"user_id": user_id, "exp": expiry}
    return jwt.encode(payload, JWT_SECRET, algorithm= "HS256")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["user_id"]
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=402, detail="Invalid Tokne")
    

#ROUTES
@app.post("/signup")
def signup(user: UserSignUp):
    try:
        auth_response = supabase.auth.sign_up({"email": user.email, "password": user.password})
        if auth_response.user is None:
            raise HTTPException(status_code=400, detail= "Signup")
        user_id = auth_response.user.id
    
        # Save food preferences
        for food_id in user.liked_food_ids:
            supabase.table("user_food_preference").insert({
                "user_id": user_id,
                "food_id": food_id
            }).execute()
        return {"message": "User signed up successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login")
def login(user: UserLogin):
    try:
        response = supabase.auth.sign_in_with_password({"email": user.email, "password": user.password})
        if response.user is None:
         raise HTTPException(status_code=400, detail="Invalid credentials")
        user_id = response.user.id
        token = genetate_token(user_id)
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/foods")
def get_all_foods():
    try:
        result = supabase.from_("food_items").select("id, name, category_id").execute()
        categories = supabase.from_("food_category").select("id, name").execute()
        return {
            "foods": result.data,
            "categories": categories.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def get_category_ids(category_name):
    cat_response = supabase.from_("food_category").select("id, name").execute()
    if not cat_response.data:
        return []
    return [cat["id"] for cat in cat_response.data if cat["name"] in category_name]

def safe_sample(items, count):
    return random.sample(items, count) if len(items) >= count else items

@app.get("/recommend")
def recommend(user_id: str = Depends(get_current_user)):
    try:
        liked = supabase.from_("user_food_preference").select("food_id").eq("user_id", user_id).execute()
        liked_ids = [item['food_id'] for item in liked.data]
        if not liked_ids:
            raise HTTPException(status_code=404, detail="No preferences found")
        
        # Fetch all food items
        all_food = supabase.from_("food_items").select("*").execute().data
        # food_dict = {f["id"]: f for f in all_food}

        # Group by category
        def filter_by(conditions):
            return [f for f in all_food if conditions(f)]
        
        rice_options= filter_by(lambda f: f.get("is_rice"))
        swallow_options = filter_by(lambda f: f.get("is_swallow"))
        fry_options = filter_by(lambda f: f.get("is_fry"))

        protein_options = filter_by(lambda f: f['category_id'] in get_category_ids(["Protein"]))
        soup_options = filter_by(lambda f: f['category_id'] in get_category_ids(["Soup"]))
        drink_options = filter_by(lambda f: f['category_id'] in get_category_ids(["Smoothie"]))
        fruit_options = filter_by(lambda f: f['category_id'] in get_category_ids(["Fruits"]))
        fast_food_options = filter_by(lambda f: f['category_id'] in get_category_ids(["Fast Food"]))

        recommendations = []
        # --- RICE RULE -----
        if rice_options:
            rice = random.choice(rice_options)
            proteins = safe_sample(protein_options,2)
            drink = random.choice(drink_options)
            combo = [rice["name"], proteins[0]["name"], proteins[1]["name"]]
            if rice.get("has_stew"):
                combo.append("Stew")
            combo.append(drink["name"])
            recommendations.append({"type": "Rice Combo", "Items": combo})

        # --- SWALLOW RULE -----
        if swallow_options:
            swallow = random.choice(swallow_options)
            proteins = random.choice([p for p in protein_options if p["name"] in ["Fish", "Meat", "Egg", "Chicken"]])
            soup = random.choice(soup_options)
            recommendations.append({"type": "Swallow Combo", "Items": [swallow["name"], soup["name"], proteins["name"]]})

        # ---- FRY RULE -------
        if fry_options:
            fry = random.choice(fry_options)
            drink = random.choice(drink_options)
            fruit = random.choice(fruit_options)
            recommendations.append({"type": "Fried combo", "Items": [fry["name"], drink["name"], fruit["name"]]})

        used_names = set(item["items"][0] for item in recommendations if item["type"] == "Extra")
        fast_food_remaining = [f for f in fast_food_options if f["name"] not in used_names]
        while len(recommendations) < 5 and fast_food_remaining:
            fast  = random.choice(fast_food_remaining)
            recommendations.append({
                "type": "Extra",
                "Items": [fast["name"]]
            })     
            used_names.add(fast["name"])
            fast_food_remaining.remove(fast)
            return {"recommendations": recommendations[:5]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)