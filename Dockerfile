# Use lightweight Python image
FROM python:3.11-slim

# Install LibreOffice
RUN apt-get update && apt-get install -y libreoffice && apt-get clean

# Set working dir
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Start FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
