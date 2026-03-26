FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /app/requirements.txt 

# Copy and prepare the startup scripts
COPY ./compose/start-django /start-django
COPY ./compose/start-celery /start-celery

# Fix line endings and make scripts executable in a single layer
RUN sed -i 's/\r$//g' /start-django /start-celery && chmod +x /start-django /start-celery 

# Copy project files
COPY ./src ./app

RUN mkdir -p ./static 
RUN mkdir -p ./media
