import requests
import tkinter as tk
from tkinter import messagebox
import os
import sys
import zipfile
import shutil

# Versão atual do aplicativo
CURRENT_VERSION = "1.0.0"

def check_for_updates():
    try:
        # URL do arquivo JSON que contém a versão mais recente
        update_url = ""
        response = requests.get(update_url)
        update_info = response.json()

        latest_version = update_info["version"]
        download_url = update_info["download_url"]

        if latest_version > CURRENT_VERSION:
            # Pergunta ao usuário se ele deseja atualizar
            if messagebox.askyesno("Atualização Disponível", f"Uma nova versão ({latest_version}) está disponível. Deseja atualizar?"):
                # Baixa a nova versão
                download_update(download_url)
        else:
            messagebox.showinfo("Sem Atualizações", "Você já está usando a versão mais recente.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao verificar atualizações: {e}")

def download_update(download_url):
    try:
        # Baixa o arquivo de atualização
        response = requests.get(download_url, stream=True)
        update_file = "update.zip"
        with open(update_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)

        # Extrai o arquivo de atualização
        with zipfile.ZipFile(update_file, 'r') as zip_ref:
            zip_ref.extractall("update_temp")

        # Move os arquivos atualizados para o diretório do aplicativo
        for item in os.listdir("update_temp"):
            src = os.path.join("update_temp", item)
            dst = os.path.join(os.getcwd(), item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        # Limpa os arquivos temporários
        shutil.rmtree("update_temp")
        os.remove(update_file)

        messagebox.showinfo("Atualização Concluída", "A atualização foi concluída com sucesso. Reinicie o aplicativo.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao baixar a atualização: {e}")

def restart_application():
    python = sys.executable
    os.execl(python, python, *sys.argv)

# Adicionando um botão para verificar atualizações na interface gráfica
def add_update_button(root):
    update_button = tk.Button(root, text="Verificar Atualizações", command=check_for_updates)
    update_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

# Exemplo de uso na sua interface gráfica
root = tk.Tk()
root.title("Velora")
root.minsize(400, 125)
root.resizable(False, False)

# Adiciona o botão de verificação de atualizações
add_update_button(root)

root.mainloop()