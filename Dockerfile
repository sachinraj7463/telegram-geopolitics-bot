FROM python:3.10-slim

# Install pip + system deps
RUN apt-get update && \
    apt-get install -y python3-distutils gcc && \
    apt-get clean

# Set work dir
WORKDIR /app

# Copy files
COPY . .

# Install Python deps
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Start the bot
CMD ["python", "manual.py"]
