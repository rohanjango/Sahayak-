from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict
from fastapi.middleware.cors import CORSMiddleware
import uuid

app = FastAPI()

# --- CORS (needed for GitHub Pages frontend) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# In-memory mock storage
# -----------------------
FORMS: Dict[str, dict] = {}
ANSWERS: Dict[str, dict] = {}

# -----------------------
# Request Models
# -----------------------

class IntentRequest(BaseModel):
    language: str
    user_text: str


class FormSubmitRequest(BaseModel):
    language: str
    source_type: str  # "link" or "file"
    form_link: str | None = None
    file_name: str | None = None


class NextQuestionRequest(BaseModel):
    form_id: str
    language: str


class AnswerSubmitRequest(BaseModel):
    form_id: str
    field_id: str
    answer: str
    language: str


# -----------------------
# 1️⃣ Analyze Intent
# -----------------------
@app.post("/analyze-intent")
def analyze_intent(req: IntentRequest):
    text = req.user_text.lower()

    if "form" in text or "bhar" in text or "fill" in text:
        return {"intent": "fill_form"}

    if "hello" in text or "hi" in text or "namaste" in text:
        return {"intent": "greeting"}

    return {"intent": "unknown"}


# -----------------------
# 2️⃣ Submit Form (Link/File)
# -----------------------
@app.post("/submit-form")
def submit_form(req: FormSubmitRequest):
    form_id = str(uuid.uuid4())

    # Mock form schema (POC-safe)
    FORMS[form_id] = {
        "steps": [
            {
                "field_id": "full_name",
                "question_hi": "Aapka poora naam kya hai?",
                "question_en": "What is your full name?",
                "selector": "input[name='name']"
            },
            {
                "field_id": "dob",
                "question_hi": "Aapki janam tithi kya hai?",
                "question_en": "What is your date of birth?",
                "selector": "input[name='dob']"
            }
        ],
        "current_step": 0
    }

    ANSWERS[form_id] = {}

    return {
        "form_id": form_id,
        "total_fields": len(FORMS[form_id]["steps"]),
        "message": "form_loaded"
    }


# -----------------------
# 3️⃣ Get Next Question
# -----------------------
@app.post("/next-question")
def next_question(req: NextQuestionRequest):
    form = FORMS.get(req.form_id)

    if not form:
        return {"status": "error", "message": "Form not found"}

    step_index = form["current_step"]

    if step_index >= len(form["steps"]):
        return {
            "status": "completed",
            "message": (
                "Form poora ho gaya" if req.language == "hi"
                else "Form completed"
            )
        }

    step = form["steps"][step_index]

    return {
        "field_id": step["field_id"],
        "question_text": (
            step["question_hi"] if req.language == "hi"
            else step["question_en"]
        ),
        "selector_hint": step["selector"]
    }


# -----------------------
# 4️⃣ Submit Answer
# -----------------------
@app.post("/submit-answer")
def submit_answer(req: AnswerSubmitRequest):
    form = FORMS.get(req.form_id)

    if not form:
        return {"status": "error", "message": "Form not found"}

    ANSWERS[req.form_id][req.field_id] = req.answer
    form["current_step"] += 1

    return {"status": "saved"}


# -----------------------
# Health Check
# -----------------------
@app.get("/")
def root():
    return {"status": "Sahayak backend running"}
