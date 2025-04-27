from pydantic import BaseModel


class SendRequest(BaseModel):
    time: int
    sender: str
    payload: str


class TransferRequest(BaseModel):
    id: str
    payload: str
    total: int
    number: int


class SendResponse(BaseModel):
    status: str = "ok"
