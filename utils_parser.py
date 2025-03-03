# utils/parser.py
import re
import json
from collections import defaultdict

# Словник блоків GNU Radio з описами та параметрами
GRC_BLOCKS = {
    "source": {
        "rtl_sdr_source": {
            "name": ["rtl-sdr", "приймач", "sdr", "ртл", "джерело"],
            "params": {
                "samp_rate": {"default": "2e6", "unit": "Hz"},
                "center_freq": {"default": "100e6", "unit": "Hz"},
                "gain": {"default": "20", "unit": "dB"}
            }
        }
    },
    "filter": {
        "low_pass_filter": {
            "name": ["фнч", "low pass", "нижніх частот", "lpf"],
            "params": {
                "cutoff_freq": {"default": "5e3", "unit": "Hz"},
                "width": {"default": "1e3", "unit": "Hz"}
            }
        }
    },
    # Додайте інші категорії та блоки тут
}

# Регулярні вирази для виявлення параметрів
RE_PATTERNS = {
    # Частоти з одиницями (Гц, кГц, МГц, ГГц)
    "freq": r'(\d+(?:\.\d+)?)\s*(?:Гц|гц|кГц|кгц|МГц|мгц|ГГц|ггц|Hz|hz|kHz|khz|MHz|mhz|GHz|ghz)',
    
    # Ширина смуги - різні способи вказати
    "bandwidth": r'(?:(?:ширин(?:а|у|ою)|пропускн(?:а|у|ою))?\s*(?:смуг(?:а|и|ою)|bandwidth|полос(?:а|у|ой)))\s*(?:в)?\s*(\d+(?:\.\d+)?)\s*(?:Гц|гц|кГц|кгц|МГц|мгц|ГГц|ггц|Hz|hz|kHz|khz|MHz|mhz|GHz|ghz)',
    
    # Детальніші регулярні вирази...
}

def normalize_frequency(value_str, unit_str):
    """Нормалізація частотних значень до герців"""
    value = float(value_str)
    unit = unit_str.lower()
    
    if unit in ['гц', 'hz']:
        return value
    elif unit in ['кгц', 'khz']:
        return value * 1e3
    elif unit in ['мгц', 'mhz']:
        return value * 1e6
    elif unit in ['ггц', 'ghz']:
        return value * 1e9
    
    return value

def extract_parameters_from_text(text):
    """Витягнення всіх параметрів з тексту"""
    parameters = defaultdict(list)
    
    # Обробка кожного шаблону та витягнення параметрів
    for param_name, pattern in RE_PATTERNS.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Витяг значення та одиниці для нормалізації
            if param_name in ["freq", "bandwidth"]:
                value = match.group(1)
                # Виокремлення одиниці виміру з тексту
                full_match = match.group(0)
                unit = full_match.split(value)[1].strip()
                
                parameters[param_name].append({
                    "value": value,
                    "unit": unit,
                    "normalized": normalize_frequency(value, unit)
                })
            else:
                # Для інших параметрів просто зберігаємо значення
                parameters[param_name].append({
                    "value": match.group(1),
                    "raw": match.group(0)
                })
    
    return parameters

def find_blocks_in_text(text):
    """Знаходження блоків GNU Radio, згаданих у тексті"""
    blocks = []
    block_types = set()  # Відстежуємо додані типи блоків
    
    # Перевірка для кожної категорії та типу блока
    for category in GRC_BLOCKS:
        for block_type, block_info in GRC_BLOCKS[category].items():
            for name in block_info["name"]:
                name = name.lower()
                # Перевірка, чи є назва блоку в тексті
                if name in text.lower():
                    if block_type not in block_types:
                        blocks.append({
                            "id": f"{block_type}_{len(blocks)}",
                            "type": block_type,
                            "category": category
                        })
                        block_types.add(block_type)
                        break
    
    # Якщо блоків не знайдено, додаємо базові блоки
    if not blocks:
        blocks = [
            {"id": "rtl_sdr_source_0", "type": "rtl_sdr_source", "category": "source"},
            {"id": "qtgui_freq_sink_0", "type": "qtgui_freq_sink", "category": "sink"}
        ]
    
    return blocks

def create_connections(blocks):
    """Створення з'єднань між блоками"""
    connections = []
    
    # Сортування блоків за категоріями для логічного потоку сигналу
    source_blocks = [b for b in blocks if b["category"] == "source"]
    filter_blocks = [b for b in blocks if b["category"] == "filter"]
    modulation_blocks = [b for b in blocks if b["category"] == "modulation"]
    sink_blocks = [b for b in blocks if b["category"] == "sink"]
    
    # Об'єднуємо всі блоки обробки (не джерела і не виходи)
    processing_blocks = filter_blocks + modulation_blocks
    
    # Починаємо з джерела
    if source_blocks:
        source = source_blocks[0]
        
        # Якщо є блоки обробки, з'єднуємо їх послідовно
        if processing_blocks:
            connections.append({
                "source_block_id": source["id"],
                "sink_block_id": processing_blocks[0]["id"],
                "source_port": 0,
                "sink_port": 0
            })
            
            # З'єднуємо блоки обробки між собою
            for i in range(len(processing_blocks) - 1):
                connections.append({
                    "source_block_id": processing_blocks[i]["id"],
                    "sink_block_id": processing_blocks[i+1]["id"],
                    "source_port": 0,
                    "sink_port": 0
                })
            
            # З'єднуємо останній блок обробки з виходами
            last_proc = processing_blocks[-1]
            for sink in sink_blocks:
                connections.append({
                    "source_block_id": last_proc["id"],
                    "sink_block_id": sink["id"],
                    "source_port": 0,
                    "sink_port": 0
                })
        
        # Якщо немає блоків обробки, з'єднуємо джерело безпосередньо з виходами
        else:
            for sink in sink_blocks:
                connections.append({
                    "source_block_id": source["id"],
                    "sink_block_id": sink["id"],
                    "source_port": 0,
                    "sink_port": 0
                })
    
    return connections

def parse_natural_language(text):
    """Головна функція для обробки природномовного опису"""
    # Витягнення параметрів за допомогою регулярних виразів
    extracted_params = extract_parameters_from_text(text)
    
    # Знаходження блоків GNU Radio, згаданих у тексті
    blocks = find_blocks_in_text(text)
    
    # Аналіз тексту для визначення з'єднань між блоками
    connections = create_connections(blocks)
    
    # Призначення параметрів блокам
    parameters = {}
    for block in blocks:
        block_type = block["type"]
        category = block["category"]
        
        # Додаємо параметри за замовчуванням
        if category in GRC_BLOCKS and block_type in GRC_BLOCKS[category]:
            parameters[block["id"]] = {}
            for param_name, param_info in GRC_BLOCKS[category][block_type]["params"].items():
                parameters[block["id"]][param_name] = param_info["default"]
        
        # Тут можна додати логіку для уточнення параметрів на основі extracted_params
        # Наприклад, якщо виявлено частоту, призначити її відповідному блоку
    
    # Уточнення параметрів блоків на основі витягнутої інформації
    # (Тут має бути складніша логіка для призначення параметрів конкретним блокам)
    
    return {
        "blocks": blocks,
        "connections": connections,
        "parameters": parameters
    }
