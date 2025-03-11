import os
import base64
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk2
from ttkbootstrap.constants import *
import threading
from urllib.parse import urljoin, urlparse
from mimetypes import guess_extension
import validators
from PIL import Image, ImageTk

# Contador global para rastrear a linha do grid
download_counter = 0

def get_image_extension(img_url, content_type):
    """
    Determina a extensão da imagem com base na URL e no Content-Type.
    """
    # Tenta obter a extensão da URL
    url_path = urlparse(img_url).path
    _, url_extension = os.path.splitext(url_path)
    if url_extension.lower() in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".avif"]:
        return url_extension.lower()

    # Tenta obter a extensão do Content-Type
    if content_type:
        extension = guess_extension(content_type)
        if extension and extension.lower() in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".avif"]:
            return extension.lower()

    # Fallback: usa .jpg como extensão padrão
    return ".jpg"

def scroll_page(driver, scroll_pause_time=2, max_scrolls=10):
    """
    Rola a página para baixo para carregar todo o conteúdo.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height or scrolls >= max_scrolls:
            break
        last_height = new_height
        scrolls += 1

def extract_image_urls(driver):
    """
    Extrai URLs de imagens do DOM, incluindo aquelas carregadas dinamicamente.
    """
    image_urls = set()

    # Extrai URLs de tags <img>
    img_elements = driver.find_elements(By.TAG_NAME, "img")
    for img in img_elements:
        src = img.get_attribute("src") or img.get_attribute("data-src")
        if src:
            image_urls.add(src)

    # Extrai URLs de elementos com background-image
    elements_with_bg = driver.find_elements(By.CSS_SELECTOR, "[style*='background-image']")
    for element in elements_with_bg:
        style = element.get_attribute("style")
        if "background-image" in style:
            url = style.split("url('")[1].split("')")[0]
            if url:
                image_urls.add(url)

    return list(image_urls)

def download_blob_image(driver, img_element, output_dir, index):
    """
    Baixa uma imagem com URL 'blob:' usando o Selenium.
    """
    try:
        # Obtém o conteúdo da imagem em base64
        img_src = img_element.get_attribute("src")
        if img_src.startswith("blob:"):
            # Executa JavaScript para obter a imagem como base64
            script = """
            var img = arguments[0];
            var canvas = document.createElement('canvas');
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            var ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            return canvas.toDataURL('image/png').split(',')[1];
            """
            img_base64 = driver.execute_script(script, img_element)

            # Decodifica o base64 e salva a imagem
            img_data = base64.b64decode(img_base64)
            img_name = os.path.join(output_dir, f"blob_image_{index + 1}.png")
            with open(img_name, 'wb') as img_file:
                img_file.write(img_data)
            
            print(f"Imagem blob salva: {img_name}")
    except Exception as e:
        print(f"Erro ao processar imagem blob: {e}")

def check_cloudflare(driver):
    """
    Verifica se há um desafio do Cloudflare na página.
    """
    try:
        # Verifica se há um desafio do Cloudflare
        if "Checking your browser before accessing" in driver.page_source:
            print("Desafio do Cloudflare detectado.")
            return True
        return False
    except Exception as e:
        print(f"Erro ao verificar o Cloudflare: {e}")
        return False

def wait_for_cloudflare(driver):
    """
    Aguarda o usuário resolver o desafio do Cloudflare manualmente.
    """
    try:
        print("Aguardando resolução manual do desafio do Cloudflare...")
        input("Resolva o desafio do Cloudflare manualmente e pressione Enter para continuar...")
        
        # Aguarda mais alguns segundos para garantir que a página foi carregada
        time.sleep(5)
    except Exception as e:
        print(f"Erro ao aguardar o Cloudflare: {e}")

def download_images(url, folder_name, progress_bar, status_label, progress_frame):
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")  # Executa o Chrome em modo headless
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument("--log-level=DEBUG")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    chrome_driver_path = os.path.join(os.getcwd(), "chromedriver.exe")

    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print(f"Acessando a URL: {url}")
        driver.get(url)

        # Verifica se há um desafio do Cloudflare
        if check_cloudflare(driver):
            # Aguarda o usuário resolver o desafio manualmente
            wait_for_cloudflare(driver)

        print("Rolando a página para carregar o conteúdo...")
        scroll_page(driver)

        # Aguarda mais tempo para garantir que as imagens sejam carregadas
        time.sleep(5)

        # Extrai URLs das imagens
        image_urls = extract_image_urls(driver)

        if not image_urls:
            print("Nenhuma imagem encontrada na página.")
            status_label.config(text="Nenhuma imagem encontrada na página.")
            return

        # Cria a pasta com o nome escolhido pelo usuário
        output_dir = os.path.join(os.getcwd(), folder_name)
        os.makedirs(output_dir, exist_ok=True)

        total_images = len(image_urls)
        progress_bar["maximum"] = total_images
        progress_bar["value"] = 0

        img_elements = driver.find_elements(By.TAG_NAME, "img")
        for index, img in enumerate(img_elements):
            try:
                img_src = img.get_attribute("src") or img.get_attribute("data-src")
                if not img_src:
                    continue

                if img_src.startswith("blob:"):
                    # Baixa imagens blob
                    download_blob_image(driver, img, output_dir, index)
                else:
                    # Baixa imagens normais
                    if not bool(urlparse(img_src).netloc):
                        img_src = urljoin(url, img_src)

                    print(f"Baixando imagem: {img_src}")
                    status_label.config(text=f"Baixando {index + 1}/{total_images}: {os.path.basename(img_src)}")
                    response = requests.get(img_src, stream=True)

                    if response.status_code == 200:
                        # Obtém o tipo de conteúdo da imagem a partir do cabeçalho
                        content_type = response.headers.get("Content-Type")

                        # Determina a extensão da imagem
                        extension = get_image_extension(img_src, content_type)

                        # Define o nome do arquivo com a extensão correta
                        base_name = os.path.basename(urlparse(img_src).path)
                        if not base_name:
                            base_name = f"image_{index + 1}"
                        img_name = os.path.join(output_dir, f"{base_name}{extension}")

                        # Verifica se o arquivo já existe e adiciona um sufixo único, se necessário
                        counter = 1
                        while os.path.exists(img_name):
                            name, ext = os.path.splitext(base_name)
                            img_name = os.path.join(output_dir, f"{name}_{counter}{ext}")
                            counter += 1

                        # Salva a imagem na pasta
                        with open(img_name, 'wb') as img_file:
                            for chunk in response.iter_content(1024):
                                img_file.write(chunk)
                        
                        print(f"Imagem salva: {img_name}")
                    else:
                        print(f"Erro ao baixar {img_src}: Status {response.status_code}")
            except Exception as e:
                print(f"Erro ao processar a imagem {img_src}: {e}")
            
            # Atualiza a barra de progresso
            progress_bar["value"] = index + 1
            root.update_idletasks()
        
        print(f"Imagens baixadas e salvas em {output_dir}")
        status_label.config(text=f"Concluído! {total_images} imagens baixadas.")

        time.sleep(5)

        progress_frame.destroy()
    
    except Exception as e:
        print(f"Erro durante a execução: {e}")
        status_label.config(text=f"Erro: {e}")
        messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
    finally:
        if driver:  # Fecha o navegador se o driver foi inicializado
            driver.quit()
            print("Navegador fechado.")

def is_valid_url(url):
    return validators.url(url)

def start_download():
    """
    Inicia o processo de download das imagens em uma thread separada.
    """
    global download_counter  # Usa o contador global

    url = entry_url.get()
    folder_name = entry_folder.get()
    
    if not url or not folder_name:
        messagebox.showwarning("Aviso", "Preencha todos os campos!")
        return
    
    if not is_valid_url(url):
        messagebox.showwarning("Aviso", "A URL fornecida não é válida!")
        return
    
    # Cria uma nova barra de progresso e label de status para esta thread
    progress_frame = tk.Frame(root)
    progress_frame.grid(row=3 + download_counter, column=0, columnspan=2, padx=10, pady=10, sticky="ew")  # Adiciona em uma nova linha

    folder_name_label = tk.Label(progress_frame, text=f"Pasta: {folder_name}")
    folder_name_label.grid(row=0, column=0, pady=5, sticky="w")

    progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="indeterminate")
    progress_bar.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    status_label = tk.Label(progress_frame, text="Aguardando início...")
    status_label.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")

    # Incrementa o contador de downloads
    download_counter += 1

    # Inicia o download em uma nova thread
    threading.Thread(
        target=download_images,
        args=(url, folder_name, progress_bar, status_label, progress_frame)
    ).start()

# Configuração da interface gráfica
def abrir_janela_info():
    # Cria uma nova janela
    janela_info = tk.Toplevel()
    janela_info.title("Informações")
    janela_info.geometry("300x200")
    janela_info.resizable(False, False)
    janela_info.minsize(400,125)
    # janela_info.iconbitmap("info.ico")

    # Adiciona conteúdo à nova janela usando grid
    label = tk.Label(janela_info, text="Esta é uma janela de informações.")
    label.grid(row=0, column=0, padx=20, pady=20)

    botao_fechar = tk.Button(janela_info, text="Fechar", command=janela_info.destroy)
    botao_fechar.grid(row=1, column=0, pady=10)

root = ttk2.Window(themename="vapor")
root.title("Velora")

root.iconbitmap(os.path.join(os.getcwd(), "icon.ico"))

root.minsize(400,125)

root.resizable(False, False)

# Configuração do grid para tornar a interface escalável
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)

#image = Image.open("C:/Users/pokek/Downloads/CapDownloader/info.png")
#image = image.resize((32, 32), Image.Resampling.LANCZOS) 
#imagem_tk = ImageTk.PhotoImage(image)

# Frame para os campos de entrada e botões
button_frame = tk.Frame(root)
button_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

# Campo de entrada para a URL
label_url = tk.Label(button_frame, text="URL da página:")
label_url.grid(row=0, column=0, padx=10, pady=5, sticky="w")

entry_url = tk.Entry(button_frame)
entry_url.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

# Campo de entrada para o nome da pasta
label_folder = tk.Label(button_frame, text="Nome da pasta para salvar o capítulo:")
label_folder.grid(row=1, column=0, padx=10, pady=5, sticky="w")

entry_folder = tk.Entry(button_frame)
entry_folder.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

# Botão para iniciar o download
button_start = tk.Button(button_frame, text="Iniciar Download", command=start_download)
button_start.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

# Tornar os botões escaláveis dentro do frame
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)

# Inicia o loop da interface gráfica
root.mainloop()