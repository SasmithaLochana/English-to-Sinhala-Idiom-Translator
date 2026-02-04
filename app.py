"""
Flask Backend for Idiom-Aware Translation
==========================================
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import json
import re

from hybrid_translator import HybridTranslator

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
MODEL_PATH = os.environ.get('MODEL_PATH', 'models/')  # Your downloaded model folder
IDIOM_MAPPING_PATH = os.environ.get('IDIOM_MAPPING_PATH', 'data/idiom_mapping.json')

# Initialize translator (lazy loading)
translator = None

# Language detection patterns
_SINHALA_CHAR_RE = re.compile(r"[\u0D80-\u0DFF]")
_LATIN_CHAR_RE = re.compile(r"[A-Za-z]")


def detect_language(text: str) -> str:
    """
    Detect if text is English or Sinhala.
    Returns: 'en', 'si', 'mixed', or 'unknown'
    """
    has_sinhala = bool(_SINHALA_CHAR_RE.search(text))
    has_latin = bool(_LATIN_CHAR_RE.search(text))
    
    if has_sinhala and has_latin:
        return 'mixed'
    elif has_sinhala:
        return 'si'
    elif has_latin:
        # Use langdetect for better accuracy on Latin text
        try:
            from langdetect import detect, DetectorFactory
            DetectorFactory.seed = 0
            detected = detect(text)
            return detected
        except:
            return 'en'  # Fallback to English
    else:
        return 'unknown'


def validate_language_support(text: str, expected_lang: str = None):
    """
    Validate that text language is supported (English or Sinhala only).
    Returns error response if unsupported, None if valid.
    """
    detected = detect_language(text)
    
    # Supported languages
    if detected in ['en', 'si', 'mixed']:
        if expected_lang and detected != expected_lang and detected != 'mixed':
            return jsonify({
                'success': False,
                'error_code': 'WRONG_LANGUAGE',
                'detected_language': detected,
                'error': f'Input appears to be {detected.upper()}, but expected {expected_lang.upper()}. Please check your text or swap languages.'
            }), 400
        return None
    
    # Unsupported language
    lang_name = {'unknown': 'unknown/unsupported'}.get(detected, detected.upper())
    return jsonify({
        'success': False,
        'error_code': 'UNSUPPORTED_LANGUAGE',
        'detected_language': detected,
        'error': f'Unsupported language detected: {lang_name}. This system only supports English ↔ Sinhala translation.'
    }), 400


def get_translator():
    """Get or initialize translator."""
    global translator
    
    if translator is None:
        print("Initializing translator...")
        
        # Check if using local model or HuggingFace
        if os.path.exists(MODEL_PATH):
            model_path = MODEL_PATH
            print(f"Using local model: {model_path}")
        else:
            model_path = "facebook/nllb-200-distilled-600M"
            print(f"Using HuggingFace model: {model_path}")
        
        translator = HybridTranslator(
            model_path=model_path,
            idiom_mapping_path=IDIOM_MAPPING_PATH,
            device='auto'
        )
        translator.load_model()
    
    return translator


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/translate', methods=['POST'])
def translate():
    """
    Bidirectional translation: English ↔ Sinhala.
    
    Request JSON:
        {
            "text": "Text here",
            "direction": "en-si" or "si-en" (optional, auto-detected if not provided)
        }
    
    Response JSON:
        {
            "success": true,
            "source": "Source text",
            "translation": "Translated text",
            "source_lang": "en",
            "target_lang": "si",
            "idioms": [...],
            "idiom_accuracy": 1.0,
            "method": "hybrid"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400
        
        text = data['text'].strip()
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'Empty text'
            }), 400
        
        # Get direction (en-si or si-en)
        direction = data.get('direction', 'auto')
        
        # Auto-detect language if direction is auto
        if direction == 'auto':
            detected = detect_language(text)
            if detected == 'si':
                direction = 'si-en'
            else:
                direction = 'en-si'
        
        # Validate language support
        error_response = validate_language_support(text)
        if error_response:
            return error_response
        
        # Get translator and translate
        trans = get_translator()
        result = trans.translate(text, direction=direction)
        
        return jsonify({
            'success': True,
            'source': result.source,
            'translation': result.translation,
            'source_lang': result.source_lang,
            'target_lang': result.target_lang,
            'idioms': result.detected_idioms,
            'idiom_accuracy': result.idiom_accuracy,
            'method': result.method
        })
    
    except Exception as e:
        print(f"Translation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/detect-idioms', methods=['POST'])
def detect_idioms():
    """
    Detect idioms in English or Sinhala text.
    
    Request JSON:
        {"text": "Text here (English or Sinhala)"}
    
    Response JSON:
        {
            "success": true,
            "idioms": [{"english": "...", "sinhala": "..."}]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400
        
        text = data['text'].strip()
        trans = get_translator()
        
        # Detect language and use appropriate idiom detector
        detected_lang = detect_language(text)
        if detected_lang == 'si':
            idioms = trans.detector.detect_sinhala(text)
        else:
            idioms = trans.detector.detect(text)
        
        return jsonify({
            'success': True,
            'idioms': idioms
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


@app.route('/idiom-list')
def idiom_list():
    """Get list of all known idioms."""
    try:
        trans = get_translator()
        idioms = [
            {'english': en, 'sinhala': si}
            for en, si in trans.detector.idiom_mapping.items()
        ]
        return jsonify({
            'success': True,
            'count': len(idioms),
            'idioms': idioms
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("="*60)
    print("🇱🇰 Sinhala-English Idiom Translator")
    print("="*60)
    print(f"Model Path: {MODEL_PATH}")
    print(f"Idiom Mapping: {IDIOM_MAPPING_PATH}")
    print("="*60)
    print("\nStarting server...")
    print("Open http://localhost:5000 in your browser\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)
