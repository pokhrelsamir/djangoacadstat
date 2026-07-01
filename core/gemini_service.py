import os
import json
from google import genai

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)


def generate_student_recommendation(student, analytics_data):
    """
    Generate AI recommendation for a student.
    Returns a Python dictionary.
    """

    prompt = f"""
You are an experienced academic advisor.

Analyze this student's academic performance.

Student Name:
{student.name}

Level:
{student.level}

Class:
{student.student_class}

Semester:
{student.semester}

Average Percentage:
{analytics_data["avg_pct"]}%

Highest Percentage:
{analytics_data["highest_pct"]}%

Lowest Percentage:
{analytics_data["lowest_pct"]}%

Pass Rate:
{analytics_data["pass_rate"]}%

Subjects:
{analytics_data["subjects"]}

Return ONLY valid JSON.

Use this exact structure.

{{
    "summary":"",

    "strengths":[
        "",
        ""
    ],

    "weaknesses":[
        "",
        ""
    ],

    "recommendations":[
        "",
        "",
        ""
    ],

    "motivation":""
}}

Do not include markdown.
Do not wrap JSON inside ```.

Return JSON only.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    text = response.text.strip()

    try:
        return json.loads(text)
    except Exception:
        return {
            "summary": text,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "motivation": ""
        }