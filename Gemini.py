import os
import google.generativeai as genai
import json
from flask import Flask
import re
import subprocess
import logging
import pandas as pd
import time
from groq import Groq
from groq import AsyncGroq
import asyncio
import Constants

log_file = "resume_generation.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Set up environment variable for API key
# os.environ['GEMINI_API_KEY'] = ""


# genai.configure(api_key=os.environ["GEMINI_API_KEY"])
genai.configure(api_key=Constants.GEMINI_API_KEY)
client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))

def validate_latex_format(text):
    """
    Ensures that text is LaTeX compatible by escaping special LaTeX characters if they are not properly formatted.
    """
    # Order matters: Backslash must be escaped first to prevent corrupting other escaped characters
    special_chars = [
        ('\\', r'\textbackslash{}'),  # Escape backslashes first
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}')
    ]
    
    for char, replacement in special_chars:
        # Escape only unescaped special characters
        text = re.sub(r'(?<!\\)' + re.escape(char), replacement, text)
    
    return text



def sanitize_filename(text):
    """
    Sanitize text for safe file naming.
    Removes or replaces special characters that might cause issues in filenames.
    """
    # Replace invalid characters with underscores
    text = re.sub(r"[^a-zA-Z0-9\s\-.]", "_", text)  # Allow only alphanumerics, spaces, dashes, and dots
    text = re.sub(r"[\s]+", "_", text)  # Replace spaces with underscores
    return text.strip("_")  # Remove leading/trailing underscores



def format_experience_points(points):
    """
    Formats and validates LaTeX compatibility of experience points.
    """
    formatted_points = []
    for point in points:
        validated_point = validate_latex_format(point)
        formatted_points.append(f"\\resumeItem{{{validated_point}}}")
    return "\n".join(formatted_points)

def getSkills(response):
    languages = response["languages"]
    tools = response["frameworks/tools"]

    lang = ', '.join(languages)
    tool = ', '.join(tools)

    output = f"""
    \\section{{Skills}}
    \\resumeSubHeadingListStart
        \\resumeSubItem{{\\textbf{{Languages:}} {validate_latex_format(lang)}}}
        \\resumeSubItem{{\\textbf{{Tools/Frameworks:}} {validate_latex_format(tool)}}}
    \\resumeSubHeadingListEnd
    """
    return output

def workex(response):
    workexperiences = response["work_experience"]
    output = """\\section{Work Experience}
                \\resumeSubHeadingListStart"""
    for experience in workexperiences:
        company = validate_latex_format(experience["Company"])
        role = validate_latex_format(experience["Role"])
        experience_points = format_experience_points(experience["Experience Points"])
        startDate = validate_latex_format(experience["StartDate"])
        endDate = validate_latex_format(experience["EndDate"])
        
        outputForOneCompany = f"""
        \\resumeSubheading
        {{\\textbf{{{company}}}}}{{}}
        {{\\textit{{{role}}}}}{{{startDate} -- {endDate}}}
        \\resumeItemListStart
            {experience_points}
        \\resumeItemListEnd
        """
        output += outputForOneCompany
    output += "\\resumeSubHeadingListEnd"
    return output



def getProjects(response, max_projects=None):
    """
    Generate the Projects section, limiting the number of projects if necessary.
    """
    logger.debug(f"Generating Projects section with max_projects={max_projects}")
    projects = response["projects"][:max_projects] if max_projects is not None else response["projects"]
    logger.debug(f"Number of projects included: {len(projects)}")

    output = """\\section{Projects}
                \\resumeSubHeadingListStart"""
    for project in projects:
        title = validate_latex_format(project["Title"])
        technologies = validate_latex_format(', '.join(project["Technologies"]))
        date_range = validate_latex_format(project["Date Range"])
        project_points = format_experience_points(project["Project Points"])

        logger.debug(f"Adding project: {title} ({len(project_points.splitlines())} points)")

        project_entry = f"""
        \\resumeProjectHeading
            {{\\textbf{{{title}}} $|$ \\emph{{{technologies}}}}}{{{date_range}}}
            \\resumeItemListStart
                {project_points}
            \\resumeItemListEnd
        """
        output += project_entry
    output += "\\resumeSubHeadingListEnd"
    return output


def generate_resume_with_project_removal(response, company_name, role):
    """
    Generate the LaTeX document, removing projects iteratively to fit one page,
    and save the PDF with a customized name in a new directory.
    """
    max_projects = len(response["projects"])  # Start with all projects included
    logger.info(f"Starting with {max_projects} projects in the resume.")

    education_section = """
    \\section{Education}
      \\resumeSubHeadingListStart
        \\resumeSubheading
          {University of Dayton}{Ohio, USA}
          {Master of Science in Computer Engineering}{Aug 2022 -- May 2024}
        \\resumeSubheading
          {Andhra University}{Andhra Pradesh, India}
          {Bachelor of Technology in Computer Science}{Aug 2017 -- May 2021}
      \\resumeSubHeadingListEnd
    """
    with open('resume.txt', 'r') as resume_file:
        data = resume_file.read()

    # Create the directory to save the resumes
    output_dir = "generated_resumes"
    os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist

    while max_projects >= 0:
        logger.debug(f"Attempting with {max_projects} projects.")

        # Generate LaTeX content
        content = (
            f"{data}\n\n"
            f"{getSkills(response)}\n\n"
            f"{workex(response)}\n\n"
            f"{getProjects(response, max_projects)}\n\n"
            f"{education_section}\n\n"
            "\\end{document}"
        )

        # Save LaTeX to a temporary file
        with open("temp_resume.tex", "w") as file:
            file.write(content)
        logger.info(f"Generated LaTeX file with {max_projects} projects.")

        # Compile to PDF and check page count
        try:
            compile_pdf("temp_resume.tex")
            page_count = get_pdf_page_count("temp_resume.pdf")
            logger.info(f"Generated PDF with {page_count} pages.")
        except RuntimeError as e:
            logger.error(f"LaTeX compilation or page count retrieval failed: {e}")
            break

        if page_count <= 1:
            print(company_name,role)
            
            # Generate the dynamic file name
            output_filename = f"Shiva_Maddala_{sanitize_filename(company_name)}_{sanitize_filename(role)}.pdf"
            full_output_path = os.path.join(output_dir, output_filename)

            # Move the generated PDF to the new directory
            os.rename("temp_resume.pdf", full_output_path)
            logger.info(f"Resume saved as: {full_output_path}")
            return full_output_path

        # Reduce the number of projects for the next iteration
        max_projects -= 1
        logger.warning(f"Reducing projects to {max_projects} for the next attempt.")

    logger.warning("Unable to fit within one page even after removing all projects.")
    output_filename = f"Shiva_Maddala_{sanitize_filename(company_name)}_{sanitize_filename(role)}.pdf"
    full_output_path = os.path.join(output_dir, output_filename)
    os.rename("temp_resume.pdf", full_output_path)
    logger.info(f"Resume saved as: {full_output_path}")
    return full_output_path  # Return the best-fit resume



def compile_pdf(tex_file):
    """
    Compiles the LaTeX file to PDF using pdflatex with a timeout.
    """
    try:
        logger.debug(f"Compiling LaTeX file: {tex_file}")
        result = subprocess.run(
            ["pdflatex", tex_file], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            timeout=30  # Timeout after 30 seconds
        )
        if result.returncode != 0:
            logger.error("Error during LaTeX compilation.")
            logger.error(result.stderr.decode())
            raise RuntimeError("LaTeX compilation failed.")
        logger.debug("LaTeX compilation successful.")
    except subprocess.TimeoutExpired:
        logger.error("pdflatex timed out.")
        raise RuntimeError("LaTeX compilation timed out.")

def get_pdf_page_count(pdf_file):
    """
    Get the page count of a PDF file using pdfinfo with a timeout.
    """
    try:
        logger.debug(f"Getting page count for PDF: {pdf_file}")
        result = subprocess.run(
            ["pdfinfo", pdf_file], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            check=True, 
            timeout=10  # Timeout after 10 seconds
        )
        for line in result.stdout.decode("utf-8").splitlines():
            if "Pages:" in line:
                page_count = int(line.split(":")[1].strip())
                logger.debug(f"PDF has {page_count} pages.")
                return page_count
    except subprocess.TimeoutExpired:
        logger.error("pdfinfo timed out.")
        raise RuntimeError("PDF info retrieval timed out.")
    except Exception as e:
        logger.error(f"Error getting PDF page count: {e}")
        raise
    return 0



def validate_json(response_json):
    """
    Validates the JSON structure to ensure it matches the expected format.
    """
    required_keys = {
        "languages": list,
        "frameworks/tools": list,
        "work_experience": list,
        "projects": list
    }
    
    for key, expected_type in required_keys.items():
        if key not in response_json or not isinstance(response_json[key], expected_type):
            return False
    
    # Check each work experience for required fields
    for experience in response_json["work_experience"]:
        if not all(k in experience for k in ("Company", "Role", "Experience Points", "StartDate", "EndDate")):
            return False
        if not isinstance(experience["Experience Points"], list):
            return False

    # Check each project for required fields
    for project in response_json["projects"]:
        if not all(k in project for k in ("Title", "Technologies", "Date Range", "Project Points")):
            return False
        if not isinstance(project["Project Points"], list):
            return False
    
    return True

def getResume(response):
    # Define the static Education section
    education_section = """
    \\section{Education}
      \\resumeSubHeadingListStart
        \\resumeSubheading
          {University of Dayton}{Ohio, USA}
          {Master of Science in Computer Engineering}{Aug 2022 -- May 2024}
        \\resumeSubheading
          {Andhra University}{Andhra Pradesh, India}
          {Bachelor of Technology in Computer Science}{Aug 2017 -- May 2021}
      \\resumeSubHeadingListEnd
    """
    
    with open('resume.txt', 'r') as resume_file:
        data = resume_file.read()
    
    # Write all sections to the temp.txt file in order
    with open('temp.txt', 'w') as file:
        file.write(data + '\n\n')
        file.write(getSkills(response) + "\n\n")
        file.write(workex(response) + '\n\n')
        file.write(getProjects(response) + "\n\n")
        file.write(education_section + "\n\n")
        file.write("\\end{document}")
    
    return "Done"


async def responseWithJD():
    results = []
    try:
        logger.info("Starting to process job descriptions from the CSV file.")
        
        # Load data from the uploaded CSV file
        csv_file_path = 'backend_engineer_jobs.csv'  # Path to the uploaded CSV
        data = pd.read_csv(csv_file_path)
        logger.info(f"Loaded CSV file with {len(data)} rows.")

        for index, row in data.iterrows():
            try:
                logger.info(f"Processing row {index + 1}/{len(data)}.")
                jobDescription = row.get("Description")  # Replace with actual column name
                company_name = row.get("Company Name")  # Replace with actual column name
                role = row.get("Job Title")             # Replace with actual column name

                logger.info(f"Extracted Job Description, Company: {company_name}, Role: {role}.")

                # Load resume content
                logger.info("Loading resume content from file.")
                with open('workex.txt', 'r') as resume_file:
                    resume = resume_file.read()
                logger.info("Resume content loaded successfully.")

                # Retry until valid JSON is received
                max_retries = 3
                valid_response = False

                logger.info("Preparing to send data for processing.")
                for attempt in range(max_retries):
                    logger.info(f"Attempt {attempt + 1} of {max_retries}.")
                    try:
                        chat_session = model.start_chat(
                            history=[
                                {
                                    "role": "user",
                                    "parts": [
                                        f'''
                                        Using the job description: {jobDescription}, and work experience: {resume}, 
                                        please generate the required JSON format.
                                        '''
                                    ]
                                }
                            ]
                        )
                        logger.info("Data sent to model successfully.")

                        # response = chat_session.send_message("There should be a single JSON output as per the system message")
                        response = await groq_resume(jobDescription,resume)
                        logger.info("Response received from model.")

                        logger.info(response)

                        raw_json = response.text.strip().replace("```json\n", "").replace("\n```", "")
                        logger.info(f"Raw JSON extracted: {raw_json[:200]}... (truncated)" if len(raw_json) > 200 else raw_json)

                        response_json = json.loads(raw_json)
                        logger.info("Parsed JSON successfully.")

                        if validate_json(response_json):
                            logger.info("JSON structure validated successfully.")
                            
                            result_path = generate_resume_with_project_removal(response_json, company_name, role)
                            logger.info(f"Resume generated and saved at: {result_path}")

                            results.append(result_path)
                            valid_response = True
                            break  # Exit the retry loop on success
                        else:
                            logger.warning(f"Invalid JSON structure on attempt {attempt + 1}.")

                    except json.JSONDecodeError as json_err:
                        logger.error(f"JSON decode error on attempt {attempt + 1}: {json_err}")
                    except Exception as model_err:
                        logger.error(f"Error during model response handling on attempt {attempt + 1}: {model_err}")

                if not valid_response:
                    logger.error(f"Failed to obtain valid JSON for {company_name}, role {role} after {max_retries} attempts.")

            except Exception as row_err:
                logger.error(f"Error processing row {index + 1}: {row_err}")

        logger.info("All rows processed. Returning results.")
        return {"results": results}

    except Exception as e:
        logger.critical(f"Critical error in responseWithJD: {e}")
        return {"error": str(e)}




generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",  # Replace with the appropriate model name
  generation_config=generation_config,
  system_instruction='''
    I will provide you with a Job Description, Work Experience, and Projects. Your task is to:

    1. **Extract Technologies**:
       - From the provided job description, identify and extract all programming languages, frameworks, and tools mentioned.
       - Group similar terms where applicable (e.g., C++ and C++14 can be grouped as "C++").
       - The output should be in JSON format with the following fields:
         - `languages`: A list of programming languages mentioned in the job description.
         - `frameworks/tools`: A list of frameworks and tools mentioned in the job description.

    2. **Update Work Experience**:
       - Using the provided work experience, revise and expand the experience points to align with the skills extracted from the job description.
       - If the candidate has less than 3 years of experience, only consider the first two work experiences. If more than 3 years, prioritize the experience at CommerceIQ.
       - For each selected work experience, create exactly **five bullet points** that are concise and impactful.
       - Each bullet point should follow the format: `Action verb + Problem + Resolution + Quantifiable Metric` (e.g., percentages, time reduction, improvement rates).
       - Structure the work experience content to fit within a one-page resume format.
       - JSON output fields for work experience should include:
         - `Company`: Company name (should remain unchanged).
         - `Role`: Job role/title (should remain unchanged).
         - `Experience Points`: Five bullet points 
         - `StartDate`: Start date of the role.
         - `EndDate`: End date of the role.

    3. **Update Projects**:
       - Using the information from the job description, create or update project descriptions that showcase the skills, languages, and frameworks relevant to the job.
       - Give me around 3 projects.
       - Each project should be intermediate-level, achievable by the candidate, and include exactly **two bullet points**.
       - Each bullet point should highlight key achievements, methodologies, or technologies utilized.
       - JSON output fields for projects should include:
         - `Title`: Project title.
         - `Technologies`: A list of technologies or tools relevant to each project.
         - `Date Range`: Project duration (e.g., "Aug 2019 -- Jan 2021").
         - `Project Points`: Two detailed bullet points about the project.

    4. **Final JSON Output**:
       - Combine all results into a single JSON object with the following structure:
         {
           "languages": [],
           "frameworks/tools": [],
           "work_experience": [
             {
               "Company": "",
               "Role": "",
               "Experience Points": [],
               "StartDate": "",
               "EndDate": ""
             }
           ],
           "projects": [
             {
               "Title": "",
               "Technologies": [],
               "Date Range": "",
               "Project Points": []
             }
           ]
         }
    '''
)


async def groq_resume(jobDescription,resume):
    stream = await client.chat.completions.create(
            model="llama-3.1-70b-versatile",  # Replace with the appropriate Groq model
            messages=[
                {
                    "role": "system",
                    "content": '''
                    I will provide you with a Job Description, Work Experience, and Projects. Your task is to:

                    1. **Extract Technologies**:
                    - From the provided job description, identify and extract all programming languages, frameworks, and tools mentioned.
                    - Group similar terms where applicable (e.g., C++ and C++14 can be grouped as "C++").
                    - The output should be in JSON format with the following fields:
                        - `languages`: A list of programming languages mentioned in the job description.
                        - `frameworks/tools`: A list of frameworks and tools mentioned in the job description.

                    2. **Update Work Experience**:
                    - Using the provided work experience, revise and expand the experience points to align with the skills extracted from the job description.
                    - If the candidate has less than 3 years of experience, only consider the first two work experiences. If more than 3 years, prioritize the experience at CommerceIQ.
                    - For each selected work experience, create exactly **five bullet points** that are concise and impactful.
                    - Each bullet point should follow the format: `Action verb + Problem + Resolution + Quantifiable Metric` (e.g., percentages, time reduction, improvement rates).
                    - Structure the work experience content to fit within a one-page resume format.
                    - JSON output fields for work experience should include:
                        - `Company`: Company name (should remain unchanged).
                        - `Role`: Job role/title (should remain unchanged).
                        - `Experience Points`: Five bullet points 
                        - `StartDate`: Start date of the role.
                        - `EndDate`: End date of the role.

                    3. **Update Projects**:
                    - Using the information from the job description, create or update project descriptions that showcase the skills, languages, and frameworks relevant to the job.
                    - Give me around 3 projects.
                    - Each project should be intermediate-level, achievable by the candidate, and include exactly **two bullet points**.
                    - Each bullet point should highlight key achievements, methodologies, or technologies utilized.
                    - JSON output fields for projects should include:
                        - `Title`: Project title.
                        - `Technologies`: A list of technologies or tools relevant to each project.
                        - `Date Range`: Project duration (e.g., "Aug 2019 -- Jan 2021").
                        - `Project Points`: Two detailed bullet points about the project.

                    4. **Final JSON Output**:
                    - Combine all results into a single JSON object with the following structure:
                        {
                        "languages": [],
                        "frameworks/tools": [],
                        "work_experience": [
                            {
                            "Company": "",
                            "Role": "",
                            "Experience Points": [],
                            "StartDate": "",
                            "EndDate": ""
                            }
                        ],
                        "projects": [
                            {
                            "Title": "",
                            "Technologies": [],
                            "Date Range": "",
                            "Project Points": []
                            }
                        ]
                        }
                    '''
                },
                {
                    "role": "user",
                    "content": '''
                        Using the job description: {jobDescription}, and work experience: {resume}, 
                        please generate the required JSON format.
                    '''.format(jobDescription=jobDescription,resume=resume)
                }
            ],
            max_tokens=7999
        )
    answer = stream.choices[0].message.content
    parsed_result = json.loads(answer)
    print(parsed_result)
    return parsed_result

    

if __name__ == '__main__':
    asyncio.run(responseWithJD())
    