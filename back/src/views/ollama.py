import logging

import requests
from controllers.SummarizeManager import SummarizeManager
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/ollama", tags=["Ollama"])


@router.get("/summary/{model}")
async def make_summary(content: str, model: str):
    try:
        return SummarizeManager.make_summary(
            input=content,
        )
    except Exception as e:
        logging.error(f"Error making summary with model {model}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error making summary with model {model}: {str(e)}"
        )


def list_models():
    response = requests.get("http://ollama:11434/api/tags")
    if response.status_code == 200:
        return response.json()["models"]
    else:
        raise Exception(
            f"Failed to fetch models: {response.status_code} {response.text}"
        )


@router.get("/list")
async def request_list_models():
    return list_models()


def pull_model(model_name):
    logging.info(f"Pulling model: {model_name}")
    response = requests.post("http://ollama:11434/api/pull", json={"name": model_name})
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(
            f"Failed to pull model '{model_name}': {response.status_code} {response.text}"
        )


@router.post("/pull/{model_name}")
async def request_pull_model(model_name: str):
    return pull_model(model_name)


@router.delete("/delete/{model_name}")
async def delete_model(model_name):
    response = requests.delete(
        "http://ollama:11434/api/delete", json={"name": "llama3"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(
            f"Failed to delete model '{model_name}': {response.status_code} {response.text}"
        )
