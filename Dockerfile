# Use official lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libgl1-mesa-dri \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (now in root)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code into a subdirectory
COPY backend/ backend/

# Copy the frontend code into a subdirectory
COPY frontend/ frontend/

# Copy the model weights into the backend directory (so they are next to main.py)
COPY yolov8x.pt backend/
COPY yolov8m_hardhat.pt backend/

# Change working directory to backend so uvicorn finds main.py easily
WORKDIR /app/backend

# Cloud Run expects the app to listen on port 8080, but HF Spaces expects 7860
ENV PORT=7860
EXPOSE 7860

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
