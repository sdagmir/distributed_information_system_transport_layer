from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import get_message_service, get_kafka_producer
from app.models.schemas import SendRequest, SendResponse, TransferRequest

from app.kafka.producer import KafkaProducerWrapper

router = APIRouter(prefix="", tags=["transport"])


@router.post(
    "/send",
    response_model=SendResponse,
    summary="Отправка сообщения с прикладного уровня",
    description="Принимает полное сообщение, разбивает на сегменты и отправляет на канальный уровень",
)
async def send_segment(
    req: SendRequest,
    svc=Depends(get_message_service),
):
    try:
        await svc.add_message(req)
        return SendResponse()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/transfer",
    response_model=SendResponse,
    summary="Передача сегмента с канального уровня",
    description="Принимает декодированный сегмент и сохраняет его для последующей сборки",
)
async def transfer_segment(
    req: TransferRequest,
    request: Request,
):
    try:
        producer: KafkaProducerWrapper = request.app.state.kafka_producer
        await producer.send_segment(req.id, req.model_dump())
        return SendResponse()
    except Exception as e:
        print("Ошибка в /transfer:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
