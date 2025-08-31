from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import os
import shutil
import tempfile

from .generator import generate_certificate
from .emailer import SendEmail

app = FastAPI(title="Completion Automation API")

# ------------------- CORS SETUP -------------------
origins = [
    "http://localhost:3000","http://localhost:8000","http://localhost:5173" ,"http://localhost:8080" ,   "https://hrms-ten-theta.vercel.app/","https://dnyx-hrms.vercel.app/",
    "https://hrms.dnyx.in/recruitment/create-job",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------- CONFIG -------------------
TEMPLATE_FILE = os.path.join("templates", "TEMPLATE.docx")
OFFER_TEMPLATE_FILE = os.path.join("templates", "offertemplate.docx")
OUTPUT_DIR = "output"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


# ------------------- HELPERS -------------------
def replace_placeholders(text: str, name: str, role: str) -> str:
    return text.replace('<NAME>', name).replace('<ROLE>', role)

def replace_offer_placeholders(text: str, name: str, domain: str) -> str:
    return text.replace('<NAME>', name).replace('<DOMAIN>', domain)


# ------------------- REQUEST MODELS -------------------
class GenerateRequest(BaseModel):
    name: str
    role: str

class EmailRequest(BaseModel):
    email: str
    name: str
    role: str
    certificate_filename: Optional[str] = None
    subject: Optional[str] = "🎉 Congrats, <NAME>! You’ve Successfully Completed Your Internship in <ROLE>!"
    body: Optional[str] = """Dear <NAME>,
Congratulations on completing your internship in <ROLE>!
Warm regards,
Your Company
"""


# ------------------- ROUTES -------------------
@app.post("/generate_certificate_only")
async def generate_certificate_only(req: GenerateRequest):
    try:
        pdf_path = generate_certificate({'Name': req.name, 'Domain': req.role}, TEMPLATE_FILE, OUTPUT_DIR)
        filename = os.path.basename(pdf_path)
        return {"status": "success", "certificate_file": filename, "saved_path": pdf_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send_certificate_email")
async def send_certificate_email(req: EmailRequest):
    try:
        attachments = []

        if req.certificate_filename:
            cert_path = os.path.join(OUTPUT_DIR, req.certificate_filename)
            if not os.path.exists(cert_path):
                raise HTTPException(status_code=404, detail=f"Certificate file '{req.certificate_filename}' not found")
            attachments.append(cert_path)
        else:
            pdf_files = [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.lower().endswith(".pdf")]
            if not pdf_files:
                raise HTTPException(status_code=404, detail="No certificate files found in output folder")
            attachments.extend(pdf_files)

        subject = replace_placeholders(req.subject, req.name, req.role)
        body = replace_placeholders(req.body, req.name, req.role)

        email = SendEmail(req.email, subject, body, attachments)
        email.sendMessage()

        return {"status": "success", "message": f"Email sent to {req.email}", "files_sent": [os.path.basename(f) for f in attachments]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process_csv")
async def process_csv(csv_file: UploadFile = File(...), send_email: bool = True):
    try:
        tmp_dir = tempfile.mkdtemp()
        csv_path = os.path.join(tmp_dir, csv_file.filename)
        with open(csv_path, "wb") as f:
            shutil.copyfileobj(csv_file.file, f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save uploaded CSV file: {e}")

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file: {e}")

    required_cols = ['Name', 'Email', 'Domain']
    if not all(col in df.columns for col in required_cols):
        raise HTTPException(status_code=400, detail=f"CSV missing required columns: {required_cols}")

    results = []
    for _, row in df.iterrows():
        row_name = str(row['Name']).strip()
        row_email = str(row['Email']).strip()
        row_role = str(row['Domain']).strip()

        row_result = {"Name": row_name, "Email": row_email, "Role": row_role, "status": "Pending"}
        try:
            pdf_path = generate_certificate({'Name': row_name, 'Domain': row_role}, TEMPLATE_FILE, OUTPUT_DIR)
            if send_email:
                subject = f"🎉 Congrats, {row_name}! You’ve Successfully Completed Your Internship in {row_role}!"
                body = f"Dear {row_name}, Congratulations on completing your internship in {row_role}!"
                email = SendEmail(row_email, subject, body, [pdf_path])
                email.sendMessage()

            row_result["status"] = "Success"
        except Exception as e:
            row_result["status"] = f"Failed: {str(e)}"

        results.append(row_result)

    try:
        shutil.rmtree(tmp_dir)
    except:
        pass

    return {"results": results}


@app.post("/generate_and_send_certificate")
async def generate_and_send_certificate(req: EmailRequest):
    try:
        pdf_path = generate_certificate({'Name': req.name, 'Domain': req.role}, TEMPLATE_FILE, OUTPUT_DIR)
        subject = replace_placeholders(req.subject, req.name, req.role)
        body = replace_placeholders(req.body, req.name, req.role)
        email = SendEmail(req.email, subject, body, [pdf_path])
        email.sendMessage()
        return {"status": "success", "message": f"Certificate generated and sent to {req.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send_offer_letter")
async def send_offer_letter(req: EmailRequest):
    try:
        pdf_path = generate_certificate({'Name': req.name, 'Domain': req.role}, OFFER_TEMPLATE_FILE, OUTPUT_DIR)
        
        subject_template = "<DOMAIN> Internship Offer Letter - DNYX"
        body_template = """Dear <NAME>, 

I am pleased to extend an offer for the <DOMAIN> Internship position at DNYX. We are excited to welcome you to our Web unit, DNYXWeb.

This 3-month remote internship will provide you with invaluable hands-on experience in <DOMAIN>. We are confident that your skills and enthusiasm will be a great addition to our team, and we look forward to supporting your growth throughout this journey.

Please find the attached offer letter for your review, which includes all the pertinent details about the internship. Should you have any questions or require further clarification, do not hesitate to reach out at contact@dnyx.in

We are delighted to have you join us and look forward to your contributions to DNYX.

With Regards,
Team DNYX
"""

        subject = replace_offer_placeholders(subject_template, req.name, req.role)
        body = replace_offer_placeholders(body_template, req.name, req.role)

        email = SendEmail(req.email, subject, body, [pdf_path])
        email.sendMessage()
        return {"status": "success", "message": f"Offer letter sent to {req.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process_offer_letter_csv")
async def process_offer_letter_csv(csv_file: UploadFile = File(...)):
    try:
        tmp_dir = tempfile.mkdtemp()
        csv_path = os.path.join(tmp_dir, csv_file.filename)
        with open(csv_path, "wb") as f:
            shutil.copyfileobj(csv_file.file, f)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save uploaded CSV file: {e}")

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file: {e}")

    required_cols = ['Name', 'Email', 'Domain']
    if not all(col in df.columns for col in required_cols):
        raise HTTPException(status_code=400, detail=f"CSV missing required columns: {required_cols}")

    results = []
    for _, row in df.iterrows():
        row_name = str(row['Name']).strip()
        row_email = str(row['Email']).strip()
        row_role = str(row['Domain']).strip()

        row_result = {"Name": row_name, "Email": row_email, "Role": row_role, "status": "Pending"}
        try:
            pdf_path = generate_certificate({'Name': row_name, 'Domain': row_role}, OFFER_TEMPLATE_FILE, OUTPUT_DIR)

            subject_template = "<DOMAIN> Internship Offer Letter - DNYX"
            body_template = """Dear <NAME>, 

I am pleased to extend an offer for the <DOMAIN> Internship position at DNYX. We are excited to welcome you to our Web unit, DNYXWeb.

This 3-month remote internship will provide you with invaluable hands-on experience in <DOMAIN>. We are confident that your skills and enthusiasm will be a great addition to our team, and we look forward to supporting your growth throughout this journey.

Please find the attached offer letter for your review, which includes all the pertinent details about the internship. Should you have any questions or require further clarification, do not hesitate to reach out at contact@dnyx.in

We are delighted to have you join us and look forward to your contributions to DNYX.

With Regards,
Team DNYX
"""
            subject = replace_offer_placeholders(subject_template, row_name, row_role)
            body = replace_offer_placeholders(body_template, row_name, row_role)

            email = SendEmail(row_email, subject, body, [pdf_path])
            email.sendMessage()
            row_result["status"] = "Success"
        except Exception as e:
            row_result["status"] = f"Failed: {str(e)}"

        results.append(row_result)

    try:
        shutil.rmtree(tmp_dir)
    except:
        pass

    return {"results": results}
