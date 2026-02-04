# 🇱🇰 Sinhala-English Idiom Translator

A Google Translate-like web application for translating English sentences with idiomatic expressions to Sinhala.

---

## 📁 Project Structure

```
idiom2.0/
├── app.py                    # Flask backend server
├── hybrid_translator.py      # Translation logic
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore file
├── templates/
│   └── index.html           # Frontend HTML
├── static/
│   ├── style.css            # Styling
│   └── script.js            # Frontend JavaScript
├── models/                   # ⬅️ Model will auto-download here
│   └── (NLLB model files)
└── data/
    └── idiom_mapping.json    # ⬅️ Your idiom dictionary
```

---

## 🚀 Setup Instructions

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd idiom2.0
```

### Step 2: Create Virtual Environment

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** First run may take 5-10 minutes to download the NLLB model (~2GB) if not present in `models/` folder.

### Step 4: Verify Idiom Mapping

The `data/idiom_mapping.json` file should already exist with your idiom dictionary.

Example format:
```json
{
    "in abeyance": "අත් හිටලා",
    "above all": "වෙන කිසිත් නැතත්",
    "cheek by jowl": "යා බදව"
}
```

### Step 5: Run the Application

```bash
python app.py
```

The server will start on **http://localhost:5000**

### Step 6: Open in Browser

Navigate to: **http://localhost:5000**

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

### Setting Custom Paths:
```powershell
# Windows PowerShell
$env:MODEL_PATH="D:\path\to\your\model"
$env:IDIOM_MAPPING_PATH="D:\path\to\idiom_mapping.json"
python app.py

# Linux/Mac
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

### "Model not found" or First Run is Slow
- First run will automatically download `facebook/nllb-200-distilled-600M` (~2GB)
- Requires internet connection
- Downloaded model will be cached in `models/` folder for future use

### "CUDA out of memory"
- The app will automatically use CPU if GPU is not available
- You can force CPU by setting `device='cpu'` in [hybrid_translator.py](hybrid_translator.py)

### "Idiom not detected"
- Verify the idiom exists in [data/idiom_mapping.json](data/idiom_mapping.json)
- Idiom matching is case-insensitive
- Check spelling and exact phrasing

### Virtual Environment Issues (Windows)
```powershell
# If activation is blocked by execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate again
.\.venv\Scripts\Activate.ps1
```

### Port Already in Use
```bash
# Change port in app.py (bottom of file)
app.run(debug=True, port=5001)  # Use different port
```

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
