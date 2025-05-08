from fastapi import FastAPI, HTTPException
from supabase import create_client, Client
import pandas as pd
from dotenv import load_dotenv
import random
import os
from typing import Optional

load_dotenv()

app = FastAPI()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define the meal-type columns
food_cols = ['mpfd', 'mps', 'mpfm', 'mpsw', 'mpdk', 'mpft']

# Fetch data from Supabase and compute popularity
def load_and_process_data():
    # Query all data from food_orders table
    response = supabase.table("food_prediction_data").select("*").execute()
    df = pd.DataFrame(response.data)
    
    # Compute popularity (value_counts) separately for each meal type
    popularity = {}
    for col in food_cols:
        counts = df[col].dropna().value_counts()
        popularity[col] = counts  # a Series indexed by food item, sorted desc.
    
    return df, popularity

# Load data at startup
df, popularity = load_and_process_data()

# Recommendation function
def recommend_for_user(user_id, top_k=10):
    """
    Returns one random recommendation per meal type for the given user,
    sampling from that type's top_k most popular foods (excluding ones
    they've already ordered).

    Output: dict mapping meal-type → recommended item (or None)
    """
    recs = {}
    user_data = df[df['customerid'] == user_id]

    for col in food_cols:
        # What the user has already tried in this meal slot
        tried = set(user_data[col].dropna().unique())

        # The top-k items for this meal slot
        top_items = list(popularity[col].index[:top_k])

        # Filter out tried items
        choices = [item for item in top_items if item not in tried]

        # Pick one at random (if anything remains)
        recs[col] = random.choice(choices) if choices else None

    return recs


# FastAPI endpoint
@app.get("/recommend/{user_id}")
async def get_recommendations(user_id: int, top_k: Optional[int] = 10):
    try:
        # Generate recommendations
        recommendations = recommend_for_user(user_id, top_k)
        
        # Return JSON response
        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)