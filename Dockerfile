FROM python:3.10-slim-buster
WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN apt update && \
    apt -y upgrade && \
    apt install -y ffmpeg && \
    apt install -y curl && \
    apt install sudo && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && \
    apt install -y nodejs &&\
    export PATH=./node_modules/.bin:$PATH && \
    npm install @digital-go-jp/abr-geocoder && \
    abrg download && \
    pip3 install --upgrade pip && \
    pip3 install poetry && \
    poetry config virtualenvs.create false && \
    poetry install

EXPOSE 8501

COPY . /app

ENTRYPOINT ["streamlit", "run"]

CMD ["app.py"]
