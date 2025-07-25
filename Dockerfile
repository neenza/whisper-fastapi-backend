FROM ubuntu:22.04

# Install build and runtime dependencies
RUN apt-get update && apt-get install -y \
    build-essential cmake ffmpeg git curl python3 python3-pip

# Set working directory
WORKDIR /app

# Copy only necessary files
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Build whisper.cpp
RUN git clone https://github.com/ggerganov/whisper.cpp.git && \
    cd whisper.cpp && \
    make && \
    find . -type f \( -name "main" -o -name "whisper" -o -name "whisper-cli" \) -exec cp {} /usr/local/bin/whisper \; -quit

# Set up the application
WORKDIR /app
COPY app ./app

# Download the model (tiny or base preferred for memory)
RUN mkdir -p models
RUN curl -L -o models/ggml-tiny.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin

# Expose FastAPI port
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
