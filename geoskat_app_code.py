
import streamlit as st
import pandas as pd

# Настройка страницы в инженерном стиле
st.set_page_config(page_title="Geoskat Catalog Debug", layout="wide")

# Ссылки из твоего ТЕХНИЧЕСКОГО ШАБЛОНА (опубликованные CSV)
DATA_URLS = {
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQD70TnSex3oRI5ZWoJjdXoUdcxRtdeFfT43p-FafqLmHv_1tMAR4E0qDOY5aVrjhI3fLoyT05HTwSe/pub?gid=1091897998&single=true&output=csv",
    "channels": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQD70TnSex3oRI5ZWoJjdXoUdcxRtdeFfT43p-FafqLmHv_1tMAR4E0qDOY5aVrjhI3fLoyT05HTwSe/pub?gid=1965738839&single=true&output=csv",
    "mapping": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQD70TnSex3oRI5ZWoJjdXoUdcxRtdeFfT43p-FafqLmHv_1tMAR4E0qDOY5aVrjhI3fLoyT05HTwSe/pub?gid=1756535560&single=true&output=csv",
    "media": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQD70TnSex3oRI5ZWoJjdXoUdcxRtdeFfT43p-FafqLmHv_1tMAR4E0qDOY5aVrjhI3fLoyT05HTwSe/pub?gid=1510444342&single=true&output=csv"
}

@st.cache_data
def get_all_data():
    data = {}
    for key, url in DATA_URLS.items():
        try:
            data[key] = pd.read_csv(url)
        except Exception as e:
            st.error(f"Ошибка загрузки {key}: {e}")
            data[key] = pd.DataFrame()
    return data

all_data = get_all_data()

# Инициализация состояния навигации
if "page" not in st.session_state:
    st.session_state.page = "catalog"
if "current_item" not in st.session_state:
    st.session_state.current_item = None

# ГЛАВНАЯ СТРАНИЦА (КАТАЛОГ)
if st.session_state.page == "catalog":
    st.title("📂 Реестр оборудования ГЕОСКАТ")
    st.write("---")
    
    df = all_data["products"]
    if not df.empty:
        # Создаем сетку из 3 колонок
        cols = st.columns(3)
        for i, (idx, row) in enumerate(df.iterrows()):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"### {row['model']}")
                    st.caption(row['full_name'])
                    st.write(f"**Габариты:** {row['length_mm']} мм / {row['weight_kg']} кг")
                    
                    if st.button(f"Спецификация {row['model']}", key=f"btn_{row['id_item']}"):
                        st.session_state.current_item = row['id_item']
                        st.session_state.page = "details"
                        st.rerun()
    else:
        st.error("Данные в таблице Products отсутствуют или ссылка неверна.")

# СТРАНИЦА ТОВАРА (ДЕТАЛИ)
elif st.session_state.page == "details":
    item_id = st.session_state.current_item
    products = all_data["products"]
    
    # Поиск данных о конкретном приборе
    prod_row = products[products['id_item'] == item_id].iloc[0]
    
    if st.button("← К списку приборов"):
        st.session_state.page = "catalog"
        st.rerun()

    st.header(f"Промышленный модуль: {prod_row['model']}")
    st.write("---")
    
    tab1, tab2, tab3 = st.tabs(["📊 Тех. Характеристики", "🔗 Измерительные каналы", "🖼 Медиа и Документация"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Полное название:** {prod_row['full_name']}")
            st.write(f"**Длина:** {prod_row['length_mm']} мм")
            st.write(f"**Вес:** {prod_row['weight_kg']} кг")
        with c2:
            st.info(f"**Описание:**\n{prod_row['Bio'] if pd.notna(prod_row['Bio']) else 'Информация в процессе наполнения...'}")

    with tab2:
        st.subheader("Конфигурация измерительных каналов")
        mapping = all_data["mapping"]
        channels = all_data["channels"]
        
        if not mapping.empty and not channels.empty:
            # Ищем привязку каналов для этого id_item
            item_map = mapping[mapping['id_item'] == item_id]
            if not item_map.empty:
                # Извлекаем ID каналов из строки (например "3,8,9")
                try:
                    raw_ids = str(item_map.iloc[0]['id_ch'])
                    ch_ids = [int(x.strip()) for x in raw_ids.split(',') if x.strip().isdigit()]
                    
                    relevant_ch = channels[channels['id_ch'].isin(ch_ids)]
                    if not relevant_ch.empty:
                        st.table(relevant_ch[['name', 'unit', 'range_from', 'range_to', 'accuracy']])
                    else:
                        st.warning("Каналы с указанными ID не найдены в справочнике.")
                except Exception as e:
                    st.error(f"Ошибка парсинга связей: {e}")
            else:
                st.write("Для данного модуля каналы еще не назначены.")
        else:
            st.error("Таблицы Mapping или Channels пусты.")

    with tab3:
        st.subheader("Связанные файлы")
        media = all_data["media"]
        if not media.empty:
            item_media = media[media['id_item'] == item_id]
            if not item_media.empty:
                for _, m in item_media.iterrows():
                    icon = "🖼" if "png" in str(m['file_type']) else "📄"
                    st.write(f"{icon} **{m['description']}**: `{m['file_name']}`")
            else:
                st.write("Медиа-файлы не найдены.")
        else:
            st.write("Справочник Media пуст.")
