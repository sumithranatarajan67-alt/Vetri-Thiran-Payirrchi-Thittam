from datetime import datetime, timezone
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Request,
    HTTPException,
    Header
)

from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, WorkoutPlan
from app.schemas import UserInput

from app.ai_service import (
    generate_workout_gemini,
    generate_nutrition_tip_with_flash,
    update_workout_plan
)

from app.config import ADMIN_TOKEN


router = APIRouter()

templates = Jinja2Templates(
    directory=str(
        Path(__file__).resolve().parent / "templates"
    )
)


@router.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@router.post("/generate-workout")
def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db)
):

    try:
        data = UserInput(
            username=username.strip(),
            user_id=user_id.strip(),
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity
        )

    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": f"Invalid input: {exc}"
            },
            status_code=422
        )

    try:

        user = db.query(User).filter(
            User.user_id == data.user_id
        ).first()

        if user is None:

            user = User(**data.model_dump())

            db.add(user)

        else:

            for key, value in data.model_dump().items():
                setattr(user, key, value)

        db.flush()

        workout_plan = generate_workout_gemini(data)

        nutrition_tip = generate_nutrition_tip_with_flash(
            data.goal
        )

        plan = WorkoutPlan(
            user_id=data.user_id,
            original_plan=workout_plan,
            nutrition_tip=nutrition_tip
        )

        db.add(plan)
        db.commit()
        db.refresh(user)
        db.refresh(plan)

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "plan": plan,
                "workout_plan": workout_plan,
                "nutrition_tip": nutrition_tip,
                "is_updated": False
            }
        )

    except Exception as exc:

        db.rollback()

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc)
            },
            status_code=503
        )


@router.post("/submit-feedback")
def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db)
):

    user_id = user_id.strip()

    user = db.query(User).filter(
        User.user_id == user_id
    ).first()

    plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == user_id
    ).order_by(
        WorkoutPlan.id.desc()
    ).first()

    if not user or not plan:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": "User or workout plan not found."
            },
            status_code=404
        )

    if len(feedback.strip()) < 5:

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "plan": plan,
                "workout_plan": plan.updated_plan or plan.original_plan,
                "nutrition_tip": plan.nutrition_tip,
                "is_updated": bool(plan.updated_plan),
                "error": "Please enter at least 5 characters."
            },
            status_code=422
        )

    try:

        revised_plan = update_workout_plan(
            plan.updated_plan or plan.original_plan,
            feedback.strip(),
            user
        )

        nutrition_tip = generate_nutrition_tip_with_flash(
            user.goal
        )

        plan.updated_plan = revised_plan
        plan.feedback = feedback.strip()
        plan.updated_at = datetime.now(timezone.utc)
        plan.nutrition_tip = nutrition_tip

        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "plan": plan,
                "workout_plan": revised_plan,
                "nutrition_tip": nutrition_tip,
                "is_updated": True,
                "success": "Your workout plan has been updated!"
            }
        )

    except Exception as exc:

        db.rollback()

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "plan": plan,
                "workout_plan": plan.updated_plan or plan.original_plan,
                "nutrition_tip": plan.nutrition_tip,
                "is_updated": bool(plan.updated_plan),
                "error": str(exc)
            },
            status_code=503
        )


@router.get("/view-all-users")
def view_all_users(
    request: Request,
    db: Session = Depends(get_db),
    x_admin_token: str | None = Header(default=None)
):

    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:

        raise HTTPException(
            status_code=401,
            detail="Valid X-Admin-Token header required."
        )

    users = db.query(User).order_by(
        User.created_at.desc()
    ).all()

    plans = db.query(WorkoutPlan).order_by(
        WorkoutPlan.created_at.desc()
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "users": users,
            "plans": plans
        }
    )


@router.get("/api/users")
def api_users(
    db: Session = Depends(get_db),
    x_admin_token: str | None = Header(default=None)
):

    if ADMIN_TOKEN and x_admin_token != ADMIN_TOKEN:

        raise HTTPException(
            status_code=401,
            detail="Valid X-Admin-Token header required."
        )

    users = db.query(User).all()

    return [
        {
            "user_id": user.user_id,
            "username": user.username,
            "age": user.age,
            "weight": user.weight,
            "goal": user.goal,
            "intensity": user.intensity
        }
        for user in users
    ]


@router.get("/api/plans/{user_id}")
def api_plan(
    user_id: str,
    db: Session = Depends(get_db)
):

    plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == user_id
    ).order_by(
        WorkoutPlan.id.desc()
    ).first()

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="Workout plan not found."
        )

    return {
        "user_id": user_id,
        "original_plan": plan.original_plan,
        "updated_plan": plan.updated_plan,
        "nutrition_tip": plan.nutrition_tip,
        "feedback": plan.feedback
    }