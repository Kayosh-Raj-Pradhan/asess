# Use an official Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv using the official installer (faster and cleaner than pip)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy only requirements first to leverage Docker layer caching
# This means dependencies are only re-installed if requirements.txt changes
COPY requirements.txt .

# Install dependencies
# --system tells uv to install into the global site-packages
# --no-cache avoids bloat in your final image
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Now copy the rest of the application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Command to run FastAPI with uvicorn
CMD ["uvicorn", "asess.main:app", "--host", "0.0.0.0", "--port", "8000"]