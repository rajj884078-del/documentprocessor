import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from google import genai

pages = convert_from_path("blurry.pdf")
text = ""
for page in pages:
    text = text + pytesseract.image_to_string(page)

print("=== OCR se nikaala text ===")
print(text)

import os
client = genai.Client(api_key=os.environ.get("GEMINI_KEY"))
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="""Tum ek invoice document processor ho. Is document ke text se ye fields nikaalo aur SIRF JSON format mein do (aur kuch nahi likhna):

{
  "vendor": "company ka naam",
  "date": "invoice ki date",
  "total": "total amount",
  "confidence": "HIGH ya MEDIUM ya LOW"
}

CONFIDENCE RULES:
- Teeno (vendor, date, total) mile → HIGH
- Ek missing → MEDIUM
- Total missing ya do se zyada missing → LOW

Sirf JSON do, koi extra text nahi.

Document text: """ + text
)
jawab = response.text
print("=== Gemini se organized data (JSON) ===")
print(jawab)

if '"confidence": "LOW"' in jawab:
    print("⚠️ HUMAN REVIEW REQUIRED: AI is not confident, pls check manually.")
elif '"confidence": "MEDIUM"' in jawab:
    print("🟡 HUMAN REVIEW SUGGESTED: AI is somewhat confident, manual check recommended.")
else:
    print("✅ AI is confident, no human review needed.")