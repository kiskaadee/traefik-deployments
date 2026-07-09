FROM python:3.11-alpine

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir markdown

# Copy application files
COPY app/ /app/

# Default Environment Variables
ENV PORT=8000
ENV DOCS_ROOT=/docs

EXPOSE 8000

CMD ["python", "main.py"]
