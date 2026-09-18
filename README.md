# Polar H10 — ECG and HRV Processing

Este repositório contém os códigos utilizados para aquisição, processamento e análise de sinais de ECG coletados com o sensor **Polar H10**.

O projeto inclui ferramentas para aquisição dos dados, processamento do ECG, cálculo de métricas de variabilidade da frequência cardíaca (HRV), processamento do questionário SUS e análise da associação entre as métricas fisiológicas e a usabilidade.

## Estrutura do repositório

```text
PolarH10/
├── dataset/
├── polarh10_driver/
├── src/
├── processar_individual.ipynb
├── processar_todos.ipynb
└── requirements.txt
```

### `dataset/`

Contém os dados experimentais organizados por participante.

Cada participante possui registros correspondentes às três condições experimentais:

- `baseline`: período de referência;
- `stage_1`: primeira condição experimental;
- `stage_8`: segunda condição experimental.

Os arquivos `.npy` armazenam os sinais de ECG, enquanto os arquivos `.json` contêm informações associadas à aquisição. Os arquivos `.xlsx` contêm as respostas ao questionário SUS.

Os arquivos `.npy` são armazenados no repositório utilizando **Git LFS**.

### `polarh10_driver/`

Contém os códigos relacionados à aquisição dos sinais diretamente do Polar H10.

- `polar_driver.py`: comunicação com o Polar H10 e aquisição dos dados;
- `scan_ble.py`: identificação de dispositivos Bluetooth Low Energy;
- `plot.py`: visualização dos sinais adquiridos.

### `src/`

Contém os módulos responsáveis pelo processamento e análise dos dados.

- `carregador_dados.py`: carregamento dos sinais e metadados experimentais;
- `processador_ecg.py`: filtragem do ECG, detecção dos picos R e obtenção dos intervalos RR utilizados na análise;
- `analisador_hrv.py`: cálculo das métricas de HRV nos domínios do tempo e da frequência;
- `analisador_sus.py`: leitura dos questionários e cálculo dos escores SUS;
- `processador_dataset.py`: processamento automatizado de todos os participantes e condições experimentais;
- `analisador_correlacao.py`: análise da associação entre métricas de HRV e SUS;
- `plot_individual.py`: funções auxiliares para visualização dos resultados individuais.

## Notebooks

### `processar_individual.ipynb`

Utilizado para inspecionar detalhadamente o processamento de um participante.

Este notebook permite acompanhar as diferentes etapas do processamento do ECG e verificar os resultados obtidos para cada condição experimental.

É o notebook recomendado para entender o funcionamento do pipeline de processamento.

### `processar_todos.ipynb`

Executa a análise consolidada do experimento.

O notebook processa todos os participantes, calcula as métricas de HRV, processa os questionários SUS e realiza as análises estatísticas utilizadas para avaliar a relação entre as medidas fisiológicas e a usabilidade.

É o notebook recomendado para reproduzir os resultados gerais do experimento.

## Fluxo geral

O processamento segue, de forma simplificada, o seguinte fluxo:

```text
ECG
 ↓
Filtragem do sinal
 ↓
Detecção dos picos R
 ↓
Intervalos RR
 ↓
Métricas de HRV
 ↓
Correção pelo baseline
 ↓
Análise em conjunto com SUS
 ↓
Correlação estatística
```

## Instalação

Clone o repositório:

```bash
git clone https://github.com/biancacmendes/PolarH10.git
cd PolarH10
```

Como os sinais de ECG são armazenados utilizando Git LFS, certifique-se de que o Git LFS esteja instalado e execute:

```bash
git lfs install
git lfs pull
```

Crie um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Por onde começar?

Para entender o projeto, a ordem recomendada é:

1. `processar_individual.ipynb` — visão detalhada do processamento de um participante;
2. `src/processador_ecg.py` — processamento do sinal de ECG;
3. `src/analisador_hrv.py` — cálculo das métricas de HRV;
4. `src/processador_dataset.py` — processamento automatizado do conjunto de dados;
5. `src/analisador_sus.py` — processamento do SUS;
6. `src/analisador_correlacao.py` — análise estatística;
7. `processar_todos.ipynb` — análise consolidada dos participantes.

Para quem deseja apenas reproduzir a análise completa, o ponto de entrada principal é `processar_todos.ipynb`.
