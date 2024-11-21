from linkedin_api import Linkedin
import csv
import logging
import time

# Configure logging
logging.basicConfig(
    filename='job_scraper.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Authenticate with LinkedIn API
api = Linkedin('Username', 'Password')

def search_backend_engineer_jobs():
    # Start timing
    start_time = time.time()

    # Define search parameters
    keywords = "Backend engineer"
    location_name = "United States"
    listed_at = 86400  # Last 24 hours

    try:
        # Log the start of the job search
        logging.info("Starting job search with keywords='%s' and location='%s'", keywords, location_name)

        # Search for jobs
        jobs = api.search_jobs(
            keywords=keywords,
            location_name=location_name,
            listed_at=listed_at,
            experience=None,  # Mid-senior to executive levels
            job_type=['F'],  # Full-time
            remote=['1', '2', '3'],  # Onsite, remote, or hybrid
            limit=50 # Return up to 3 results
        )
        logging.info("Found %d jobs", len(jobs))

        # Open the CSV file for writing
        with open('backend_engineer_jobs.csv', 'w', newline='') as csvfile:
            fieldnames = ['Company Name', 'Job Title', 'Description', 'Job Link']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for index, job in enumerate(jobs, start=1):
                job_id = job["trackingUrn"].split(":")[-1]
                job_data = api.get_job(job_id)

                # Log the raw job data for debugging
                logging.debug("Raw job data for job #%d: %s", index, job_data)

                # Extract the company name
                company_details = job_data.get("companyDetails", {}).get(
                    "com.linkedin.voyager.deco.jobs.web.shared.WebCompactJobPostingCompany", {}
                )
                company_name = company_details.get("companyResolutionResult", {}).get("name", "Unknown")

                # Log the extracted company name
                logging.info("Job #%d: Extracted company name: %s", index, company_name)

                # Extract other details
                title = job_data.get("title", "Unknown")
                description = job_data.get("description", {}).get("text", "Unknown")
                job_link = f"https://www.linkedin.com/jobs/view/{job_id}"

                # Write to CSV
                writer.writerow({
                    'Company Name': company_name,
                    'Job Title': title,
                    'Description': description,
                    'Job Link': job_link
                })

                logging.info("Job #%d: Successfully wrote to CSV", index)

        logging.info("Job details saved to 'backend_engineer_jobs.csv'")

    except Exception as e:
        logging.error("An error occurred during job search: %s", str(e))

    # End timing and log the duration
    end_time = time.time()
    total_time = end_time - start_time
    logging.info("Total execution time: %.2f seconds", total_time)

# Call the function
search_backend_engineer_jobs()
