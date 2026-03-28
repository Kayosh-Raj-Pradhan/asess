FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the frontend files
COPY . .

# Expose port for development server
EXPOSE 8080

# Install deps at runtime too (in case volume mount overrides /app)
# Then start the dev server
CMD pip install -q -r requirements.txt && python server.py
