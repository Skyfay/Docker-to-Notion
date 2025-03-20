FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy script
COPY src/ /app/

# Set environment variables (must be overridden when starting)
ENV NOTION_API_KEY=""
ENV NOTION_DATABASE_ID=""
ENV CHECK_INTERVAL=3600
ENV GITHUB_TOKEN=""
ENV AWS_ACCESS_KEY=""
ENV AWS_SECRET_KEY=""
ENV AWS_REGION="eu-central-1"
ENV EXCLUDED_IMAGES="[]"

CMD ["python", "main.py"]