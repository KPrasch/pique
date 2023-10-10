# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install . -r requirements.txt

# Set this environment variable to ensure output isn't buffered, making it easier to view logs
ENV PYTHONUNBUFFERED=1
