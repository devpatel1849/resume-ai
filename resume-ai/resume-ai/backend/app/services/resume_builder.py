from app.services.llm_service import llm_service


class ResumeBuilder:
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

        Format:
        - Professional Summary
        - Core Skills
        - Experience (with bullet points)
        - Projects (if available)
        - Education
        - Certifications (if available)
        """

        return llm_service.generate_response(prompt)


resume_builder = ResumeBuilder()