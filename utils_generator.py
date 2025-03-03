# utils/generator.py
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

def calculate_block_positions(blocks):
    """Розрахунок позицій блоків у потоковому графіку"""
    positions = {}
    
    # Групування блоків за категоріями
    categories = {"source": [], "filter": [], "modulation": [], "sink": []}
    
    for block in blocks:
        category = block["category"]
        if category in categories:
            categories[category].append(block)
    
    # Розміщення блоків у стовпцях за категоріями
    x_pos = 100
    for category in ["source", "filter", "modulation", "sink"]:
        y_pos = 100
        for block in categories[category]:
            positions[block["id"]] = {"x": x_pos, "y": y_pos}
            y_pos += 150
        x_pos += 300  # Перехід до наступного стовпця
    
    return positions

def generate_grc_xml(parsed_data):
    """Генерація XML-файлу GRC з проаналізованих даних"""
    # Створення кореневого елементу
    root = ET.Element("flow_graph")
    
    # Додавання блоку options
    options = ET.SubElement(root, "block")
    ET.SubElement(options, "key").text = "options"
    ET.SubElement(options, "id").text = "options"
    
    # Додавання параметрів options
    param = ET.SubElement(options, "param")
    ET.SubElement(param, "key").text = "title"
    ET.SubElement(param, "value").text = "Згенерований потоковий графік"
    
    param = ET.SubElement(options, "param")
    ET.SubElement(param, "key").text = "author"
    ET.SubElement(param, "value").text = "NLP-to-GRC Converter"
    
    param = ET.SubElement(options, "param")
    ET.SubElement(param, "key").text = "description"
    ET.SubElement(param, "value").text = "Згенеровано з природомовного опису"
    
    param = ET.SubElement(options, "param")
    ET.SubElement(param, "key").text = "generate_options"
    ET.SubElement(param, "value").text = "qt_gui"
    
    # Додавання змінної samp_rate (частота дискретизації)
    var_block = ET.SubElement(root, "block")
    ET.SubElement(var_block, "key").text = "variable"
    ET.SubElement(var_block, "id").text = "samp_rate"
    
    param = ET.SubElement(var_block, "param")
    ET.SubElement(param, "key").text = "value"
    ET.SubElement(param, "value").text = "2e6"
    
    coord = ET.SubElement(var_block, "coord")
    ET.SubElement(coord, "x").text = "10"
    ET.SubElement(coord, "y").text = "10"
    
    # Розрахунок позицій блоків для візуально чистого розташування
    positions = calculate_block_positions(parsed_data["blocks"])
    
    # Додавання всіх блоків
    for block in parsed_data["blocks"]:
        block_xml = ET.SubElement(root, "block")
        ET.SubElement(block_xml, "key").text = block["type"]
        ET.SubElement(block_xml, "id").text = block["id"]
        
        # Додавання параметрів блоку
        for param_name, param_value in parsed_data["parameters"].get(block["id"], {}).items():
            param = ET.SubElement(block_xml, "param")
            ET.SubElement(param, "key").text = param_name
            ET.SubElement(param, "value").text = str(param_value)
        
        # Додавання позиції блоку
        coord = ET.SubElement(block_xml, "coord")
        ET.SubElement(coord, "x").text = str(positions[block["id"]]["x"])
        ET.SubElement(coord, "y").text = str(positions[block["id"]]["y"])
    
    # Додавання з'єднань
    for conn in parsed_data["connections"]:
        connection = ET.SubElement(root, "connection")
        ET.SubElement(connection, "source_block_id").text = conn["source_block_id"]
        ET.SubElement(connection, "sink_block_id").text = conn["sink_block_id"]
        ET.SubElement(connection, "source_key").text = str(conn["source_port"])
        ET.SubElement(connection, "sink_key").text = str(conn["sink_port"])
    
    # Перетворення на XML з форматуванням
    xml_str = ET.tostring(root, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    return pretty_xml
