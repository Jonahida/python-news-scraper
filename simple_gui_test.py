import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
from functions import read_urls, process_urls

def start_scraper():
    start_button.config(state=tk.DISABLED)
    progress_bar['value'] = 0
    log_area.delete(1.0, tk.END)
    status_label.config(text="Running...")

    urls = url_list.copy()
    total = len(urls)

    def run():
        logs = process_urls(urls)
        for i, log in enumerate(logs):
            log_area.insert(tk.END, log + "\n")
            progress_bar["value"] = ((i + 1) / len(logs)) * 100
            root.update_idletasks()
        status_label.config(text="Done!")
        start_button.config(state=tk.NORMAL)

    threading.Thread(target=run, daemon=True).start()

def load_urls():
    file_path = filedialog.askopenfilename(title="Select URLs file", filetypes=[("Text Files", "*.txt")])
    if file_path:
        global url_list
        url_list = read_urls(file_path)
        status_label.config(text=f"{len(url_list)} URLs loaded.")

# GUI Setup
root = tk.Tk()
root.title("Visual News Scraper")
root.geometry("600x500")

ttk.Label(root, text="Visual News Scraper", font=("Helvetica", 16)).pack(pady=10)

ttk.Button(root, text="Load URLs File", command=load_urls).pack(pady=5)

start_button = ttk.Button(root, text="Start Scraping", command=start_scraper)
start_button.pack(pady=5)

progress_bar = ttk.Progressbar(root, orient='horizontal', length=500, mode='determinate')
progress_bar.pack(pady=10)

log_area = scrolledtext.ScrolledText(root, width=70, height=15)
log_area.pack(pady=10)

status_label = ttk.Label(root, text="Idle")
status_label.pack(pady=5)

# Load default URLs at startup
url_list = read_urls()
status_label.config(text=f"{len(url_list)} default URLs loaded.")

root.mainloop()

