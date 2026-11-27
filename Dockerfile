FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && groupadd -g 10001 photo && useradd -u 10001 -g 10001 -M photo && mkdir /photos
COPY photo_api.py photo_catalog.py device_profiles.py image_pipeline.py frame_encoding.py ./
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD ["python", "-c", "import os,urllib.request; r=urllib.request.Request('http://127.0.0.1:8080/api/health',headers={'Authorization':'Bearer '+os.environ['PHOTO_API_TOKEN']}); urllib.request.urlopen(r,timeout=3).close()"]
CMD ["python", "photo_api.py", "--photos", "/photos", "--host", "0.0.0.0", "--port", "8080"]
