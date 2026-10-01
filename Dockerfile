# Use Official Python 3.12 Slim Image
FROM python:3.12-slim

# Set Working Directory
WORKDIR /app

# Prevent Python from writing .pyc files & buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Install System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy Requirements & Install Python Packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy All Application Files
COPY . .

# Expose Hugging Face Default Port
EXPOSE 7860

# Command to Start FastAPI Backend (which also serves the Frontend UI)
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "7860"]
