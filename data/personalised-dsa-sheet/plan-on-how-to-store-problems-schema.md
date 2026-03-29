# 📋 CrackDSA: Problem Data & Generation Strategy

## 1. Modular Data Structure
To prevent LLM context overflow, the problem database is split by **Topic Slugs**. Each file contains a stratified list of problems categorized by difficulty and pattern.

### **Problem Schema (`topic_name.json`)**
```json
{
  "topic": "Binary Search",
  "slug": "binary-search",
  "problem_pool": {
    "easy": [
      {
        "id": "bs-01",
        "name": "Binary Search",
        "url": "https://leetcode.com/problems/binary-search/",
        "pattern": "Basic Iteration",
        "is_foundational": true,
        "estimated_minutes": 15,
        "summary": "Standard search in a sorted array. Teaches boundary conditions and mid calculation.",
        "similar_problems": ["bs-05", "bs-12"]
      }
    ],
    "medium": [],
    "hard": []
  }
}
```

### **Key Metadata Fields**
* **`pattern`**: The specific sub-technique (e.g., *Search on Answer*, *Rotated Array*).
* **`is_foundational`**: Flag for "must-do" problems that define a topic.
* **`similar_problems`**: IDs of problems with identical logic for "Extra Practice" suggestions.
* **`summary`**: Short technical brief used by the AI to understand the problem's role in the roadmap.

---

## 2. Multi-Step Generation Pipeline
Instead of generating a 60-day plan in one prompt, the system uses a **three-tier "Zoom-In" strategy**.

### **Phase 1: Macro-Plan (Topic Allocation)**
* **Input**: User Preferences (`total_days`, `weak_topics`, `target_level`).
* **AI Task**: Distribute the total days across the high-level Topic Slugs.
* **Example Output**: 
    * *Days 1-4: Arrays*
    * *Days 5-10: Binary Search*
    * *Days 11-15: Linked Lists*

### **Phase 2: Weekly/Topic-Plan (Problem Selection)**
* **Input**: The assigned Topic (e.g., Binary Search) + the number of days + the Problem Pool for that specific topic.
* **AI Task**: Select specific `problem_id`s from the pool that fit the user's `weekly_hours` and `target_level`.
* **Constraint**: Ensure `is_foundational` problems are scheduled first.

### **Phase 3: Daily Guidance (Content Enrichment)**
* **Input**: The specific problem assigned for the day.
* **AI Task**: Generate a "Daily Tip" or "Focus Point" (e.g., *"Today, pay extra attention to how you handle the `low <= high` condition to avoid infinite loops."*).

---

## 3. The Adaptive "More Practice" Logic
This feature is handled via **Deterministic Backend Logic** (No AI required):
1.  User clicks **"Need more practice on this pattern"**.
2.  Backend fetches the current problem's `pattern` and its `similar_problems` array.
3.  Backend checks the `tasks` table to find the next available "Empty" or "Buffer" slot.
4.  Backend inserts the similar problem into the user's roadmap.

---

## 4. File Organization
The data will be stored in a directory-per-topic format to allow the FastAPI server to load only the necessary context:

```text
/data
  /problems
    arrays.json
    binary-search.json
    stack-queue.json
    dynamic-programming.json
    ...
```

---

## 🚀 Benefits of this Strategy
* **Zero Hallucination**: AI only chooses from a provided list of IDs; it cannot "make up" problems.
* **Scalability**: Adding a new topic only requires adding one `.json` file.
* **Personalization**: High-intensity users get more problems from the "Medium/Hard" arrays, while beginners get the `is_foundational` Easy set.