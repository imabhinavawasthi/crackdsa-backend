# 📄 CrackDSA — Roadmap Generation API (MVP)

---

# 🎯 Objective

Build a backend API that generates a personalized DSA roadmap based on:

1. User preferences (from onboarding)
2. A static dataset of DSA problems (JSON for now)
3. AI-assisted generation (LLM)

This is the **core feature of CrackDSA**.

---

# 🧠 High-Level Flow

1. Client sends user preferences
2. Backend loads problem dataset (JSON)
3. Backend prepares structured input
4. Backend calls AI (LLM)
5. AI returns roadmap (day-wise plan)
6. Backend validates + formats response
7. Response returned to client

---

# 🧱 Architecture (MVC Pattern)

Follow MVC structure:

```
app/
  ├── controllers/
  │     roadmap_controller.py
  │
  ├── services/
  │     roadmap_service.py
  │     ai_service.py
  │
  ├── models/
  │     user_preferences.py
  │     roadmap.py
  │
  ├── utils/
  │     problem_loader.py
  │     validators.py
  │
  ├── routes/
  │     roadmap_routes.py
```

---

# 📥 API Design

## Endpoint

POST `/api/v1/roadmap/generate`

---

## Request Body

```json
{
  "prep_type": "placements",
  "target_level": "tier1",
  "timeline_days": 90,
  "weekly_hours": 10,
  "consistency_type": "consistent",
  "dsa_exposure": "basic",
  "strong_topics": ["arrays"],
  "weak_topics": ["dp", "graphs"],
  "language": "cpp",
  "language_level": "comfortable",
  "practice_preference": "guided",
  "revision_frequency": "medium"
}
```

---

## Response (MVP)

```json
{
  "total_days": 90,
  "days": [
    {
      "day": 1,
      "topic": "arrays",
      "tasks": [
        {
          "problem_id": "two_sum",
          "title": "Two Sum",
          "difficulty": "easy"
        }
      ],
      "revision": []
    }
  ]
}
```

---

# 📦 Problem Dataset (Static JSON)

File: `data/problems.json`

Structure:

```json
[
  {
    "id": "two_sum",
    "title": "Two Sum",
    "topic": "arrays",
    "subtopic": "hashing",
    "difficulty": "easy",
    "link": "https://...",
    "order_index": 1
  }
]
```

---

# 🔧 Components

---

## 1. Controller

File: `roadmap_controller.py`

Responsibilities:

* Receive API request
* Validate input
* Call service layer
* Return response

---

## 2. Service Layer

### roadmap_service.py

Responsibilities:

* Load problems
* Prepare structured input
* Call AI service
* Post-process AI response

---

### ai_service.py

Responsibilities:

* Call LLM (OpenAI / Gemini / etc.)
* Pass prompt + structured data
* Return parsed response

---

## 3. Models

### user_preferences.py

Pydantic model for input validation

---

### roadmap.py

Defines output structure

---

## 4. Utils

### problem_loader.py

* Load JSON dataset
* Filter by topic/difficulty

---

### validators.py

* Validate timeline
* Validate hours
* Sanitize inputs

---

# 🤖 AI Integration (IMPORTANT)

We will use an LLM to generate the roadmap.

---

## Prompt Strategy

The AI should:

* Take user preferences
* Take list of problems
* Generate a **day-wise roadmap**
* Distribute problems across days
* Prioritize weak topics
* Balance difficulty

---

## Example Prompt (to AI)

```
You are building a personalized DSA roadmap.

User Preferences:
- Timeline: 90 days
- Weak topics: dp, graphs
- Strong topics: arrays
- Weekly hours: 10

Problem Dataset:
[...list of problems...]

Task:
Generate a day-wise roadmap.

Rules:
- Each day should have 2-3 problems
- Include revision every 7th day
- Prioritize weak topics more frequently
- Start from easier problems and increase difficulty gradually

Return JSON format:
{
  "days": [
    {
      "day": 1,
      "topic": "...",
      "problems": [...]
    }
  ]
}
```

---

# ⚠️ Important Constraints

* Do NOT send entire dataset if too large (limit to relevant subset)
* Keep response structured JSON
* Validate AI output before returning
* Handle failures gracefully

---

# 🧪 Validation Rules

* timeline_days >= 30 (placements/switch)
* weekly_hours >= 5
* topics must be valid

---

# 🚀 MVP Scope

We are building:

* Single API
* Static problem dataset
* AI-based roadmap generation
* Basic validation

We are NOT building:

* DB persistence
* user authentication
* adaptive learning
* analytics

---

# 🔮 Future Improvements

* Move problems to DB
* Add caching
* Hybrid logic (AI + deterministic)
* Adaptive roadmap updates

---

# 📦 Output Requirements

The implementation should:

* Follow clean MVC structure
* Use FastAPI
* Use Pydantic models
* Be modular and readable
* Be easy to extend

---

# 🎯 Summary

This API is the core of CrackDSA.

It transforms:
👉 user input → personalized roadmap

Focus on:

* clarity
* structure
* correctness

Avoid:

* overengineering
* unnecessary complexity
