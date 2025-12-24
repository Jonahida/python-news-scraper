# Python News Scraper & AI Generator

A Python project that scrapes news headlines, translates them, generates AI-based descriptions, and can optionally generate images using a local Stable Diffusion WebUI.
The project includes experimental GUIs and scripts used to test and validate the pipeline.

# What this project can do

- Scrape headlines from multiple news websites
- Apply per-site scraping rules
- Filter out unwanted sections
- Translate headlines between languages
- Generate short descriptive texts using a language model
- Generate images from text prompts via Stable Diffusion
- Display progress and logs through simple graphical interfaces

# Core Logic (How it works)

The project follows this pipeline:
- Load URLs from a text file
- Scrape headlines using BeautifulSoup and site-specific rules
- Filter content using ignored section lists
- Translate text using MarianMT models
- Generate descriptions using a GPT-style language model
- (Optional) Generate images using a Stable Diffusion WebUI API
- Log results to console or GUI

This logic is centralized in the backend functions and reused by all test interfaces.

# Main Files Overview (Renamed for clarity)

## Core backend
`pipeline.py`

Main backend engine of the project.
- Scrapes headlines from websites
- Translates text
- Generates AI descriptions
- Calls Stable Diffusion APIs
- Orchestrates the full processing pipeline

This file contains the real functionality of the project.

## Test / Prototype Files

These files are not production entry points. They exist to test, visualize, or experiment with the pipeline.

`cli_pipeline_demo.py`
- Command-line prototype demonstrating the entire pipeline end-to-end.
- No GUI
- Sequential execution
- Prints results to terminal
- Useful for debugging and experimentation

`simple_gui_test.py`
- Minimal Tkinter GUI to visually test scraping progress.
- Progress bar
- Log output
- Loads URLs from file
- Designed for quick testing, not final UX

`gui_mockup_demo.py`
- Pure UI prototype with simulated scraping.
- No real scraping
- No AI logic
- Used only to test GUI layout and threading behavior


## Important
Only `pipeline.py` contains real business logic. The other files should be considered experimental test harnesses.

## Configuration Files

`config.json`

Defines:
- Scraping rules per domain
- Ignored sections
- AI model names
- Stable Diffusion WebUI endpoint

`default_sites.txt`
- Default list of news websites to scrape

`news_sites.txt`
- Custom list of news websites

## Main Requirements (Why they exist)

**Web scraping**
- requests
- beautifulsoup4.

Used to fetch and parse news websites.

**AI & NLP**
- transformers
- torch
- sentencepiece
- sacremoses
- tokenizers.

Used for:
- Translation (MarianMT)
- Text generation (GPT-style models)

**Note:** These libraries are heavy and may require GPU support for good performance.

**Image generation**

- Stable Diffusion WebUI (external)
- Communication via HTTP API
- Images decoded using `base64`

**GUI**
- tkinter (standard library)
Used for simple desktop interfaces and testing tools.

# Stable Diffusion API requirement

Image generation in this project is handled by an external Stable Diffusion WebUI service, which must be running in API-only mode.

A helper Bash script is used to activate the Stable Diffusion virtual environment and launch the WebUI with the API enabled, low VRAM usage, and no browser interface.

The scraper sends text prompts to this local API, receives generated images encoded in Base64, and saves them to disk.

If this service is not running, the project will continue scraping and generating text, but image generation will be unavailable.


## Project Status

This project is currently:
- Functionally complete
- Experimental by design
- Not yet production-hardened
- Not optimized for packaging or distribution

It is best suited for:

-Learning
-Prototyping
-AI pipeline experimentation
-Local desktop usage

# License

MIT License