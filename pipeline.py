import json
import os
import requests
from bs4 import BeautifulSoup
import base64
from datetime import datetime
from transformers import GPT2LMHeadModel, GPT2Tokenizer, MarianMTModel, MarianTokenizer
import urllib.request

# Load config
with open('config.json') as f:
    CONFIG = json.load(f)

out_dir = 'api_out'
out_dir_t2i = os.path.join(out_dir, 'txt2img')
os.makedirs(out_dir_t2i, exist_ok=True)

# Load GPT2 model
gpt_model = GPT2LMHeadModel.from_pretrained(CONFIG['models']['gpt2'])
gpt_tokenizer = GPT2Tokenizer.from_pretrained(CONFIG['models']['gpt2'])
gpt_tokenizer.pad_token = gpt_tokenizer.eos_token

def timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def read_urls(file_path='default_sites.txt'):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def scrape_headlines(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = []
        domain = url.split("//")[-1].split("/")[0].replace("www.", "")
        rules = CONFIG['scraping_rules'].get(domain, [])

        for rule in rules:
            if isinstance(rule, str):
                headlines += soup.find_all(rule)
            elif isinstance(rule, dict):
                headlines += soup.find_all(rule['tag'], class_=rule.get('class'))
        
        return [h.get_text(strip=True) for h in headlines if h.get_text(strip=True) not in CONFIG['ignored_sections']]
    except Exception as e:
        return [f"Error scraping {url}: {e}"]

def translate_text(text):
    src = CONFIG['models']['translation']['source_lang']
    tgt = CONFIG['models']['translation']['target_lang']
    model_name = f'Helsinki-NLP/opus-mt-{src}-{tgt}'
    model = MarianMTModel.from_pretrained(model_name)
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    encoded = tokenizer.encode(text, return_tensors="pt", padding=True)
    translated = model.generate(encoded, max_length=100)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

def generate_description(text):
    inputs = gpt_tokenizer.encode(text, return_tensors='pt')
    outputs = gpt_model.generate(
        inputs, max_length=100, no_repeat_ngram_size=2,
        top_p=0.95, top_k=60, do_sample=True,
        attention_mask=(inputs != gpt_tokenizer.pad_token_id),
        pad_token_id=gpt_tokenizer.eos_token_id
    )
    return gpt_tokenizer.decode(outputs[0], skip_special_tokens=True)

def call_api(endpoint, **payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{CONFIG['webui_server_url']}/{endpoint}",
                                 headers={'Content-Type': 'application/json'},
                                 data=data)
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode())

def generate_image(prompt, seed=1, steps=20):
    payload = {
        "prompt": prompt, "negative_prompt": "",
        "seed": seed, "steps": steps,
        "width": 512, "height": 512,
        "cfg_scale": 7, "sampler_name": "DPM++ 2M",
        "n_iter": 1, "batch_size": 1
    }
    images = call_api('sdapi/v1/txt2img', **payload).get('images', [])
    for idx, img_b64 in enumerate(images):
        save_path = os.path.join(out_dir_t2i, f'image_{timestamp()}_{idx}.png')
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(img_b64))

def process_urls(urls, stop_event=None, generate_images=True):
    logs = []
    for url in urls:
        if stop_event and stop_event.is_set():
            logs.append("Scraping stopped by user.")
            break

        logs.append(f"Scraping {url}")
        headlines = scrape_headlines(url)

        for headline in headlines:
            if stop_event and stop_event.is_set():
                logs.append("Scraping stopped by user.")
                return logs

            logs.append(f"Headline: {headline}")
            translated = translate_text(headline)
            logs.append(f"Translated: {translated}")
            desc = generate_description(translated)
            logs.append(f"Description: {desc}")

            if generate_images:
                logs.append(f"Generating image...")
                generate_image(desc)
                logs.append("Image generated.")
            else:
                logs.append("Image generation skipped.")

    logs.append("Scraping completed.")
    return logs
