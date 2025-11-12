#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
from dotenv import load_dotenv
from mistralai import Mistral
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from collections import deque

console = Console()

# === Configuração de endpoints ===
ENDPOINTS = {
    "saldo": {"url": "http://127.0.0.1:8000/funcoes/saldo", "method": "GET"},
    "extrato": {"url": "http://127.0.0.1:8000/funcoes/extrato", "method": "GET"},
    "adicionar_conta": {"url": "http://127.0.0.1:8000/funcoes/adicionar_conta", "method": "POST"},
}

# === Carrega variáveis de ambiente ===
load_dotenv("/home/vitorgabrieldev/.config/ia/.env")
API_KEY = os.getenv("MISTRAL_API_KEY")

if not API_KEY:
    console.print("[bold red]❌ Error:[/bold red] Missing MISTRAL_API_KEY in environment.")
    sys.exit(1)

client = Mistral(api_key=API_KEY)

# === Histórico de conversa (deque para limitar tamanho) ===
conversation_history = deque(maxlen=6)  # Armazena últimas 6 mensagens (user + assistant)

# === Funções utilitárias ===
def print_panel(title: str, content: str, border_color: str = "blue", subtitle: str = ""):
    markdown = Markdown(content)
    box = Panel(
        markdown,
        border_style=border_color,
        padding=(1, 4),
        expand=False,
        title=title,
        subtitle=subtitle
    )
    console.print(box)

def execute_endpoint(func_name: str, args: str):
    endpoint_info = ENDPOINTS.get(func_name)
    if not endpoint_info:
        return "Endpoint não definido"

    url = endpoint_info["url"]
    method = endpoint_info.get("method", "GET").upper()

    try:
        payload = json.loads(args) if args else {}
    except Exception:
        payload = {}

    try:
        if method == "GET":
            resp = requests.get(url, params=payload)
        elif method == "POST":
            resp = requests.post(url, json=payload)
        else:
            return "Método HTTP não suportado"
        return resp.text
    except Exception as e:
        return f"Erro ao chamar endpoint: {str(e)}"

def handle_output(out):
    if hasattr(out, "content") and out.content:
        print_panel(
            title="[bold cyan]🧠 Resposta[/bold cyan]",
            content=out.content,
            border_color="bright_blue",
            subtitle="[dim]Agente Técnico[/dim]"
        )
        conversation_history.append({"role": "assistant", "content": out.content})

    elif hasattr(out, "name") and hasattr(out, "arguments"):
        func_name = out.name
        args = out.arguments
        resp_text = execute_endpoint(func_name, args)
        box_content = (
            f"🛠️ Função chamada: [bold]{func_name}[/bold]\n"
            f"Argumentos: {args}\n"
            f"Endpoint: [green]{ENDPOINTS.get(func_name, {}).get('url', 'N/A')}[/green]\n"
            f"Resposta: [yellow]{resp_text}[/yellow]"
        )
        console.print(Panel.fit(box_content, border_style="magenta", title="[bold magenta]Function Call[/bold magenta]"))
        conversation_history.append({"role": "assistant", "content": box_content})

# === Entrada do usuário ===
if len(sys.argv) < 2:
    console.print("[yellow]⚠️ Use:[/yellow] ia-agente \"sua mensagem aqui\"")
    sys.exit(1)

user_input = " ".join(sys.argv[1:])
conversation_history.append({"role": "user", "content": user_input})
AGENT_ID = "ag_019a7879574071dab4e683d9560a681f"

# === Executa a conversa com histórico limitado ===
try:
    response = client.beta.conversations.start(
        agent_id=AGENT_ID,
        inputs=list(conversation_history)
    )

    if not hasattr(response, "outputs") or not response.outputs:
        console.print("[red]⚠️ Nenhum output retornado.[/red]")
        sys.exit(0)

    console.print(Panel.fit("💬 [bold cyan]Agent Response[/bold cyan]", border_style="cyan", padding=(0, 2)))
    console.print()

    for out in response.outputs:
        handle_output(out)

except Exception as e:
    console.print(f"[bold red]❌ Error:[/bold red] {str(e)}")

console.print()
console.print("[bold green]✅ Done.[/bold green]")
