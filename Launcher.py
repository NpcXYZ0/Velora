import os
import sys
import requests
import zipfile
import shutil
import subprocess

# URL do arquivo de versão
VERSION_URL = "https://raw.githubusercontent.com/NpcXYZ0/Velora/refs/heads/main/version.json"

# Nome do executável principal
MAIN_EXECUTABLE = "Velora.exe"

# Arquivo para armazenar a versão atual
VERSION_FILE = "version.txt"

def get_current_version():
    """
    Obtém a versão atual do aplicativo a partir do arquivo version.txt.
    Se o arquivo não existir, retorna None.
    """
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as file:
            return file.read().strip()
    else:
        return None  # Retorna None se o arquivo não existir

def set_current_version(version):
    """
    Atualiza a versão atual no arquivo version.txt.
    """
    with open(VERSION_FILE, "w") as file:
        file.write(version)

def check_for_updates():
    """
    Verifica se há uma nova versão disponível.
    """
    try:
        response = requests.get(VERSION_URL)
        response.raise_for_status()
        update_info = response.json()
        return update_info
    except Exception as e:
        print(f"Erro ao verificar atualizações: {e}")
        return None

def download_update(download_url):
    """
    Baixa a atualização.
    """
    try:
        update_file = "update_temp.zip"
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        # Baixa o arquivo de atualização
        with open(update_file, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)

        # Extrai o conteúdo do arquivo ZIP
        with zipfile.ZipFile(update_file, "r") as zip_ref:
            zip_ref.extractall("update_temp")

        # Substitui o executável antigo pelo novo
        if os.path.exists(MAIN_EXECUTABLE):
            os.remove(MAIN_EXECUTABLE)
        shutil.move(os.path.join("update_temp", MAIN_EXECUTABLE), MAIN_EXECUTABLE)

        # Limpa arquivos temporários
        shutil.rmtree("update_temp")
        os.remove(update_file)

        print("Atualização concluída com sucesso!")
        return True
    except Exception as e:
        print(f"Erro durante a atualização: {e}")
        return False

def main():
    # Obtém a versão atual
    current_version = get_current_version()
    if current_version:
        print(f"Versão atual: {current_version}")
    else:
        print("Arquivo version.txt não encontrado. O Velora.exe deve criar este arquivo.")

    # Verifica se há uma nova versão
    update_info = check_for_updates()
    if update_info:
        latest_version = update_info.get("version")
        download_url = update_info.get("download_url")

        if latest_version and download_url:
            # Compara a versão atual com a versão mais recente
            if current_version is None or latest_version > current_version:
                print(f"Nova versão disponível: {latest_version}")
                if download_update(download_url):
                    # Atualiza a versão no arquivo version.txt
                    set_current_version(latest_version)
                    print(f"Versão atualizada para: {latest_version}")
            else:
                print(f"Você já está usando a versão mais recente: {current_version}")

    # Executa o aplicativo principal
    if os.path.exists(MAIN_EXECUTABLE):
        subprocess.run([MAIN_EXECUTABLE])
    else:
        print(f"Erro: {MAIN_EXECUTABLE} não encontrado.")

if __name__ == "__main__":
    main()