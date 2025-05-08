from flask import Flask, request, jsonify
from supabase import create_client
import pandas as pd
import random
import os

app = Flask(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "your-supabase-url")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-key")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define the meal-type columns
food_cols = ['mptd', 'mps', 'mpfm', 'mpsw', 'mpdk', 'mpft']

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


# Flask endpoint
@app.route('/recommend/<int:user_id>', methods=['GET'])
def get_recommendations(user_id):
    try:
        # Get top_k from query parameter, default to 10
        top_k = int(request.args.get('top_k', 10))
        
        # Generate recommendations
        recommendations = recommend_for_user(user_id, top_k)
        
        # Return JSON response
        return jsonify({
            "user_id": user_id,
            "recommendations": recommendations,
            "status": "success"
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)