import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
from time import sleep

# Simulate your scraping process here for demo
def start_scraping():
    progress_bar["value"] = 0
    status_label.config(text="Scraping started...")
    log_area.delete(1.0, tk.END)
    
    total_sites = 5  # For example
    for i in range(1, total_sites + 1):
        sleep(1)  # Simulating scraping delay
        log_area.insert(tk.END, f"Scraped headlines from site {i}\n")
        progress_bar["value"] = (i / total_sites) * 100
        root.update_idletasks()
    
    status_label.config(text="Scraping completed!")

# To prevent freezing, run in a thread
def run_scraper_in_thread():
    threading.Thread(target=start_scraping, daemon=True).start()

# GUI Setup
root = tk.Tk()
root.title("News Scraper Dashboard")
root.geometry("500x400")

ttk.Label(root, text="Python News Scraper", font=("Helvetica", 16)).pack(pady=10)

progress_bar = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
progress_bar.pack(pady=10)

start_button = ttk.Button(root, text="Start Scraping", command=run_scraper_in_thread)
start_button.pack(pady=10)

log_area = scrolledtext.ScrolledText(root, width=60, height=10)
log_area.pack(pady=10)

status_label = ttk.Label(root, text="Idle", font=("Helvetica", 12))
status_label.pack(pady=10)

root.mainloop()

