FROM python:3.12-slim-bookworm


# UPDATE
RUN apt-get update -y
RUN apt-get upgrade -y
RUN pip install --upgrade pip

# RUN apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-fra -y
RUN apt-get install -y libgl1 \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libglib2.0-0

WORKDIR /
COPY requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt


COPY src /app
EXPOSE 80
EXPOSE 81
ENTRYPOINT ["python"]
CMD ["/app/main.py"]