FROM python:3.12-slim
WORKDIR /code
# Dependencies first (cache-friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# App code
COPY . .
EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]
