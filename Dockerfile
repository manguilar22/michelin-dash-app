FROM python:3.12

WORKDIR /app

COPY utils/ utils/
COPY main.py .
COPY requirements.txt .

RUN ["pip", "install", "--upgrade", "pip"]
RUN ["pip", "install", "-r", "requirements.txt"]

ENV DEBUG "False"
ENV OPENAI_SECRET_KEY ""
# Postgresql credentials
ENV HOST ""
ENV PORT ""
ENV USER ""
ENV PASSWORD ""
ENV DATABASE ""

EXPOSE 8080

CMD ["python", "main.py"]