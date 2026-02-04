# 🇱🇰 Sinhala-English Idiom Translator

A Google Translate-like web application for translating English sentences with idiomatic expressions to Sinhala.

---

## 📁 Project Structure

```
idiom_translator_app/
├── app.py                    # Flask backend server
├── hybrid_translator.py      # Translation logic
├── requirements.txt          # Python dependencies
├── templates/
│   └── index.html           # Frontend HTML
├── static/
│   ├── style.css            # Styling
│   └── script.js            # Frontend JavaScript
├── models/                   # ⬅️ Put your downloaded model here
│   ├── config.json
│   ├── pytorch_model.bin (or model.safetensors)
│   ├── tokenizer.json
│   └── ...
└── data/
    └── idiom_mapping.json    # ⬅️ Your idiom dictionary
```

---

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
cd idiom_translator_app
pip install -r requirements.txt
```

### Step 2: Add Your Model

**Option A: Use Downloaded Model (from Kaggle/Colab)**

1. Copy your model folder to `models/`
2. Make sure it contains:
   - `config.json`
   - `pytorch_model.bin` or `model.safetensors`
   - `tokenizer_config.json`
   - `tokenizer.json` or `sentencepiece.bpe.model`

**Option B: Use HuggingFace Model (Auto-download)**

If `models/` folder is empty, the app will automatically download `facebook/nllb-200-distilled-600M`

### Step 3: Add Idiom Mapping

Copy your `idiom_mapping.json` to `data/` folder.

Format:
```json
{
    "in abeyance": "අත් හිටලා",
    "above all": "වෙන කිසිත් නැතත්",
    "cheek by jowl": "යා බදව"
}
```

### Step 4: Run the App

```bash
python app.py
```

### Step 5: Open in Browser

Go to: **http://localhost:5000**

---

## 💻 Usage

1. **Enter English text** in the left box
2. **Click "Translate"** button
3. **View Sinhala translation** in the right box
4. **See detected idioms** highlighted below the input

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `models/` | Path to your model |
| `IDIOM_MAPPING_PATH` | `data/idiom_mapping.json` | Path to idiom mapping |

### Example:
```bash
export MODEL_PATH=/path/to/your/model
export IDIOM_MAPPING_PATH=/path/to/idiom_mapping.json
python app.py
```

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/translate` | POST | Translate text |
| `/detect-idioms` | POST | Detect idioms only |
| `/idiom-list` | GET | Get all idiom pairs |
| `/health` | GET | Health check |

### Example API Call:

```bash
curl -X POST http://localhost:5000/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "That matter has been in abeyance for years."}'
```

Response:
```json
{
    "success": true,
    "source": "That matter has been in abeyance for years.",
    "translation": "ඒ කරුණ අවුරුදු ගණනකට අත් හිටලාය.",
    "idioms": [{"english": "in abeyance", "sinhala": "අත් හිටලා"}],
    "idiom_accuracy": 1.0,
    "method": "hybrid"
}
```

---

## 🐛 Troubleshooting

### "Model not found"
- Make sure model files are in `models/` folder
- Or let it download automatically (needs internet)

### "CUDA out of memory"
- The app will auto-use CPU if GPU is not available
- Or set: `device='cpu'` in `hybrid_translator.py`

### "Idiom not detected"
- Check `idiom_mapping.json` contains the idiom
- Idiom matching is case-insensitive

---

## 📊 Research Project

This application was developed as part of a research project on **idiom-aware machine translation** for low-resource languages.

**Method:** Hybrid NLLB + Idiom Dictionary

---

## 📝 License

For research and educational purposes.

---

## 🙏 Credits

- NLLB Model: Meta AI / Facebook
- Framework: Flask, Transformers (HuggingFace)
