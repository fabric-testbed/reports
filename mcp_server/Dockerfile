# Use the official Python image from Docker Hub as the base image
FROM python:3.11-slim

# Set environment variables for better Python and server operation
ENV PYTHONUNBUFFERED 1
ENV FASTAPI_APP_MODULE mcp_reports_server:app
ENV FASTAPI_HOST 0.0.0.0
ENV FASTAPI_PORT 5000

# Create and set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
# We install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- NOTE on Client Files ---
# Since your reports_api.py is a custom file, we need to copy it too.
# Assuming it's in a subfolder named 'fabric_reports_client'
# You would need to ensure the correct path exists on your host machine.
# If fabric_reports_client is a package name, remove these lines.
COPY fabric_reports_client /app/fabric_reports_client
# -----------------------------

# Copy the main application server file
COPY mcp_reports_server.py /app/

# Expose the port the application runs on
EXPOSE 5000

# Command to run the application using Uvicorn
# We explicitly call the main app instance defined in the environment variable.
CMD ["uvicorn", "$FASTAPI_APP_MODULE", "--host", "$FASTAPI_HOST", "--port", "$FASTAPI_PORT"]
