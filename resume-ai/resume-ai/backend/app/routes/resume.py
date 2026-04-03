import os
import tempfile
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.services.parser_service import parser_service
from app.services.resume_builder import resume_builder
from app.models.request_models import ResumePdfRequest, ResumeRequest

router = APIRouter()


@router.post("/generate")
def generate_resume(data: ResumeRequest):
    result = resume_builder.build_resume(
        data.text,
        old_resume_text=data.old_resume_text,
        job_description=data.job_description,
        template=data.template,
    )
    return {"resume": result}


@router.post("/parse-file")
async def parse_resume_file(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_resume"
    extension = os.path.splitext(filename)[1].lower()

    if extension not in {".pdf", ".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Supported file types: .pdf, .txt, .md")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if extension in {".txt", ".md"}:
        text = content.decode("utf-8", errors="ignore").strip()
        if not text:
            raise HTTPException(status_code=400, detail="Could not extract text from uploaded file")
        return {"text": text}

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        text = parser_service.parse_resume(temp_path).strip()
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from uploaded file")

    return {"text": text}


@router.post("/download-pdf")
def download_resume_pdf(data: ResumePdfRequest):
    resume_text = (data.resume_text or "").strip()
    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume content is required before PDF download")

    selected_template = (data.template or "ATS Professional").strip()
    title = f"Resume Pattern: {selected_template}"
    safe_name = (data.file_name or "tailored_resume").strip().replace(" ", "_")
    if not safe_name.lower().endswith(".pdf"):
        safe_name = f"{safe_name}.pdf"

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 50, "Tailored Resume")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, height - 68, title)

    y_pos = height - 95
    pdf.setFont("Helvetica", 11)

    for paragraph in resume_text.split("\n"):
        line = paragraph.rstrip()
        if not line:
            y_pos -= 9
            if y_pos < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 11)
                y_pos = height - 50
            continue

        words = line.split()
        wrapped_line = ""
        for word in words:
            candidate = f"{wrapped_line} {word}".strip()
            if pdf.stringWidth(candidate, "Helvetica", 11) > width - 100:
                pdf.drawString(50, y_pos, wrapped_line)
                y_pos -= 16
                wrapped_line = word
                if y_pos < 50:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 11)
                    y_pos = height - 50
            else:
                wrapped_line = candidate

        if wrapped_line:
            pdf.drawString(50, y_pos, wrapped_line)
            y_pos -= 16

        if y_pos < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y_pos = height - 50

    pdf.save()
    buffer.seek(0)

    headers = {"Content-Disposition": f'attachment; filename="{safe_name}"'}
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)