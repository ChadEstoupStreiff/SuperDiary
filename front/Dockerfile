FROM python:3.11-slim-buster

RUN apt-get update -y


COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# COPY config.toml config.toml
# COPY credentials.toml credentials.toml
# RUN mkdir -p ~/.streamlit
# RUN cp config.toml ~/.streamlit/config.toml
# RUN cp credentials.toml ~/.streamlit/credentials.toml

COPY src /app
WORKDIR /app

EXPOSE 80
ENTRYPOINT ["streamlit", "run"]
CMD ["main.py"]