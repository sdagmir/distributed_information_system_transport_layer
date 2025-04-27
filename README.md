# Транспортный уровень — FastAPI + Kafka

Транспортный уровень обеспечивает надёжную асинхронную доставку сообщений в распределённой системе обмена данными в реальном времени. Сервис принимает полное сообщение от прикладного уровня, разбивает его на сегменты фиксированного размера, публикует сегменты в Kafka, затем собирает их обратно и передаёт восстановленное сообщение в прикладной уровень.

---

## Ключевые возможности

- **HTTP‑API (FastAPI)**
  - `POST /transport/send` — приём полного сообщения и сегментация.
  - `POST /transport/transfer` — приём декодированного сегмента от канального уровня.
  - `POST /receive` — внутренний эндпоинт для собранного сообщения.
- **Интеграция с Kafka (aiokafka)**
  - Продюсер публикует каждый сегмент в топик `segmentation`.
  - Консьюмер читает сегменты, хранит их и инициирует сборку.
- **Единый конфиг `config.yaml`** — все параметры настраиваются без изменения кода.
- **Плагины хранилища** — по умолчанию in‑memory, легко заменить на Redis/PostgreSQL.
- **Docker‑first** — docker‑compose с Zookeeper и Kafka для локальной разработки.

---

## Структура проекта

```
app/
├── api/           # Роуты FastAPI и зависимости
├── config.py      # Загрузка YAML‑конфигурации (Pydantic v2)
├── kafka/         # Обёртки Kafka‑продюсера и консьюмера
├── models/        # Pydantic‑схемы запросов/ответов
├── repos/         # Репозитории (по умолчанию — in‑memory)
├── services/      # MessageService — бизнес‑логика
└── main.py        # Точка входа FastAPI
config.yaml        # Главный файл конфигурации
requirements.txt   # Python‑зависимости
Dockerfile         # Контейнер транспортного уровня
docker-compose.yml # Zookeeper, Kafka, транспортный уровень
```

---

## Быстрый запуск

```bash
# Клонирование репозитория
$ git clone https://github.com/<user>/transport-layer.git
$ cd transport-layer

# Виртуальное окружение
$ python -m venv venv
$ source venv/bin/activate   # Windows: venv\Scripts\activate
$ pip install -r requirements.txt

# Запуск стека Kafka
$ docker compose up -d   # Zookeeper + Kafka + транспортный уровень

# Локальный запуск без Docker
$ python -m app.main     # http://localhost:8090
```

Документация API доступна по адресу **http://localhost:8090/docs** (Swagger UI).

---

## Основные параметры `config.yaml`

| Раздел             | Ключ                | Назначение                                             |
| ------------------ | ------------------- | ------------------------------------------------------ |
| **http**           | `host`, `port`      | Интерфейс и порт FastAPI‑сервера                       |
| **http_client**    | `code_url`          | URL канального уровня для получения сегментов          |
|                    | `receive_url`       | URL прикладного уровня для готовых сообщений           |
| **kafka.producer** | `brokers`, `topic`  | Список брокеров и топик для публикации сегментов       |
| **kafka.consumer** | `brokers`, `topic`  | Список брокеров и топик для получения сегментов        |
|                    | `auto_offset_reset` | Политика смещения (`earliest` / `latest`)              |
| **segment**        | `max_size`          | Максимальный размер полезной нагрузки сегмента (байт)  |
|                    | `assembly_period`   | Период проверки готовности сообщения (например `"2s"`) |

После изменения конфигурации перезапустите сервис.

---

## Развёртывание через Docker Compose

```yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on: [zookeeper]
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
    ports:
      - "29092:29092" # Доступ с хоста

  transport_layer:
    build: .
    depends_on: [kafka]
    ports:
      - "8090:8090"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8090
```

Запуск:

```bash
$ docker compose up --build
```
