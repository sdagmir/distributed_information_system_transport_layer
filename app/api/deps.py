# app/api/deps.py
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.config import AppConfig, load_config
from app.repos.inmemory import InMemoryRepo
from app.services.message import MessageService
from app.kafka.producer import KafkaProducerWrapper
from app.kafka.consumer import KafkaConsumerWrapper


@lru_cache()
def get_config() -> AppConfig:
    """
    Чтение и кэширование конфига из YAML.
    """
    return load_config("config.yaml")


@lru_cache()
def get_repository() -> InMemoryRepo:
    """
    In-memory репозиторий.
    """
    return InMemoryRepo()


def get_message_service(
    cfg: Annotated[AppConfig, Depends(get_config)],
    repo: Annotated[InMemoryRepo, Depends(get_repository)],
) -> MessageService:
    """
    DI-точка для FastAPI: инжектим config + repo → получаем MessageService.
    """
    return MessageService(
        max_segment_size=cfg.segment.max_size,
        assembly_period=cfg.segment.assembly_period,
        repo=repo,
        http_client_cfg=cfg.http_client,
    )


@lru_cache()
def create_kafka_producer() -> KafkaProducerWrapper:
    cfg = get_config()
    return KafkaProducerWrapper(
        brokers=cfg.kafka.producer.brokers,
        topic=cfg.kafka.producer.topic,
    )


def get_kafka_producer(
    cfg: AppConfig = Depends(get_config),
) -> KafkaProducerWrapper:
    return KafkaProducerWrapper(
        brokers=cfg.kafka.producer.brokers,
        topic=cfg.kafka.producer.topic,
    )


@lru_cache()
def create_kafka_consumer(service: MessageService) -> KafkaConsumerWrapper:
    cfg = get_config()
    return KafkaConsumerWrapper(
        brokers=cfg.kafka.consumer.brokers,
        topic=cfg.kafka.consumer.topic,
        auto_offset_reset=cfg.kafka.consumer.auto_offset_reset,
        service=service,
    )


def get_kafka_consumer(
    svc: MessageService = Depends(get_message_service),
    cfg: AppConfig = Depends(get_config),
) -> KafkaConsumerWrapper:
    return KafkaConsumerWrapper(
        brokers=cfg.kafka.consumer.brokers,
        topic=cfg.kafka.consumer.topic,
        auto_offset_reset=cfg.kafka.consumer.auto_offset_reset,
        service=svc,
    )


def create_message_service() -> MessageService:
    """
    Ручной конструктор для lifespan: берём уже закэшированные config+repo.
    """
    cfg = get_config()
    repo = get_repository()
    return MessageService(
        max_segment_size=cfg.segment.max_size,
        assembly_period=cfg.segment.assembly_period,
        repo=repo,
        http_client_cfg=cfg.http_client,
    )
