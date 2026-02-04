"""
Hybrid Translator Module
========================
Combines NLLB Neural Translation + Idiom Dictionary
"""

import torch
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


@dataclass
class TranslationResult:
    """Translation result with metadata."""
    source: str
    translation: str
    source_lang: str
    target_lang: str
    detected_idioms: List[Dict]
    idiom_accuracy: float
    method: str


class IdiomDetector:
    """Detects idioms in English and Sinhala text."""
    
    def __init__(self, idiom_mapping: Dict[str, str]):
        # English -> Sinhala mapping
        self.idiom_mapping = {k.lower(): v for k, v in idiom_mapping.items()}
        
        # Sinhala -> English reverse mapping
        self.reverse_mapping = {v: k for k, v in self.idiom_mapping.items()}
        
        # English idiom patterns
        self.patterns = {}
        for idiom in self.idiom_mapping.keys():
            escaped = re.escape(idiom)
            pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
            self.patterns[idiom] = pattern
        
        self.sorted_idioms = sorted(self.patterns.keys(), key=len, reverse=True)
        
        # Sinhala idiom patterns
        self.sinhala_patterns = {}
        for sinhala_idiom in self.reverse_mapping.keys():
            # Sinhala doesn't have word boundaries like English, so we use simpler pattern
            escaped = re.escape(sinhala_idiom)
            pattern = re.compile(escaped)
            self.sinhala_patterns[sinhala_idiom] = pattern
        
        self.sorted_sinhala_idioms = sorted(self.sinhala_patterns.keys(), key=len, reverse=True)
    
    def detect(self, text: str) -> List[Dict]:
        """Detect English idioms in text."""
        detected = []
        used_positions = set()
        
        for idiom in self.sorted_idioms:
            pattern = self.patterns[idiom]
            
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()
                
                if any(start < ue and end > us for us, ue in used_positions):
                    continue
                
                detected.append({
                    'english': idiom,
                    'sinhala': self.idiom_mapping[idiom],
                    'position': (start, end)
                })
                used_positions.add((start, end))
        
        return detected
    
    def detect_sinhala(self, text: str) -> List[Dict]:
        """Detect Sinhala idioms in text."""
        detected = []
        used_positions = set()
        
        for sinhala_idiom in self.sorted_sinhala_idioms:
            pattern = self.sinhala_patterns[sinhala_idiom]
            
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()
                
                if any(start < ue and end > us for us, ue in used_positions):
                    continue
                
                detected.append({
                    'sinhala': sinhala_idiom,
                    'english': self.reverse_mapping[sinhala_idiom],
                    'position': (start, end)
                })
                used_positions.add((start, end))
        
        return detected
    
    def get_sinhala_idiom(self, english_idiom: str) -> Optional[str]:
        """Get Sinhala translation of an English idiom."""
        return self.idiom_mapping.get(english_idiom.lower())
    
    def get_english_idiom(self, sinhala_idiom: str) -> Optional[str]:
        """Get English translation of a Sinhala idiom."""
        return self.reverse_mapping.get(sinhala_idiom)


class HybridTranslator:
    """
    Hybrid Translation System: NLLB + Idiom Dictionary
    """
    
    def __init__(self, model_path: str, idiom_mapping_path: str, device: str = 'auto'):
        self.model_path = model_path
        self.device = self._get_device(device)
        
        with open(idiom_mapping_path, 'r', encoding='utf-8') as f:
            idiom_mapping = json.load(f)
        
        self.detector = IdiomDetector(idiom_mapping)
        
        self.source_lang = "eng_Latn"
        self.target_lang = "sin_Sinh"
        
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
    
    def _get_device(self, device: str) -> torch.device:
        """Determine the best device."""
        if device == 'auto':
            if torch.cuda.is_available():
                return torch.device('cuda')
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return torch.device('mps')
            else:
                return torch.device('cpu')
        return torch.device(device)
    
    def load_model(self):
        """Load the NLLB model."""
        if self.is_loaded:
            return
        
        print(f"Loading model from {self.model_path}...")
        print(f"Using device: {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            src_lang=self.source_lang,
            tgt_lang=self.target_lang
        )
        
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
        self.model = self.model.to(self.device)
        self.model.eval()
        
        self.is_loaded = True
        print(" Model loaded successfully!")
    
    def _nllb_translate(self, text: str, direction: str = 'en-si', max_length: int = 256) -> str:
        """Basic NLLB translation with direction support."""
        if not self.is_loaded:
            self.load_model()
        
        # Set source and target languages based on direction
        if direction == 'en-si':
            src_lang = "eng_Latn"
            tgt_lang = "sin_Sinh"
        else:  # si-en
            src_lang = "sin_Sinh"
            tgt_lang = "eng_Latn"
        
        self.tokenizer.src_lang = src_lang
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=max_length
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        forced_bos_token_id = self.tokenizer.convert_tokens_to_ids(tgt_lang)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                forced_bos_token_id=forced_bos_token_id,
                num_beams=5,
                max_length=max_length
            )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    def _get_dataset_translation(self, text: str) -> dict:
        """Check if exact sentence exists in dataset."""
        if not hasattr(self, 'sentence_mapping'):
            self.sentence_mapping = {}
            try:
                import pandas as pd
                df = pd.read_excel('data/idioms_dataset.xlsx')
                df.columns = [col.strip() for col in df.columns]
                for _, row in df.iterrows():
                    en = str(row.get('Figurative Example', '')).strip().lower()
                    si = str(row.get('Sinhala Translation Example', '')).strip()
                    if en and si and en != 'nan' and si != 'nan':
                        self.sentence_mapping[en] = {'sinhala': si}
                print(f"✅ Loaded {len(self.sentence_mapping)} sentence pairs from dataset")
            except Exception as e:
                print(f"⚠️ Dataset not loaded: {e}")
        
        text_lower = text.strip().lower()
        
        if text_lower in self.sentence_mapping:
            return self.sentence_mapping[text_lower]
        
        text_clean = re.sub(r'[^\w\s]', '', text_lower)
        for en, data in self.sentence_mapping.items():
            en_clean = re.sub(r'[^\w\s]', '', en)
            if text_clean == en_clean:
                return data
        
        return None
    
    def _smart_inject(self, translation: str, sinhala_idiom: str) -> str:
        """Inject idiom into translation."""
        if sinhala_idiom in translation:
            return translation
        
        words = translation.split()
        if len(words) <= 3:
            return sinhala_idiom + ' ' + translation
        
        insert_pos = min(3, len(words) // 2)
        words.insert(insert_pos, sinhala_idiom)
        return ' '.join(words)
    
    def translate(self, text: str, direction: str = 'en-si') -> TranslationResult:
        """
        Bidirectional translation with hybrid approach and idiom detection.
        1. Detect idioms in source language
        2. Check if exact sentence exists in dataset (en-si only)
        3. Use NLLB + idiom injection for both directions
        
        Args:
            text: Text to translate
            direction: 'en-si' or 'si-en'
        """
        detected_idioms = []
        
        if direction == 'en-si':
            # English to Sinhala
            detected_idioms = self.detector.detect(text)
            
            # Check if we have exact match in dataset
            exact_translation = self._get_dataset_translation(text)
            
            if exact_translation:
                return TranslationResult(
                    source=text,
                    translation=exact_translation['sinhala'],
                    source_lang='en',
                    target_lang='si',
                    detected_idioms=detected_idioms,
                    idiom_accuracy=1.0,
                    method="dataset_match"
                )
            
            # Use NLLB + idiom injection
            if detected_idioms:
                modified_text = text
                placeholder_map = {}
                
                for i, idiom in enumerate(detected_idioms):
                    placeholder = f"__IDIOM_{i}__"
                    pattern = re.compile(re.escape(idiom['english']), re.IGNORECASE)
                    modified_text = pattern.sub(placeholder, modified_text, count=1)
                    placeholder_map[placeholder] = idiom['sinhala']
                
                translation = self._nllb_translate(modified_text, direction=direction)
                
                for placeholder, target_idiom in placeholder_map.items():
                    if placeholder in translation:
                        translation = translation.replace(placeholder, target_idiom)
                    else:
                        translation = self._smart_inject(translation, target_idiom)
                
                method = "hybrid"
            else:
                translation = self._nllb_translate(text, direction=direction)
                method = "nllb"
                
            # Calculate accuracy for English idioms
            found = sum(1 for i in detected_idioms if i['sinhala'] in translation)
            accuracy = found / len(detected_idioms) if detected_idioms else 1.0
            
        else:
            # Sinhala to English
            detected_idioms = self.detector.detect_sinhala(text)
            
            # Use NLLB + idiom injection
            if detected_idioms:
                modified_text = text
                placeholder_map = {}
                
                for i, idiom in enumerate(detected_idioms):
                    placeholder = f"__IDIOM_{i}__"
                    # For Sinhala, do direct string replacement (no word boundaries)
                    modified_text = modified_text.replace(idiom['sinhala'], placeholder, 1)
                    placeholder_map[placeholder] = idiom['english']
                
                translation = self._nllb_translate(modified_text, direction=direction)
                
                for placeholder, target_idiom in placeholder_map.items():
                    if placeholder in translation:
                        translation = translation.replace(placeholder, target_idiom)
                    else:
                        # For English output, try to inject idiom naturally
                        translation = self._smart_inject(translation, target_idiom)
                
                method = "hybrid"
            else:
                translation = self._nllb_translate(text, direction=direction)
                method = "nllb"
            
            # Calculate accuracy for Sinhala idioms
            found = sum(1 for i in detected_idioms if i['english'].lower() in translation.lower())
            accuracy = found / len(detected_idioms) if detected_idioms else 1.0
        
        source_lang = 'en' if direction == 'en-si' else 'si'
        target_lang = 'si' if direction == 'en-si' else 'en'
        
        return TranslationResult(
            source=text,
            translation=translation,
            source_lang=source_lang,
            target_lang=target_lang,
            detected_idioms=detected_idioms,
            idiom_accuracy=accuracy,
            method=method
        )


# Singleton instance
_translator = None

def get_translator(model_path: str = None, idiom_mapping_path: str = None) -> HybridTranslator:
    """Get or create translator instance."""
    global _translator
    
    if _translator is None:
        if model_path is None or idiom_mapping_path is None:
            raise ValueError("Must provide model_path and idiom_mapping_path on first call")
        _translator = HybridTranslator(model_path, idiom_mapping_path)
    
    return _translator