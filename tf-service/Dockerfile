FROM python:3.11-slim

# Install system dependencies for OpenCV and Matplotlib
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    # Matplotlib dependencies
    libfreetype6-dev \
    libpng-dev \
    pkg-config \
    python3-dev \
    # For saving figures
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p /app/uploads /app/output /app/app/data /mnist

# Setting Matplotlib to use the 'Agg' backend (for headless environments)
ENV MPLBACKEND=Agg

# Expose port
EXPOSE 9005

# Command to run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9005", "--reload"]