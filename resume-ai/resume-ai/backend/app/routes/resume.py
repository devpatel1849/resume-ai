import os
import re
import tempfile
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.services.parser_service import parser_service
from app.services.resume_builder import resume_builder
from app.models.request_models import ResumePdfRequest, ResumeRequest

router = APIRouter()

SUPPORTED_TEMPLATES = {
    "ATS Professional",
    "Modern Impact",
    "Executive Brief",
    "Technical Deep",
    "Classic Serif",
}

KNOWN_SECTIONS = {
    "summary": "Summary",
    "professional summary": "Professional Summary",
    "core skills": "Core Skills",
    "skills": "Skills",
    "experience": "Experience",
    "work experience": "Work Experience",
    "projects": "Projects",
    "education": "Education",
    "certifications": "Certifications",
}


def _normalize_heading(line: str) -> str:
    return line.strip().strip(":").strip("-").strip().lower()


def _clean_line_for_render(line: str) -> str:
    cleaned = (line or "").strip()
    if not cleaned:
        return ""

    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned)
    cleaned = cleaned.replace("**", "").replace("__", "").replace("`", "")
    cleaned = re.sub(r"^[>\"'\s]+", "", cleaned)
    cleaned = re.sub(r"[\"'\s]+$", "", cleaned)

    if cleaned.startswith(("•", "*", "- ")):
        cleaned = f"- {cleaned.lstrip('•*- ').strip()}"

    if set(cleaned) <= {"-", "_", "="}:
        return ""

    return cleaned


def _looks_like_heading(line: str) -> bool:
    compact = _clean_line_for_render(line)
    if not compact:
        return False

    normalized = _normalize_heading(compact)
    if normalized in KNOWN_SECTIONS:
        return True

    return compact.isupper() and len(compact.split()) <= 4


def _parse_resume_structure(resume_text: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    header_lines: list[str] = []
    sections: list[tuple[str, list[str]]] = []

    current_title = ""
    current_lines: list[str] = []

    for raw_line in resume_text.splitlines():
        line = _clean_line_for_render(raw_line)

        if not line:
            if current_title and current_lines and current_lines[-1] != "":
                current_lines.append("")
            elif not current_title and header_lines and header_lines[-1] != "":
                header_lines.append("")
            continue

        if _looks_like_heading(line):
            if current_title:
                sections.append((current_title, current_lines))
            normalized = _normalize_heading(line)
            current_title = KNOWN_SECTIONS.get(normalized, line.title())
            current_lines = []
            continue

        if current_title:
            current_lines.append(line)
        else:
            header_lines.append(line)

    if current_title:
        sections.append((current_title, current_lines))

    if not sections:
        sections = [("Resume", [line for line in resume_text.splitlines() if line.strip()])]

    return header_lines, sections


def _is_bullet_line(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("- ") or stripped.startswith("* ")


def _draw_wrapped_text(
    pdf: canvas.Canvas,
    text: str,
    x_pos: float,
    y_pos: float,
    max_width: float,
    font_name: str,
    font_size: int,
    leading: int,
) -> float:
    words = text.split()
    if not words:
        return y_pos - leading

    current_line = ""
    for word in words:
        candidate = f"{current_line} {word}".strip()
        if pdf.stringWidth(candidate, font_name, font_size) <= max_width:
            current_line = candidate
            continue

        pdf.drawString(x_pos, y_pos, current_line)
        y_pos -= leading
        current_line = word

    if current_line:
        pdf.drawString(x_pos, y_pos, current_line)
        y_pos -= leading

    return y_pos


def _render_template_pdf(pdf: canvas.Canvas, resume_text: str, selected_template: str, width: float, height: float) -> None:
    header_lines, sections = _parse_resume_structure(resume_text)

    name_line = header_lines[0] if header_lines else "Tailored Resume"
    role_line = header_lines[1] if len(header_lines) > 1 else ""
    contact_line = " | ".join([line for line in header_lines[2:] if line]) if len(header_lines) > 2 else ""

    template_styles = {
        "ATS Professional": {
            "header_font": "Helvetica-Bold",
            "header_size": 20,
            "sub_font": "Helvetica",
            "sub_size": 10,
            "section_font": "Helvetica-Bold",
            "section_size": 11,
            "body_font": "Helvetica",
            "body_size": 10,
            "header_color": colors.HexColor("#0f172a"),
            "section_color": colors.HexColor("#1f2937"),
            "line_color": colors.HexColor("#d1d5db"),
        },
        "Modern Impact": {
            "header_font": "Helvetica-Bold",
            "header_size": 21,
            "sub_font": "Helvetica",
            "sub_size": 10,
            "section_font": "Helvetica-Bold",
            "section_size": 11,
            "body_font": "Helvetica",
            "body_size": 10,
            "header_color": colors.HexColor("#0b4f6c"),
            "section_color": colors.HexColor("#145374"),
            "line_color": colors.HexColor("#8fbcd4"),
        },
        "Executive Brief": {
            "header_font": "Times-Bold",
            "header_size": 23,
            "sub_font": "Times-Italic",
            "sub_size": 11,
            "section_font": "Times-Bold",
            "section_size": 12,
            "body_font": "Times-Roman",
            "body_size": 10,
            "header_color": colors.HexColor("#111827"),
            "section_color": colors.HexColor("#1f2937"),
            "line_color": colors.HexColor("#9ca3af"),
        },
        "Technical Deep": {
            "header_font": "Helvetica-Bold",
            "header_size": 20,
            "sub_font": "Courier",
            "sub_size": 10,
            "section_font": "Courier-Bold",
            "section_size": 10,
            "body_font": "Helvetica",
            "body_size": 10,
            "header_color": colors.HexColor("#0a3a5a"),
            "section_color": colors.HexColor("#0a3a5a"),
            "line_color": colors.HexColor("#9abfd3"),
        },
        "Classic Serif": {
            "header_font": "Times-Bold",
            "header_size": 22,
            "sub_font": "Times-Roman",
            "sub_size": 10,
            "section_font": "Times-Bold",
            "section_size": 11,
            "body_font": "Times-Roman",
            "body_size": 10,
            "header_color": colors.HexColor("#111827"),
            "section_color": colors.HexColor("#111827"),
            "line_color": colors.HexColor("#6b7280"),
        },
    }

    style = template_styles.get(selected_template, template_styles["ATS Professional"])

    left_margin = 44
    right_margin = 44
    top_margin = 52
    bottom_margin = 44
    content_width = width - left_margin - right_margin
    y_pos = height - top_margin

    if selected_template == "Modern Impact":
        pdf.setFillColor(colors.HexColor("#0e5a7d"))
        pdf.rect(0, height - 62, width, 62, stroke=0, fill=1)
        pdf.setFillColor(colors.white)
        pdf.setFont(style["header_font"], style["header_size"])
        pdf.drawString(left_margin, height - 34, name_line)
        if role_line:
            pdf.setFont(style["sub_font"], style["sub_size"])
            pdf.drawString(left_margin, height - 48, role_line)
        y_pos = height - 82
    else:
        pdf.setFillColor(style["header_color"])
        pdf.setFont(style["header_font"], style["header_size"])
        if selected_template in {"Executive Brief", "Classic Serif"}:
            text_width = pdf.stringWidth(name_line, style["header_font"], style["header_size"])
            pdf.drawString((width - text_width) / 2, y_pos, name_line)
        else:
            pdf.drawString(left_margin, y_pos, name_line)
        y_pos -= 18

        if role_line:
            pdf.setFont(style["sub_font"], style["sub_size"])
            if selected_template in {"Executive Brief", "Classic Serif"}:
                role_width = pdf.stringWidth(role_line, style["sub_font"], style["sub_size"])
                pdf.drawString((width - role_width) / 2, y_pos, role_line)
            else:
                pdf.drawString(left_margin, y_pos, role_line)
            y_pos -= 14

    if contact_line:
        pdf.setFillColor(colors.HexColor("#374151"))
        pdf.setFont(style["sub_font"], style["sub_size"])
        if selected_template in {"Executive Brief", "Classic Serif", "Modern Impact"}:
            contact_width = pdf.stringWidth(contact_line, style["sub_font"], style["sub_size"])
            pdf.drawString((width - contact_width) / 2, y_pos, contact_line)
        else:
            pdf.drawString(left_margin, y_pos, contact_line)
        y_pos -= 14

    pdf.setStrokeColor(style["line_color"])
    pdf.setLineWidth(1.2 if selected_template == "Executive Brief" else 1.0)
    pdf.line(left_margin, y_pos, width - right_margin, y_pos)
    y_pos -= 16

    for section_title, section_lines in sections:
        if y_pos < bottom_margin + 45:
            pdf.showPage()
            y_pos = height - top_margin
            pdf.setStrokeColor(style["line_color"])
            pdf.line(left_margin, y_pos, width - right_margin, y_pos)
            y_pos -= 16

        pdf.setFillColor(style["section_color"])
        pdf.setFont(style["section_font"], style["section_size"])
        title_text = section_title.upper() if selected_template == "Technical Deep" else section_title
        pdf.drawString(left_margin, y_pos, title_text)
        y_pos -= 8
        pdf.setStrokeColor(style["line_color"])
        pdf.line(left_margin, y_pos, width - right_margin, y_pos)
        y_pos -= 12

        pdf.setFillColor(colors.black)
        for line in section_lines:
            if y_pos < bottom_margin + 20:
                pdf.showPage()
                y_pos = height - top_margin
                pdf.setFillColor(colors.black)

            if not line:
                y_pos -= 6
                continue

            cleaned_line = line
            bullet_line = _is_bullet_line(cleaned_line)
            if bullet_line:
                cleaned_line = cleaned_line[2:].strip()
                pdf.setFont(style["body_font"], style["body_size"])
                pdf.drawString(left_margin + 2, y_pos, "-")
                y_pos = _draw_wrapped_text(
                    pdf,
                    cleaned_line,
                    left_margin + 12,
                    y_pos,
                    content_width - 12,
                    style["body_font"],
                    style["body_size"],
                    14,
                )
            else:
                pdf.setFont(style["body_font"], style["body_size"])
                y_pos = _draw_wrapped_text(
                    pdf,
                    cleaned_line,
                    left_margin,
                    y_pos,
                    content_width,
                    style["body_font"],
                    style["body_size"],
                    14,
                )

        y_pos -= 3


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
    if selected_template not in SUPPORTED_TEMPLATES:
        selected_template = "ATS Professional"

    safe_name = (data.file_name or "tailored_resume").strip().replace(" ", "_")
    if not safe_name.lower().endswith(".pdf"):
        safe_name = f"{safe_name}.pdf"

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    _render_template_pdf(pdf, resume_text, selected_template, width, height)

    pdf.save()
    buffer.seek(0)

    headers = {"Content-Disposition": f'attachment; filename="{safe_name}"'}
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)