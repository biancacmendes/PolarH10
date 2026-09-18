from pathlib import Path
import subprocess


DIRETORIO = Path("./dataset")


def converter_numbers(caminho_numbers):
    """Converte um questionário SUS de .numbers para .xlsx."""

    caminho_numbers = caminho_numbers.resolve()
    caminho_xlsx = caminho_numbers.with_suffix(".xlsx")

    if caminho_xlsx.exists():
        print(f"Já existe: {caminho_xlsx.name}")
        return

    script = f'''
    tell application "Numbers"
        open POSIX file "{caminho_numbers}"

        delay 1

        tell front document
            export to POSIX file "{caminho_xlsx}" as Microsoft Excel
            close saving no
        end tell
    end tell
    '''

    subprocess.run(
        ["osascript", "-e", script],
        check=True,
    )

    print(f"Convertido: {caminho_xlsx.name}")


def main():

    arquivos = []

    for pasta in DIRETORIO.iterdir():

        # Processa somente participantes USAB
        if not pasta.is_dir():
            continue

        if not pasta.name.startswith("USAB-"):
            continue

        # Procura somente arquivos .numbers contendo SUS
        for arquivo in pasta.glob("*.numbers"):

            if "SUS" in arquivo.name.upper():
                arquivos.append(arquivo)

    arquivos = sorted(arquivos)

    print(
        f"Questionários SUS encontrados: {len(arquivos)}"
    )

    for arquivo in arquivos:

        print(f"Convertendo: {arquivo}")

        try:
            converter_numbers(arquivo)

        except subprocess.CalledProcessError:
            print(
                f"Erro ao converter: {arquivo}"
            )


if __name__ == "__main__":
    main()
