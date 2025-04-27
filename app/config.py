from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field
from typing import List, Annotated
import yaml


class HTTPSettings(BaseSettings):
    host: str
    port: Annotated[int, Field(gt=0, lt=65536)]
    read_timeout: str
    write_timeout: str
    max_header_bytes: int


class HTTPClientSettings(BaseSettings):
    code_url: AnyHttpUrl
    receive_url: AnyHttpUrl


class KafkaProducerSettings(BaseSettings):
    brokers: List[str]
    topic: str
    required_acks: int
    retry_max: int
    return_success: bool


class KafkaConsumerSettings(BaseSettings):
    brokers: List[str]
    topic: str
    auto_offset_reset: str
    return_errors: bool


class KafkaSettings(BaseSettings):
    producer: KafkaProducerSettings
    consumer: KafkaConsumerSettings


class SegmentSettings(BaseSettings):
    max_size: int
    assembly_period: str


class AppConfig(BaseSettings):
    http: HTTPSettings
    http_client: HTTPClientSettings
    kafka: KafkaSettings
    segment: SegmentSettings

    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config(path: str = "config.yaml") -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppConfig.parse_obj(data)
