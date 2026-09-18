#!/usr/bin/env python3
"""
Conecta no Polar H10 via Bluetooth LE, grava o ECG bruto em formato binário
(.npy + .json de metadados) e mostra um gráfico em tempo real do sinal,
com o tempo decorrido no formato MM:SS.

Requisitos:
    pip install bleak bleakheart matplotlib numpy

Uso:
    python3 main.py

O programa pede o nome da pessoa no início e cria:
    dataset/<nome>/experimento_<timestamp>.npy   -- valores brutos do ECG (int16)
    dataset/<nome>/experimento_<timestamp>.json  -- metadados (taxa, início, etc)

Feche a janela do gráfico para encerrar a gravação -- os dados coletados
até esse momento ficam salvos normalmente (há também um salvamento
periódico de segurança durante a gravação).
"""

import asyncio
import json
import os
import threading
import time
from collections import deque
from datetime import datetime, timezone

import numpy as np
from bleak import BleakScanner, BleakClient
from bleakheart import PolarMeasurementData
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ---------------------------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------------------------

# Endereço do dispositivo (no macOS é um UUID, não um MAC address de verdade;
# pode mudar entre sessões -- se parar de conectar, rode de novo o scan por
# nome para pegar o endereço atual)
DEVICE_ADDRESS = "E6332DC0-A58F-1207-977B-4036C5414AC5"

ECG_SAMPLE_RATE_HZ = 130      # taxa de amostragem fixa do H10
PLOT_WINDOW_SECONDS = 8       # quantos segundos de sinal ficam visíveis no gráfico

# Pasta raiz onde ficam os dados de todas as pessoas/experimentos
DATASET_DIR = "dataset"

# ---------------------------------------------------------------------------
# ESTADO COMPARTILHADO entre a thread do Bluetooth e a thread do gráfico
# ---------------------------------------------------------------------------

plot_buffer = deque(maxlen=ECG_SAMPLE_RATE_HZ * PLOT_WINDOW_SECONDS)
all_samples = []         # buffer com TODAS as amostras da sessão (int16)
start_time_wall = None   # timestamp (time.time()) de quando o streaming começou
stop_flag = threading.Event()


def format_mmss(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def salvar_dados(npy_path, json_path, nome, device_name, device_address,
                  inicio_iso, finalizado):
    """Salva o array de amostras em .npy e os metadados em .json.
    Pode ser chamada tanto periodicamente (salvamento de segurança)
    quanto ao final da gravação."""
    arr = np.array(all_samples, dtype=np.int16)
    np.save(npy_path, arr)

    meta = {
        "pessoa": nome,
        "dispositivo": device_name,
        "device_address": device_address,
        "taxa_hz": ECG_SAMPLE_RATE_HZ,
        "unidade": "uV",
        "inicio_iso": inicio_iso,
        "amostras": len(all_samples),
        "duracao_s": len(all_samples) / ECG_SAMPLE_RATE_HZ,
        "gravacao_completa": finalizado,
    }
    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# COLETA DE DADOS (roda em thread separada, com seu próprio loop asyncio)
# ---------------------------------------------------------------------------

async def ble_main(npy_path, json_path, nome):
    global start_time_wall

    print(f"Procurando dispositivo {DEVICE_ADDRESS} ...")
    device = await BleakScanner.find_device_by_address(DEVICE_ADDRESS, timeout=15)
    if device is None:
        print("Dispositivo não encontrado. Verifique se o sensor está "
              "ligado (contato com a pele/umidade nos eletrodos) e "
              "dentro de alcance.")
        stop_flag.set()
        return

    print(f"Encontrado: {device.name} ({device.address})")

    ecg_queue = asyncio.Queue()

    async with BleakClient(device) as client:
        print("Conectado:", client.is_connected)

        pmd = PolarMeasurementData(client, ecg_queue=ecg_queue)

        err_code, err_msg, _ = await pmd.start_streaming("ECG")
        if err_code != 0:
            print(f"Erro ao iniciar streaming de ECG: {err_msg}")
            stop_flag.set()
            return

        start_time_wall = time.time()
        inicio_iso = datetime.now(timezone.utc).isoformat()
        print(f"Streaming iniciado. Gravando em: {npy_path}")
        print("Feche a janela do gráfico para parar.\n")

        try:
            while not stop_flag.is_set():
                try:
                    frame = await asyncio.wait_for(ecg_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                _, _tstamp_ns, samples = frame  # ('ECG', tstamp, [s1, s2, ...])
                all_samples.extend(samples)
                plot_buffer.extend(samples)

                # salvamento periódico de segurança (a cada ~5s de dados)
                if len(all_samples) % (ECG_SAMPLE_RATE_HZ * 5) < len(samples):
                    salvar_dados(npy_path, json_path, nome, device.name,
                                 device.address, inicio_iso, finalizado=False)
                    print(f"{len(all_samples)} amostras gravadas...")
        finally:
            err_code, err_msg = await pmd.stop_streaming("ECG")
            salvar_dados(npy_path, json_path, nome, device.name,
                         device.address, inicio_iso, finalizado=True)
            print(f"\nStreaming parado ({err_msg}). "
                  f"Total de amostras gravadas: {len(all_samples)}")


def run_ble_thread(npy_path, json_path, nome):
    asyncio.run(ble_main(npy_path, json_path, nome))


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL: pede o nome, inicia a coleta e mostra o gráfico
# ---------------------------------------------------------------------------

def main():
    nome = input("Digite o nome da pessoa: ").strip() or "sem_nome"
    nome_pasta = "_".join(nome.lower().split())

    # dataset/<nome>/ -- cada experimento vira um par .npy + .json nessa pasta
    pasta_pessoa = os.path.join(DATASET_DIR, nome_pasta)
    os.makedirs(pasta_pessoa, exist_ok=True)

    timestamp_experimento = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_path = os.path.join(pasta_pessoa, f"experimento_{timestamp_experimento}")
    npy_path = base_path + ".npy"
    json_path = base_path + ".json"

    ble_thread = threading.Thread(
        target=run_ble_thread, args=(npy_path, json_path, nome), daemon=True
    )
    ble_thread.start()

    # espera a conexão ser estabelecida (ou falhar) antes de abrir o gráfico
    while start_time_wall is None and not stop_flag.is_set():
        time.sleep(0.1)

    if stop_flag.is_set():
        print("Não foi possível iniciar a gravação.")
        return

    fig, ax = plt.subplots(figsize=(12, 5))
    line, = ax.plot([], [], linewidth=0.8)
    ax.set_xlabel("Amostras (janela recente)")
    ax.set_ylabel("ECG (µV)")
    title = ax.set_title(f"ECG - {nome} - 00:00")

    def update(_frame):
        data = list(plot_buffer)
        line.set_data(range(len(data)), data)
        if data:
            ax.set_xlim(0, len(data))
            margem = (max(data) - min(data)) * 0.1 or 10
            ax.set_ylim(min(data) - margem, max(data) + margem)

        elapsed = time.time() - start_time_wall
        title.set_text(f"ECG - {nome} - {format_mmss(elapsed)}")
        return line, title

    ani = animation.FuncAnimation(fig, update, interval=100, blit=False)

    plt.tight_layout()
    plt.show()  # bloqueia até a janela do gráfico ser fechada

    print("\nJanela fechada, encerrando gravação...")
    stop_flag.set()
    ble_thread.join(timeout=5)
    print(f"Arquivos salvos: {npy_path} / {json_path}")


if __name__ == "__main__":
    main()
