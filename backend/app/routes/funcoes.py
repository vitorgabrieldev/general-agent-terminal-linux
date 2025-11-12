from fastapi import APIRouter, Query
from app.services import funcoes_service
from pydantic import BaseModel
from typing import Optional
from datetime import date
import json
import os

router = APIRouter()

class NovaConta(BaseModel):
    produto: str
    valor_total: float
    parcelas: Optional[int] = 1
    valor_parcela: Optional[float] = None
    data_primeira_parcela: Optional[str] = None
    tipo_pagamento: str
    cartao: Optional[str] = None
    banco: Optional[str] = None
    data: str
    local: Optional[str] = None
    observacoes: Optional[str] = None

JSON_PATH = os.path.join("app", "services", "contas.json")

@router.post("/adicionar_conta")
def adicionar_conta(conta: NovaConta):
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            contas = json.load(f)
    else:
        contas = []

    contas.append(conta.dict())

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(contas, f, ensure_ascii=False, indent=2)

    return {
        "status": "sucesso",
        "mensagem": f"Conta do produto {conta.produto} adicionada.",
        "dados_recebidos": conta.dict()
    }

@router.get("/saldo")
def route_sobre_mim():
    return {funcoes_service.saldo()}