import os
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import agents
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

registered_users = []
daily_whatsapp_reminders_list = {}
def send_daily_hackathon_reminders():
    global daily_whatsapp_reminders_list
    daily_whatsapp_reminders_list = {}

    for user in registered_users:
        msg = (
            f"Reminder for Team {user['team_name']}! "
            f"Keep building for {user['hackathon_name']}."
        )

        encoded = urllib.parse.quote(msg)
        phone = user["leader_phone"].replace("+", "").replace(" ", "")

        if len(phone) == 10:
            phone = "91" + phone

        whatsapp_link = (
            f"https://api.whatsapp.com/send?"
            f"phone={phone}&text={encoded}"
        )

        daily_whatsapp_reminders_list[user["team_name"]] = {
            "phone": user["leader_phone"],
            "message": msg,
            "link": whatsapp_link
        }


scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_hackathon_reminders, "interval", days=1)
scheduler.start()

def send_email_smtp(smtp_settings, recipient, subject, body):
    try:
        print("Connecting SMTP...")
        print("Server:", smtp_settings["server"])
        print("Recipient:", recipient)

        msg = MIMEMultipart()
        msg['From'] = smtp_settings["sender"]
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_settings["server"], 587)
        server.starttls()

        print("Logging in...")
        server.login(
            smtp_settings["sender"],
            smtp_settings["password"]
        )

        print("Sending...")
        server.sendmail(
            smtp_settings["sender"],
            recipient,
            msg.as_string()
        )

        server.quit()
        print("MAIL SENT SUCCESS")
        return "Success"

    except Exception as e:
        print("SMTP ERROR:", e)
        raise e
    
class LaunchKitRequest(BaseModel):
    name: str
    theme: str
    audience: str
    rounds: int
    venue: Optional[str] = ""
    insta_id: Optional[str] = ""
    linkedin_id: Optional[str] = ""

# 🌟 1. மெயின் FastAPI ஆப்ஜெக்ட் (இதுதான் மிஸ் ஆகியிருந்தது பாஸ்!)
app = FastAPI(title="Hackathon Launch & Marketing Agent")

# 🌟 2. CORS செட்டிங்ஸ் (ஃபிரண்ட்-எண்ட் கனெக்ட் ஆக மிக முக்கியம்)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class RegistrationInput(BaseModel):
    team_name: str
    leader_email: str
    leader_phone: str
    hackathon_name: str


class CampaignInput(BaseModel):
    name: str
    theme: str
    audience: str
    budget: float


@app.get("/")
def read_root():
    return {"status": "Hackathon Launch & Marketing Agent is running perfectly, boss!"}

@app.post("/api/generate-launch-kit")
async def generate_launch_kit(payload: LaunchKitRequest):
    try:
        result = await agents.generate_launch_kit(
            name=payload.name,
            theme=payload.theme,
            audience=payload.audience,
            rounds=payload.rounds,
            venue=payload.venue,          # இங்கிருந்துதான் டேட்டா போகும்
            insta_id=payload.insta_id,
            linkedin_id=payload.linkedin_id
        )
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
# 🌟 3. சோஷியல் மீடியா ஐடி, பாஸ்வேர்ட் மற்றும் கன்பர்மேஷன் வாங்கும் மாடல்
class SocialPostRequest(BaseModel):
    platform: str  # "instagram" அல்லது "linkedin"
    username: str  
    password: str  
    caption: str
    confirm_post: bool  # பயனர் 'Yes' கொடுத்து கன்பர்ம் பண்ணா மட்டும் True
    demo_mode: Optional[bool] = False  # பிட்ச்/டெமோவிற்காக

@app.post("/api/share-social-media")
async def share_social_media(payload: SocialPostRequest):
    # பயனர் கன்பர்மேஷன் தராவிட்டால் போஸ்ட் ஆகாது பாஸ்!
    if not payload.confirm_post:
        return {"status": "Cancelled", "message": "Post was cancelled by the user. Confirmation not received."}

    import tempfile
    image_path = os.path.join(tempfile.gettempdir(), "hackathon_poster.jpg")
    if not os.path.exists(image_path) and not getattr(agents, "POSTER_GENERATED", False):
        # Fallback to local workspace
        image_path = os.path.join(os.path.dirname(__file__), "hackathon_poster.jpg")
        if not os.path.exists(image_path):
            raise HTTPException(status_code=400, detail="Poster image not found! Please generate launch kit first.")

    # டெமோ மோட் என்றால் சிமுலேஷன் செய்து உடனே சக்சஸ் தரும்!
    if payload.demo_mode:
        platform_name = "Instagram" if payload.platform.lower() == "instagram" else "LinkedIn"
        return {
            "status": "Success", 
            "message": f"[DEMO MODE] Successfully posted to {platform_name}! Caption: '{payload.caption[:60]}...'"
        }

    if payload.platform.lower() == "instagram":
        try:
            from instagrapi import Client
            cl = Client()
            cl.login(payload.username, payload.password)
            cl.photo_upload(image_path, payload.caption)
            return {"status": "Success", "message": "Successfully posted to Instagram for real!"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Instagram Real Post Error: {str(e)}")

    elif payload.platform.lower() == "linkedin":
        try:
            url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                "Authorization": f"Bearer {payload.username}",
                "X-Restli-Protocol-Version": "2.0.0",
                "Content-Type": "application/json"
            }
            share_json = {
                "author": f"urn:li:person:{payload.password}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": payload.caption},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
            res = requests.post(url, headers=headers, json=share_json)
            if res.status_code in [200, 201]:
                return {"status": "Success", "message": "Successfully verified and posted to LinkedIn!"}
            else:
                raise HTTPException(status_code=res.status_code, detail=res.text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LinkedIn Post Error: {str(e)}")

    raise HTTPException(status_code=400, detail="Invalid platform selected.")



class ReminderRequest(BaseModel):
    round_number: int
    days_left: int
    candidate_emails: Optional[str] = ""
    smtp_settings: Optional[dict] = None


@app.post("/api/round-reminder")
async def round_reminder(payload: ReminderRequest):
    try:
        message = await agents.generate_round_reminder(
            round_number=payload.round_number,
            days_left=payload.days_left,
        )
        
        email_status = ""
        if payload.candidate_emails:
            emails = [e.strip() for e in payload.candidate_emails.split(",") if e.strip()]
            subject = f"Deadline Reminder: Round {payload.round_number} - {payload.days_left} Days Left!"
            smtp_settings = {
                "server": "smtp.gmail.com",
                "port": "587",
                "sender": "mahamoorthi246@gmail.com",
                "password": "xqonynmtvkpdczip",
                "conductor_email": "mahamoorthi246@gmail.com"
            }
            for email in emails:
                send_email_smtp(smtp_settings, email, subject, message)
            email_status = f"Reminders sent to {len(emails)} candidate(s)!"
            
        return {"message": message, "email_status": email_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# 3. Registration event -> organizer alert + candidate confirmation message
#    (fired from your own registration form's backend logic)
# ---------------------------------------------------------------------------
class RegistrationEventRequest(BaseModel):
    candidate_name: str
    candidate_email: Optional[str] = ""
    hackathon_name: str
    total_registrations_today: int
    problem_statement: str
    smtp_settings: Optional[dict] = None


@app.post("/api/registration-event")
async def registration_event(payload: RegistrationEventRequest):
    try:
        result = await agents.generate_registration_update(
            candidate_name=payload.candidate_name,
            hackathon_name=payload.hackathon_name,
            total_registrations_today=payload.total_registrations_today,
            problem_statement=payload.problem_statement,
        )
        
        # Send emails if SMTP settings are provided
        smtp_settings = {
    "server": "smtp.gmail.com",
    "port": "587",
    "sender": "mahamoorthi246@gmail.com",
    "password": "xqonynmtvkpdczip",
    "conductor_email": "mahamoorthi246@gmail.com"
}
        
        # 1. Send welcoming email to Candidate with Welcome Msg & Problem Statement
        candidate_msg = result.get("candidate_message", "")
        candidate_subject = f"Welcome to {payload.hackathon_name}!"
        candidate_body = f"{candidate_msg}\n\nHere is your Problem Statement for the round:\n\n{payload.problem_statement}"
        
        cand_status = ""
        if payload.candidate_email:
            cand_status = send_email_smtp(smtp_settings, payload.candidate_email, candidate_subject, candidate_body)
            
        # 2. Send registration update to Organizer/Conductor
        conductor_msg = result.get("organizer_alert", "")
        conductor_subject = f"[Milestone Alert] {payload.hackathon_name}: {payload.total_registrations_today} Registrations!"
        
        conductor_email = smtp_settings.get("conductor_email") or smtp_settings.get("sender")
        cond_status = ""
        if conductor_email:
            cond_status = send_email_smtp(smtp_settings, conductor_email, conductor_subject, conductor_msg)
            
        result["email_status"] = f"Candidate: {cand_status} | Conductor: {cond_status}"
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# 4. Vision check — analyze an uploaded marketing asset
# ---------------------------------------------------------------------------
@app.post("/api/analyze-vision-assets")
async def analyze_vision_assets(campaign_name: str = Form(...), image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
        analysis = agents.analyze_vision_asset(
            image_bytes=image_bytes,
            mime_type=image.content_type or "image/jpeg",
            campaign_name=campaign_name,
        )
        return {"vision_analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# 5. Final Round Meet Scheduler
# ---------------------------------------------------------------------------
class MeetSchedulerRequest(BaseModel):
    candidates_raw: str
    start_time: str
    slot_duration_minutes: int
    platform: str
    confirm_scheduling: bool
    smtp_settings: Optional[dict] = None
    demo_mode: Optional[bool] = True

@app.post("/api/schedule-final-round")
async def schedule_final_round(payload: MeetSchedulerRequest):
    import datetime
    import random
    
    try:
        candidates = []
        raw_parts = payload.candidates_raw.split(",")
        for part in raw_parts:
            part = part.strip()
            if not part:
                continue
            if "<" in part and ">" in part:
                name = part.split("<")[0].strip()
                email = part.split("<")[1].replace(">", "").strip()
            else:
                name = part
                email = part
            candidates.append({"name": name, "email": email})
            
        if not candidates:
            raise HTTPException(status_code=400, detail="No valid candidates provided.")
            
        try:
            current_time = datetime.datetime.fromisoformat(payload.start_time)
        except Exception:
            current_time = datetime.datetime.now() + datetime.timedelta(days=1)
            
        schedule = []
        platform_name = "Google Meet" if payload.platform == "google_meet" else "Zoom"
        
        for cand in candidates:
            slot_start = current_time.strftime("%I:%M %p (%d %b %Y)")
            end_time = current_time + datetime.timedelta(minutes=payload.slot_duration_minutes)
            slot_end = end_time.strftime("%I:%M %p (%d %b %Y)")
            
            if payload.platform == "google_meet":
                code = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))
                meet_link = f"https://meet.google.com/{code[:3]}-{code[3:7]}-{code[7:]}"
            else:
                meet_id = "".join(random.choices("0123456789", k=10))
                pwd = "".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=12))
                meet_link = f"https://zoom.us/j/{meet_id}?pwd={pwd}"
                
            schedule.append({
                "name": cand["name"],
                "email": cand["email"],
                "start": slot_start,
                "end": slot_end,
                "link": meet_link
            })
            
            body = (
                f"Hi {cand['name']},\n\n"
                f"You have been scheduled for the Final Interview/Review Round!\n\n"
                f"Details:\n"
                f"- Platform: {platform_name}\n"
                f"- Date & Time: {slot_start} to {slot_end}\n"
                f"- Meeting Link: {meet_link}\n\n"
                f"Please join on time. Good luck!"
            )
            subject = f"Final Round Interview Schedule - {cand['name']}"
            
            if not payload.demo_mode and payload.smtp_settings:
                send_email_smtp(payload.smtp_settings, cand["email"], subject, body)
                
            current_time = end_time
            
        summary_table = "\n".join([f"- {s['name']} ({s['email']}): {s['start']} | {s['link']}" for s in schedule])
        conductor_body = (
            f"Hi Hackathon Conductor,\n\n"
            f"Here is the allocated slots schedule for the Final Round:\n\n"
            f"{summary_table}\n\n"
            f"Emails have been dispatched to all candidates."
        )
        conductor_subject = "Final Round Slots Allocation Table"
        
        conductor_email = payload.smtp_settings.get("conductor_email") if payload.smtp_settings else None
        if not conductor_email and payload.smtp_settings:
            conductor_email = payload.smtp_settings.get("sender")
            
        if not payload.demo_mode and payload.smtp_settings and conductor_email:
            send_email_smtp(payload.smtp_settings, conductor_email, conductor_subject, conductor_body)
            
        return {
            "status": "Success",
            "message": f"Successfully allocated slots for {len(candidates)} candidates and generated {platform_name} links.",
            "schedule": schedule
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v4/register-and-notify")
def register_and_notify(data: RegistrationInput):
    user = {
        "team_name": data.team_name,
        "leader_email": data.leader_email,
        "leader_phone": data.leader_phone,
        "hackathon_name": data.hackathon_name
    }

    registered_users.append(user)
    send_daily_hackathon_reminders()

    return {
        "status": "Registered Successfully",
        "total_registered": len(registered_users)
    }
@app.get("/api/v4/admin/daily-whatsapp-reminders")
def get_daily_whatsapp_reminders():
    return daily_whatsapp_reminders_list
@app.post("/api/v4/generate-lifecycle-campaign")
def generate_campaign(payload: CampaignInput):
    result = agents.run_lifecycle_marketing_workflow(
        payload.name,
        payload.theme,
        payload.audience,
        payload.budget
    )
    return result