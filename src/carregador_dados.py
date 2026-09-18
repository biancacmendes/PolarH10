"""
carregador_dados.py

Carregamento e organização dos registros de ECG utilizados no
processamento fisiológico.

Cada participante possui três condições experimentais:

    - baseline
    - stage_1
    - stage_8

Para cada condição são utilizados dois arquivos:

    experimento_<condicao>.npy
        Sinal de ECG adquirido durante o experimento.

    experimento_<condicao>.json
        Metadados associados à aquisição, incluindo frequência de
        amostragem, unidade, dispositivo, instante inicial, duração
        e número de amostras.

O carregamento não realiza filtragem ou transformação do sinal.
O ECG e seus metadados são apenas organizados em objetos
ExperimentoECG para utilização nas etapas posteriores do pipeline.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class ExperimentoECG:
    """
    Representa uma aquisição de ECG em uma condição experimental.

    Attributes
    ----------
    participante : str
        Identificação anonimizada do participante.

    condicao : str
        Condição experimental correspondente ao registro:
        baseline, stage_1 ou stage_8.

    sinal : numpy.ndarray
        Sinal de ECG carregado do arquivo NPY.

    taxa_amostragem : float
        Frequência de amostragem do ECG em Hz.

    unidade : str
        Unidade utilizada para representar a amplitude do ECG.

    dispositivo : str
        Dispositivo utilizado na aquisição.

    inicio : str
        Instante inicial da aquisição registrado nos metadados.

    duracao : float
        Duração total do registro em segundos.

    numero_amostras : int
        Número de amostras registradas.
    """

    participante: str
    condicao: str

    sinal: np.ndarray
    taxa_amostragem: float
    unidade: str

    dispositivo: str
    inicio: str
    duracao: float
    numero_amostras: int


class CarregadorDados:
    """
    Carrega os registros de ECG e seus metadados.

    Parameters
    ----------
    diretorio_dados : str ou pathlib.Path
        Diretório principal contendo uma pasta para cada participante.

    Notes
    -----
    Para cada participante são esperados registros correspondentes
    ao baseline, Stage 1 e Stage 8.
    """

    ARQUIVOS = {
        "baseline": "experimento_baseline",
        "stage_1": "experimento_stage1",
        "stage_8": "experimento_stage8",
    }

    def __init__(self, diretorio_dados):
        """Define o diretório principal do conjunto de dados."""

        self.diretorio_dados = Path(
            diretorio_dados
        )

    def carregar_experimento(
        self,
        participante,
        condicao,
    ):
        """
        Carrega o ECG e os metadados de uma condição experimental.

        O sinal é obtido do arquivo NPY, enquanto as informações
        da aquisição são obtidas do arquivo JSON correspondente.

        Parameters
        ----------
        participante : str
            Identificação do participante.

        condicao : str
            Condição a ser carregada: baseline, stage_1 ou stage_8.

        Returns
        -------
        ExperimentoECG
            Objeto contendo o sinal de ECG e os respectivos metadados.

        Raises
        ------
        FileNotFoundError
            Se o arquivo JSON ou NPY correspondente não for encontrado.
        """

        diretorio = (
            self.diretorio_dados
            / participante
        )

        nome_arquivo = self.ARQUIVOS[
            condicao
        ]

        caminho_json = (
            diretorio
            / f"{nome_arquivo}.json"
        )

        caminho_npy = (
            diretorio
            / f"{nome_arquivo}.npy"
        )

        if not caminho_json.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: "
                f"{caminho_json}"
            )

        if not caminho_npy.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: "
                f"{caminho_npy}"
            )

        with open(
            caminho_json,
            "r",
            encoding="utf-8",
        ) as arquivo:
            metadados = json.load(
                arquivo
            )

        sinal = np.load(
            caminho_npy
        )

        return ExperimentoECG(
            participante=participante,
            condicao=condicao,
            sinal=sinal,
            taxa_amostragem=metadados[
                "taxa_hz"
            ],
            unidade=metadados[
                "unidade"
            ],
            dispositivo=metadados[
                "dispositivo"
            ],
            inicio=metadados[
                "inicio_iso"
            ],
            duracao=metadados[
                "duracao_s"
            ],
            numero_amostras=metadados[
                "amostras"
            ],
        )

    def carregar_participante(
        self,
        participante,
    ):
        """
        Carrega todas as condições experimentais de um participante.

        São carregados:

            - baseline
            - Stage 1
            - Stage 8

        Parameters
        ----------
        participante : str
            Identificação do participante.

        Returns
        -------
        dict
            Dicionário no qual cada condição experimental está
            associada ao respectivo objeto ExperimentoECG.
        """

        experimentos = {}

        for condicao in self.ARQUIVOS:

            experimentos[condicao] = (
                self.carregar_experimento(
                    participante,
                    condicao,
                )
            )

        return experimentos