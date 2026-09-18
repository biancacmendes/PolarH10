"""
analisador_hrv.py

Cálculo das métricas de variabilidade da frequência cardíaca (HRV)
a partir dos intervalos NN.

O módulo recebe uma sequência de intervalos NN, expressos em
milissegundos, previamente obtidos pelo processamento do ECG.

São calculadas métricas nos domínios do tempo e da frequência,
além da métrica MF P95/Mean baseada na distribuição temporal da
potência da banda MF.

Métricas calculadas
-------------------
Domínio do tempo:
    - HR médio (bpm)
    - RMSSD (ms)
    - SDNN (ms)

Domínio da frequência:
    - MF: potência entre 0,07 e 0,15 Hz (ms²)
    - HF: potência entre 0,15 e 0,40 Hz (ms²)

Análise temporal da potência MF:
    - MF médio das janelas (ms²)
    - MF P95 (ms²)
    - MF P95/Mean (adimensional)

Para a análise espectral, os intervalos NN são interpolados por
spline cúbica e reamostrados uniformemente a 4 Hz. A densidade
espectral de potência é estimada pelo método de Welch.

Para MF P95/Mean, a série interpolada é analisada em janelas de
60 segundos, deslocadas a cada 10 segundos.
"""

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import welch


class AnalisadorHRV:
    """
    Calcula métricas de HRV a partir dos intervalos NN.

    Parameters
    ----------
    intervalos_nn : array-like
        Sequência de intervalos NN expressos em milissegundos.
    """

    def __init__(self, intervalos_nn):
        """Armazena os intervalos NN utilizados na análise."""

        self.nn = np.asarray(
            intervalos_nn,
            dtype=float,
        )

    def calcular_hr_medio(self):
        """
        Calcula a frequência cardíaca média.

        A frequência cardíaca é obtida a partir do intervalo
        NN médio:

            HR = 60000 / NN_médio

        Returns
        -------
        float
            Frequência cardíaca média em batimentos por minuto (bpm).
        """

        rr_medio = np.mean(self.nn)

        hr_medio = 60000.0 / rr_medio

        return float(hr_medio)

    def calcular_metricas_tempo(self):
        """
        Calcula RMSSD e SDNN.

        RMSSD representa a raiz quadrada da média dos quadrados
        das diferenças entre intervalos NN sucessivos.

        SDNN corresponde ao desvio-padrão amostral dos intervalos NN.

        Returns
        -------
        dict
            rmssd_ms : float
                RMSSD em milissegundos.

            sdnn_ms : float
                SDNN em milissegundos.
        """

        diferencas_nn = np.diff(self.nn)

        rmssd = np.sqrt(
            np.mean(diferencas_nn ** 2)
        )

        sdnn = np.std(
            self.nn,
            ddof=1,
        )

        return {
            "rmssd_ms": float(rmssd),
            "sdnn_ms": float(sdnn),
        }

    def interpolar_nn(
        self,
        frequencia_amostragem=4.0,
    ):
        """
        Converte os intervalos NN em uma série uniformemente amostrada.

        Os intervalos NN originalmente ocorrem em instantes não
        uniformemente espaçados. Para permitir a análise espectral,
        é construído um eixo temporal acumulado e aplicada
        interpolação por spline cúbica.

        A série resultante é reamostrada, por padrão, a 4 Hz.

        Parameters
        ----------
        frequencia_amostragem : float, optional
            Frequência de reamostragem em Hz. Padrão: 4 Hz.

        Returns
        -------
        tempo_uniforme : numpy.ndarray
            Instantes da série uniformemente amostrada, em segundos.

        nn_interpolado : numpy.ndarray
            Intervalos NN interpolados, em milissegundos.
        """

        tempo_nn = (
            np.cumsum(self.nn)
            / 1000.0
        )

        tempo_nn = (
            tempo_nn
            - tempo_nn[0]
        )

        interpolador = CubicSpline(
            tempo_nn,
            self.nn,
        )

        tempo_uniforme = np.arange(
            tempo_nn[0],
            tempo_nn[-1],
            1.0 / frequencia_amostragem,
        )

        nn_interpolado = interpolador(
            tempo_uniforme
        )

        return (
            tempo_uniforme,
            nn_interpolado,
        )

    def calcular_metricas_frequencia(self):
        """
        Calcula as potências espectrais MF e HF.

        A série NN é interpolada e reamostrada a 4 Hz. A média
        da série é removida antes da estimativa da densidade
        espectral de potência (PSD) pelo método de Welch.

        Bandas utilizadas:
            MF: 0,07 <= f < 0,15 Hz
            HF: 0,15 <= f <= 0,40 Hz

        A potência de cada banda é obtida pela integração da PSD
        dentro dos respectivos limites de frequência.

        Returns
        -------
        dict
            mf_ms2 : float
                Potência absoluta da banda MF em ms².

            hf_ms2 : float
                Potência absoluta da banda HF em ms².
        """

        frequencia_amostragem = 4.0

        _, nn_interpolado = (
            self.interpolar_nn(
                frequencia_amostragem
            )
        )

        nn_interpolado = (
            nn_interpolado
            - np.mean(nn_interpolado)
        )

        frequencias, psd = welch(
            nn_interpolado,
            fs=frequencia_amostragem,
        )

        mascara_mf = (
            (frequencias >= 0.07)
            & (frequencias < 0.15)
        )

        mascara_hf = (
            (frequencias >= 0.15)
            & (frequencias <= 0.40)
        )

        mf = np.trapezoid(
            psd[mascara_mf],
            frequencias[mascara_mf],
        )

        hf = np.trapezoid(
            psd[mascara_hf],
            frequencias[mascara_hf],
        )

        return {
            "mf_ms2": float(mf),
            "hf_ms2": float(hf),
        }

    def calcular_mfp95_mean(
        self,
        tamanho_janela=60,
        passo=10,
    ):
        """
        Calcula MF médio, MF P95 e MF P95/Mean.

        A série NN é inicialmente interpolada e reamostrada a
        4 Hz. Em seguida, é dividida em janelas de 60 segundos
        com deslocamento de 10 segundos.

        Para cada janela:
            1. remove-se a média da série;
            2. estima-se a PSD pelo método de Welch;
            3. integra-se a potência entre 0,07 e 0,15 Hz.

        A partir das potências MF obtidas nas janelas são
        calculados:

            MF médio = média das potências MF

            MF P95 = percentil 95 das potências MF

            MF P95/Mean = MF P95 / MF médio

        Parameters
        ----------
        tamanho_janela : float, optional
            Duração de cada janela em segundos. Padrão: 60 s.

        passo : float, optional
            Deslocamento entre janelas consecutivas em segundos.
            Padrão: 10 s.

        Returns
        -------
        dict
            mf_medio_janelas_ms2 : float
                Potência MF média entre as janelas, em ms².

            mf_p95_ms2 : float
                Percentil 95 das potências MF, em ms².

            mfp95_mean : float
                Razão entre MF P95 e MF médio. Adimensional.

        Raises
        ------
        ValueError
            Se a duração do registro for insuficiente para formar
            pelo menos uma janela completa.
        """

        frequencia_amostragem = 4.0

        _, nn_interpolado = (
            self.interpolar_nn(
                frequencia_amostragem
            )
        )

        amostras_janela = int(
            tamanho_janela
            * frequencia_amostragem
        )

        amostras_passo = int(
            passo
            * frequencia_amostragem
        )

        valores_mf = []

        for inicio in range(
            0,
            len(nn_interpolado)
            - amostras_janela
            + 1,
            amostras_passo,
        ):

            fim = (
                inicio
                + amostras_janela
            )

            janela_nn = (
                nn_interpolado[
                    inicio:fim
                ]
            )

            janela_nn = (
                janela_nn
                - np.mean(janela_nn)
            )

            frequencias, psd = welch(
                janela_nn,
                fs=frequencia_amostragem,
                nperseg=len(janela_nn),
            )

            mascara_mf = (
                (frequencias >= 0.07)
                & (frequencias < 0.15)
            )

            mf = np.trapezoid(
                psd[mascara_mf],
                frequencias[mascara_mf],
            )

            valores_mf.append(mf)

        if not valores_mf:
            raise ValueError(
                "Duração insuficiente para "
                "calcular MF P95/Mean."
            )

        valores_mf = np.asarray(
            valores_mf,
            dtype=float,
        )

        mf_medio = np.mean(
            valores_mf
        )

        mf_p95 = np.percentile(
            valores_mf,
            95,
        )

        if mf_medio == 0:
            mfp95_mean = np.nan

        else:
            mfp95_mean = (
                mf_p95
                / mf_medio
            )

        return {
            "mf_medio_janelas_ms2": float(
                mf_medio
            ),
            "mf_p95_ms2": float(
                mf_p95
            ),
            "mfp95_mean": float(
                mfp95_mean
            ),
        }

    def calcular_hrv(self):
        """
        Executa o cálculo completo das métricas de HRV.

        Returns
        -------
        dict
            Dicionário contendo HR, RMSSD, SDNN, MF, HF,
            MF médio das janelas, MF P95 e MF P95/Mean.

        Raises
        ------
        ValueError
            Se houver menos de dois intervalos NN disponíveis.
        """

        if len(self.nn) < 2:
            raise ValueError(
                "Número insuficiente de "
                "intervalos NN."
            )

        resultados = {
            "hr_bpm": (
                self.calcular_hr_medio()
            ),
        }

        resultados.update(
            self.calcular_metricas_tempo()
        )

        resultados.update(
            self.calcular_metricas_frequencia()
        )

        resultados.update(
            self.calcular_mfp95_mean()
        )

        return resultados