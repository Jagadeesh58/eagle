FROM python:3.9-slim
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py /app/
COPY static /app/static
COPY templates /app/templates
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]