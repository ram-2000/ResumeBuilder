from flask import Flask
import os
from groq import Groq
import re
import json
import asyncio

from groq import AsyncGroq

os.environ['GROQ_API_KEY'] = "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"

app = Flask(__name__)
client = AsyncGroq(api_key=os.environ.get("GROQ_API_KEY"))


@app.route('/findWords')
async def findWords():
    with open('jobDescription.txt', 'r') as job_description_file:
        jobDescription = job_description_file.read()
    
    try:
        stream = await client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Job searcher.You are looking for all the keywords in the job description."
                },
                {
                    "role": "user",
                    "content": '''
                                Here is the job description : {jobDescription}.Find all the keywords in the job description and layout it in the form 
                                Skills I want them to be divided into two languages and frameworks.give the answer to me in json format.
                                '''.format(jobDescription=jobDescription)
                }
            ],
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        answer = stream.choices[0].message.content
        answer = json.loads(answer)
        return answer
    except Exception as e:
        return str(e)
        
    











@app.route('/skills')
def getSkills():
    with open('skills.txt', 'r') as resume_file:
        resume = resume_file.read()

    with open('jobDescription.txt', 'r') as job_description_file:
        jobDescription = job_description_file.read()

    try:
        
        stream = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a LaTeX expert specialized in resume editing. Provide the LaTeX code for the skills section, and output only the LaTeX code, with no additional explanation or text."
                },
                {
                    "role": "user",
                    "content": "Here is the current skills section of my resume: " + resume + ". I am targeting the job described here: " + jobDescription + ". Adjust the skills section to align with the job's requirements. The revised section should be concise, limited to two lines, and formatted in LaTeX as specified.They should be Languages, Tools/Framework"
                }
            ],
            max_tokens=4098
        )


        
        print(stream)
        result = stream.choices[0].message.content
        pattern = r"\\section\{Skills\}.*?\\end\{itemize\}"

        # Using regex to find the LaTeX block
        latex_code = re.search(pattern, result, re.DOTALL)
        if latex_code:
            return latex_code.group()
            print(latex_code.group())
        else:
            print("No LaTeX code found.")
        return result
    except Exception as e:
        return str(e), 500
    
@app.route('/workex')
def getWorkExp():
    with open('workex.txt', 'r') as resume_file:
        resume = resume_file.read()

    with open('jobDescription.txt', 'r') as job_description_file:
        jobDescription = job_description_file.read()

    try:
        
        stream = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{
                "role": "system",
                "content": "You are a resume editor, and output only the LaTeX code, with no additional explanation or text."
            }
                      ,{
                "role": "user",
                "content": "This is my resume with work Experience section:" + resume + " for job description " + jobDescription + "I need you to update my work experience with respect to the job description.You can change the job designation.Please dont add anythingand give me in the format that is mentioned.I want my points to be started with action verb and should have problem +soution and how u handled it.I need to have some quantifying metric in it."
            }],
            max_tokens=4098
        )
        
        result = stream.choices[0].message.content
        # temp = result.split(":")
        # return temp[1]
        return result
    except Exception as e:
        return str(e), 500

@app.route('/projects')
def getProjects():
    with open('projects.txt', 'r') as resume_file:
        resume = resume_file.read()

    with open('jobDescription.txt', 'r') as job_description_file:
        jobDescription = job_description_file.read()

    try:
        
        stream = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{
                "role": "system",
                "content": "You are a resume editor, and output only the LaTeX code, with no additional explanation or text. "
            }
                      ,{
                "role": "user",
                "content": "this is my resume with projects section:" + resume + " for job description " + jobDescription + "I need you to  Update and give me Three project which align with the job description.Give me in the format that is mentioned."
            }],
            max_tokens=4098
        )
        
        result = stream.choices[0].message.content
        # temp = result.split(":")
        # return temp[1]
        return result
    except Exception as e:
        return str(e), 500


def getEducation():
    with open('education.txt', 'r') as resume_file:
        data = resume_file.read()    
    return data

def getresume():
    with open('resume.txt', 'r') as resume_file:
        data = resume_file.read()
    return data



@app.route('/getharry')
def getharry():
    s="amlorvo"
@app.route('/getResume')
def getResume():
    skills = getSkills()
    Experience = getWorkExp()
    projects = getProjects()
    Education = getEducation()
    resume = getresume()
    print(skills)
    with open('temp.txt', 'w') as file:
        file.write(resume + '\n\n')
        file.write(Education + '\n\n')
        file.write(skills + "\n\n")
        file.write(Experience + '\n\n')
        file.write(projects + '\n\n')
        
        file.write("\\end{document}")
    # finalResume = resume  +skills + Experience + projects + Education

    return "done"


if __name__ == '__main__':
    app.run()