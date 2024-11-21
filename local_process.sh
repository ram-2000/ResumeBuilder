#!/bin/bash

# Set executable permissions on this file: chmod +x run_scripts.sh

# Run the first Python script
echo "Running Linkedin_API.py..."
python3 Linkedin_API.py
if [ $? -ne 0 ]; then
    echo "Linkedin_API.py failed. Exiting."
    exit 1
fi

# Run the second Python script
echo "Running Gemini.py..."
python3 Gemini.py
if [ $? -ne 0 ]; then
    echo "Gemini.py failed. Exiting."
    exit 1
fi
echo "Both scripts ran successfully."
