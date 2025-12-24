import requests
from bs4 import BeautifulSoup
import urllib.request
import base64
import json
import time
import os
from datetime import datetime
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
from transformers import MarianMTModel, MarianTokenizer

# Web UI server URL
webui_server_url = 'http://127.0.0.1:7861'

# Output directories
out_dir = 'api_out'
out_dir_t2i = os.path.join(out_dir, 'txt2img')
os.makedirs(out_dir_t2i, exist_ok=True)

# List of section names to be ignored
ignored_sections = [
    "Primo piano", "Repubblica 50", "Sanremo 75", "Life", "Magazine",
    "Focus", "Pianeta economia", "Podcast", "I Parlamenti buffi",
    "Top Video", "Il mondo Repubblica", "Leggi Repubblica", "Video", "Audioarticoli", "Iniziative speciali", "Social", "App", 
    "Supplementi Repubblica", "Gedi News Network", "Quotidiani locali", "Periodici", "Radio", "Iniziative Editoriali", "Partnership"
]

# Load pre-trained GPT-2 model and tokenizer
model_name = "gpt2"  # You can use "distilgpt2" for a smaller model
model = GPT2LMHeadModel.from_pretrained(model_name)
tokenizer = GPT2Tokenizer.from_pretrained(model_name)

# Ensure pad_token_id is set for proper handling of padding
tokenizer.pad_token = tokenizer.eos_token

# Function to load MarianMT translation model
def load_translation_model(src_lang='it', tgt_lang='en'):
    model_name = f'Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}'
    model = MarianMTModel.from_pretrained(model_name)
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    return model, tokenizer

# Function to translate text
def translate_text(text, src_lang='it', tgt_lang='en'):
    model, tokenizer = load_translation_model(src_lang, tgt_lang)
    encoded = tokenizer.encode(text, return_tensors="pt", padding=True)
    translated = model.generate(encoded, max_length=100)
    translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
    return translated_text

def timestamp():
    return datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S")

def encode_file_to_base64(path):
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')

def decode_and_save_base64(base64_str, save_path):
    with open(save_path, "wb") as file:
        file.write(base64.b64decode(base64_str))

def call_api(api_endpoint, **payload):
    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        f'{webui_server_url}/{api_endpoint}',
        headers={'Content-Type': 'application/json'},
        data=data,
    )
    response = urllib.request.urlopen(request)
    return json.loads(response.read().decode('utf-8'))

def call_txt2img_api(prompt, **payload):
    payload["prompt"] = prompt  # Set the input prompt as a variable
    response = call_api('sdapi/v1/txt2img', **payload)
    for index, image in enumerate(response.get('images')):
        save_path = os.path.join(out_dir_t2i, f'txt2img-{timestamp()}-{index}.png')
        decode_and_save_base64(image, save_path)

def generate_image(prompt, seed=1, steps=20, width=512, height=512, cfg_scale=7, sampler_name="DPM++ 2M", n_iter=1, batch_size=1):
    # Prepare payload using passed arguments
    payload = {
        "negative_prompt": "",
        "seed": seed,
        "steps": steps,
        "width": width,
        "height": height,
        "cfg_scale": cfg_scale,
        "sampler_name": sampler_name,
        "n_iter": n_iter,
        "batch_size": batch_size,
    }

    call_txt2img_api(prompt, **payload)

def generate_description(headline):
    # Encode the headline as input for the model
    inputs = tokenizer.encode(headline, return_tensors='pt')
    
    # Manually create an attention mask (all ones, since we don't have padding in this case)
    attention_mask = torch.ones(inputs.shape, dtype=torch.long)

    # Generate output using the model with sampling enabled
    outputs = model.generate(
        inputs, 
        max_length=100, 
        num_return_sequences=1, 
        no_repeat_ngram_size=2, 
        top_p=0.95, 
        top_k=60, 
        do_sample=True,  # Set do_sample to True to enable sampling
        attention_mask=attention_mask,  # Pass the attention mask
        pad_token_id=tokenizer.eos_token_id  # Set pad_token_id to eos_token_id
    )
    
    # Decode the output to text
    description = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return description

def read_urls(file_path):
    with open(file_path, 'r') as file:
        urls = file.readlines()
    return [url.strip() for url in urls]

def scrape_headlines(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for request errors
        soup = BeautifulSoup(response.content, 'html.parser')

        print(f"Headlines from {url}:")

        headlines = []
        if "repubblica.it" in url:
            # Using h1, h2, and h3 for Repubblica as it worked previously
            headlines = soup.find_all(['h1', 'h2', 'h3'])
        elif "corriere.it" in url:
            # For Corriere, handle as previously
            headlines = soup.find_all('h4', class_='title-art-hp')

        headline_texts = []
        for headline in headlines:
            headline_text = headline.get_text(strip=True)
            if headline_text and headline_text not in ignored_sections:
                headline_texts.append(headline_text)

        return headline_texts

    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return []

def main():
    # Scrape URLs from a file
    urls = read_urls('news_sites.txt')
    
    # Scrape headlines from each URL
    for url in urls:
        headlines = scrape_headlines(url)
        
        if headlines:
            # Loop through all the headlines and process each one
            for headline in headlines:
                print(f"Original headline: {headline}")
                translated_headline = translate_text(headline, src_lang='it', tgt_lang='en')
                print(f"Translated headline: {translated_headline}")
                
                # Generate a description based on the translated headline
                print(f"Generating description for: {translated_headline}")
                description = generate_description(translated_headline)
                print(f"Generated description: {description}")
                
                # Generate an image based on the description
                print(f"Generating image for: {description}")
                generate_image(description)

if __name__ == "__main__":
    main()
