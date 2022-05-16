FROM python:3.8.6
ENV PYTHONBUFFERED=1
ENV PORT 8080
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip==22.0.4
RUN pip install -r requirements.txt
COPY . /app/
CMD daphne -b 0.0.0.0 -p "${PORT}" server.asgi:application
EXPOSE ${PORT}