import re

from app.services.llm_service import llm_service


class ResumeBuilder:
    _SECTION_ALIASES = {
        "summary": "Professional Summary",
        "professional summary": "Professional Summary",
        "core skills": "Core Skills",
        "skills": "Core Skills",
        "technical skills": "Core Skills",
        "experience": "Experience",
        "work experience": "Experience",
        "projects": "Projects",
        "education": "Education",
        "certifications": "Certifications",
    }

    def _normalize_heading_key(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().strip(":").strip("-").lower())

    def _sanitize_model_output(self, content: str) -> str:
        if not content or content.startswith("Error:"):
            return content

        cleaned_lines: list[str] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
                continue

            if set(line) <= {"-", "_", "="}:
                continue

            line = re.sub(r"^#{1,6}\s*", "", line)
            line = line.replace("**", "").replace("__", "").replace("`", "")
            line = re.sub(r"^[>\"'\s]+", "", line)
            line = re.sub(r"[\"'\s]+$", "", line)

            key = self._normalize_heading_key(line)
            if key in self._SECTION_ALIASES:
                normalized_heading = self._SECTION_ALIASES[key]
                if cleaned_lines and cleaned_lines[-1] != "":
                    cleaned_lines.append("")
                cleaned_lines.append(normalized_heading)
                continue

            if line.startswith(("•", "*", "- ")):
                line = f"- {line.lstrip('•*- ').strip()}"

            cleaned_lines.append(line)

        while cleaned_lines and cleaned_lines[-1] == "":
            cleaned_lines.pop()

        return "\n".join(cleaned_lines)

    def build_resume(
        self,
        data: str,
        old_resume_text: str | None = None,
        job_description: str | None = None,
        template: str = "ATS Professional",
    ):
        old_resume_section = old_resume_text.strip() if old_resume_text else "Not provided"
        job_description_section = job_description.strip() if job_description else "Not provided"

        template_guidelines = {
            "ATS Professional": (
                "Use an ATS-safe structure with direct headings, compact bullets, and keyword-rich phrasing."
            ),
            "Modern Impact": (
                "Use concise storytelling, high-impact bullets, and stronger achievement-first statements."
            ),
            "Executive Brief": (
                "Use a leadership-focused tone, strategic impact highlights, and senior-level summary language."
            ),
            "Technical Deep": (
                "Emphasize technologies, architecture, implementation detail, and engineering outcomes."
            ),
            "Classic Serif": (
                "Use a timeless, formal style with polished language, balanced section depth, and readable accomplishment bullets."
            ),
        }
        chosen_template = template if template in template_guidelines else "ATS Professional"
        template_instruction = template_guidelines[chosen_template]

        prompt = f"""
        Create a professional ATS-friendly resume that is tailored to the target job.

        Selected resume pattern:
        {chosen_template}

        Template behavior:
        {template_instruction}

        Candidate source data:
        {data}

        Existing/old resume (if available):
        {old_resume_section}

        Target job description (if available):
        {job_description_section}

        Output requirements:
        - Use clear section headings
        - Use strong action verbs and measurable impact
        - Prioritize skills and achievements most relevant to the job description
        - Keep language concise and professional
        - Include ATS-friendly keywords naturally
        - Avoid fake experience, tools, or metrics
        - Keep section ordering aligned to the selected resume pattern
        - Return plain text only (no markdown)
        - Do not use **, *, #, backticks, quotes, or code blocks
        - Use simple headings with this style: Professional Summary
        - Use bullet points with '- ' only
        - Keep the content clean and publication-ready

        Format:
        - Candidate Name
        - Target Role
        - Contact Line (email | phone | location | LinkedIn/GitHub if available)
        - Professional Summary
        - Core Skills
        - Experience (with bullet points)
        - Projects (if available)
        - Education
        - Certifications (if available)
        """

        response = llm_service.generate_response(prompt)
        return self._sanitize_model_output(response)


resume_builder = ResumeBuilder()