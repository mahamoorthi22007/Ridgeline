import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# கூகுளுக்கு பதிலாக இப்போ Groq API Key-ஐ வாங்குகிறோம்
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Error: GROQ_API_KEY கன்பார்மா வேணும் பாஸ்!")

# Groq அதிகாரப்பூர்வ கிளைன்ட் செட்டப்
ai_client = Groq(api_key=GROQ_API_KEY)

# 2.5-flash-க்கு இணையான மிக வேகமான மற்றும் சக்திவாய்ந்த இலவச மாடல் (Llama 3.3 70B)
# (அல்லது சிறிய மாடல் வேண்டுமென்றால் "llama-3.1-8b-instant" பயன்படுத்தலாம்)
# புதிய வரி (தற்போது Groq-ல் இருக்கும் ஆக்டிவ் மாடல்)
MODEL_ID = "llama-3.3-70b-versatile"


def generate_text(prompt: str) -> str:
    """Simple one-off text generation, bypassing the agent pipeline.
    Kept for quick utility calls that don't need memory/tools."""
    response = ai_client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    return response.choices[0].message.content