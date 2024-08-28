# Use the latest Python image as the base
FROM python:3.12.3-slim

# Install gcc
RUN apt-get update && apt-get install -y gcc

RUN pip install numpy
# RUN pip install numpy
# RUN pip install six

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code to the working directory
COPY . .

# Set the entry point to execute the main file embeddings.py
CMD ["python", "embeddings.py"]