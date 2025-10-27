import streamlit as st

import os

# Kevyt salasanasuojaus: aseta salasana ympäristömuuttujaan APP_PASSWORD
APP_PWD = os.getenv("APP_PASSWORD", "")

if APP_PWD:
    pw = st.text_input("Password", type="password", placeholder="Enter password")
    if pw != APP_PWD:
        st.stop()


st.set_page_config(page_title="Asuntosalkku", layout="wide")

st.title("Asuntosalkku")

with st.sidebar:
    st.header("Valikko")
    page = st.radio(
        "Valitse sivu",
        [
            "Etusivu",
            "Tulot ja kulut",
            "Lainanlyhennys",
            "Asunnot ja asuntojen materiaalit",
            "Tuloslaskelmaennuste",
            "Kasvusimulaattori",
        ],
        index=0,
    )

if page == "Etusivu":
    st.subheader("Salkun yhteenveto")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Salkun arvo (€)", "—")
    with col2:
        st.metric("Velat (€)", "—")
    with col3:
        st.metric("Oma pääoma (€)", "—")
    with col4:
        st.metric("LTV", "—")

    st.divider()
    st.write("Tähän lisätään pian: kuukausikassavirta, vuokra-aste, korkokehitys ja viimeisimmät tapahtumat.")

elif page == "Tulot ja kulut":
    st.subheader("Tulot ja kulut -sivu")

elif page == "Lainanlyhennys":
    st.subheader("Lainanlyhennyksen seuranta")

elif page == "Asunnot ja asuntojen materiaalit":
    st.subheader("Asuntolista ja dokumentit")

elif page == "Tuloslaskelmaennuste":
    st.subheader("Tuloslaskelmaennuste")

elif page == "Kasvusimulaattori":
    st.subheader("Kasvusimulaattori")
