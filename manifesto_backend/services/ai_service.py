import os
import json

from dotenv import load_dotenv
from groq import Groq


# ==========================================
# ENVIRONMENT CONFIGURATION
# ==========================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(BASE_DIR, ".env"))

api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key) if api_key else None


# ==========================================
# MANIFESTO GENERATION
# ==========================================

def generate_manifesto_content(data: dict) -> dict:
    """
    Generate detailed, structured manifesto content using Groq AI.

    Returns:
        A validated Python dictionary containing manifesto content.
    """

    if client is None:
        raise ValueError(
            "GROQ_API_KEY missing hai. Please .env file check karo."
        )

    language = data.get("language", "English")

    key_issues = data.get("key_issues", [])

    if isinstance(key_issues, list):
        key_issues_text = ", ".join(
            str(issue) for issue in key_issues
        )
    else:
        key_issues_text = str(key_issues)

    prompt = f"""
You are an expert policy researcher, professional manifesto writer,
public policy analyst, and editorial content designer.

Your task is to create a comprehensive, detailed, visually structured
election manifesto using the information supplied below.

The output will be converted into a professional PDF report.
Therefore, the content must be detailed enough for a multi-page
publication, not a short chatbot response.

==================================================
CANDIDATE AND ELECTION DETAILS
==================================================

Leader Name: {data.get("leader_name", "")}
Political Party: {data.get("party_name", "")}
Party Tagline: {data.get("party_tagline") or "Not provided"}
Election Type: {data.get("election_type", "")}
State: {data.get("state", "")}
Constituency: {data.get("constituency") or "Not provided"}

Requested Language: {language}

Party Vision:
{data.get("vision") or "Develop a vision based on the provided priorities."}

Key Issues:
{key_issues_text}

==================================================
POLICY PRIORITIES
==================================================

Education:
{data.get("education") or "Develop relevant, practical proposals."}

Healthcare:
{data.get("healthcare") or "Develop relevant, practical proposals."}

Employment:
{data.get("employment") or "Develop relevant, practical proposals."}

Infrastructure:
{data.get("infrastructure") or "Develop relevant, practical proposals."}

Women Empowerment:
{data.get("women_empowerment") or "Develop relevant, practical proposals."}

Agriculture:
{data.get("agriculture") or "Develop relevant, practical proposals."}

Environment:
{data.get("environment") or "Develop relevant, practical proposals."}

==================================================
REQUIRED OUTPUT STRUCTURE
==================================================

Return ONLY valid JSON in the following structure:

{{
    "title": "Professional manifesto title",
    "subtitle": "A concise description of the manifesto's vision",
    "introduction": "Detailed introduction",
    "executive_summary": [
        "Major priority one",
        "Major priority two",
        "Major priority three"
    ],
    "vision_statement": "Long-term vision",
    "sections": [
        {{
            "heading": "Policy section heading",
            "problem": "Description of the issue and its local relevance",
            "content": "Detailed explanation of the proposed policy",
            "proposed_solutions": [
                "Specific proposed solution one",
                "Specific proposed solution two",
                "Specific proposed solution three"
            ],
            "implementation": [
                "Practical implementation step one",
                "Practical implementation step two",
                "Practical implementation step three"
            ],
            "expected_outcomes": [
                "Expected outcome one",
                "Expected outcome two",
                "Expected outcome three"
            ],
            "image_suggestion": {{
                "description": "Description of a relevant editorial photograph",
                "alt_text": "Accessible description of the suggested image"
            }}
        }}
    ],
    "conclusion": "Detailed concluding statement",
    "disclaimer": "These are proposed policies and are not guarantees of implementation."
}}

==================================================
CONTENT REQUIREMENTS
==================================================

1. LANGUAGE
Write all manifesto content in {language}.
Keep the language natural, clear, professional, and appropriate
for the intended audience.

2. DETAILED CONTENT
Generate a substantial report, targeting approximately 1800-2600
words where practical.

Write a detailed introduction and a meaningful conclusion.

Generate approximately 7-10 policy sections, depending on the
provided issues and priorities.

Do not repeat the same generic statements across sections.

3. EACH POLICY SECTION
Each section must explain:

- The problem being addressed.
- Why the issue matters to citizens.
- Specific proposed solutions.
- A practical implementation roadmap.
- Expected outcomes.
- A relevant image suggestion.

Write meaningful paragraphs rather than only short bullet points.

4. LOCAL RELEVANCE
Relate proposals to the specified state and constituency wherever
reasonable.

Do not invent local statistics or claim that research has been
conducted when it has not.

When reliable figures are unavailable, use qualitative descriptions.

5. REALISTIC PROPOSALS
Proposals should be practical and clearly worded.

Distinguish proposed actions from existing policies and verified facts.

Do not claim that a proposal is approved, funded, or guaranteed.

Do not invent budgets, deadlines, achievements, or numerical targets.

6. VISUAL PLANNING
For every policy section, suggest a relevant editorial photograph.

Examples:
- Education: students in a classroom or a school library.
- Healthcare: healthcare professionals in a community clinic.
- Employment: vocational training and skill development.
- Infrastructure: roads and public transport.
- Women empowerment: women entrepreneurs.
- Agriculture: farmers working in agricultural fields.
- Environment: tree planting or renewable energy.

Image suggestions are descriptions only.
Do not pretend that actual image files have been generated.

7. OUTPUT QUALITY
Use clear headings and distinct policy sections.

Avoid unnecessary repetition, slogans in every paragraph, and
unsupported claims.

The output must be valid JSON, with properly escaped characters.

Return ONLY the JSON object. Do not use Markdown fences.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional policy-report writer. "
                        "Generate detailed, practical, structured content. "
                        "Follow the requested JSON schema exactly. "
                        "Do not invent facts, statistics, or achievements."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.5,
            max_tokens=8000,
        )

        result = response.choices[0].message.content

        if not result:
            raise ValueError(
                "Groq AI ne empty response return kiya."
            )

        manifesto = json.loads(result)

        # ==========================================
        # RESPONSE VALIDATION
        # ==========================================

        required_fields = [
            "title",
            "introduction",
            "sections",
            "conclusion",
        ]

        for field in required_fields:
            if field not in manifesto:
                raise ValueError(
                    f"AI response mein required field missing hai: {field}"
                )

        if not isinstance(manifesto["sections"], list):
            raise ValueError(
                "Manifesto sections ka format invalid hai."
            )

        if not manifesto["sections"]:
            raise ValueError(
                "AI ne koi policy section generate nahi kiya."
            )

        # Validate every policy section
        for index, section in enumerate(manifesto["sections"]):

            if not isinstance(section, dict):
                raise ValueError(
                    f"Policy section {index + 1} ka format invalid hai."
                )

            section.setdefault(
                "problem",
                "Problem details not provided."
            )

            section.setdefault(
                "content",
                ""
            )

            section.setdefault(
                "proposed_solutions",
                []
            )

            section.setdefault(
                "implementation",
                []
            )

            section.setdefault(
                "expected_outcomes",
                []
            )

            section.setdefault(
                "image_suggestion",
                {
                    "description": (
                        "A relevant editorial photograph illustrating "
                        "this policy topic."
                    ),
                    "alt_text": section.get(
                        "heading",
                        "Policy illustration"
                    ),
                },
            )

        # Add safe defaults for optional fields
        manifesto.setdefault(
            "subtitle",
            "A Vision for Inclusive Development"
        )

        manifesto.setdefault(
            "executive_summary",
            []
        )

        manifesto.setdefault(
            "vision_statement",
            data.get("vision", "")
        )

        manifesto.setdefault(
            "disclaimer",
            "This document contains proposed policies, not guaranteed outcomes."
        )

        return manifesto

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Groq AI ne valid JSON return nahi kiya (line {exc.lineno}, column {exc.colno}). "
            "Please dobara try karein."
        ) from exc

    except ValueError:
        raise

    except Exception as exc:
        raise RuntimeError(
            f"Manifesto generate karte waqt error aaya: {exc}"
        ) from exc