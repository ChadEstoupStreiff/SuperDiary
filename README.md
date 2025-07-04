<img src="front/assets/logo.png" alt="drawing" width="30"/>  

# Super Diary

**Super Diary** is a powerful, AI-enhanced web application for organizing, searching, and extracting content from your documents. Inspired by tools like Paperless, it leverages state-of-the-art models to unlock the full potential of your file collection.

## 🚀 Features

- 🔍 **Smart Search**: Find files using natural language queries.
- 🧠 **AI Extraction**:
  - **Whisper** for audio transcription
  - **Tesseract** for OCR on images and PDFs
  - **LLMs** (llama3) for text understanding, summarization, tagging, and Q&A
- 📂 **Universal File Support**: Text, PDF, images, audio, and more.
- 🔒 **Local-first**: You control your data.

## 📦 Tech Stack

- **Back**: Python / FastAPI / SQLAlchemy  
- **Front**: Streamlit  
- **AI**: Whisper, Tesseract, Hugging Face LLMs  
- **Infra**: Docker for deployment

## 📷 Preview  
In coming...

## 🚀 Launch

> Install [Docker](https://docs.docker.com/engine/install/) and [docker compose](https://docs.docker.com/compose/install/).  
#### ⚠️ Make sure you allocated enough RAM to docker (see in settings) ! AI models may crash if not enough RAM.  

Get the app on your server or computer
```bash
git clone https://github.com/yourusername/super-diary.git
cd super-diary
```

Copy and edit .env
```bash
cp .env_ex .env
vim .env
```

Start the web app
```bash
./up.sh
```

Stop the web app
```bash
./down.sh
```  

## 🎓 License

MIT License © Chad Estoup-Streiff


### TODO / Ideas
Favorites files ? Will display on top when search
https://github.com/PaddlePaddle/PaddleOCR  
Dashboard -> Recently added
Dashboard -> Recently opened

Bugs:  
- HEIC images
- md files dont load
