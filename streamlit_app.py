# streamlit_app.py
import streamlit as st
from utils.parser import parse_natural_language
from utils.generator import generate_grc_xml

# Налаштування сторінки
st.set_page_config(
    page_title="Конвертер природної мови в GRC",
    page_icon="📻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ініціалізація стану сесії
if 'parsed_data' not in st.session_state:
    st.session_state['parsed_data'] = None
if 'grc_xml' not in st.session_state:
    st.session_state['grc_xml'] = None

# Функція для обробки введення користувача
def process_input(text_input):
    # Обробка тексту
    with st.spinner("Аналізую ваш запит..."):
        try:
            # Аналіз природної мови
            parsed_data = parse_natural_language(text_input)
            st.session_state['parsed_data'] = parsed_data
            
            # Генерація GRC XML
            grc_xml = generate_grc_xml(parsed_data)
            st.session_state['grc_xml'] = grc_xml
            
            return True
        except Exception as e:
            st.error(f"Виникла помилка під час обробки: {str(e)}")
            return False

# Головний інтерфейс
def main():
    st.title("Конвертер природної мови в GRC потокові графіки")
    
    # Бічна панель з інформацією
    with st.sidebar:
        st.header("Про додаток")
        st.info("""
        Цей додаток перетворює описи, написані природною мовою, у потокові графіки GNU Radio Companion (.grc формат).
        
        Просто опишіть, що ви хочете створити, і система згенерує повний GRC файл для вас.
        """)
        
        st.header("Приклади")
        st.markdown("""
        Спробуйте ці приклади:
        1. "Створи FM-радіоприймач на 100 МГц з шириною смуги 200 кГц"
        2. "Побудуй аналізатор спектру для сканування діапазону 430-440 МГц"
        3. "Зроби GSM детектор сигналів із записом у файл"
        """)
    
    # Поле введення для природномовного опису
    text_input = st.text_area(
        "Опишіть потоковий графік, який ви хочете створити:", 
        height=100,
        placeholder="Наприклад: Створи FM-радіоприймач на 100 МГц з аудіовиходом та відображенням спектру"
    )
    
    # Обробка введення
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Згенерувати потоковий графік", type="primary"):
            if text_input:
                success = process_input(text_input)
                if success:
                    st.success("Потоковий графік успішно згенеровано!")
            else:
                st.warning("Будь ласка, введіть опис потокового графіку.")
    
    with col2:
        if st.button("Завантажити приклад", type="secondary"):
            examples = [
                "Створи FM-радіоприймач на 100 МГц з шириною смуги 200 кГц та аудіовиходом",
                "Побудуй аналізатор спектру для сканування діапазону 430-440 МГц",
                "Налаштуй військовий детектор сигналів із записом у файл detected_signals.dat"
            ]
            import random
            selected_example = random.choice(examples)
            st.session_state['example_text'] = selected_example
            st.experimental_rerun()
    
    # Якщо є оброблені дані, показуємо результати
    if 'parsed_data' in st.session_state and st.session_state['parsed_data']:
        parsed_data = st.session_state['parsed_data']
        
        # Показуємо виявлені блоки
        st.subheader("Виявлені блоки")
        cols = st.columns(3)
        for i, block in enumerate(parsed_data["blocks"]):
            with cols[i % 3]:
                st.markdown(f"**{block['type']}** (`{block['id']}`)")
                
                # Показуємо параметри для цього блоку
                if block["id"] in parsed_data["parameters"]:
                    params = parsed_data["parameters"][block["id"]]
                    for param_name, param_value in params.items():
                        st.caption(f"- {param_name}: {param_value}")
        
        # Показуємо з'єднання
        st.subheader("З'єднання сигнальних потоків")
        for conn in parsed_data["connections"]:
            source_block = next((b for b in parsed_data["blocks"] if b["id"] == conn["source_block_id"]), None)
            sink_block = next((b for b in parsed_data["blocks"] if b["id"] == conn["sink_block_id"]), None)
            
            if source_block and sink_block:
                st.write(f"`{source_block['type']}` → `{sink_block['type']}`")
        
        # Показуємо згенерований XML
        if 'grc_xml' in st.session_state and st.session_state['grc_xml']:
            st.subheader("Згенерований GRC файл")
            with st.expander("Переглянути GRC XML"):
                st.code(st.session_state['grc_xml'], language="xml")
            
            # Кнопка завантаження для XML-файлу
            st.download_button(
                label="Завантажити GRC файл",
                data=st.session_state['grc_xml'],
                file_name="generated_flowgraph.grc",
                mime="application/xml"
            )

if __name__ == "__main__":
    main()
