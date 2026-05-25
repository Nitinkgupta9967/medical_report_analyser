# ================================
# main.py
# ================================

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import time
import uuid
import os
import traceback

from models import *
from services import process_medical_report
from errors import *
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Medical Report Analyzer API",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
START_TIME = time.time()


# =========================================================
# HEALTH ENDPOINT
# =========================================================

@app.get("/api/v1/health")
async def health_check():

    uptime = round(time.time() - START_TIME, 2)

    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "uptime_seconds": uptime,
            "ai_status": "connected"
        },
        "error": None,
        "meta": {
            "processing_time_ms": 0,
            "pages_processed": 0,
            "model_used": "gemini-2.5-flash",
            "request_id": str(uuid.uuid4())
        }
    }


# =========================================================
# ANALYZE REPORT ENDPOINT
# =========================================================

@app.post("/api/v1/analyze")
async def analyze_report(file: UploadFile = File(...)):

    start = time.time()

    request_id = str(uuid.uuid4())

    try:

        # ============================================
        # VALIDATE FILE TYPE
        # ============================================

        allowed_types = [
            "application/pdf",
            "image/png",
            "image/jpeg"
        ]

        if file.content_type not in allowed_types:

            return JSONResponse(
                status_code=422,
                content=error_response(
                    INVALID_FILE_TYPE,
                    "Only PDF, PNG and JPG files are allowed.",
                    request_id,
                    start
                )
            )

        # ============================================
        # SAVE FILE
        # ============================================

        os.makedirs("uploads", exist_ok=True)

        file_path = f"uploads/{file.filename}"

        with open(file_path, "wb") as f:
            f.write(await file.read())

        # ============================================
        # PROCESS REPORT
        # ============================================

        result, pages_processed = process_medical_report(file_path)

        # ============================================
        # EMPTY EXTRACTION
        # ============================================

        if not result:

            return JSONResponse(
                status_code=422,
                content=error_response(
                    EMPTY_EXTRACTION,
                    "Could not extract data from report.",
                    request_id,
                    start,
                    pages_processed
                )
            )

        # ============================================
        # SUCCESS RESPONSE
        # ============================================

        return {
            "success": True,
            "data": result,
            "error": None,
            "meta": {
                "processing_time_ms": elapsed_ms(start),
                "pages_processed": pages_processed,
                "model_used": "gemini-2.5-flash",
                "request_id": request_id
            }
        }

    except Exception as e:

        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content=error_response(
                INTERNAL_SERVER_ERROR,
                str(e),
                request_id,
                start
            )
        )


# =========================================================
# HELPERS
# =========================================================

def elapsed_ms(start):
    return int((time.time() - start) * 1000)


def error_response(code, message, request_id, start, pages=0):

    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": None
        },
        "meta": {
            "processing_time_ms": elapsed_ms(start),
            "pages_processed": pages,
            "model_used": None,
            "request_id": request_id
        }
    }