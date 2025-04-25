#!/usr/bin/env python3
import os
from datetime import datetime
import subprocess

log_path = os.path.join(os.path.dirname(__file__), "inicializar.log")

def log_message(message: str) -> None:
    """Registra uma mensagem no arquivo de log."""
    with open(log_path, "a") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} – {message}\n")

def run(cmd: list[str]) -> None:
    """Executa o comando e registra erros no log se falhar."""
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        log_message(f"Comando executado com sucesso: {' '.join(cmd)}")
    except subprocess.CalledProcessError as e:
        log_message(f"Erro ao executar o comando: {' '.join(cmd)}")
        log_message(f"Saída de erro: {e.stderr.decode().strip()}")
        raise

log_message("Script inicializar.py executado.")

limita_velocidade = [
    "tc", "qdisc", "add", "dev", "eth0", "root", "tbf",
    "rate", "110mbit", "burst", "1mb", "latency", "1000ms"
]
run(limita_velocidade)

log_message("Script inicializar.py terminado.")