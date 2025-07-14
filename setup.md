This guide covers the setup for the AI Plant Adviser.

## Quick Start

1. **Install Python dependencies:**
   bash
   pip install -r requirements.txt
   

2. **Installing and Using Ollama**

## Ollama (Free + Local)

### Setup:
1. **Install Ollama:**
   bash
   curl -fsSL https://ollama.ai/install.sh | sh
   

2. **Start Ollama server:**
   bash
   ollama serve
   

3. **Download a model (in new terminal):**
   bash
   ollama pull llama3.2
   

4. **Run the plant adviser:**
   bash
   python plantadviser_ollama.py
   

### Benefits:
- Completely free
- Runs locally (no internet needed for AI)
- No API Needed
- Privacy (all data stays on your computer)

---

## Troubleshooting

### Ollama Issues:
- **"Model not found"**: Run `ollama list` to see available models
- **"Connection refused"**: Make sure `ollama serve` is running
- **Slow responses**: Try a smaller model like `llama2:3b`
