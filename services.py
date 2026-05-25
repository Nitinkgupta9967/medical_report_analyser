# ================================
# services.py
# ================================

import os
import json
import pymupdf as fitz
import pytesseract
from PIL import Image
import google.genai as genai
from dotenv import load_dotenv

# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# =========================================================
# TESSERACT PATH
# =========================================================

import platform

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

# =========================================================
# PDF TO IMAGES
# =========================================================

def pdf_to_images(pdf_path):

    os.makedirs("temp_pages", exist_ok=True)

    doc = fitz.open(pdf_path)

    image_paths = []

    for i, page in enumerate(doc):

        pix = page.get_pixmap(dpi=300)

        img_path = f"temp_pages/page_{i+1}.png"

        pix.save(img_path)

        image_paths.append(img_path)

    doc.close()

    return image_paths


# =========================================================
# OCR
# =========================================================

def extract_text(image_path):

    text = pytesseract.image_to_string(
        Image.open(image_path),
        config='--oem 3 --psm 6'
    )

    return text


# =========================================================
# NORMALIZE FLAG
# =========================================================

def normalize_flag(flag, abnormal_flag):

    # already proper flag
    if flag:

        flag = str(flag).upper()

        if flag in ["HIGH", "LOW", "NORMAL", "CRITICAL"]:
            return flag

    # old boolean style
    if abnormal_flag is True:
        return "HIGH"

    if abnormal_flag is False:
        return "NORMAL"

    return None


# =========================================================
# NORMALIZE REFERENCE RANGE
# =========================================================

def normalize_reference_range(ref):

    # already object
    if isinstance(ref, dict):

        return {
            "min": ref.get("min"),
            "max": ref.get("max"),
            "text": ref.get("text")
        }

    # string range
    if isinstance(ref, str):

        cleaned = ref.strip()

        # range like 70-100
        if "-" in cleaned:

            parts = cleaned.split("-")

            if len(parts) == 2:

                return {
                    "min": parts[0].strip(),
                    "max": parts[1].strip(),
                    "text": cleaned
                }

        # text range like >0.5
        return {
            "min": None,
            "max": None,
            "text": cleaned
        }

    # fallback
    return {
        "min": None,
        "max": None,
        "text": None
    }


# =========================================================
# NORMALIZE PARAMETERS
# =========================================================

def normalize_parameters(parameters):

    normalized = []

    for item in parameters:

        normalized.append({

            "parameter_name":
                item.get("parameter_name")
                or item.get("name"),

            "value":
                item.get("value")
                or item.get("result"),

            "unit":
                item.get("unit"),

            "reference_range":
                normalize_reference_range(
                    item.get("reference_range")
                ),

            "flag":
                normalize_flag(
                    item.get("flag"),
                    item.get("abnormal_flag")
                )
        })

    return normalized


# =========================================================
# GEMINI ANALYSIS
# =========================================================

def analyze_with_gemini(text):

    prompt = f"""
RULES:
1. Return ONLY raw JSON.
2. Never hallucinate values.
3. Use null if field missing.
4. Include all parameters found.
5. Correct obvious OCR mistakes if highly confident.
6. If values appear medically impossible, treat as OCR uncertainty.
7. Return valid JSON only.

OCR TEXT:
{text}

Return EXACT schema:

{{
  "patient_info": {{
    "name": null,
    "age": null,
    "gender": null,
    "report_date": null
  }},

  "test_info": {{
    "test_type": null,
    "test_name": null,
    "category": null
  }},

  "parameters": [
    {{
      "parameter_name": null,
      "value": null,
      "unit": null,
      "reference_range": {{
        "min": null,
        "max": null,
        "text": null
      }},
      "flag": null
    }}
  ],

  "interpretation": {{
    "impression": null,
    "summary": null
  }},

  "diagnosis": {{
    "conditions": [],
    "clinical_notes": null
  }},

  "recommendations": {{
    "next_steps": null,
    "follow_up": null,
    "lifestyle_advice": null
  }},

  "lab_details": {{
    "lab_name": null,
    "hospital_name": null,
    "doctor_name": null,
    "accreditation": null,
    "signature_present": null
  }},

  "metadata": {{
    "report_id": null,
    "source": null,
    "extraction_confidence": null
  }}
}}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text.strip()

    # remove markdown wrappers
    if raw.startswith("```"):

        raw = raw.replace("```json", "")
        raw = raw.replace("```", "")
        raw = raw.strip()

    parsed = json.loads(raw)

    # normalize parameters
    parsed["parameters"] = normalize_parameters(
        parsed.get("parameters", [])
    )

    return parsed


# =========================================================
# MAIN PROCESSOR
# =========================================================

def process_medical_report(file_path):

    ext = file_path.lower().split(".")[-1]

    image_paths = []

    # =====================================================
    # PDF
    # =====================================================

    if ext == "pdf":

        image_paths = pdf_to_images(file_path)

    else:

        image_paths = [file_path]

    # =====================================================
    # OCR
    # =====================================================

    full_text = ""

    for path in image_paths:

        full_text += extract_text(path)

        full_text += "\n\n"

    # =====================================================
    # GEMINI
    # =====================================================

    result = analyze_with_gemini(full_text)

    return result, len(image_paths)