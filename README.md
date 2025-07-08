# Food Prediction API

This project is a FastAPI-based web service that provides personalized food recommendations for users based on their preferences. It connects to a Supabase database to fetch food and user data, and uses this data to recommend food combos the user hasn't tried yet.

---

## Table of Contents

- [Features](#features)
- [Data Structure](#data-structure)
- [Project Structure](#project-structure)
- [How It Works (Step by Step)](#how-it-works-step-by-step)
  - [1. User Authentication](#1-user-authentication)
  - [2. Food Recommendation Logic](#2-food-recommendation-logic)
  - [3. API Endpoints](#3-api-endpoints)
- [Example Usage](#example-usage)
- [Environment Variables](#environment-variables)
- [Dependencies](#dependencies)

---

## Features

- **User Signup/Login:** Secure authentication using JWT tokens.
- **Personalized Recommendations:** Suggests food combos based on user preferences and popular items.
- **Supabase Integration:** Fetches and processes data from Supabase tables.
- **REST API:** Endpoints for signup, login, fetching foods, and getting recommendations.

---

## Data Structure

The main tables used are:

- `food_items`: List of foods, with fields like `id`, `name`, `category_id`, and flags like `is_rice`, `is_swallow`, etc.
- `food_category`: Food categories (e.g., Protein, Soup, Fruits).
- `user_food_preference`: Stores which foods a user likes.
- `users`: Managed by Supabase Auth.

---

## Project Structure

- `main.py`: Main FastAPI app, authentication, and recommendation logic.
- `model.py`: Pydantic models for request validation.
- `.env`: Environment variables (Supabase credentials, JWT secret).
- `README.md`: Project documentation.

---

## How It Works (Step by Step)

### 1. User Authentication

- **Signup (`/signup`):**
  - User provides email, password, and a list of liked food IDs.
  - Registers user with Supabase Auth.
  - Saves liked foods in `user_food_preference`.

- **Login (`/login`):**
  - User provides email and password.
  - If credentials are valid, returns a JWT token for authentication.

- **JWT Token:**
  - Used to protect endpoints (like `/recommend`).
  - Token contains user ID and expiry.

### 2. Food Recommendation Logic

- **Fetching Preferences:**
  - For the authenticated user, fetches their liked food IDs.

- **Fetching Food Items:**
  - Loads all food items and categories from Supabase.

- **Grouping Foods:**
  - Foods are grouped by type using flags (`is_rice`, `is_swallow`, `is_fry`) or by category (Protein, Soup, Fruits, etc.).

- **Building Combos:**
  - **Rice Combo:** Random rice, two proteins, drink, and stew if available.
  - **Swallow Combo:** Swallow, soup, and a protein.
  - **Fried Combo:** Fried food, drink, and fruit.
  - **Extras:** Fills up to 5 combos with fast food items not already recommended.

- **Result:**
  - Returns up to 5 recommended combos, each as a list of food names.

### 3. API Endpoints

- `POST /signup`  
  Registers a new user and saves their food preferences.

- `POST /login`  
  Authenticates a user and returns a JWT token.

- `GET /foods`  
  Returns all food items and categories.

- `GET /recommend`  
  Returns up to 5 personalized food combos for the authenticated user.

---

## Example Usage

Start the API locally:

```sh
make run-local
```

**Signup Example:**

```json
POST /signup
{
  "email": "user@example.com",
  "password": "securepassword",
  "liked_food_ids": ["1", "2", "3"]
}
```

**Login Example:**

```json
POST /login
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Get Recommendations:**

```http
GET /recommend
Authorization: Bearer <your_jwt_token>
```

**Example response:**

```json
{
  "recommendations": [
    {"type": "Rice Combo", "Items": ["Jollof Rice", "Chicken", "Fish", "Stew", "Smoothie"]},
    {"type": "Swallow Combo", "Items": ["Amala", "Egusi", "Meat"]},
    {"type": "Fried combo", "Items": ["Fried Yam", "Smoothie", "Banana"]},
    {"type": "Extra", "Items": ["Burger"]},
    {"type": "Extra", "Items": ["Pizza"]}
  ]
}
```

---

## Environment Variables

Create a `.env` file with:

```plaintext
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
JWT_SECRET=your_jwt_secret
JWT_EXP_TIME=86400
```

---

## Dependencies

- fastapi
- uvicorn
- supabase
- pandas
- python-dotenv
- bcrypt
- pyjwt

Install with:

```sh
pip install fastapi uvicorn supabase pandas python-dotenv bcrypt pyjwt
```

---

## Code Reference

### model.py

```python
from pydantic import BaseModel
from typing import List

class UserSignUp(BaseModel):
    email: str
    password: str
    liked_food_ids: List[str]

class UserLogin(BaseModel):
    email: str
    password: str
```

### main.py (Key Parts)

- **Authentication:** Uses bcrypt for password hashing and JWT for tokens.
- **Supabase:** Connects using credentials from `.env`.
- **Recommendation:** Groups foods, builds combos, and returns up to 5 recommendations.
- **Endpoints:** `/signup`, `/login`, `/foods`, `/recommend` (JWT protected).

---

For more details, see the code in `main.py` and