import logging


from typing import Union

from fastapi import FastAPI

app = FastAPI()


logger = logging.getLogger(__name__)

@app.get("/")
def read_root():
    logger.info("Hello World")
    print("Hello World")
    return {"status": "Test"}


