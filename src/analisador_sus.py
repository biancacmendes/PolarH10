"""
analisador_sus.py

Carregamento, validação e cálculo do System Usability Scale (SUS).

Cada participante possui uma avaliação de usabilidade para cada
condição experimental:

    - Stage 1
    - Stage 8

O questionário SUS contém 10 questões respondidas em uma escala
Likert de 1 a 5.

O escore é calculado utilizando o procedimento padrão:

    Questões ímpares (1, 3, 5, 7 e 9):
        contribuição = resposta - 1

    Questões pares (2, 4, 6, 8 e 10):
        contribuição = 5 - resposta

A soma das contribuições é multiplicada por 2,5, produzindo um
escore final entre 0 e 100.

O escore SUS representa uma medida global de usabilidade percebida.
Valores maiores correspondem a avaliações mais favoráveis de
usabilidade.
"""

from pathlib import Path

import numpy as np
import pandas as pd


class AnalisadorSUS:
    """
    Carrega as respostas e calcula os escores SUS de um participante.

    Parameters
    ----------
    diretorio_dados : str ou pathlib.Path
        Diretório principal contendo as pastas dos participantes.
    """

    def __init__(self, diretorio_dados):
        """Define o diretório principal dos dados experimentais."""

        self.diretorio_dados = Path(
            diretorio_dados
        )

    def localizar_questionario(
        self,
        participante,
    ):
        """
        Localiza o arquivo XLSX contendo o questionário SUS.

        A busca é realizada na pasta do participante. São considerados
        arquivos XLSX que contenham "SUS" no nome. Arquivos temporários
        do Excel, iniciados por "~$", são ignorados.

        Parameters
        ----------
        participante : str
            Identificação do participante.

        Returns
        -------
        pathlib.Path
            Caminho do arquivo XLSX encontrado.

        Raises
        ------
        FileNotFoundError
            Se nenhum questionário SUS for encontrado.
        """

        diretorio = (
            self.diretorio_dados
            / participante
        )

        arquivos = [
            arquivo
            for arquivo in diretorio.glob("*.xlsx")
            if "SUS" in arquivo.name.upper()
            and not arquivo.name.startswith("~$")
        ]

        if not arquivos:
            raise FileNotFoundError(
                f"Questionário SUS não encontrado: "
                f"{participante}"
            )

        return arquivos[0]

    def carregar_respostas(
        self,
        participante,
    ):
        """
        Carrega e organiza as respostas SUS do participante.

        A planilha utilizada possui:

            coluna 0: timestamp
            coluna 1: Stage
            coluna 2: identificação do participante
            colunas 3 a 12: respostas das 10 questões SUS

        A identificação da condição experimental é normalizada para
        permitir tanto valores numéricos (1 e 8) quanto representações
        textuais ("Stage 1" e "Stage 8").

        As respostas das questões SUS são convertidas para valores
        numéricos antes do cálculo do escore.

        Parameters
        ----------
        participante : str
            Identificação do participante.

        Returns
        -------
        pandas.DataFrame
            Tabela contendo Stage, identificação do participante e
            respostas das 10 questões SUS.
        """

        arquivo = self.localizar_questionario(
            participante
        )

        dados = pd.read_excel(
            arquivo,
            sheet_name=0,
            header=None,
        )

        # Remove as duas primeiras linhas da planilha:
        # nome da tabela e cabeçalho original.
        dados = dados.iloc[2:].copy()

        # Mantém apenas as colunas utilizadas na análise.
        dados = dados.iloc[:, :13]

        dados.columns = (
            [
                "timestamp",
                "stage",
                "participante",
            ]
            + [
                f"sus_{i}"
                for i in range(1, 11)
            ]
        )

        # Normaliza a identificação das condições:
        #
        # 1       -> 1
        # 8       -> 8
        # Stage 1 -> 1
        # Stage 8 -> 8

        dados["stage"] = (
            dados["stage"]
            .astype(str)
            .str.strip()
            .str.replace(
                "Stage",
                "",
                case=False,
                regex=False,
            )
        )

        dados["stage"] = pd.to_numeric(
            dados["stage"],
            errors="coerce",
        )

        colunas_sus = [
            f"sus_{i}"
            for i in range(1, 11)
        ]

        dados[colunas_sus] = (
            dados[colunas_sus]
            .apply(
                pd.to_numeric,
                errors="coerce",
            )
        )

        return dados

    def calcular_score(
        self,
        respostas,
    ):
        """
        Calcula o escore do System Usability Scale.

        Para as questões ímpares:

            contribuição = resposta - 1

        Para as questões pares:

            contribuição = 5 - resposta

        O escore final é:

            SUS = 2,5 × soma das contribuições

        Parameters
        ----------
        respostas : array-like
            Respostas das 10 questões SUS, com valores entre 1 e 5.

        Returns
        -------
        float
            Escore SUS entre 0 e 100.

        Raises
        ------
        ValueError
            Se não houver exatamente 10 respostas, se existirem
            valores ausentes ou se alguma resposta estiver fora
            do intervalo de 1 a 5.
        """

        respostas = np.asarray(
            respostas,
            dtype=float,
        )

        if len(respostas) != 10:
            raise ValueError(
                "O SUS deve possuir exatamente "
                "10 respostas."
            )

        if np.isnan(respostas).any():
            raise ValueError(
                "Existem respostas SUS ausentes."
            )

        if np.any(
            (respostas < 1)
            | (respostas > 5)
        ):
            raise ValueError(
                "As respostas SUS devem estar "
                "entre 1 e 5."
            )

        contribuicoes = np.zeros(10)

        # Questões ímpares: 1, 3, 5, 7 e 9.
        contribuicoes[0::2] = (
            respostas[0::2] - 1
        )

        # Questões pares: 2, 4, 6, 8 e 10.
        contribuicoes[1::2] = (
            5 - respostas[1::2]
        )

        score = (
            np.sum(contribuicoes)
            * 2.5
        )

        return float(score)

    def analisar_participante(
        self,
        participante,
    ):
        """
        Calcula os escores SUS de Stage 1 e Stage 8.

        As condições são selecionadas explicitamente pela coluna
        "stage", independentemente da ordem das linhas na planilha.

        Parameters
        ----------
        participante : str
            Identificação do participante.

        Returns
        -------
        list of dict
            Resultados contendo:

            - participante
            - condicao
            - sus_score

            São produzidos dois registros por participante:
            um para Stage 1 e outro para Stage 8.

        Raises
        ------
        ValueError
            Se Stage 1 ou Stage 8 não estiver presente nos dados.
        """

        dados = self.carregar_respostas(
            participante
        )

        resultados = []

        mapa_condicoes = {
            1: "stage_1",
            8: "stage_8",
        }

        colunas_sus = [
            f"sus_{i}"
            for i in range(1, 11)
        ]

        for stage, condicao in mapa_condicoes.items():

            dados_stage = dados[
                dados["stage"] == stage
            ]

            if dados_stage.empty:
                raise ValueError(
                    f"Stage {stage} não encontrado "
                    f"para {participante}."
                )

            respostas = (
                dados_stage.iloc[0][
                    colunas_sus
                ].values
            )

            score = self.calcular_score(
                respostas
            )

            resultados.append(
                {
                    "participante": participante,
                    "condicao": condicao,
                    "sus_score": score,
                }
            )

        return resultados