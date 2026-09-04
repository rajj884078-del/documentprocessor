from fastapi import FastAPI, UploadFile
import pytesseract
from pdf2image import convert_from_path
from google import genai
import json
from fastapi.responses import FileResponse


app = FastAPI()

@app.get("/")
def home():
    return FileResponse("index.html")

@app.post("/process")
def process(file: UploadFile):
    # Step 0: File save karo (uska asli naam/extension ke saath)
    filename = file.filename
    with open(filename, "wb") as f:
        f.write(file.file.read())

    # Step 1: OCR — PDF ya image, dono handle karo
    text = ""
    if filename.endswith(".pdf"):
        # PDF hai — pehle image mein badlo, phir OCR
        from pdf2image import convert_from_path
        pages = convert_from_path(filename)
        for page in pages:
            text = text + pytesseract.image_to_string(page)
    else:
        # Image hai (png/jpg) — seedhа OCR
        from PIL import Image
        image = Image.open(filename)
        text = pytesseract.image_to_string(image)

    # ... baaki (Gemini, JSON, flag) wahi rehega
    # Step 2: Gemini se info — RETRY ke saath (agar 503/fail ho)
    import time
    import os
    client = genai.Client(api_key=os.environ.get("GEMINI_KEY"))
    response = None
    for attempt in range(3):          # 3 baar try karo
        try:
            response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="""Tum ek insurance document processor ho. Is document se ye insurance fields nikaalo. Har field ke saath ye bhi batao ki wo document mein KAHA se aaya (source — jaise woh line ya text jahan se value mili).

SIRF JSON do is format mein:
{
  "policy_number": {"value": "...", "source": "wo text/line jahan se mila"},
  "claim_number": {"value": "...", "source": "..."},
  "claimant_name": {"value": "...", "source": "..."},
  "claim_amount": {"value": "...", "source": "..."},
  "incident_date": {"value": "...", "source": "..."},
  "confidence": "HIGH/MEDIUM/LOW"
}

Rules: saare 5 mile HIGH, 1-2 missing MEDIUM, claim_amount missing ya 3+ missing LOW.
Koi field na mile to value aur source dono null rakhna. Sirf JSON do.

Document text: """ + text
    )
            break                      # kaam ho gaya, loop se bahar
        except:
            time.sleep(3)              # fail hua — 3 second ruko, phir dobara try

    if response is None:               # 3 baar bhi fail
        return {"error": "Server busy, please try again later"}
    
    jawab = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(jawab)

    # Step 3: Flag decide karo
    confidence = data["confidence"]
    if confidence == "LOW":
        flag = "⚠️ HUMAN REVIEW REQUIRED"
    elif confidence == "MEDIUM":
        flag = "🟡 PARTIAL REVIEW"
    else:
        flag = "✅ AI is confident"

    return {"result": data, "review_status": flag}