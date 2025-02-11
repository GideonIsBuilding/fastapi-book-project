# Use official lightweight Python image
FROM python:3.12-alpine

# Set the working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the api code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]