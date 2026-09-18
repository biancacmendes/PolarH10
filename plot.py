#!/usr/bin/env python3
"""
Plota o sinal de ECG salvo pelo main.py no formato binário (.npy + .json).

Requisitos:
    pip install numpy matplotlib

Uso:
    python3 plot_ecg.py dataset/bianca/experimento_20260818_143000.npy
"""

import sys
import json
import numpy as np
import matplotlib.pyplot as plt

if len(sys.argv) != 2:
    print("Uso: python3 plot_ecg.py caminho/para/experimento.npy")
    sys.exit(1)

npy_path = sys.argv[1]
json_path = npy_path.replace(".npy", ".json")

valores = np.load(npy_path)

try:
    with open(json_path) as f:
        meta = json.load(f)
    taxa_hz = meta.get("taxa_hz", 130)
    titulo = f"ECG - {meta.get('pessoa', '?')} ({meta.get('duracao_s', 0):.1f}s)"
except FileNotFoundError:
    print(f"Aviso: {json_path} não encontrado, assumindo 130Hz.")
    taxa_hz = 130
    titulo = f"ECG - {npy_path}"

tempo_s = np.arange(len(valores)) / taxa_hz

plt.figure(figsize=(12, 4))
plt.plot(tempo_s, valores, linewidth=0.8)
plt.xlabel("Tempo (s)")
plt.ylabel("ECG (µV)")
plt.title(titulo)
plt.tight_layout()
plt.show()
