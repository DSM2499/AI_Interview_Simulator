import os
import json
import openai
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
from PyPDF2 import PdfReader

#Load environment variables (API key)
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key = api_key)

#Output Folder
output_dir = Path("data/profiles")

system_prompt = """
You are a professional resume writer and career advisor specializing in fictional yet realistic resumes for data analyst roles. Generate a single resume formatted as **strictly valid JSON** with no commentary or explanations.

Use the following schema:
{
  "name": "Fictional Full Name",
  "summary": "1-2 sentence professional summary tailored for a data analyst",
  "education": [
    {
      "degree": "Degree Title",
      "institution": "Fictional Institution",
      "year": "Graduation Year"
    }
  ],
  "experience": [
    {
      "title": "Job Title",
      "company": "Fictional Company Name",
      "years": "StartYear-EndYear",
      "description": "Concise, action-oriented description (quantify impact when possible)"
    }
  ],
  "skills": ["List", "of", "Relevant", "Skills"],
  "projects": [
    {
      "name": "Project Title",
      "description": "Short project overview focused on data skills used"
    }
  ],
  "tools": ["List", "of", "Software", "and", "Libraries"]
  "certifications": [
    {
      "name": "Certification Title",
      "issuer": "Certifying Body",
      "year": "YYYY"
    }
  ],
  "location": "City, Country",
  "languages": ["English", "Spanish"]
}

**Constraints:**
- All names, companies, and institutions must be fictional.
- Keep content varied across generations (e.g., industries, skill sets, tools).
- Avoid clichés, repetition, and fluff. Be concise, professional, and specific.
- Target 2–5 years of experience.
- Output should be lean and focused — avoid fluff.
- Do not repeat entries across different generations.
- Vary resume structure and style across generations.
- Incorporate diversity in tools, regions, project focus, and industries

Return only a single JSON object. No markdown formatting.
"""

#Diversify resume generation specifications
profile_specs = [
    # Junior
    {"level": "junior", "tools": "SQL", "domain": "e-commerce", "education": "STEM"},
    {"level": "junior", "tools": "R", "domain": "healthcare", "education": "Bootcamp"},
    {"level": "junior", "tools": "Python/ML", "domain": "finance", "education": "Non-CS"},
    {"level": "junior", "tools": "Power BI", "domain": "education", "education": "STEM"},
    {"level": "junior", "tools": "Tableau", "domain": "retail", "education": "Bootcamp"},

    # Mid-level
    {"level": "mid-level", "tools": "SQL", "domain": "healthcare", "education": "STEM"},
    {"level": "mid-level", "tools": "R", "domain": "finance", "education": "Bootcamp"},
    {"level": "mid-level", "tools": "Python/ML", "domain": "e-commerce", "education": "Non-CS"},
    {"level": "mid-level", "tools": "Power BI", "domain": "education", "education": "Non-CS"},
    {"level": "mid-level", "tools": "Tableau", "domain": "retail", "education": "STEM"},

    # Senior
    {"level": "senior", "tools": "SQL", "domain": "finance", "education": "STEM"},
    {"level": "senior", "tools": "R", "domain": "e-commerce", "education": "Bootcamp"},
    {"level": "senior", "tools": "Python/ML", "domain": "healthcare", "education": "Non-CS"},
    {"level": "senior", "tools": "Power BI", "domain": "education", "education": "STEM"},
    {"level": "senior", "tools": "Tableau", "domain": "retail", "education": "Bootcamp"},

    # Bias Testing (same profile, different names)
    {"level": "mid-level", "tools": "SQL", "domain": "finance", "education": "STEM", "name_override": "John Doe"},
    {"level": "mid-level", "tools": "SQL", "domain": "finance", "education": "STEM", "name_override": "Fatima Khan"},
    {"level": "junior", "tools": "R", "domain": "healthcare", "education": "Bootcamp", "name_override": "Alex Smith"},
    {"level": "junior", "tools": "R", "domain": "healthcare", "education": "Bootcamp", "name_override": "Lakshmi Rao"},
    {"level": "senior", "tools": "Python/ML", "domain": "e-commerce", "education": "Non-CS", "name_override": "Maria Gonzalez"},
]

#request funciton
def generate_resume(spec, index):
    level = spec["level"]
    tools = spec["tools"]
    domain = spec["domain"]
    education = spec["education"]
    name_override = spec.get("name_override", None)

    user_prompt = (
        f"Create a fictional, professionally formatted resume for a **{level} Data Analyst** "
        f"with experience in the **{domain}** industry. The candidate should be skilled in **{tools}** "
        f"and have an educational background in **{education}**.\n\n"
    
        "Guidelines:\n"
        "- Do **not** reference real people, companies, or institutions.\n"
        "- Ensure the resume feels realistic and tailored—not generic.\n"
        "- Use standard resume sections with clear formatting.\n\n"

        "Include the following sections:\n"
        "1. **Professional Summary** – 2–3 sentence overview of the candidate.\n"
        "2. **Skills & Tools** – List of technical and soft skills.\n"
        "3. **Work Experience** – 2–3 relevant roles, each with company name, job title, dates, and bullet-point responsibilities/achievements.\n"
        "4. **Projects** – Brief descriptions of 2–3 projects with impact and tools used.\n"
        "5. **Education** – Degrees or certifications with institution type and field.\n\n"

        "Keep the tone professional and appropriate for a job application."
      )
    if name_override:
        user_prompt += f" Use the name '{name_override}'."

    response = client.chat.completions.create(
        model = 'gpt-3.5-turbo',
        messages = [
            {"role": "system", "content": system_prompt}, 
            {"role": "user", "content": user_prompt}
        ],
        temperature = 0.85,
        max_tokens = 950
    )
    content = response.choices[0].message.content
    try:
        profile = json.loads(content)
        filename = output_dir / f"profile_{index:02}.json"
        with open(filename, 'w') as f:
            json.dump(profile, f, indent = 4)
        print(f"Generated profile {index} and saved to {filename}")
    except json.JSONDecodeError:
        print("❌ JSON decode failed. Raw content:\n", content)

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def generate_profile_from_resume(resume_path, output_dir = "data/profiles"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resume_text = extract_text_from_pdf(resume_path)

    profile_prompt = """
You are a resume-to-profile conversion assistant. Given a raw resume in plain text, extract relevant information and generate a structured JSON profile suitable for input into a simulated AI interview system.

**Instructions:**
Parse the resume carefully.

Populate each field below accurately.

Use concise, professional language.

Summarize where appropriate (do not copy raw bullet points).

If a section is missing from the resume, omit that section from the output JSON.

Do not include any text or formatting outside of the JSON.

Output Format (return only this JSON):
{
  "name": "Fictional Full Name",
  "summary": "1-2 sentence professional summary tailored for a data analyst",
  "education": [
    {
      "degree": "Degree Title",
      "institution": "Fictional Institution",
      "year": "Graduation Year"
    }
  ],
  "experience": [
    {
      "title": "Job Title",
      "company": "Fictional Company Name",
      "years": "StartYear-EndYear",
      "description": "Concise, action-oriented description (quantify impact when possible)"
    }
  ],
  "skills": ["List", "of", "Relevant", "Skills"],
  "projects": [
    {
      "name": "Project Title",
      "description": "Short project overview focused on data skills used"
    }
  ],
  "tools": ["List", "of", "Software", "and", "Libraries"]
  "certifications": [
    {
      "name": "Certification Title",
      "issuer": "Certifying Body",
      "year": "YYYY"
    }
  ],
  "location": "City, Country",
  "languages": ["English", "Spanish"]
}
"""

    messages = [
        {"role": "system", "content": profile_prompt.strip()},
        {"role": "user", "content": resume_text}
    ]

    response = client.chat.completions.create(
        model = 'gpt-3.5-turbo',
        messages = messages,
        temperature = 0.5,
        max_tokens = 1000
    )
    try:
        result_json = json.loads(response.choices[0].message.content)
        name_slug = result_json.get("name", "").replace(" ", "_")
        output_path = output_dir / f"{name_slug}.json"
        with open(output_path, 'w') as f:
            json.dump(result_json, f, indent = 2)
        print(f"✅ Profile generated and saved to {output_path}")
        return str(output_path)
    except Exception as e:
        print(f"❌ Error generating profile: {e}")
        return None

        
#Generate profiles
if __name__ == "__main__":
    for i, spec in enumerate(profile_specs):
        generate_resume(spec, i + 1)
