"""
processador_dataset.py

Execução do pipeline de processamento fisiológico para todos os
participantes do conjunto de dados.

Para cada participante são processadas três condições experimentais:

    - baseline
    - stage_1
    - stage_8

O processamento segue as etapas:

    Carregamento do ECG
        ↓
    Processamento do sinal
        ↓
    Obtenção dos intervalos NN
        ↓
    Cálculo das métricas de HRV
        ↓
    Consolidação dos resultados absolutos
        ↓
    Correção das métricas pelo baseline

Além das métricas de HRV, são preservados indicadores relacionados
à qualidade e ao processamento do ECG, como SNR, número de picos R
e quantidade de intervalos RR removidos.

A correção pelo baseline é realizada individualmente para cada
participante:

    ΔHRV = HRV(Stage) - HRV(Baseline)

São produzidos resultados para Stage 1 e Stage 8.
"""

from pathlib import Path

import pandas as pd

from src.carregador_dados import CarregadorDados
from src.processador_ecg import ProcessadorECG
from src.analisador_hrv import AnalisadorHRV


class ProcessadorDataset:
    """
    Executa o processamento de ECG e HRV para todo o dataset.

    Parameters
    ----------
    diretorio_dados : str ou pathlib.Path
        Diretório principal contendo as pastas dos participantes.
    """

    def __init__(self, diretorio_dados):
        """Inicializa o processador e o carregador dos dados."""

        self.diretorio_dados = Path(
            diretorio_dados
        )

        self.carregador = CarregadorDados(
            diretorio_dados
        )

    def processar_participante(
        self,
        participante,
    ):
        """
        Processa todas as condições experimentais de um participante.

        Para cada condição, o ECG é processado para obtenção dos
        intervalos NN. Em seguida, são calculadas as métricas de HRV.

        Também são armazenados indicadores do processamento do ECG
        para permitir a avaliação da qualidade dos registros.

        Parameters
        ----------
        participante : str
            Identificação do participante.

        Returns
        -------
        list of dict
            Resultados de baseline, Stage 1 e Stage 8 contendo
            métricas de HRV e indicadores do processamento do ECG.
        """

        experimentos = (
            self.carregador.carregar_participante(
                participante
            )
        )

        resultados = []

        for condicao, experimento in experimentos.items():

            processador_ecg = ProcessadorECG(
                experimento
            )

            resultado_ecg = (
                processador_ecg.processar()
            )

            analisador_hrv = AnalisadorHRV(
                resultado_ecg["intervalos_nn"]
            )

            resultado_hrv = (
                analisador_hrv.calcular_hrv()
            )

            resultado = {
                "participante": participante,
                "condicao": condicao,
                "duracao_s": experimento.duracao,
                "snr_db": resultado_ecg["snr_db"],
                "numero_picos_r": resultado_ecg[
                    "numero_picos_r"
                ],
                "numero_rr": resultado_ecg[
                    "numero_rr"
                ],
                "numero_rr_removidos": resultado_ecg[
                    "numero_rr_removidos"
                ],
                "percentual_rr_removidos": resultado_ecg[
                    "percentual_rr_removidos"
                ],
                **resultado_hrv,
            }

            resultados.append(
                resultado
            )

        return resultados

    def processar_todos(self):
        """
        Processa todos os participantes identificados por USAB-*.

        Apenas diretórios cujo nome inicia com "USAB-" são incluídos,
        evitando o processamento de outras pastas presentes no
        diretório principal.

        Returns
        -------
        pandas.DataFrame
            Tabela contendo os resultados absolutos de HRV e os
            indicadores de processamento para todos os participantes
            e condições experimentais.
        """

        resultados = []

        participantes = sorted(
            [
                pasta.name
                for pasta
                in self.diretorio_dados.iterdir()
                if pasta.is_dir()
                and pasta.name.startswith("USAB-")
            ]
        )

        for participante in participantes:

            print(
                f"Processando: {participante}"
            )

            resultado = (
                self.processar_participante(
                    participante
                )
            )

            resultados.extend(
                resultado
            )

        return pd.DataFrame(
            resultados
        )

    def calcular_variacao_baseline(
        self,
        resultados,
    ):
        """
        Calcula a alteração das métricas de HRV em relação ao baseline.

        A correção é realizada separadamente para cada participante
        e condição experimental:

            ΔHRV = HRV(Stage) - HRV(Baseline)

        São calculadas as alterações para Stage 1 e Stage 8.

        Parameters
        ----------
        resultados : pandas.DataFrame
            Resultados absolutos produzidos pelo processamento
            do dataset.

        Returns
        -------
        pandas.DataFrame
            Tabela contendo as métricas de HRV corrigidas pelo
            baseline para Stage 1 e Stage 8.
        """

        metricas = [
            "hr_bpm",
            "rmssd_ms",
            "sdnn_ms",
            "mf_ms2",
            "hf_ms2",
            "mf_medio_janelas_ms2",
            "mf_p95_ms2",
            "mfp95_mean",
        ]

        resultados_corrigidos = []

        for participante in resultados[
            "participante"
        ].unique():

            dados = resultados[
                resultados["participante"]
                == participante
            ]

            baseline = dados[
                dados["condicao"]
                == "baseline"
            ]

            if baseline.empty:

                print(
                    f"Baseline não encontrado: "
                    f"{participante}"
                )

                continue

            baseline = baseline.iloc[0]

            for condicao in [
                "stage_1",
                "stage_8",
            ]:

                dados_condicao = dados[
                    dados["condicao"]
                    == condicao
                ]

                if dados_condicao.empty:
                    continue

                dados_condicao = (
                    dados_condicao.iloc[0]
                )

                resultado = {
                    "participante": participante,
                    "condicao": condicao,
                }

                for metrica in metricas:

                    valor_baseline = baseline[
                        metrica
                    ]

                    valor_condicao = (
                        dados_condicao[
                            metrica
                        ]
                    )

                    variacao = (
                        valor_condicao
                        - valor_baseline
                    )

                    resultado[
                        f"{metrica}_corrigida"
                    ] = variacao

                resultados_corrigidos.append(
                    resultado
                )

        return pd.DataFrame(
            resultados_corrigidos
        )

    def salvar_resultados(
        self,
        resultados_absolutos,
        resultados_corrigidos,
        diretorio_resultados="./resultados",
    ):
        """
        Salva os resultados do processamento em arquivos CSV.

        São gerados dois arquivos:

            hrv_absoluta.csv
                Métricas de HRV obtidas diretamente em cada condição.

            hrv_corrigida_baseline.csv
                Alterações de HRV em relação ao baseline.

        Parameters
        ----------
        resultados_absolutos : pandas.DataFrame
            Resultados absolutos de HRV.

        resultados_corrigidos : pandas.DataFrame
            Resultados de HRV após subtração do baseline.

        diretorio_resultados : str ou pathlib.Path, optional
            Diretório utilizado para salvar os arquivos.
        """

        diretorio = Path(
            diretorio_resultados
        )

        diretorio.mkdir(
            parents=True,
            exist_ok=True,
        )

        resultados_absolutos.to_csv(
            diretorio / "hrv_absoluta.csv",
            index=False,
        )

        resultados_corrigidos.to_csv(
            diretorio / "hrv_corrigida_baseline.csv",
            index=False,
        )

        print(
            f"Resultados salvos em: "
            f"{diretorio}"
        )