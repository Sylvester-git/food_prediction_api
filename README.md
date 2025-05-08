# Food Prediction API

This project is a FastAPI-based web service that provides personalized food recommendations for users based on their past orders. It connects to a Supabase database to fetch historical food order data and uses this data to recommend popular food items that the user hasn't tried yet.

## Features

- **Personalized Recommendations:** For each meal type, the API recommends a popular food item the user hasn't ordered before.
- **Popularity-Based:** Recommendations are chosen from the top-k most popular items for each meal type.
- **Supabase Integration:** Fetches and processes data from a Supabase table.
- **REST API:** Exposes a `/recommend/{user_id}` endpoint for fetching recommendations.

## CSV/Data Structure

The data is expected to have the following columns:

| vendor       | mpfd | mps | mpfm | mpsw | mpdk | mpft     | customerid |
|--------------|------|-----|------|------|------|----------|------------|
| BOLE WOMAN   | Rice | Plantain| Jollof Rice | Amala | Fante | Tigernut | 15232      |

**Column meanings:**

- `vendor`: Name of the food vendor.
- `mpfd`: Most preferred dish.
- `mps`: Most preferred supplement.
- `mpfm`: Most preferred meal.
- `mpsw`: Most preferred swallow.
- `mpdk`: Most preferred drink.
- `mpft`: Most preferred fruit.
- `customerid`: Unique identifier for the customer.

## Project Structure

- `main.py`: Main application code (FastAPI app, data loading, recommendation logic).
- `.env`: Stores environment variables (Supabase credentials).
- `makefile`: Contains a command to run the API locally.
- `.gitignore`: Ignores `.env` file.

## How It Works

1. **Startup:**
   - Loads environment variables from `.env`.
   - Connects to Supabase using credentials.
   - Fetches all data from the `food_prediction_data` table.
   - Computes the most popular items for each meal type.

2. **Recommendation Logic:**
   - For a given user, finds all foods they've already ordered for each meal type.
   - For each meal type, selects the top-k most popular items the user hasn't tried.
   - Randomly picks one item from these as the recommendation for that meal type.

3. **API Endpoint:**
   - `GET /recommend/{user_id}?top_k=10`
   - Returns a JSON object with recommendations for each meal type.

## Example Usage

Start the API locally:

```sh
make run-local
```

Example response:

```json
{
  "user_id": 123,
  "recommendations": {
    "mpfd": "Pizza",
    "mps": "Salad",
    "mpfm": "Burger",
    "mpsw": null,
    "mpdk": "Sushi",
    "mpft": "Pasta"
  },
  "status": "success"
}
```

## Environment Variables

Create a .env file with the following variables:

```plaintext
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Dependencies

- fastapi
- uvicorn
- supabase
- pandas
- python-dotenv

pip install fastapi uvicorn supabase pandas python-dotenv
