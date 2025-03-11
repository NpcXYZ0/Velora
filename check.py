import requests
import tkinter as tk
from tkinter import messagebox
import os
import sys
import zipfile
import shutil

# Versão atual do aplicativo
CURRENT_VERSION = "0.0.1"

def check_for_updates():
    try:
        update_url = "https://raw.githubusercontent.com/NpcXYZ0/Velora/refs/heads/main/version.json"
        response = requests.get(update_url)
        response.raise_for_status()  # Lança erro se o status não for 200 OK

        update_info = response.json()
        latest_version = update_info.get("version")
        download_url = update_info.get("download_url")

        if not latest_version or not download_url:
            messagebox.showerror("Erro", "Resposta de atualização inválida.")
            return

        if latest_version > CURRENT_VERSION:
            if messagebox.askyesno("Atualização Disponível", f"Uma nova versão ({latest_version}) está disponível. Deseja atualizar?"):
                download_update(download_url)
        else:
            messagebox.showinfo("Sem Atualizações", "Você já está usando a versão mais recente.")
    except requests.RequestException as e:
        messagebox.showerror("Erro", f"Erro de rede ao verificar atualizações: {e}")
    except ValueError:
        messagebox.showerror("Erro", "Erro ao interpretar a resposta do servidor.")

def download_update(download_url):
    try:
        update_file = "update.zip"
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        with open(update_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)

        with zipfile.ZipFile(update_file, 'r') as zip_ref:
            zip_ref.extractall("update_temp")

        for item in os.listdir("update_temp"):
            src = os.path.join("update_temp", item)
            dst = os.path.join(os.getcwd(), item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        shutil.rmtree("update_temp")
        os.remove(update_file)

        messagebox.showinfo("Atualização Concluída", "A atualização foi concluída com sucesso. Reinicie o aplicativo.")
        restart_application()
    except requests.RequestException as e:
        messagebox.showerror("Erro", f"Erro ao baixar a atualização: {e}")
    except zipfile.BadZipFile:
        messagebox.showerror("Erro", "O arquivo de atualização está corrompido.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro inesperado: {e}")

def restart_application():
    python = sys.executable
    os.execl(python, python, *sys.argv)

def add_update_button(root):
    update_button = tk.Button(root, text="Verificar Atualizações", command=check_for_updates)
    update_button.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

root = tk.Tk()
root.title("Velora")
root.minsize(400, 125)
root.resizable(False, False)

add_update_button(root)
root.mainloop()
