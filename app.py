# =============================
# Imports
# =============================
import os
import json
import threading
import base64
import urllib.request
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
from transformers import (
    GPT2LMHeadModel, GPT2Tokenizer,
    MarianMTModel, MarianTokenizer
)

# =============================
# Configuration
# =============================
CONFIG_FILE = "config.json"
DEFAULT_SITES_FILE = "default_sites.txt"

OUTPUT_DIR = "api_out/txt2img"
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(CONFIG_FILE) as f:
    CONFIG = json.load(f)

# Load models once
gpt_model = GPT2LMHeadModel.from_pretrained(CONFIG["models"]["gpt2"])
gpt_tokenizer = GPT2Tokenizer.from_pretrained(CONFIG["models"]["gpt2"])
gpt_tokenizer.pad_token = gpt_tokenizer.eos_token

# =============================
# Utilities
# =============================
def timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def read_urls(path=DEFAULT_SITES_FILE):
    with open(path) as f:
        return [l.strip() for l in f if l.strip()]

# =============================
# Scraping
# =============================
def scrape_headlines(url):
    try:
        soup = BeautifulSoup(requests.get(url).content, "html.parser")
        domain = url.split("//")[-1].split("/")[0].replace("www.", "")
        rules = CONFIG["scraping_rules"].get(domain, [])

        headlines = []
        for rule in rules:
            if isinstance(rule, str):
                headlines += soup.find_all(rule)
            else:
                headlines += soup.find_all(rule["tag"], class_=rule.get("class"))

        return [
            h.get_text(strip=True)
            for h in headlines
            if h.get_text(strip=True) not in CONFIG["ignored_sections"]
        ]
    except Exception as e:
        return [f"Error scraping {url}: {e}"]

# =============================
# AI processing
# =============================
def translate_text(text):
    src = CONFIG["models"]["translation"]["source_lang"]
    tgt = CONFIG["models"]["translation"]["target_lang"]
    model_name = f"Helsinki-NLP/opus-mt-{src}-{tgt}"

    model = MarianMTModel.from_pretrained(model_name)
    tokenizer = MarianTokenizer.from_pretrained(model_name)

    encoded = tokenizer.encode(text, return_tensors="pt", padding=True)
    translated = model.generate(encoded, max_length=100)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

def generate_description(text):
    inputs = gpt_tokenizer.encode(text, return_tensors="pt")
    outputs = gpt_model.generate(
        inputs,
        max_length=100,
        top_p=0.95,
        top_k=60,
        do_sample=True,
        no_repeat_ngram_size=2,
        pad_token_id=gpt_tokenizer.eos_token_id,
    )
    return gpt_tokenizer.decode(outputs[0], skip_special_tokens=True)

def call_sd_api(endpoint, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{CONFIG['webui_server_url']}/{endpoint}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req).read().decode())

def generate_image(prompt):
    payload = {
        "prompt": prompt,
        "steps": 20,
        "width": 512,
        "height": 512,
        "cfg_scale": 7,
    }

    images = call_sd_api("sdapi/v1/txt2img", payload).get("images", [])
    for i, img in enumerate(images):
        path = f"{OUTPUT_DIR}/img_{timestamp()}_{i}.png"
        with open(path, "wb") as f:
            f.write(base64.b64decode(img))

# =============================
# Pipeline
# =============================
def process_urls(urls, stop_event, generate_images, log_cb):
    for url in urls:
        if stop_event.is_set():
            log_cb("Stopped by user.")
            return

        log_cb(f"Scraping: {url}")
        for headline in scrape_headlines(url):
            if stop_event.is_set():
                return

            log_cb(f"Headline: {headline}")
            translated = translate_text(headline)
            log_cb(f"Translated: {translated}")

            desc = generate_description(translated)
            log_cb(f"Description: {desc}")

            if generate_images:
                log_cb("Generating image...")
                generate_image(desc)
                log_cb("Image generated.")

    log_cb("Scraping completed.")

# =============================
# GUI
# =============================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Python News Scraper")
        self.root.geometry("900x600")

        self.stop_event = threading.Event()
        self.urls = read_urls()

        self.log = scrolledtext.ScrolledText(root)
        self.log.pack(expand=True, fill="both")

        controls = tk.Frame(root)
        controls.pack(pady=10)

        tk.Button(controls, text="Load URLs", command=self.load_urls).pack(side="left")
        tk.Button(controls, text="Start", command=self.start).pack(side="left")
        tk.Button(controls, text="Stop", command=self.stop).pack(side="left")

        self.gen_images = tk.BooleanVar(value=True)
        tk.Checkbutton(
            controls, text="Generate Images", variable=self.gen_images
        ).pack(side="left")

    def log_line(self, text):
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)

    def load_urls(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            self.urls = read_urls(path)
            self.log_line(f"Loaded {len(self.urls)} URLs")

    def start(self):
        self.stop_event.clear()
        threading.Thread(
            target=process_urls,
            args=(self.urls, self.stop_event, self.gen_images.get(), self.log_line),
            daemon=True,
        ).start()

    def stop(self):
        self.stop_event.set()

# =============================
# Entry point
# =============================
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()

