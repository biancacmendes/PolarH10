"""
analisador_correlacao.py

Responsável pela análise da associação entre as métricas de HRV
e os escores de usabilidade (SUS).

São realizadas duas análises:

1. Valores absolutos de HRV:
   HRV(Stage) ↔ SUS(Stage)

2. HRV corrigida pelo baseline:
   [HRV(Stage) - HRV(Baseline)] ↔ SUS(Stage)

A associação é avaliada pelo coeficiente de correlação de Spearman.
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


class AnalisadorCorrelacao:
    """Calcula as correlações de Spearman entre HRV e SUS."""

    METRICAS_HRV = [
        "hr_bpm",
        "rmssd_ms",
        "sdnn_ms",
        "mf_ms2",
        "hf_ms2",
        "mf_medio_janelas_ms2",
        "mf_p95_ms2",
        "mfp95_mean",
    ]

    def calcular_correlacao(
        self,
        dados,
        coluna_hrv,
    ):
        """
        Calcula a correlação de Spearman entre uma métrica
        de HRV e o escore SUS.

        Valores ausentes ou infinitos são removidos antes
        do cálculo.

        Parameters
        ----------
        dados : pandas.DataFrame
            Dados contendo HRV e SUS.

        coluna_hrv : str
            Nome da coluna contendo a métrica de HRV.

        Returns
        -------
        tuple
            Coeficiente de Spearman, valor-p e número de
            observações válidas.
        """

        dados_validos = dados[
            [coluna_hrv, "sus_score"]
        ].replace(
            [np.inf, -np.inf],
            np.nan,
        ).dropna()

        if len(dados_validos) < 3:
            return np.nan, np.nan, len(dados_validos)

        rho, p_valor = spearmanr(
            dados_validos[coluna_hrv],
            dados_validos["sus_score"],
        )

        return rho, p_valor, len(dados_validos)

    def calcular_correlacoes(
        self,
        dados_absolutos,
        dados_corrigidos,
        nomes_metricas,
    ):
        """
        Calcula as correlações entre HRV e SUS para os valores
        absolutos e para os valores corrigidos pelo baseline.

        Para cada métrica são calculadas:

        - correlação entre HRV absoluta e SUS;
        - correlação entre HRV corrigida pelo baseline e SUS.

        Returns
        -------
        pandas.DataFrame
            Tabela contendo a métrica, tipo de análise,
            coeficiente de Spearman, valor-p e número de
            observações válidas.
        """

        correlacoes = []

        for metrica in self.METRICAS_HRV:

            # Valores absolutos

            rho, p_valor, n = self.calcular_correlacao(
                dados_absolutos,
                metrica,
            )

            correlacoes.append({
                "metrica": nomes_metricas[metrica],
                "analise": "Absoluta",
                "rho": rho,
                "p_valor": p_valor,
                "n_observacoes": n,
            })

            # Valores corrigidos pelo baseline

            coluna_corrigida = f"{metrica}_corrigida"

            rho, p_valor, n = self.calcular_correlacao(
                dados_corrigidos,
                coluna_corrigida,
            )

            correlacoes.append({
                "metrica": nomes_metricas[metrica],
                "analise": "Corrigida pelo baseline",
                "rho": rho,
                "p_valor": p_valor,
                "n_observacoes": n,
            })

        return pd.DataFrame(correlacoes)