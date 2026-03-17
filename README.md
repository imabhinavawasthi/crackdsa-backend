# CrackDSA Backend

This is the FastAPI backend foundation for the CrackDSA coding interview preparation platform. It provides a clean, minimal, and scalable structure using Python 3, FastAPI, SQLAlchemy, and Pydantic.

## Prerequisites

- Python 3.9+
- PostgreSQL (if utilizing the real `DATABASE_URL` setup later on)

## Project Structure

```bash
backend/
├ app/
│   ├ main.py          # Application entry point, defines root and health endpoints
│   ├ config.py        # Environment variables loader
│   ├ database.py      # SQLAlchemy connection setup
│   ├ models/          # Database models (SQLAlchemy)
│   ├ schemas/         # Pydantic validation schemas
│   ├ routes/          # API route handlers
│   └ services/        # Business logic layer
```

## Setup Instructions

### 1. Create a Virtual Environment

It is recommended to use a virtual environment to manage dependencies locally.
Run the following at the root of the `backend` directory:

```bash
python3 -m venv venv
```

### 2. Activate the Virtual Environment

**On Mac/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

Install required libraries via pip:
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Ensure your `.env` file is present in the `backend/` directory. For a standard setup, fill in the `.env` file like this (adjust credentials as needed):
```ini
DATABASE_URL=postgresql://user:password@localhost/dbname
OPENAI_API_KEY=your-openai-key
```
*Note: If `DATABASE_URL` is empty, the application will default to an in-memory SQLite connection so that the app starts up without crashing, enabling rapid iteration on non-db functionality.*

### 5. Running the Server

Start the application with Uvicorn utilizing the reload flag for live reloads during development:

```bash
uvicorn app.main:app --reload
```
You can access the API safely running locally here:
- **Root URL**: http://127.0.0.1:8000/
- **Health Check URL**: http://127.0.0.1:8000/health
- **Swagger Documentation**: http://127.0.0.1:8000/docs
