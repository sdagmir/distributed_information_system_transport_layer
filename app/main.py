import logging
import uvicorn
import asyncio

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.deps import create_message_service, create_kafka_consumer, create_kafka_producer
from app.config import load_config

CONFIG = load_config("config.yaml")

logger = logging.getLogger("transport")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):

    svc = create_message_service()
    producer = create_kafka_producer()
    consumer = create_kafka_consumer(svc)

    await producer.start()
    await consumer.start()

    app.state.kafka_producer = producer
    app.state.kafka_consumer = consumer

    asyncio.create_task(consumer.run())
    svc.start_assembly()

    yield

    logger.info("Сервер остановлен!")
    await producer.stop()
    await consumer.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="Transport Layer", lifespan=lifespan)

    @app.post("/receive")
    async def receive_stub(body: dict):
        # просто выводим в консоль собранное сообщение
        print("📬 Собранное сообщение:", body)
        return {"status": "ok"}

    from app.api.routes import router as transport_router
    app.include_router(transport_router, prefix="/transport")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=CONFIG.http.host,
        port=CONFIG.http.port,
        log_level="info",
    )
