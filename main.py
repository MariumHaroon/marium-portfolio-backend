import os
import json
import smtplib
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from twilio.rest import Client as TwilioClient
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
# Mount Static Files Folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Root route serves HTML
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("static/index.html", "r") as f:
        return f.read()

# Aapke existing AI Chat routes niche jaise hain waise hi rahenge
@app.post("/api/chat")
async def chat_ai(data: dict):
    # logic...
    return {"reply": "AI Response"}


load_dotenv()

app = FastAPI(title="Marium Portfolio AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_key = os.getenv("GROQ_API_KEY")
if not groq_key:
    raise RuntimeError("GROQ_API_KEY is missing in .env file")

client = Groq(api_key=groq_key)


# --- 1. EMAIL HELPER ---
def send_email_notification(subject: str, body: str):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    receiver_email = os.getenv("MY_PERSONAL_EMAIL")

    if not all([sender_email, sender_password, receiver_email]):
        print("⚠️ Email credentials missing in .env")
        return

    try:
        msg = f"Subject: {subject}\n\n{body}"
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.encode('utf-8'))
        server.quit()
        print("✅ Email notification sent successfully!")
    except Exception as e:
        print(f"❌ Email notification failed: {e}")


# --- 2. WHATSAPP HELPER (SINGLE CLEAN FUNCTION) ---
def send_whatsapp_notification(text: str):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_whatsapp = os.getenv("TWILIO_WHATSAPP_NUMBER")
    to_whatsapp = os.getenv("MY_WHATSAPP_NUMBER")

    if not all([account_sid, auth_token, from_whatsapp, to_whatsapp]):
        print("⚠️ Twilio credentials missing in .env")
        return

    # Clean whitespace & quotes
    account_sid = account_sid.strip().strip('"').strip("'")
    auth_token = auth_token.strip().strip('"').strip("'")
    from_whatsapp = from_whatsapp.strip()
    to_whatsapp = to_whatsapp.strip()

    # Format numbers
    if not from_whatsapp.startswith("whatsapp:"):
        from_whatsapp = f"whatsapp:{from_whatsapp}"
    if not to_whatsapp.startswith("whatsapp:"):
        to_whatsapp = f"whatsapp:{to_whatsapp}"

    try:
        twilio_client = TwilioClient(account_sid, auth_token)
        
        # Split text into safe chunks of 1200 chars
        chunks = [text[i:i+1200] for i in range(0, len(text), 1200)]
        for chunk in chunks:
            message = twilio_client.messages.create(
                body=chunk,
                from_=from_whatsapp,
                to=to_whatsapp
            )
            print(f"✅ WhatsApp notification sent! SID: {message.sid}")
    except Exception as e:
        print(f"❌ WhatsApp failed: {e}")


# --- 3. LEAD LOGGING HELPER ---
def log_conversation_lead(visitor_name: str, inquiry_summary: str, contact_info: str = "Not provided"):
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    entry = f"[{time_str}] Name: {visitor_name} | Contact: {contact_info} | Summary: {inquiry_summary}\n"
    
    try:
        with open("my_inquiries_log.txt", "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"File log skipped: {e}")
    
    subject = f"🚨 New Client Lead: {visitor_name}"
    body = f"Hello Marium,\n\nA new client left details on your portfolio:\n\nName: {visitor_name}\nContact: {contact_info}\nSummary: {inquiry_summary}"
    
    send_email_notification(subject, body)
    send_whatsapp_notification(f"🚨 *New Client Lead*\n\n*Name:* {visitor_name}\n*Contact:* {contact_info}\n*Summary:* {inquiry_summary}")
    return "Lead logged."


# --- 4. FULL SESSION ROUTE ---
class ChatSessionLog(BaseModel):
    user_name: str = "Visitor"
    chat_history: list

@app.post("/log-full-session")
def log_full_session(data: ChatSessionLog):
    if not data.chat_history or len(data.chat_history) <= 1:
        return {"status": "ignored"}

    formatted_chat = ""
    for msg in data.chat_history:
        role = "👤 Visitor" if msg.get("sender") == "user" else "🤖 AI Agent"
        formatted_chat += f"{role}: {msg.get('text')}\n"

    time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Save local copy safely
    try:
        with open("full_chat_history.txt", "a", encoding="utf-8") as f:
            f.write(f"\n--- SESSION [{time_str}] ---\n{formatted_chat}{'-'*40}\n")
    except Exception as e:
        print(f"File write skipped: {e}")

    # Send Email
    subject = f"💬 Full Chat Transcript [{time_str}]"
    body = f"Hello Marium,\n\nHere is a complete chat transcript from your portfolio visitor:\n\n--- CHAT TRANSCRIPT ---\n\n{formatted_chat}"
    send_email_notification(subject, body)

    # Send WhatsApp
    whatsapp_body = f"💬 *Full Chat Transcript [{time_str}]*\n\n{formatted_chat}"
    send_whatsapp_notification(whatsapp_body)

    return {"status": "success"}


# --- 5. AI AGENT TOOL & ROUTE ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "log_conversation_lead",
            "description": "Logs inquiry details and notifies Marium via email and WhatsApp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "visitor_name": {"type": "string", "description": "Name of the visitor"},
                    "inquiry_summary": {"type": "string", "description": "Summary of project requirements or scope"},
                    "contact_info": {"type": "string", "description": "Email or WhatsApp number provided by user"}
                },
                "required": ["visitor_name", "inquiry_summary"]
            }
        }
    }
]

SYSTEM_PROMPT = """
You are 'Marium's AI Representative', representing Marium, an expert Full-Stack Developer specializing in MERN stack and Laravel.
NEVER identify yourself as OpenAI, Groq, Llama, Meta, or Gemini. Always identify as Marium's AI Representative.
Greet visitors politely, explain Marium's web/app development services, and gather their Name, Contact Info (Email/WhatsApp), and Project Details.
When they share their details, ALWAYS invoke the `log_conversation_lead` tool immediately.
"""

class UserInquiry(BaseModel):
    user_name: str = "Visitor"
    message: str

@app.post("/handle-message")
def handle_message(request: UserInquiry):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message empty")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{request.user_name}: {request.message}"}
    ]

    models_to_try = ["qwen/qwen3.6-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.3
            )
            response_message = response.choices[0].message

            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    if tool_call.function.name == "log_conversation_lead":
                        args = json.loads(tool_call.function.arguments)
                        log_conversation_lead(
                            visitor_name=args.get("visitor_name", "Visitor"),
                            inquiry_summary=args.get("inquiry_summary", "No summary provided"),
                            contact_info=args.get("contact_info", "Not provided")
                        )
                return {"reply": "Thank you! I have logged your details and notified Marium via Email and WhatsApp. She will reach out soon!"}

            return {"reply": response_message.content}
        except Exception:
            continue

    return {"reply": "Server busy, please try again."}