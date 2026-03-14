import logging

from core.config import settings

logger = logging.getLogger(__name__)

FRAMEWORK_LABELS = {"soc2": "SOC 2", "iso27001": "ISO 27001", "hipaa": "HIPAA"}


def _build_prompt(framework: str, score_data: dict) -> str:
    label = FRAMEWORK_LABELS.get(framework, framework.upper())

    lines = []
    for c in score_data["controls"]:
        covered = ", ".join(c["covered_types"]) if c["covered_types"] else "none"
        missing = ", ".join(c["missing_types"]) if c["missing_types"] else "none"
        lines.append(
            f"- {c['name']}: {c['score']}% ({c['status']}) | "
            f"evidence count: {c['evidence_count']} | "
            f"covered types: {covered} | "
            f"missing types: {missing}"
        )

    controls_text = "\n".join(lines)

    return f"""You are a compliance advisor helping an engineering team understand their {label} posture.

Framework: {label}
Overall Score: {score_data["overall_score"]}%

Control breakdown:
{controls_text}

Write a 3-4 sentence summary that:
1. States the overall posture plainly (good/needs work/critical gaps)
2. Calls out what is working well, if anything
3. Names the single most critical gap and gives one specific, concrete action to fix it

Rules:
- Write in flowing prose — no bullet points
- Be specific: use actual control names and evidence type names from the data
- Do not give generic compliance advice — ground everything in the numbers above
- Keep it under 90 words"""


async def generate_compliance_summary(framework: str, score_data: dict) -> str:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured on this server.")

    try:
        from groq import AsyncGroq
    except ImportError as exc:
        raise RuntimeError("groq package not installed — add it to requirements.txt") from exc

    client = AsyncGroq(api_key=settings.groq_api_key)
    prompt = _build_prompt(framework, score_data)

    completion = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=220,
    )

    return completion.choices[0].message.content.strip()
