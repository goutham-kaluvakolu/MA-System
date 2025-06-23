from __future__ import annotations

import base64
import os.path
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from fastapi import FastAPI, HTTPException, Query
from fastapi_mcp import FastApiMCP

from pydantic import BaseModel
import uvicorn

# ──────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Gmail API Server",
    description="A FastAPI server for accessing Gmail messages",
    version="1.0.0"
)

mcp = FastApiMCP(app)
mcp.mount()

# Gmail OAuth / API helpers
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

BASE_DIR = Path(__file__).resolve().parent
CREDS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

_service = None  # module-level cache

# ──────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────────────────────
class MessageDetail(BaseModel):
    id: str
    subject: str
    sender: str
    to: str
    date: str
    has_attachment: bool 
    body: Optional[str] = None



class MessagesListResponse(BaseModel):
    messages: List[MessageDetail]
    count: int
    query: str

class GreetingResponse(BaseModel):
    greeting: str
    name: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# ──────────────────────────────────────────────────────────────────────────────
# Gmail helper functions
# ──────────────────────────────────────────────────────────────────────────────
def extract_text_from_payload(payload):
    """Extract plain text content from Gmail message payload."""
    if payload.get("parts"):
        # Multipart message
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
            # Recursively check nested parts
            if part.get("parts"):
                nested_text = extract_text_from_payload(part)
                if nested_text:
                    return nested_text
    else:
        # Simple message
        if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
    return None
def has_attachment(payload):
    if payload.get("filename"):
        return True
    if "parts" in payload:
        return any(has_attachment(part) for part in payload["parts"])
    return False
def get_service():
    """Return an authenticated gmail v1 service, refreshing / re-authing if needed."""
    global _service
    if _service:
        return _service

    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("No credentials found, creating new ones by running login.py")

    _service = build("gmail", "v1", credentials=creds)
    return _service


def list_message_ids(service, *, max_results: int = 10, query: str | None = None):
    """Get list of message IDs based on query."""
    try:
        resp = (
            service.users()
            .messages()
            .list(userId="me", maxResults=max_results, q=query)
            .execute()
        )
        return [m["id"] for m in resp.get("messages", [])]
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []


def fetch_message(service, msg_id: str) -> Optional[dict]:
    """Fetch message details: id, subject, from, to, date, and body."""
    try:
        msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        # Extract headers
        subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown Sender")
        to = next((h["value"] for h in headers if h["name"].lower() == "to"), "Unknown Recipient")
        date = next((h["value"] for h in headers if h["name"].lower() == "date"), "No Date")
        
        # Extract plain text from message
        body = extract_text_from_payload(payload)
        
        return {
            "id": msg_id,
            "subject": subject,
            "sender": sender,
            "to": to,
            "date": date,
            "body": body if body else "(no plain-text body found)"
        }
        
    except HttpError as error:
        print(f"An error occurred fetching message {msg_id}: {error}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None



def fetch_messages_in_batch(service, msg_ids: List[str]) -> List[MessageDetail]:
    """Fetches details for a list of message IDs in a single batch request."""
    detailed_messages: List[MessageDetail] = []
    
    def batch_callback(request_id, response, exception):
        if exception:
            print(f"Error in batch request {request_id}: {exception}")
        else:
            # Process the response from fetch_message logic
            payload = response.get("payload", {})
            headers = payload.get("headers", [])
            subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Unknown Sender")
            to = next((h["value"] for h in headers if h["name"].lower() == "to"), "Unknown Recipient")
            date = next((h["value"] for h in headers if h["name"].lower() == "date"), "No Date")
            
            body = extract_text_from_payload(payload)
            
            msg_detail = MessageDetail(
                id=response.get("id"),
                subject=subject,
                sender=sender,
                to=to,
                date=date,
                has_attachment=has_attachment(payload),
                body=body if body else "(no plain-text body found)"
            )
            detailed_messages.append(msg_detail)

    batch = service.new_batch_http_request(callback=batch_callback)

    for msg_id in msg_ids:
        batch.add(service.users().messages().get(userId="me", id=msg_id, format="full"))

    batch.execute()
    return detailed_messages


# ──────────────────────────────────────────────────────────────────────────────
# API Routes
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Gmail API Server",
        "version": "1.0.0",
        "endpoints": {
            "messages": "/messages",
            "greeting": "/greeting/{name}",
            "docs": "/docs"
        }
    }

@app.get("/messages", response_model=MessagesListResponse, summary="Get Gmail messages")
async def get_gmail_messages(
    max_results: int = Query(default=10, ge=1, le=100, description="Maximum number of messages to retrieve"),
    query: str = Query(default="", description="Search query for Gmail messages")
):
    try:
        service = get_service()
        ids = list_message_ids(service, max_results=max_results, query=query)

        if not ids:
            return MessagesListResponse(messages=[], count=0, query=query)

        detailed_messages = fetch_messages_in_batch(service, ids)

        return MessagesListResponse(
            messages=detailed_messages,
            count=len(detailed_messages),
            query=query
        )
    except Exception as e:
        print(f"Error in get_gmail_messages: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving messages: {str(e)}"
        )
@app.get("/greeting/{name}", response_model=GreetingResponse, summary="Get personalized greeting")
async def get_greeting(name: str) -> GreetingResponse:
    """
    Return a personalized greeting for the given name.
    
    - **name**: The name to include in the greeting
    """
    return GreetingResponse(
        greeting=f"Hello, {name}!",
        name=name
    )

@app.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "gmail-api-server"}



mcp.setup_server()

# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Starting Gmail FastAPI Server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation available at: http://localhost:8000/docs")
    print("Alternative docs at: http://localhost:8000/redoc")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)