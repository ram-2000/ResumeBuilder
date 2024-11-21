# AI-Powered Resume Tailor

An automated system that scrapes job descriptions from LinkedIn and Indeed, then uses Gemini AI to generate tailored resumes based on job requirements. The system runs automatically every 5 hours using containerized cron jobs.

## 🌟 Features

- **Automated Job Scraping**
  - Periodically scrapes job listings from LinkedIn and Indeed
  - Stores job descriptions in a database
  - Configurable job search criteria

- **Smart Resume Generation**
  - Uses Gemini AI for intelligent resume tailoring
  - Matches resume content with job requirements
  - Generates multiple versions based on different job descriptions

- **Containerized Solution**
  - Fully dockerized application
  - Automated scheduling with cron jobs
  - Easy deployment and scaling

## 🛠️ Technology Stack

- **Backend**: Python
- **AI**: Google's Gemini AI
- **Database**: [Your Database Choice]
- **Containerization**: Docker
- **Job Sources**: 
  - LinkedIn
  - Indeed

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.x
- Gemini AI API key
- LinkedIn API credentials (if using API)
- Indeed API credentials (if using API)

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone [your-repository-url]
   cd ai-resume-tailor
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

3. **Build and run with Docker**
   ```bash
   docker-compose up --build
   ```

## 🔧 Configuration

### Cron Schedule
The default scraping interval is set to 5 hours. Modify the crontab in the Dockerfile:
