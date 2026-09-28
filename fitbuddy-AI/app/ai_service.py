from google import genai
from google.genai import types

from app.config import (
    GOOGLE_API_KEY,
    WORKOUT_MODEL,
    TIP_MODEL
)


def get_client():

    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "Google API key is missing. "
            "Please add GOOGLE_API_KEY to your .env file."
        )

    return genai.Client(
        api_key=GOOGLE_API_KEY
    )


def generate_text(model, prompt):

    client = get_client()

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=5000
        )
    )

    result = (response.text or "").strip()

    if not result:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return result


def generate_workout_gemini(user):

    prompt = f"""
Create a personalized 7-day fitness workout plan.

User Information:
Name: {user.username}
Age: {user.age}
Weight: {user.weight} kg
Fitness Goal: {user.goal}
Workout Intensity: {user.intensity}

Requirements:

1. Create a complete 7-day workout schedule.
2. Include a warm-up of 5-10 minutes.
3. Include exercises with sets and repetitions.
4. Include cooldown and recovery guidance.
5. Include at least one rest or recovery day.
6. Make the plan suitable for the selected intensity.
7. Use clear headings for each day.
8. Avoid extreme exercise recommendations.
9. Remind the user to stop if they experience pain.

Return a clear, structured workout plan.
"""

    return generate_text(
        WORKOUT_MODEL,
        prompt
    )


def generate_nutrition_tip_with_flash(goal):

    prompt = f"""
Provide one concise, practical nutrition or recovery tip
for someone whose fitness goal is: {goal}.

Keep it easy to understand.
Avoid extreme dieting and medical claims.
"""

    return generate_text(
        TIP_MODEL,
        prompt
    )


def update_workout_plan(
    original_plan,
    feedback,
    user
):

    prompt = f"""
Update the following workout plan based on user feedback.

User Goal: {user.goal}
Workout Intensity: {user.intensity}

Original Plan:
{original_plan}

User Feedback:
{feedback}

Requirements:
- Return the complete revised 7-day plan.
- Incorporate the user's feedback where appropriate.
- Keep the plan safe and practical.
- Include recovery and rest.
- Use clear day-by-day headings.
"""

    return generate_text(
        WORKOUT_MODEL,
        prompt
    )