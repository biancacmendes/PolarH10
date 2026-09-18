"""
processador_ecg.py

Processamento do sinal de ECG para obtenção dos intervalos utilizados
posteriormente no cálculo das métricas de HRV.

O processamento segue as seguintes etapas:

    ECG bruto
        ↓
    Estimativa da relação sinal-ruído (SNR)
        ↓
    Filtragem passa-banda
        ↓
    Detecção dos picos R
        ↓
    Cálculo dos intervalos RR
        ↓
    Controle de artefatos por faixa fisiológica
        ↓
    Intervalos RR utilizados na análise de HRV

O sinal é filtrado utilizando um filtro Butterworth passa-banda de
4ª ordem entre 0,5 e 30 Hz, aplicado com filtragem de fase zero.

Os picos R são detectados utilizando a função ecg_peaks do
NeuroKit2.

Os intervalos RR são calculados a partir da diferença temporal entre
picos R consecutivos e expressos em milissegundos.

Como controle de artefatos, são mantidos apenas intervalos RR entre
300 e 1500 ms. A quantidade e o percentual de intervalos removidos
são registrados para rastreabilidade do processamento.

A estimativa de SNR é utilizada como indicador descritivo da qualidade
do sinal e não como critério automático de exclusão de registros.
"""

import numpy as np
import neurokit2 as nk
from scipy.signal import butter, sosfiltfilt


class ProcessadorECG:
    """
    Processa um registro de ECG para obtenção dos intervalos RR
    utilizados na análise de HRV.

    Parameters
    ----------
    experimento : ExperimentoECG
        Objeto contendo o sinal de ECG e os metadados da aquisição,
        incluindo a frequência de amostragem.
    """

    def __init__(self, experimento):
        """
        Armazena o sinal de ECG e a frequência de amostragem
        associados ao experimento.
        """

        self.experimento = experimento

        self.sinal = np.asarray(
            experimento.sinal,
            dtype=float,
        ).squeeze()

        self.taxa_amostragem = (
            experimento.taxa_amostragem
        )

    def calcular_snr(self):
        """
        Estima a relação sinal-ruído (SNR) do registro de ECG.

        O componente considerado como sinal é obtido pela filtragem
        passa-banda do ECG. O componente de ruído é estimado pela
        diferença entre o sinal bruto e o sinal filtrado:

            ruido = ECG_bruto - ECG_filtrado

        A SNR é calculada como:

            SNR = 10 log10(P_sinal / P_ruido)

        onde P_sinal e P_ruido representam as potências médias do
        sinal filtrado e do componente residual, respectivamente.

        A SNR é utilizada como indicador descritivo da qualidade do
        registro e não como critério automático de exclusão.

        Returns
        -------
        float
            Estimativa da SNR em decibéis (dB). Caso a potência
            estimada do ruído seja zero, retorna infinito.
        """

        sinal_filtrado = self.filtrar_sinal()

        ruido = (
            self.sinal
            - sinal_filtrado
        )

        potencia_sinal = np.mean(
            sinal_filtrado ** 2
        )

        potencia_ruido = np.mean(
            ruido ** 2
        )

        if potencia_ruido == 0:
            return np.inf

        snr = 10 * np.log10(
            potencia_sinal
            / potencia_ruido
        )

        return float(snr)

    def filtrar_sinal(self):
        """
        Filtra o sinal de ECG.

        É aplicado um filtro Butterworth passa-banda de 4ª ordem,
        com frequências de corte de 0,5 e 30 Hz.

        O filtro é implementado em seções de segunda ordem (SOS) e
        aplicado nos sentidos direto e reverso por meio de
        sosfiltfilt, resultando em filtragem de fase zero.

        Returns
        -------
        numpy.ndarray
            Sinal de ECG filtrado.
        """

        frequencia_nyquist = (
            self.taxa_amostragem
            / 2
        )

        sos = butter(
            4,
            [
                0.5 / frequencia_nyquist,
                30.0 / frequencia_nyquist,
            ],
            btype="bandpass",
            output="sos",
        )

        sinal_filtrado = sosfiltfilt(
            sos,
            self.sinal,
        )

        return sinal_filtrado

    def detectar_picos_r(
        self,
        sinal_filtrado,
    ):
        """
        Detecta os picos R no sinal de ECG filtrado.

        A detecção é realizada pela função ecg_peaks do NeuroKit2,
        utilizando a frequência de amostragem original do registro.

        Parameters
        ----------
        sinal_filtrado : numpy.ndarray
            Sinal de ECG após filtragem passa-banda.

        Returns
        -------
        numpy.ndarray
            Índices das amostras correspondentes aos picos R
            detectados.
        """

        _, informacoes = nk.ecg_peaks(
            sinal_filtrado,
            sampling_rate=self.taxa_amostragem,
        )

        picos_r = np.asarray(
            informacoes["ECG_R_Peaks"]
        )

        return picos_r

    def calcular_intervalos_rr(
        self,
        picos_r,
    ):
        """
        Calcula os intervalos RR a partir dos picos R consecutivos.

        A diferença entre os índices dos picos é convertida para
        tempo utilizando a frequência de amostragem:

            RR = diferença_amostras / fs × 1000

        Parameters
        ----------
        picos_r : numpy.ndarray
            Índices dos picos R detectados.

        Returns
        -------
        numpy.ndarray
            Intervalos RR em milissegundos.
        """

        intervalos_rr = (
            np.diff(picos_r)
            / self.taxa_amostragem
            * 1000
        )

        return intervalos_rr

    def corrigir_artefatos_rr(
        self,
        intervalos_rr,
    ):
        """
        Aplica um controle de artefatos baseado em faixa fisiológica.

        São mantidos apenas intervalos RR compreendidos entre
        300 e 1500 ms:

            300 ms <= RR <= 1500 ms

        Intervalos fora dessa faixa são removidos. O método também
        registra a quantidade absoluta e o percentual de intervalos
        removidos.

        Este procedimento constitui um controle baseado exclusivamente
        nos limites dos intervalos RR. Portanto, intervalos dentro da
        faixa estabelecida não são necessariamente livres de ectopias
        ou outros artefatos.

        Parameters
        ----------
        intervalos_rr : numpy.ndarray
            Intervalos RR em milissegundos.

        Returns
        -------
        intervalos_nn : numpy.ndarray
            Intervalos RR remanescentes após aplicação dos limites
            fisiológicos e utilizados posteriormente na análise HRV.

        numero_removidos : int
            Número de intervalos removidos.

        percentual_removidos : float
            Percentual dos intervalos RR removidos.
        """

        mascara = (
            (intervalos_rr >= 300)
            & (intervalos_rr <= 1500)
        )

        intervalos_nn = (
            intervalos_rr[mascara]
        )

        numero_removidos = np.sum(
            ~mascara
        )

        percentual_removidos = (
            numero_removidos
            / len(intervalos_rr)
            * 100
            if len(intervalos_rr) > 0
            else 0.0
        )

        return (
            intervalos_nn,
            int(numero_removidos),
            float(percentual_removidos),
        )

    def processar(self):
        """
        Executa o pipeline completo de processamento do ECG.

        Etapas:
            1. Estimativa da SNR.
            2. Filtragem passa-banda do ECG.
            3. Detecção dos picos R.
            4. Cálculo dos intervalos RR.
            5. Remoção dos intervalos fora da faixa fisiológica.

        Returns
        -------
        dict
            Dicionário contendo:

            snr_db
                Estimativa da relação sinal-ruído em dB.

            sinal_filtrado
                ECG após filtragem passa-banda.

            picos_r
                Índices dos picos R detectados.

            intervalos_rr
                Intervalos RR antes do controle de artefatos.

            intervalos_nn
                Intervalos RR remanescentes utilizados na análise HRV.

            numero_picos_r
                Número de picos R detectados.

            numero_rr
                Número total de intervalos RR calculados.

            numero_rr_removidos
                Número de intervalos removidos.

            percentual_rr_removidos
                Percentual de intervalos removidos.
        """

        snr = self.calcular_snr()

        sinal_filtrado = (
            self.filtrar_sinal()
        )

        picos_r = self.detectar_picos_r(
            sinal_filtrado
        )

        intervalos_rr = (
            self.calcular_intervalos_rr(
                picos_r
            )
        )

        (
            intervalos_nn,
            numero_removidos,
            percentual_removidos,
        ) = self.corrigir_artefatos_rr(
            intervalos_rr
        )

        return {
            "snr_db": snr,
            "sinal_filtrado": sinal_filtrado,
            "picos_r": picos_r,
            "intervalos_rr": intervalos_rr,
            "intervalos_nn": intervalos_nn,
            "numero_picos_r": len(picos_r),
            "numero_rr": len(intervalos_rr),
            "numero_rr_removidos": numero_removidos,
            "percentual_rr_removidos": percentual_removidos,
        }