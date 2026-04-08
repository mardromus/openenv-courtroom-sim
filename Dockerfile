FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir openenv-core

COPY . /app

EXPOSE 7860

# Provide the default command for Hugging Face Spaces (which expects 7860 port)
CMD ["uvicorn", "env:app", "--host", "0.0.0.0", "--port", "7860"]
