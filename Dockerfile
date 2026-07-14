FROM python:3.12-slim

ENV TZ=Asia/Jakarta

WORKDIR /app

# install dependency python
COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# copy seluruh project
COPY . .

EXPOSE 5000

CMD ["python", "run.py"]
