#!/bin/bash

echo "Activating virtual environment..."
source /app/venv/bin/activate || {
  echo "Virtual environment activation failed. Exiting.";
  exit 1;
}

echo "Installing dependencies from requirements.txt..."
pip install -r /app/requirements.txt --quiet
if [ $? -ne 0 ]; then
  echo "Dependency installation failed."
  deactivate
  exit 1
fi

echo "Fetching jobs using Linkedin API..."
python3 /app/Linkedin_API.py
if [ $? -ne 0 ]; then
  echo "Linkedin_API failed to execute."
  deactivate
  exit 1
fi

echo "Generating PDFs using Gemini..."
python3 /app/Gemini.py
if [ $? -ne 0 ]; then
  echo "Gemini failed to execute."
  deactivate
  exit 1
fi

echo "Deactivating virtual environment..."
deactivate

echo "Process completed successfully at $(date)"
