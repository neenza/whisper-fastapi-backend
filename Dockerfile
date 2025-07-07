FROM ubuntu:22.04

# Install build and runtime dependencies
RUN apt-get update && apt-get install -y \
    build-essential cmake ffmpeg git curl python3 python3-pip

# Set working directory
WORKDIR /app

# Copy only necessary files
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Clone and build whisper.cpp
RUN git clone https://github.com/ggerganov/whisper.cpp.git
WORKDIR /app/whisper.cpp
RUN make -j

# Go back to /app and copy the FastAPI app files
WORKDIR /app
COPY app ./app

# Download the model (tiny or base preferred for memory)
RUN mkdir -p models
RUN curl -L -o models/ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/models/ggml-base.en.bin

# Expose FastAPI port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
