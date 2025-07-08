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

@app.get("/recommend")
def recommend(user_id: str = Depends(get_current_user)):
    try:
        liked = supabase.from_("user_food_preference").select("food_id").eq("user_id", user_id).execute()
        liked_ids = [item['food_id'] for item in liked.data]
        if not liked_ids:
            raise HTTPException(status_code=404, detail="No preferences found")

        #Get releated foods by same category or type
        liked_foods = supabase.from_("food_items").select("*").in_("id", liked_ids).execute().data
        liked_categories = list({f['category_id'] for f in liked_foods})

        #Recommend randowm from same category
        similar_foods = supabase.from_("food_item").select("*").in_("category_id", liked_categories).execute().data
        return {"recommendations": similar_foods}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# # Define the meal-type columns
# food_cols = ['mpfd', 'mps', 'mpfm', 'mpsw', 'mpdk', 'mpft']

# # Fetch data from Supabase and compute popularity
# def load_and_process_data():
#     # Query all data from food_orders table
#     response = supabase.table("food_prediction_data").select("*").execute()
#     df = pd.DataFrame(response.data)
    
#     # Compute popularity (value_counts) separately for each meal type
#     popularity = {}
#     for col in food_cols:
#         counts = df[col].dropna().value_counts()
#         popularity[col] = counts  # a Series indexed by food item, sorted desc.
    
#     return df, popularity

# # Load data at startup
# df, popularity = load_and_process_data()

# # Recommendation function
# def recommend_for_user(user_id, top_k=10):
#     """
#     Returns one random recommendation per meal type for the given user,
#     sampling from that type's top_k most popular foods (excluding ones
#     they've already ordered).

#     Output: dict mapping meal-type → recommended item (or None)
#     """
#     recs = {}
#     user_data = df[df['customerid'] == user_id]

#     for col in food_cols:
#         # What the user has already tried in this meal slot
#         tried = set(user_data[col].dropna().unique())

#         # The top-k items for this meal slot
#         top_items = list(popularity[col].index[:top_k])

#         # Filter out tried items
#         choices = [item for item in top_items if item not in tried]

#         # Pick one at random (if anything remains)
#         recs[col] = random.choice(choices) if choices else None

#     return recs


# # FastAPI endpoint
# @app.get("/recommend/{user_id}")
# async def get_recommendations(user_id: int, top_k: Optional[int] = 10):
#     try:
#         # Generate recommendations
#         recommendations = recommend_for_user(user_id, top_k)
        
#         # Return JSON response
#         return {
#             "user_id": user_id,
#             "recommendations": recommendations,
#             "status": "success"
#         }
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)