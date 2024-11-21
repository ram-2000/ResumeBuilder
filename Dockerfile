# Use Python base image
FROM python:3.10-slim

# Install required dependencies for pip, cron, and LaTeX
RUN apt-get update && apt-get install -y \
    gcc \
    libssl-dev \
    libffi-dev \
    make \
    cron \
    texlive-full \
    && apt-get clean

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY . /app

# Install Python dependencies globally
RUN pip install --no-cache-dir -r /app/requirements.txt

# Add the cron job to run the script every 5 hours
RUN echo "0 */5 * * * /bin/bash /app/run_process.sh >> /var/log/cron.log 2>&1" > /etc/cron.d/generate_pdfs

# Apply permissions
RUN chmod +x /app/run_process.sh
RUN chmod 0644 /etc/cron.d/generate_pdfs

# Start cron service when the container starts
CMD ["cron", "-f"]
