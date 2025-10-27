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

    # ------------------ YLÄRIVI: syötteet ------------------
    colA, colB, colC, colD, colE = st.columns([1.2, 1.2, 1.2, 1.2, 1.6])

    with colA:
        base_loan = st.number_input("Lainan lähtömäärä (€)", min_value=0.0, value=346_835.0, step=1_000.0, format="%.2f")

    with colB:
        growth = st.select_slider("Lainan kasvukerroin", options=[1.3, 1.4, 1.5, 1.6, 1.7], value=1.5)

    with colC:
        year = st.selectbox("Vuosi", [2025, 2026, 2027, 2028, 2029, 2030], index=0)

    with colD:
        interest_pct = st.number_input("Korko (vuosi, %)", min_value=0.0, max_value=20.0, value=4.4, step=0.1, format="%.2f")
        interest = interest_pct / 100.0

    with colE:
        term_years = st.number_input("Laina-aika (vuotta)", min_value=1, max_value=40, value=15, step=1)
        occ_pct = st.slider("Vuokrausaste (%)", min_value=0, max_value=100, value=100, step=1)
        tax_pct = st.slider("Tuloveroprosentti (%)", min_value=0, max_value=40, value=20, step=1)
        osakaslainat_lyh_korko = st.number_input("Lainanlyhennys ja korkokulut (osakaslainat) €/v", min_value=0.0, value=622.50, step=50.0, format="%.2f")

    year_idx = year - 2025  # 0...5
    loan_amount = base_loan * (growth ** year_idx)

    # ------------- Liiketoiminnan kulut, jotka kasvavat 1.5x/v -------------
    # Kirjanpito 1000, Korjaukset 1500, Muut 500 (kasvavat), Procountor 180 (vakio)
    scale = (1.5 ** year_idx)
    kirjanpito = 1000.0 * scale
    korjaukset = 1500.0 * scale
    muut = 500.0 * scale
    procountor = 180.0  # ei kasva

    # Yhtiövastikkeen suhde vuokratuloihin (esimerkkitaulukosta ~33.5 %)
    yv_share = 0.335

    # Tavoite-NOI (vuokrausaste 100 % tapauksessa) on 15.7 % lainasta
    noi_target_full_occ = 0.157 * loan_amount
    occ = occ_pct / 100.0

    # Ratkaistaan vuokra (vuositaso, 100 % käyttöasteessa)
    # Malli: NOI = occ*R - yv_share*R - (kasvavat kulut + procountor)
    other_ops_costs = kirjanpito + korjaukset + muut + procountor

    # varmistus: ettei jakaja mene nollaan (jos käyttäjä tiputtaa occ liian alas)
    denom = max(occ - yv_share, 0.0001)
    rent_gross = (noi_target_full_occ + other_ops_costs) / denom

    # Vuositason erät valitulle vuodelle
    vuokratulot = occ * rent_gross
    yhtiovastikkeet = yv_share * rent_gross  # vastike ei riipu käyttöasteesta (realistisempi)

    liikevoitto = vuokratulot - yhtiovastikkeet - kirjanpito - procountor - korjaukset - muut  # NOI toteutunut

    # ------------- Rahoituskulut (pankkilaina) -------------
    n = term_years * 12
    if interest > 0:
        ann_pmt_m = loan_amount * (interest / 12.0) / (1 - (1 + interest / 12.0) ** (-n))
    else:
        ann_pmt_m = loan_amount / n
    ann_pmt_y = ann_pmt_m * 12.0

    # Ensimmäisen vuoden korko ~ L * korko
    korko_pankkilaina = loan_amount * interest
    lyhennysosuus = ann_pmt_y - korko_pankkilaina
    if lyhennysosuus < 0:
        lyhennysosuus = 0.0

    rahoituskulut_yht = korko_pankkilaina  # osakaslainat käsitellään myöhemmin kassavirrassa

    voitto_ennen_veroja = liikevoitto - rahoituskulut_yht
    tuloverot = max(voitto_ennen_veroja, 0.0) * (tax_pct / 100.0)
    tilikauden_voitto = voitto_ennen_veroja - tuloverot

    # ------------- Kassavirta pankkilainalle -------------
    vapaa_kassavirta = tilikauden_voitto - lyhennysosuus
    vapaa_kassavirta_jaannos = vapaa_kassavirta - osakaslainat_lyh_korko

    # ------------------ OTSIKKO ------------------
    st.markdown(f"### {year} – lainasumma {loan_amount:,.2f} €  |  kerroin {growth}  |  korko {interest_pct:.2f}%  |  laina-aika {term_years} v  |  vuokrausaste {occ_pct}%")

    # ------------------ Vasen: Tuloslaskelmaennuste ------------------
    import pandas as pd

    fmt = lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", " ")

    tl_rows = [
        ("**Liiketoiminnan tulot**", ""),
        ("Vuokratulot", fmt(vuokratulot)),
        ("", ""),
        ("**Liiketoiminnan kulut**", ""),
        ("Yhtiövastikkeet", f"-{fmt(yhtiovastikkeet)}"),
        ("Kirjanpito ja tilinpäätöskulut", f"-{fmt(kirjanpito)}"),
        ("Procountor", f"-{fmt(procountor)}"),
        ("Korjaukset ja huoltokulut", f"-{fmt(korjaukset)}"),
        ("Muut kulut", f"-{fmt(muut)}"),
        ("**Liikevoitto**", fmt(liikevoitto)),
        ("", ""),
        ("**Rahoituskulut**", ""),
        ("Korkokulut pankkilaina", f"-{fmt(korko_pankkilaina)}"),
        ("Rahoituskulut yhteensä", f"-{fmt(rahoituskulut_yht)}"),
        ("", ""),
        ("**Voitto ennen veroja**", fmt(voitto_ennen_veroja)),
        ("Tuloverot", f"-{fmt(tuloverot)}"),
        ("**Tilikauden voitto**", fmt(tilikauden_voitto)),
    ]
    df_tl = pd.DataFrame(tl_rows, columns=["Tuloslaskelmaennuste 12 kk", "€"])

    # ------------------ Oikea: Kassavirtalaskelma ------------------
    kv_rows = [
        ("**Kassavirtalaskelma pankkilainalle, laina ja korkokulu**", ""),
        ("Annuiteettilaina", fmt(loan_amount)),
        (f"Lainanlyhennys + korko {interest_pct:.2f} %", f"{fmt(ann_pmt_m)} / kk"),
        ("Vuosierä", fmt(ann_pmt_y)),
        ("Korkokulut pankkilaina", f"-{fmt(korko_pankkilaina)}"),
        ("Lyhennysosuus", f"-{fmt(lyhennysosuus)}"),
        ("", ""),
        ("Tilikauden voitto", fmt(tilikauden_voitto)),
        ("Lainan lyhennysosuus", f"-{fmt(lyhennysosuus)}"),
        ("**Vapaa kassavirta**", fmt(vapaa_kassavirta)),
        ("Lainanlyhennys ja korkokulut osakaslainat", f"-{fmt(osakaslainat_lyh_korko)}"),
        ("**Vapaa kassavirta jäännös**", fmt(vapaa_kassavirta_jaannos)),
    ]
    df_kv = pd.DataFrame(kv_rows, columns=["Kassavirtalaskelma", "€"])

    left, right = st.columns(2)
    with left:
        st.dataframe(df_tl, use_container_width=True, hide_index=True)
    with right:
        st.dataframe(df_kv, use_container_width=True, hide_index=True)

