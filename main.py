from fastapi import FastAPI
from fastapi import Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
import logging
import os
import sqlite3
import json

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")

app = FastAPI()
DB_FILE = "semut_trace.db"


class RequestIn(BaseModel):
    type: str
    text: str


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_type TEXT NOT NULL,
            request_text TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            owner_notes TEXT,
            created_at TEXT NOT NULL
        )
    """)

    columns = {
        row[1]
        for row in cur.execute("PRAGMA table_info(requests)").fetchall()
    }
    if "owner_notes" not in columns:
        cur.execute("ALTER TABLE requests ADD COLUMN owner_notes TEXT")

    conn.commit()
    conn.close()


init_db()


@app.get("/")
def root():
    return {"message": "Semut Trace Online"}


@app.post("/request")
def create_request(req: RequestIn):
    request_text = req.text.strip()
    if not request_text:
        raise HTTPException(
            status_code=422,
            detail="Please enter a request."
        )

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    created_at = datetime.utcnow().isoformat()

    cur.execute("""
        INSERT INTO requests (request_type, request_text, status, result, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        req.type,
        request_text,
        "submitted",
        None,
        created_at
    ))

    request_id = cur.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": request_id,
        "type": req.type,
        "text": request_text,
        "status": "submitted",
        "created_at": created_at
    }


@app.get("/requests")
def get_requests():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, request_type, request_text, status, result, owner_notes, created_at
        FROM requests
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/new")
def new_request_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="new.html",
        context={"request": request}
    )

@app.post("/submit")
def submit_request(
    request: Request,
    request_text: str = Form("")
):
    request_text = request_text.strip()
    if not request_text:
        return templates.TemplateResponse(
            request=request,
            name="new.html",
            context={
                "request": request,
                "request_text": request_text,
                "error": "Please enter a request."
            },
            status_code=422
        )

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO requests
        (request_type, request_text, status, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        "Other",
        request_text,
        "submitted",
        datetime.utcnow().isoformat()
    ))

    request_id = cur.lastrowid
    conn.commit()
    conn.close()

    try:
        draft = _generate_ai_draft(request_id)
    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="new.html",
            context={
                "request": request,
                "request_text": request_text,
                "generation_error": exc.detail
            },
            status_code=exc.status_code
        )

    return templates.TemplateResponse(
        request=request,
        name="new.html",
        context={
            "request": request,
            "request_text": request_text,
            "draft": draft,
            "request_id": request_id
        }
    )


@app.get("/requests_page")
def requests_page(request: Request):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT *
        FROM requests
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="requests.html",
        context={
            "request": request,
            "requests": rows
        }
    )

@app.post("/request/{request_id}/result")
def save_result(
    request_id: int,
    result: str = Form(...)
):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        UPDATE requests
        SET result = ?, status = ?
        WHERE id = ?
    """, (
        result,
        "completed",
        request_id
    ))

    conn.commit()
    conn.close()

    return RedirectResponse(
        url="/requests_page",
        status_code=303
    )


@app.post("/request/{request_id}/notes")
def save_owner_notes(
    request_id: int,
    owner_notes: str = Form("")
):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        UPDATE requests
        SET owner_notes = ?
        WHERE id = ?
    """, (
        owner_notes,
        request_id
    ))

    conn.commit()
    conn.close()

    return RedirectResponse(
        url="/requests_page",
        status_code=303
    )


def _generate_ai_draft(request_id: int):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    request_row = conn.execute("""
        SELECT request_type, request_text, owner_notes
        FROM requests
        WHERE id = ?
    """, (request_id,)).fetchone()

    conn.close()

    if request_row is None:
        raise HTTPException(status_code=404, detail="Request not found")

    request_text = (request_row["request_text"] or "").strip()
    if not request_text:
        raise HTTPException(
            status_code=422,
            detail="Please enter a request before generating a draft"
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured"
        )

    request_type = (request_row["request_type"] or "").strip() or "Other"
    owner_notes = request_row["owner_notes"] or "No owner notes provided."

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            instructions=(
                "Create a professional business draft for the request below. "
                "Use the owner's notes as additional context. Return only the "
                "draft text. Do not claim the message was sent or approved. "
                "The business owner must review and approve the draft."
            ),
            input=(
                f"Request type:\n{request_type}\n\n"
                f"Request:\n{request_text}\n\n"
                f"Owner notes:\n{owner_notes}"
            )
        )
    except OpenAIError as exc:
        logger.exception(
            "OpenAI draft generation failed for request %s",
            request_id
        )

        api_status = getattr(exc, "status_code", None)
        if api_status == 401:
            detail = "OpenAI authentication failed; check OPENAI_API_KEY"
            response_status = 401
        elif api_status == 429:
            detail = "OpenAI quota or rate limit exceeded; check API billing and limits"
            response_status = 429
        elif api_status == 404:
            detail = "Configured OpenAI model was not found or is unavailable"
            response_status = 502
        elif api_status == 400:
            detail = "OpenAI rejected the draft generation request"
            response_status = 502
        elif api_status is None:
            detail = "Could not connect to OpenAI; check server network access"
            response_status = 502
        else:
            detail = f"OpenAI API request failed with status {api_status}"
            response_status = 502

        raise HTTPException(
            status_code=response_status,
            detail=detail
        ) from exc

    draft = response.output_text.strip()
    if not draft:
        raise HTTPException(
            status_code=502,
            detail="OpenAI returned an empty draft"
        )

    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        UPDATE requests
        SET result = ?
        WHERE id = ?
    """, (draft, request_id))
    conn.commit()
    conn.close()

    return draft


@app.post("/request/{request_id}/generate")
def generate_ai_draft(request_id: int):
    _generate_ai_draft(request_id)
    return RedirectResponse(
        url="/requests_page",
        status_code=303
    )
