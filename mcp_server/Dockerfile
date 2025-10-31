# Use the official Python image from Docker Hub as the base image
FROM python:3.11-slim

# Set environment variables for better Python and server operation
ENV PYTHONUNBUFFERED 1

# Create and set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
# We install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main application server file
COPY mcp_reports_server.py /app/

# Expose the port the application runs on
EXPOSE 5000

# HARDCODING THE PORT 5000 HERE
CMD ["uvicorn", "mcp_reports_server:app", "--host", "0.0.0.0", "--port", "5000"]
