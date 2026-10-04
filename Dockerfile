FROM python:3.12-slim
WORKDIR /app
COPY app.py dashboard.html services.json ./
RUN groupadd --gid 10001 observatory && useradd --uid 10001 --gid 10001 --create-home observatory && mkdir /data && chown observatory:observatory /data
USER observatory
EXPOSE 8080
CMD ["python", "app.py", "--host", "0.0.0.0", "--db", "/data/observatory.db"]
