"""
seed_pyq_data.py
-----------------
Seeds realistic multi-year PYQ data for a Metallurgical Engineering course
(MT301 - Physical Metallurgy) so the High-Yield Topic Predictor has genuine
historical patterns to learn from, rather than an empty database.

Design choices (deliberate, not random):
- Some topics appear almost every year (structurally important, e.g. Phase Diagrams)
- Some topics are cyclical/intermittent (appear every 2-3 years)
- One topic is "emerging" - only appears in the most recent 2 years (tests
  whether the model can pick up on recency trends, not just raw frequency)
- One topic was frequent early on but stopped appearing (tests whether the
  model correctly predicts it as LOW-yield now, not just high because
  historically frequent)
- Marks and difficulty vary realistically per question
"""

import random
from backend.db.sql_client import get_db, init_db

random.seed(42)  # reproducible

COURSE_CODE = "MT301"
YEARS = [2019, 2020, 2021, 2022, 2023, 2024]

# topic: (years_it_appears, typical_marks_range, difficulty_pool)
TOPIC_PATTERNS = {
    "Phase Diagrams":         (YEARS,                         (5, 10), ["Medium", "Hard"]),
    "Diffusion":              (YEARS,                         (5, 8),  ["Medium"]),
    "Heat Treatment":         (YEARS,                         (8, 10), ["Hard"]),
    "Crystal Structures":     ([2019, 2021, 2023],            (2, 5),  ["Easy", "Medium"]),
    "Nucleation and Growth":  ([2019, 2020, 2022, 2024],      (5, 8),  ["Medium", "Hard"]),
    "Recrystallization":      ([2020, 2022, 2024],            (5, 8),  ["Medium"]),
    "Solidification":         (YEARS,                         (8, 10), ["Hard"]),
    "TTT Diagrams":           ([2023, 2024],                   (8, 10), ["Hard"]),      # emerging topic
    "Fick's Laws":            ([2019, 2020, 2021],            (5, 8),  ["Medium"]),      # faded out
    "Corrosion":              ([2019, 2020, 2021, 2022],      (2, 5),  ["Easy"]),
    "Dislocation Theory":     ([2021, 2022, 2023, 2024],      (5, 8),  ["Medium", "Hard"]),
    "Martensitic Transformation": ([2022, 2023, 2024],        (8, 10), ["Hard"]),         # emerging topic
}

QUESTION_TYPES = ["Theory", "Numerical", "Derivation"]

def generate_questions():
    questions = []
    for topic, (years, marks_range, difficulties) in TOPIC_PATTERNS.items():
        for year in years:
            # 1-3 questions per topic per year it appears
            n_questions = random.choice([1, 1, 2, 3])
            for _ in range(n_questions):
                questions.append({
                    "course_code": COURSE_CODE,
                    "year": year,
                    "topic": topic,
                    "subtopic": None,
                    "question_type": random.choice(QUESTION_TYPES),
                    "marks": random.randint(*marks_range),
                    "raw_question": f"[Seeded] Explain/derive/solve a problem on {topic}.",
                    "difficulty": random.choice(difficulties),
                })
    return questions


def seed():
    init_db()
    questions = generate_questions()

    with get_db() as conn:
        # Clear any existing seeded data for this course (safe re-run)
        conn.execute("DELETE FROM pyq_questions WHERE course_code = ?", (COURSE_CODE,))
        conn.execute("DELETE FROM pyq_papers WHERE course_code = ?", (COURSE_CODE,))

        # Create one paper record per year (simulating one uploaded PDF per year)
        paper_ids = {}
        for year in YEARS:
            cur = conn.execute(
                "INSERT INTO pyq_papers (course_code, filename, year, exam_type) VALUES (?, ?, ?, ?)",
                (COURSE_CODE, f"MT301_endsem_{year}.pdf", year, "Endsem")
            )
            paper_ids[year] = cur.lastrowid

        # Insert questions, linked to their year's paper
        for q in questions:
            conn.execute("""
                INSERT INTO pyq_questions
                (paper_id, course_code, year, topic, subtopic, question_type, marks, raw_question, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper_ids[q["year"]], q["course_code"], q["year"], q["topic"],
                q["subtopic"], q["question_type"], q["marks"], q["raw_question"], q["difficulty"]
            ))

    print(f"Seeded {len(questions)} questions across {len(YEARS)} years for course {COURSE_CODE}.")
    print(f"Topics: {list(TOPIC_PATTERNS.keys())}")


if __name__ == "__main__":
    seed()