import logging

import uvicorn
from fastapi import FastAPI

from app.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="BioKey V2",
    description="ML-Based Continuous Behavioral Authentication and Cybersecurity "
                "Framework for Real-Time Session Protection",
    version="v2-week3-stub",
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
