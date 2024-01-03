# Use an official lightweight Python image.
# alpine is chosen for its small footprint compared to Ubuntu.
FROM python:3.8-alpine

# Set environment variables.
# Python won't try to write .pyc files on the container.
ENV PYTHONDONTWRITEBYTECODE 1
# Python outputs all messages directly to the terminal (e.g. your container's log) without buffering.
ENV PYTHONUNBUFFERED 1

# Set work directory.
WORKDIR /app

# Copy the dependencies file to the working directory.
COPY requirements.txt .

# Install any dependencies.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory.
COPY . .

# Specify the command to run on container start.
CMD [ "python", "./app/main.py" ]
