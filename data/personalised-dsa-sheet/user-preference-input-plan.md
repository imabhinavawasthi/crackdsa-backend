# 📋 CrackDSA User Preference Specification

This document defines the schema and allowed values for the onboarding flow. This data is used by the backend to filter the problem pool and by the AI to sequence the daily roadmap.

---

## 1. Request Schema (JSON)

```json
{
  "prep_type": "placement",
  "target_level": "tier-1",
  "timeline_days": 60,
  "weekly_hours_estimate": 25,
  "dsa_exposure": "basic",
  "strong_topics": ["arrays", "hashing"],
  "weak_topics": ["dynamic-programming", "graphs"],
  "revision_strategy": "weekend_batch"
}
```

---

## 2. Field Definitions & Constraints

| Field | Type | Enum / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `prep_type` | `String` | `placement`, `switch`, `learning` | The primary goal of the preparation. |
| `target_level` | `String` | `tier-1`, `tier-2`, `tier-3` | Company difficulty tier (MAANG vs Service). |
| `timeline_days` | `Integer` | `15` to `180` | Total duration of the generated roadmap. |
| `weekly_hours_estimate` | `Integer` | `5` to `80` | Used to calculate total problem count. |
| `dsa_exposure` | `String` | `none`, `basic`, `intermediate`, `advanced` | Current proficiency level. |
| `strong_topics` | `List[String]` | See Topic Slugs | Topics to prune/reduce density. |
| `weak_topics` | `List[String]` | See Topic Slugs | Topics to prioritize/increase density. |
| `revision_strategy` | `String` | `weekend_batch` | Default logic for moving 'Revise' tasks. |

---

## 3. Master Topic Slugs

Use these exact string identifiers in the `strong_topics` and `weak_topics` arrays.

| Slug | Category |
| :--- | :--- |
| `arrays` | Arrays & Dynamic Arrays |
| `strings` | String Manipulation |
| `hashing` | Hash Maps & Sets |
| `linked-list` | Singly/Doubly Linked Lists |
| `stack-queue` | Stacks, Queues, Deques |
| `recursion-backtracking` | Recursion & State Space Search |
| `trees` | Binary Trees, BST, Heaps |
| `graphs` | BFS, DFS, Shortest Path |
| `dynamic-programming` | DP & Memoization |
| `greedy` | Greedy Algorithms |
| `sorting-searching` | Binary Search & Sort Algos |
| `bit-manipulation` | Bitwise Ops |
| `heaps` | Priority Queues |

---

## 4. Logical Enums (Backend Reference)

- **Target Tiers:**
  - `tier-1`: MAANG, Tier-1 Startups (High difficulty).
  - `tier-2`: Mid-tier Product Companies (Medium difficulty).
  - `tier-3`: Service-based/General (Easy/Medium difficulty).

- **Exposure Levels:**
  - `none`: Complete beginner, needs fundamentals first.
  - `basic`: Knows syntax, can solve Easy problems.
  - `intermediate`: Knows standard patterns (BFS/DFS), 100+ solved.
  - `advanced`: 300+ solved, targeting Hard optimization.