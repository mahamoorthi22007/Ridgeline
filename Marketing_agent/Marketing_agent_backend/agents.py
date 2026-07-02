import os
import hashlib
import random
import urllib.parse
import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import MODEL_ID, ai_client, generate_text
import memory

# ---------------------------------------------------------------------------
# Text-block parsing (Groq copy generation)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# NEW: Lifecycle Marketing Workflow
# ---------------------------------------------------------------------------
def run_lifecycle_marketing_workflow(name: str, theme: str, audience: str, budget: float):
    try:
        router_prompt = (
            f"You are an Advanced Growth Hacker.\n"
            f"Hackathon Name: {name}\n"
            f"Theme: {theme}\n"
            f"Audience: {audience}\n"
            f"Budget: {budget}\n\n"
            f"Generate a strategy and campaign content."
        )

        strategy = generate_text(router_prompt)

        content_prompt = (
            f"Based on this strategy:\n{strategy}\n\n"
            f"Generate:\n"
            f"1. Email Campaign\n"
            f"2. WhatsApp Campaign\n"
            f"3. Instagram Ad Copy"
        )

        assets = generate_text(content_prompt)

        return {
            "strategy": strategy,
            "content_assets": assets
        }

    except Exception as e:
        return {
            "strategy": "Fallback strategy",
            "content_assets": f"Generation failed: {str(e)}"
        }


# ---------------------------------------------------------------------------
# NEW: Vision Placeholder
# ---------------------------------------------------------------------------
def analyze_vision_asset(image_bytes, mime_type, campaign_name):
    return (
        f"Vision analysis placeholder for campaign '{campaign_name}'. "
        f"Image received ({mime_type}), {len(image_bytes)} bytes."
    )

def _clean_section(text: str, marker: str, next_marker: str = None) -> str:
    """Helper to extract a clean string between two markdown markers."""
    if marker not in text:
        return ""
    try:
        start_idx = text.find(marker) + len(marker)
        if next_marker and next_marker in text:
            end_idx = text.find(next_marker, start_idx)
            return text[start_idx:end_idx].strip()
        return text[start_idx:].strip()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Poster composition
#
# AI image models (Flux included) are unreliable at rendering multi-word,
# crisp typography -- that's why the old poster had garbled letters. So we
# split the job in two:
#   1) Ask the AI image model for a pure abstract/art background (explicitly
#      told to draw NO text at all).
#   2) Draw the event name, theme, tagline, and detail chips ourselves with
#      PIL, using real fonts, glow effects, a glass-card frame, and an
#      accent palette chosen per-event. This guarantees the letters are
#      100% legible while still looking designed, not slapped-on.
# If the AI background fetch fails for any reason (offline, rate limit),
# we fall back to a procedurally generated abstract background so poster
# generation never breaks.
# ---------------------------------------------------------------------------

POSTER_W, POSTER_H = 1080, 1350

_FONT_DIRS = [
    "C:/Windows/Fonts", "C:/WINDOWS/Fonts",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    os.path.dirname(os.path.abspath(__file__)),
]
_BOLD_CANDIDATES = ["arialbd.ttf", "Arial Bold.ttf", "seguisb.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"]
_REG_CANDIDATES = ["arial.ttf", "segoeui.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]

_PALETTES = [
    ((0, 229, 255), (10, 12, 24)),    # cyan on near-black
    ((255, 61, 129), (18, 8, 20)),    # magenta on deep plum
    ((255, 176, 32), (16, 12, 6)),    # amber on dark brown
    ((124, 92, 255), (10, 8, 26)),    # violet on indigo-black
    ((57, 255, 176), (6, 16, 14)),    # mint on dark green-black
]


def _find_font(candidates, size):
    for d in _FONT_DIRS:
        for name in candidates:
            path = os.path.join(d, name)
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
    try:
        return ImageFont.truetype(candidates[0], size)
    except Exception:
        return ImageFont.load_default()


def _bold_font(size):
    return _find_font(_BOLD_CANDIDATES, size)


def _reg_font(size):
    return _find_font(_REG_CANDIDATES, size)


def _pick_palette(seed_text: str):
    h = int(hashlib.md5(seed_text.encode("utf-8")).hexdigest(), 16)
    return _PALETTES[h % len(_PALETTES)]


def _fit_text(draw, text, font_loader, max_width, start_size, min_size, max_lines=2):
    """Shrinks font size until the wrapped text fits within max_width / max_lines."""
    size = start_size
    lines = [text]
    while size >= min_size:
        font = font_loader(size)
        words = text.split()
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if draw.textlength(trial, font=font) <= max_width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        if len(lines) <= max_lines and all(draw.textlength(l, font=font) <= max_width for l in lines):
            return font, lines
        size -= 4
    font = font_loader(min_size)
    return font, (lines or [text])[:max_lines]


def _draw_glow_text(base_img, xy, lines, font, fill, glow_color, line_gap=1.15, glow_radius=16):
    """Draws centered text with a soft neon glow behind crisp solid letters."""
    glow_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    x, y = xy
    line_height = font.size * line_gap
    for i, line in enumerate(lines):
        w = gd.textlength(line, font=font)
        gd.text((x - w / 2, y + i * line_height), line, font=font, fill=glow_color + (255,))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(glow_radius))
    base_img.alpha_composite(glow_layer)

    draw = ImageDraw.Draw(base_img)
    for i, line in enumerate(lines):
        w = draw.textlength(line, font=font)
        draw.text((x - w / 2, y + i * line_height), line, font=font, fill=fill)
    return len(lines) * line_height


def _procedural_background(accent, dark, seed_text: str) -> Image.Image:
    """Offline fallback background: glow blobs + circuit-style lines."""
    img = Image.new("RGB", (POSTER_W, POSTER_H), dark).convert("RGBA")
    rnd = random.Random(seed_text)
    for _ in range(5):
        cx, cy = rnd.randint(0, POSTER_W), rnd.randint(0, POSTER_H)
        r = rnd.randint(150, 420)
        glow = Image.new("RGBA", (POSTER_W, POSTER_H), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent + (40,))
        glow = glow.filter(ImageFilter.GaussianBlur(120))
        img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img, "RGBA")
    for _ in range(28):
        x1, y1 = rnd.randint(0, POSTER_W), rnd.randint(0, POSTER_H)
        length = rnd.randint(60, 260)
        horiz = rnd.random() > 0.5
        x2, y2 = (x1 + length, y1) if horiz else (x1, y1 + length)
        draw.line([x1, y1, x2, y2], fill=accent + (60,), width=2)
        draw.ellipse([x2 - 3, y2 - 3, x2 + 3, y2 + 3], fill=accent + (120,))
    return img


def _fetch_ai_background(theme: str, seed_text: str) -> "Image.Image | None":
    """Text-free abstract art background from the AI image model."""
    image_prompt = (
        f"A premium abstract futuristic tech background themed around '{theme}'. "
        f"Glowing neon geometric shapes, circuit-like network lines, particles, depth of field, "
        f"cinematic lighting, 8k digital art. "
        f"ABSOLUTELY NO TEXT, NO WORDS, NO LETTERS, NO NUMBERS, NO TYPOGRAPHY, NO WATERMARK, "
        f"NO LOGOS anywhere in the image -- pure abstract background art only."
    )
    encoded_prompt = urllib.parse.quote(image_prompt)
    seed = int(hashlib.md5(seed_text.encode("utf-8")).hexdigest(), 16) % 100000
    url = (
        f"https://image.pollinations.ai/p/{encoded_prompt}"
        f"?width={POSTER_W}&height={POSTER_H}&model=flux&seed={seed}&nologo=true"
    )
    try:
        response = requests.get(url, timeout=25)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            if img.size != (POSTER_W, POSTER_H):
                img = img.resize((POSTER_W, POSTER_H))
            return img
    except Exception as e:
        print(f"AI background fetch failed, using procedural fallback: {e}")
    return None


def _compose_poster(name: str, theme: str, tagline: str, poster_text: str, audience: str, rounds: int,venue="") -> Image.Image:
    seed_text = f"{name}|{theme}"
    accent, dark = _pick_palette(seed_text)

    bg = _fetch_ai_background(theme, seed_text)
    if bg is None:
        bg = _procedural_background(accent, dark, seed_text)
    img = bg.convert("RGBA")

    # Bottom-weighted dark gradient so text stays legible over busy art
    grad = Image.new("L", (1, POSTER_H), 0)
    for y in range(POSTER_H):
        t = y / POSTER_H
        val = int(255 * min(1.0, max(0.0, (t - 0.22) / 0.60)))
        grad.putpixel((0, y), val)
    grad = grad.resize((POSTER_W, POSTER_H))
    dark_layer = Image.new("RGBA", (POSTER_W, POSTER_H), dark + (255,))
    dark_layer.putalpha(grad)
    img = Image.alpha_composite(img, dark_layer)

    draw = ImageDraw.Draw(img, "RGBA")

    # Glass-card frame
    margin = 36
    draw.rounded_rectangle([margin, margin, POSTER_W - margin, POSTER_H - margin], radius=28, outline=accent + (220,), width=4)
    draw.rounded_rectangle([margin + 10, margin + 10, POSTER_W - margin - 10, POSTER_H - margin - 10], radius=22, outline=accent + (90,), width=1)

    # Corner brackets
    cl = 46
    for (cx, cy, dx, dy) in [
        (margin, margin, 1, 1), (POSTER_W - margin, margin, -1, 1),
        (margin, POSTER_H - margin, 1, -1), (POSTER_W - margin, POSTER_H - margin, -1, -1),
    ]:
        draw.line([cx, cy, cx + dx * cl, cy], fill=accent + (255,), width=5)
        draw.line([cx, cy, cx, cy + dy * cl], fill=accent + (255,), width=5)

    # Top badge
    badge_font = _bold_font(28)
    badge_text = (poster_text or "HACKATHON").strip().upper()[:24] or "HACKATHON"
    bw = draw.textlength(badge_text, font=badge_font)
    bx0, by0 = POSTER_W / 2 - bw / 2 - 26, 90
    bx1, by1 = POSTER_W / 2 + bw / 2 + 26, 90 + 52
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=26, fill=accent + (230,))
    draw.text((POSTER_W / 2, by0 + 26), badge_text, font=badge_font, fill=dark, anchor="mm")

    # Event name -- big glowing title (this is what has to stay crisp/readable)
    title_font, title_lines = _fit_text(draw, name.upper(), _bold_font, POSTER_W - 220, 96, 44, max_lines=2)
    title_y = 200
    used_h = _draw_glow_text(img, (POSTER_W / 2, title_y), title_lines, title_font, (255, 255, 255, 255), accent, glow_radius=16)
    draw = ImageDraw.Draw(img, "RGBA")

    # Theme ling
    theme_font, theme_lines = _fit_text(draw, theme.upper(), _bold_font, POSTER_W - 260, 46, 26, max_lines=2)
    theme_y = title_y + used_h + 20
    used_h2 = _draw_glow_text(img, (POSTER_W / 2, theme_y), theme_lines, theme_font, accent + (255,), accent, glow_radius=10)
    draw = ImageDraw.Draw(img, "RGBA")

    # Tagline
    clean_tagline = (tagline or "").strip().strip('"').strip()
    tag_font, tag_lines = _fit_text(draw, clean_tagline, _reg_font, POSTER_W - 260, 34, 20, max_lines=3)
    tag_y = theme_y + used_h2 + 30
    for i, line in enumerate(tag_lines):
        w = draw.textlength(line, font=tag_font)
        draw.text((POSTER_W / 2 - w / 2, tag_y + i * tag_font.size * 1.3), line, font=tag_font, fill=(235, 235, 245, 235))

    # Venue
    if venue:
        clean_venue = venue.strip().upper()
        venue_font, venue_lines = _fit_text(draw, f"VENUE: {clean_venue}", _bold_font, POSTER_W - 260, 28, 18, max_lines=2)
        venue_y = tag_y + len(tag_lines) * tag_font.size * 1.3 + 40
        for i, line in enumerate(venue_lines):
            w = draw.textlength(line, font=venue_font)
            draw.text((POSTER_W / 2 - w / 2, venue_y + i * venue_font.size * 1.3), line, font=venue_font, fill=accent + (255,))

    # Footer detail chips
    chip_font = _bold_font(24)
    chips = [f"Audience: {audience}", f"{rounds} Round" + ("s" if rounds != 1 else "")]
    chip_y = POSTER_H - margin - 90
    widths = [draw.textlength(c, font=chip_font) + 56 for c in chips]
    total_w = sum(widths) + 20 * (len(chips) - 1)
    cx = POSTER_W / 2 - total_w / 2
    for c, cw in zip(chips, widths):
        draw.rounded_rectangle([cx, chip_y, cx + cw, chip_y + 56], radius=28, outline=accent + (255,), width=2, fill=dark + (160,))
        draw.text((cx + cw / 2, chip_y + 28), c, font=chip_font, fill=(255, 255, 255, 255), anchor="mm")
        cx += cw + 20

    return img.convert("RGB")


POSTER_GENERATED = False


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def generate_launch_kit(
    name: str, 
    theme: str, 
    audience: str, 
    rounds: int = 1, 
    venue: str = "", 
    insta_id: str = "", 
    linkedin_id: str = ""
) -> dict:
    """Generates marketing copy + a composed poster image for a hackathon."""

    text_prompt = (
        f"You are an expert tech growth hacker.\n"
        f"Based on the following hackathon details, generate high-converting marketing copy:\n"
        f"- Name: {name}\n"
        f"- Theme: {theme}\n"
        f"- Target: {audience}\n"
        f"- Rounds: {rounds}\n"
        f"- Venue/Date: {venue}\n"
        f"- Instagram Handle: {insta_id}\n"
        f"- LinkedIn Handle: {linkedin_id}\n\n"
        f"CRITICAL: Break your output EXACTLY into these blocks using the bracket tags:\n"
        f"[TAGLINE_WHATSAPP] -> A short, high-open-rate tagline/hook for WhatsApp broadcasts.\n"
        f"[TAGLINE_INSTAGRAM] -> A viral, catchy tagline/hook for Instagram posts.\n"
        f"[TAGLINE_EMAIL] -> An irresistible, clickable subject line/tagline for Email invites.\n"
        f"[TAGLINE_LINKEDIN] -> A professional, scroll-stopping headline/tagline for LinkedIn posts.\n"
        f"[POSTER_TEXT] -> Write 2-3 extremely short words for the poster overlay.\n"
        f"[INSTAGRAM] -> Write an exciting Instagram caption with emojis and hashtags, mentioning {insta_id}.\n"
        f"[LINKEDIN] -> Write a professional LinkedIn post built for maximum engagement, mentioning {linkedin_id}.\n"
        f"[WHATSAPP] -> Write a punchy WhatsApp broadcast message.\n"
        f"[EMAIL] -> Write an irresistible invite email template.\n"
        f"[UNSTOP_COPY] -> Provide a listing description for Unstop including Title, Rules, Eligibility, and Rewards.\n"
        f"[DEVPOST_COPY] -> Provide a listing description for Devpost including Pitch, What it does, and Challenges.\n"
        f"[HACKEREARTH_COPY] -> Provide a listing description for HackerEarth including Description, Stages, and Timeline."
    )

    raw_content = generate_text(text_prompt)

    tagline_whatsapp = _clean_section(raw_content, "[TAGLINE_WHATSAPP]", "[TAGLINE_INSTAGRAM]")
    tagline_instagram = _clean_section(raw_content, "[TAGLINE_INSTAGRAM]", "[TAGLINE_EMAIL]")
    tagline_email = _clean_section(raw_content, "[TAGLINE_EMAIL]", "[TAGLINE_LINKEDIN]")
    tagline_linkedin = _clean_section(raw_content, "[TAGLINE_LINKEDIN]", "[POSTER_TEXT]")
    poster_text_content = _clean_section(raw_content, "[POSTER_TEXT]", "[INSTAGRAM]")
    insta_caption = _clean_section(raw_content, "[INSTAGRAM]", "[LINKEDIN]")
    linkedin_content = _clean_section(raw_content, "[LINKEDIN]", "[WHATSAPP]")
    whatsapp_content = _clean_section(raw_content, "[WHATSAPP]", "[EMAIL]")
    email_content = _clean_section(raw_content, "[EMAIL]", "[UNSTOP_COPY]")
    unstop_content = _clean_section(raw_content, "[UNSTOP_COPY]", "[DEVPOST_COPY]")
    devpost_content = _clean_section(raw_content, "[DEVPOST_COPY]", "[HACKEREARTH_COPY]")
    hackerearth_content = _clean_section(raw_content, "[HACKEREARTH_COPY]")

    # Default fallbacks
    if not tagline_whatsapp: tagline_whatsapp = "Innovate the future!"
    if not tagline_instagram: tagline_instagram = "Are you ready to build?"
    if not tagline_email: tagline_email = "Exclusive Invite: Summit Build 2026"
    if not tagline_linkedin: tagline_linkedin = "Join the next wave of innovation."
    if not unstop_content: unstop_content = "Hackathon on Unstop. Rules and Eligibility details inside."
    if not devpost_content: devpost_content = "Hackathon on Devpost. Pitch and Challenges details inside."
    if not hackerearth_content: hackerearth_content = "Hackathon on HackerEarth. Description and Stages details inside."
    
    img_html_render = ""
    try:
        # Poster composition
        poster_img = _compose_poster(
            name=name, theme=theme, tagline=tagline_instagram,
            poster_text=poster_text_content, audience=audience, rounds=rounds, venue=venue
        )
        # Save to temp directory to prevent hot-reload refresh of client page
        import tempfile
        poster_path = os.path.join(tempfile.gettempdir(), "hackathon_poster.jpg")
        poster_img.save(poster_path, format="JPEG", quality=95)
        
        # Mark as generated for main.py check
        global POSTER_GENERATED
        POSTER_GENERATED = True
        
        # Base64 render for frontend
        buffered = BytesIO()
        poster_img.save(buffered, format="JPEG", quality=95)
        base64_image_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        img_html_render = f"data:image/jpeg;base64,{base64_image_str}"
    except Exception as e:
        print(f"Poster composition error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    try:
        memory.store_content(name, "launch_kit", raw_content)
    except Exception as e:
        print(f"Memory store error: {e}")

    response_data = {
        "poster_image": img_html_render,
        "tagline_whatsapp": tagline_whatsapp,
        "tagline_instagram": tagline_instagram,
        "tagline_email": tagline_email,
        "tagline_linkedin": tagline_linkedin,
        "instagram_poster": insta_caption,
        "whatsapp_message": whatsapp_content,
        "email": email_content,
        "linkedin_post": linkedin_content,
        "unstop_copy": unstop_content,
        "devpost_copy": devpost_content,
        "hackerearth_copy": hackerearth_content,
        "venue": venue,
        "insta_handle": insta_id,
        "linkedin_handle": linkedin_id,
        "sections": {
            "tagline_whatsapp": tagline_whatsapp,
            "tagline_instagram": tagline_instagram,
            "tagline_email": tagline_email,
            "tagline_linkedin": tagline_linkedin,
            "instagram_poster": insta_caption,
            "whatsapp_message": whatsapp_content,
            "email": email_content,
            "linkedin_post": linkedin_content,
            "unstop_copy": unstop_content,
            "devpost_copy": devpost_content,
            "hackerearth_copy": hackerearth_content,
            "venue_info": venue
        },
    }

    return response_data


async def generate_registration_update(
    candidate_name: str,
    hackathon_name: str,
    total_registrations_today: int,
    problem_statement: str
) -> dict:
    """Generates an organizer milestone alert and a candidate welcome message."""
    
    prompt = (
        f"You are a hackathon marketing coordinator.\n"
        f"A candidate named '{candidate_name}' has registered for '{hackathon_name}'.\n"
        f"The total registrations for today has reached '{total_registrations_today}'.\n"
        f"The problem statement is: '{problem_statement}'.\n\n"
        f"CRITICAL: Break your output EXACTLY into these blocks using the bracket tags:\n"
        f"[ORGANIZER_ALERT] -> A brief, exciting milestone alert to the hackathon conductors about reaching {total_registrations_today} signups today.\n"
        f"[CANDIDATE_MESSAGE] -> A warm, professional welcome message to {candidate_name} acknowledging their registration, with exciting expectations."
    )
    
    raw_content = generate_text(prompt)
    
    organizer_alert = _clean_section(raw_content, "[ORGANIZER_ALERT]", "[CANDIDATE_MESSAGE]")
    candidate_message = _clean_section(raw_content, "[CANDIDATE_MESSAGE]")
    
    if not organizer_alert:
        organizer_alert = f"Milestone update for {hackathon_name}: {total_registrations_today} registrations today!"
    if not candidate_message:
        candidate_message = f"Hi {candidate_name}, welcome to {hackathon_name}! We are thrilled to have you."
        
    return {
        "organizer_alert": organizer_alert,
        "candidate_message": candidate_message
    }


async def generate_round_reminder(
    round_number: int,
    days_left: int
) -> str:
    """Generates a deadline reminder message for a specific round."""
    
    prompt = (
        f"You are a hackathon coordinator.\n"
        f"Generate a countdown reminder message for Round {round_number} with exactly {days_left} day(s) left before the submission deadline.\n"
        f"Make it urgent, exciting, and clear. Encourage candidates to push their final commits!"
    )
    
    message = generate_text(prompt)
    if not message:
        message = f"Warning: Only {days_left} day(s) left to submit your projects for Round {round_number}!"
    return message.strip()

# ---------------------------------------------------------------------------
# NEW: Interview Slot Allocation Utility
# ---------------------------------------------------------------------------
def allocate_interview_slots(candidates, start_time, slot_duration):
    import datetime

    schedule = []
    current = start_time

    for candidate in candidates:
        end_time = current + datetime.timedelta(minutes=slot_duration)

        code = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=10))
        meet_link = f"https://meet.google.com/{code[:3]}-{code[3:7]}-{code[7:]}"

        schedule.append({
            "candidate": candidate,
            "start": current.strftime("%I:%M %p"),
            "end": end_time.strftime("%I:%M %p"),
            "link": meet_link
        })

        current = end_time

    return schedule