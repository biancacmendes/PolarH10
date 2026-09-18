"""
plot_individual.py

Funções para visualização individual dos dados de ECG e HRV.

Gráficos disponíveis:
    1. ECG bruto
    2. ECG bruto e filtrado
    3. ECG filtrado com picos R
    4. Intervalos RR e NN
    5. HR médio
    6. RMSSD
    7. SDNN
    8. MF
    9. HF

Condições experimentais:
    baseline
    stage_1: jogo fácil
    stage_8: jogo difícil
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# Funções auxiliares
# ============================================================

def salvar_figura(figura, nome, diretorio_saida=None):
    """
    Salva a figura em PNG e PDF.
    """

    if diretorio_saida is None:
        return

    diretorio = Path(diretorio_saida)
    diretorio.mkdir(parents=True, exist_ok=True)

    caminho = diretorio / nome

    figura.savefig(
        caminho.with_suffix(".png"),
        dpi=300,
        bbox_inches="tight",
    )

    figura.savefig(
        caminho.with_suffix(".pdf"),
        bbox_inches="tight",
    )


# ============================================================
# ECG bruto
# ============================================================

def plotar_ecg_bruto(
    experimento,
    diretorio_saida=None,
):
    """
    Plota todo o sinal bruto de ECG.
    """

    sinal = np.asarray(
        experimento.sinal
    ).squeeze()

    fs = experimento.taxa_amostragem

    tempo = np.arange(len(sinal)) / fs

    fig, ax = plt.subplots(
        figsize=(6.5, 4.2)
    )

    ax.plot(
        tempo,
        sinal,
        linewidth=1.0,
    )

    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel(
        f"ECG ({experimento.unidade})"
    )

    ax.grid(
        linestyle="--",
        alpha=0.5,
    )

    fig.tight_layout()

    salvar_figura(
        fig,
        f"{experimento.condicao}_ecg_bruto",
        diretorio_saida,
    )

    plt.show()


# ============================================================
# ECG bruto e filtrado
# ============================================================

def plotar_ecg_filtrado(
    experimento,
    resultado_ecg,
    inicio=0,
    duracao=10,
    diretorio_saida=None,
):
    """
    Compara o ECG bruto e filtrado.

    Por padrão, mostra uma janela de 10 segundos para
    facilitar a visualização da morfologia do ECG.
    """

    sinal_bruto = np.asarray(
        experimento.sinal
    ).squeeze()

    sinal_filtrado = np.asarray(
        resultado_ecg["sinal_filtrado"]
    )

    fs = experimento.taxa_amostragem

    amostra_inicio = int(inicio * fs)

    amostra_fim = int(
        (inicio + duracao) * fs
    )

    amostra_fim = min(
        amostra_fim,
        len(sinal_bruto),
    )

    tempo = (
        np.arange(
            amostra_inicio,
            amostra_fim,
        )
        / fs
    )

    fig, ax = plt.subplots(
        figsize=(6.5, 4.2)
    )

    ax.plot(
        tempo,
        sinal_bruto[
            amostra_inicio:amostra_fim
        ],
        linewidth=1.0,
        label="ECG bruto",
    )

    ax.plot(
        tempo,
        sinal_filtrado[
            amostra_inicio:amostra_fim
        ],
        linewidth=1.8,
        label="ECG filtrado",
    )

    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel(
        f"ECG ({experimento.unidade})"
    )

    ax.grid(
        linestyle="--",
        alpha=0.5,
    )

    ax.legend(
        frameon=True
    )

    fig.tight_layout()

    salvar_figura(
        fig,
        f"{experimento.condicao}_ecg_filtrado",
        diretorio_saida,
    )

    plt.show()


# ============================================================
# Picos R
# ============================================================

def plotar_picos_r(
    experimento,
    resultado_ecg,
    inicio=0,
    duracao=10,
    diretorio_saida=None,
):
    """
    Plota o ECG filtrado com os picos R detectados.

    Por padrão, mostra uma janela de 10 segundos.
    """

    sinal = np.asarray(
        resultado_ecg["sinal_filtrado"]
    )

    picos_r = np.asarray(
        resultado_ecg["picos_r"]
    )

    fs = experimento.taxa_amostragem

    amostra_inicio = int(inicio * fs)

    amostra_fim = int(
        (inicio + duracao) * fs
    )

    amostra_fim = min(
        amostra_fim,
        len(sinal),
    )

    picos_janela = picos_r[
        (picos_r >= amostra_inicio)
        & (picos_r < amostra_fim)
    ]

    tempo = (
        np.arange(
            amostra_inicio,
            amostra_fim,
        )
        / fs
    )

    fig, ax = plt.subplots(
        figsize=(6.5, 4.2)
    )

    ax.plot(
        tempo,
        sinal[
            amostra_inicio:amostra_fim
        ],
        linewidth=1.8,
        label="ECG filtrado",
    )

    ax.scatter(
        picos_janela / fs,
        sinal[picos_janela],
        s=30,
        label="Picos R",
        zorder=3,
    )

    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel(
        f"ECG ({experimento.unidade})"
    )

    ax.grid(
        linestyle="--",
        alpha=0.5,
    )

    ax.legend(
        frameon=True
    )

    fig.tight_layout()

    salvar_figura(
        fig,
        f"{experimento.condicao}_picos_r",
        diretorio_saida,
    )

    plt.show()


# ============================================================
# Intervalos RR e NN
# ============================================================

def plotar_intervalos_rr_nn(
    resultado_ecg,
    condicao,
    diretorio_saida=None,
):
    """
    Plota os intervalos RR originais e os intervalos NN
    após a remoção de artefatos.
    """

    rr = np.asarray(
        resultado_ecg["intervalos_rr"]
    )

    nn = np.asarray(
        resultado_ecg["intervalos_nn"]
    )

    batimentos_rr = np.arange(
        1,
        len(rr) + 1,
    )

    batimentos_nn = np.arange(
        1,
        len(nn) + 1,
    )

    fig, ax = plt.subplots(
        figsize=(6.5, 4.2)
    )

    ax.plot(
        batimentos_rr,
        rr,
        linewidth=1.0,
        label="RR",
    )

    ax.plot(
        batimentos_nn,
        nn,
        linewidth=1.8,
        label="NN",
    )

    ax.set_xlabel("Intervalo")
    ax.set_ylabel("Intervalo (ms)")

    ax.grid(
        linestyle="--",
        alpha=0.5,
    )

    ax.legend(
        frameon=True
    )

    fig.tight_layout()

    salvar_figura(
        fig,
        f"{condicao}_rr_nn",
        diretorio_saida,
    )

    plt.show()


# ============================================================
# Métricas de HRV
# ============================================================

def plotar_metrica_hrv(
    hrv_baseline,
    hrv_facil,
    hrv_dificil,
    metrica,
    ylabel,
    diretorio_saida=None,
):
    """
    Compara uma métrica de HRV entre baseline,
    Stage 1 e Stage 8.
    """

    condicoes = [
        "Baseline",
        "Stage 1\nFácil",
        "Stage 8\nDifícil",
    ]

    valores = [
        hrv_baseline[metrica],
        hrv_facil[metrica],
        hrv_dificil[metrica],
    ]

    fig, ax = plt.subplots(
        figsize=(6.5, 4.2)
    )

    barras = ax.bar(
        condicoes,
        valores,
    )

    ax.set_ylabel(ylabel)

    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.5,
    )

    # Valor numérico acima de cada barra
    for barra, valor in zip(
        barras,
        valores,
    ):
        ax.text(
            barra.get_x()
            + barra.get_width() / 2,
            barra.get_height(),
            f"{valor:.2f}",
            ha="center",
            va="bottom",
        )

    fig.tight_layout()

    salvar_figura(
        fig,
        metrica,
        diretorio_saida,
    )

    plt.show()


def plotar_hrv(
    hrv_baseline,
    hrv_facil,
    hrv_dificil,
    diretorio_saida=None,
):
    """
    Gera os gráficos individuais das métricas de HRV.
    """

    metricas = {
        "hr_bpm": "Frequência cardíaca (bpm)",
        "rmssd_ms": "RMSSD (ms)",
        "sdnn_ms": "SDNN (ms)",
        "mf_ms2": "MF (ms²)",
        "hf_ms2": "HF (ms²)",
    }

    for metrica, ylabel in metricas.items():

        plotar_metrica_hrv(
            hrv_baseline=hrv_baseline,
            hrv_facil=hrv_facil,
            hrv_dificil=hrv_dificil,
            metrica=metrica,
            ylabel=ylabel,
            diretorio_saida=diretorio_saida,
        )


# ============================================================
# Todos os plots do participante
# ============================================================

def plotar_participante(
    baseline,
    facil,
    dificil,
    resultado_baseline,
    resultado_facil,
    resultado_dificil,
    hrv_baseline,
    hrv_facil,
    hrv_dificil,
    diretorio_saida=None,
):
    """
    Gera todos os gráficos individuais do participante.
    """

    experimentos = [
        baseline,
        facil,
        dificil,
    ]

    resultados_ecg = [
        resultado_baseline,
        resultado_facil,
        resultado_dificil,
    ]

    # ECG
    for experimento, resultado in zip(
        experimentos,
        resultados_ecg,
    ):

        plotar_ecg_bruto(
            experimento,
            diretorio_saida,
        )

        plotar_ecg_filtrado(
            experimento,
            resultado,
            inicio=0,
            duracao=10,
            diretorio_saida=diretorio_saida,
        )

        plotar_picos_r(
            experimento,
            resultado,
            inicio=0,
            duracao=10,
            diretorio_saida=diretorio_saida,
        )

        plotar_intervalos_rr_nn(
            resultado,
            experimento.condicao,
            diretorio_saida,
        )

    # HRV
    plotar_hrv(
        hrv_baseline,
        hrv_facil,
        hrv_dificil,
        diretorio_saida,
    )