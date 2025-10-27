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
    import numpy as np
    import pandas as pd

    st.subheader("Kasvusimulaattori")

    # --- Ohjaimet ylös (keskitettynä) ---
    with st.container():
        colA, colB, colC, colD = st.columns([1,1,1,1])

        with colA:
            start_year = 2025
            end_year = 2030  # sisällytetään 2025–2030
            years = list(range(start_year, end_year + 1))
            start_loan = st.number_input("Lainan lähtömäärä (€)", min_value=0, value=346_835, step=1_000)

        with colB:
            growth = st.radio("Lainakertoimen valinta", [1.3, 1.4, 1.5, 1.6, 1.7], index=0, horizontal=True)

        with colC:
            rate_annual = st.number_input("Korko (% p.a.)", min_value=0.0, max_value=20.0, value=4.4, step=0.1) / 100.0
            loan_years = st.number_input("Laina-aika (vuotta)", min_value=1, max_value=35, value=25, step=1)

        with colD:
            st.markdown("**Nettovuokratuotto**")
            st.write("15,7 % lainasummasta (lukittu)")
            NOI_pct = 0.157

    st.divider()

    # --- Apukaavat ---
    def annuity_payment(principal, annual_rate, years):
        """Vuosierän annuiteetti (kuukausierä * 12) oletuksella kuukausittainen maksutahti."""
        m = annual_rate / 12.0
        n = years * 12
        if annual_rate == 0:
            return principal / years
        if n == 0:
            return 0.0
        monthly = principal * (m * (1 + m) ** n) / ((1 + m) ** n - 1)
        return monthly * 12.0

    # --- Lainapolku 2025–2030 ---
    loans = []
    cur = float(start_loan)
    for i, y in enumerate(years):
        if i == 0:
            loans.append(cur)
        else:
            cur = cur * growth
            loans.append(cur)

    # --- Kulut (lukitut, kasvavat 1.5x/vuosi) ---
    base_acc = 1000.0
    base_rep = 1500.0
    base_oth = 500.0

    rows_income = []
    rows_debt = []

    for idx, y in enumerate(years):
        loan_y = loans[idx]

        # Nettovuokratuotto (vuositaso)
        noi_y = NOI_pct * loan_y

        # Yleiskulut (kasvavat 1.5x joka vuosi)
        factor = 1.5 ** idx
        acc_y = base_acc * factor
        rep_y = base_rep * factor
        oth_y = base_oth * factor
        opex_y = acc_y + rep_y + oth_y

        # Lainan kustannukset 4.4 %: korko + lyhennys (annuiteettina)
        annual_payment = annuity_payment(loan_y, rate_annual, loan_years)  # erä/vuosi
        interest_y = loan_y * rate_annual                                # arvioitu korko/vuosi
        principal_y = max(annual_payment - interest_y, 0.0)              # lyhennys/vuosi

        # Nettotulos 12 kk
        net_profit = noi_y - opex_y - annual_payment

        rows_income.append({
            "Vuosi": y,
            "Laina (€)": loan_y,
            "NOI 15,7% (€)": noi_y,
            "Kirjanpito+tilinpäätös (€)": acc_y,
            "Korjaukset ja huolto (€)": rep_y,
            "Muut kulut (€)": oth_y,
            "Yleiskulut yhteensä (€)": opex_y,
            "Lainan erä/vuosi (€)": annual_payment,
            "Nettotulos 12 kk (€)": net_profit
        })

        rows_debt.append({
            "Vuosi": y,
            "Laina (€)": loan_y,
            "Korko 4,4% (€)": interest_y,
            "Lyhennys (arvio) (€)": principal_y,
            "Erä/kk (€)": annual_payment / 12.0,
            "Erä/vuosi (€)": annual_payment
        })

    df_income = pd.DataFrame(rows_income)
    df_debt = pd.DataFrame(rows_debt)

    # --- Yläkortit ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Laina 2030", f"{df_income.loc[df_income['Vuosi']==2030, 'Laina (€)'].iloc[0]:,.0f} €".replace(",", " "))
    with c2:
        st.metric("NOI 2030 (15,7%)", f"{df_income.loc[df_income['Vuosi']==2030, 'NOI 15,7% (€)'].iloc[0]:,.0f} €".replace(",", " "))
    with c3:
        st.metric("Yleiskulut 2030", f"{df_income.loc[df_income['Vuosi']==2030, 'Yleiskulut yhteensä (€)'].iloc[0]:,.0f} €".replace(",", " "))
    with c4:
        st.metric("Nettotulos 2030", f"{df_income.loc[df_income['Vuosi']==2030, 'Nettotulos 12 kk (€)'].iloc[0]:,.0f} €".replace(",", " "))

    st.divider()

    # --- Alalayout: vasen = tuloslaskelmaennuste, oikea = kassavirtalaskelma pankkilainalle ---
    left, right = st.columns(2)

    with left:
        st.markdown("### Tuloslaskelmaennuste 12 kk")
        st.dataframe(
            df_income.style.format({
                "Laina (€)": "{:,.0f}".format,
                "NOI 15,7% (€)": "{:,.0f}".format,
                "Kirjanpito+tilinpäätös (€)": "{:,.0f}".format,
                "Korjaukset ja huolto (€)": "{:,.0f}".format,
                "Muut kulut (€)": "{:,.0f}".format,
                "Yleiskulut yhteensä (€)": "{:,.0f}".format,
                "Lainan erä/vuosi (€)": "{:,.0f}".format,
                "Nettotulos 12 kk (€)": "{:,.0f}".format,
            }),
            use_container_width=True
        )

    with right:
        st.markdown("### Kassavirtalaskelma pankkilainalle (laina + korko)")
        st.dataframe(
            df_debt.style.format({
                "Laina (€)": "{:,.0f}".format,
                "Korko 4,4% (€)": "{:,.0f}".format,
                "Lyhennys (arvio) (€)": "{:,.0f}".format,
                "Erä/kk (€)": "{:,.0f}".format,
                "Erä/vuosi (€)": "{:,.0f}".format,
            }),
            use_container_width=True
        )

