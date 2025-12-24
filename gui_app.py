import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import functions
import sys

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("News Scraper & AI Generator")
        self.root.geometry("800x600")

        self.stop_event = threading.Event()
        self.scraping_thread = None

        self.file_label = tk.Label(root, text="Selected file: default_sites.txt")
        self.file_label.pack(pady=5)

        self.log_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Courier", 10))
        self.log_text.pack(expand=True, fill="both", padx=10, pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.load_btn = tk.Button(btn_frame, text="Load URL File", command=self.load_file)
        self.load_btn.grid(row=0, column=0, padx=5)

        self.start_btn = tk.Button(btn_frame, text="Start Scraping", command=self.start_scraping)
        self.start_btn.grid(row=0, column=1, padx=5)

        self.stop_btn = tk.Button(btn_frame, text="Stop Scraping", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=5)

        self.urls = functions.read_urls()  # Default URLs on load

        self.generate_images_var = tk.BooleanVar(value=True)  # Default: generate images
        self.chk_generate_images = tk.Checkbutton(
            btn_frame,
            text="Generate Images",
            variable=self.generate_images_var
        )
        self.chk_generate_images.grid(row=1, column=0, columnspan=3, pady=5)

        # Handle safe close
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.urls = functions.read_urls(file_path)
            self.file_label.config(text=f"Selected file: {file_path}")

    def start_scraping(self):
        self.log_text.delete(1.0, tk.END)
        self.stop_event.clear()
        self.scraping_thread = threading.Thread(target=self.run_scraping)
        self.scraping_thread.start()
        self.stop_btn.config(state=tk.NORMAL)

    def run_scraping(self):
        try:
            logs = functions.process_urls(
                self.urls,
                stop_event=self.stop_event,
                generate_images=self.generate_images_var.get()
            )
            for line in logs:
                self.log_text.insert(tk.END, line + "\n")
                self.log_text.see(tk.END)
                if self.stop_event.is_set():
                    break
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.stop_btn.config(state=tk.DISABLED)

    def stop_scraping(self):
        self.stop_event.set()

    def on_close(self):
        if messagebox.askokcancel("Quit", "Do you want to exit?"):
            self.stop_scraping()
            if self.scraping_thread and self.scraping_thread.is_alive():
                self.scraping_thread.join()  # Wait until thread exits
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()

