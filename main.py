import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from script import *

st.title("Catalyst")
st.caption("in beta")

# Session state setup
if "deactivatedStocks" not in st.session_state:
    st.session_state["deactivatedStocks"] = []

pages = ["Login/Signup", "My Stocks", "Stock Dashboard"]
pageCurrent = st.sidebar.radio("Page", pages)

# ---------------- LOGIN / SIGNUP ----------------
if pageCurrent == "Login/Signup":
    login_tab, signup_tab = st.tabs(["Login", "Signup"])
    with login_tab:
        with st.form("Login"):
            userID = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                response = login(userID, password)
                st.session_state["userID"] = userID
                st.info(response)

    with signup_tab:
        with st.form("Signup"):
            name = st.text_input("Name")
            userID = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Signup")
            if submitted:
                signup(userID, name, password)
                st.session_state["userID"] = userID
                st.info("Signup Successful")

# ---------------- MY STOCKS ----------------
elif pageCurrent == "My Stocks":
    if "userID" not in st.session_state:
        st.error("Sign Up Rascal")
    else:
        st.success(f"Welcome {st.session_state['userID']}")

        # Add stock form
        with st.form("Add Stock"):
            st.header("Stock Details")
            ticker = st.text_input("Ticker")
            price = st.number_input("Price (as of buy)", min_value=0.0)
            quantity = st.number_input("Quantity", min_value=1)
            dateOfBuy = st.date_input("Date of Buy")

            submitted = st.form_submit_button("Add")
            if submitted:
                # Convert to ISO string
                date_str = dateOfBuy.isoformat()  # "YYYY-MM-DD"
                addStock(ticker, price, quantity, date_str, st.session_state['userID'])

        stocks = getStocks(st.session_state["userID"])

        st.subheader("Active Stocks")
        for s in stocks:
            with st.container(border=True):
                st.header(getStockName(s))
                st.write(f"Buy Price: {s['info'][0]}")
                st.write(f"Quantity: {s['info'][1]}")
                st.write(f"Date of Buy: {s['info'][2]}")

                if st.button(f"Remove {s['ticker']}"):
                    removeStock(s)

                if st.button(f"Sell {s['ticker']}"):
                    # Freeze current price at sell time
                    s["soldPrice"] = getPrice(s["ticker"])
                    st.session_state["deactivatedStocks"].append(s)
                    stocks.remove(s)

        # Show sold stocks
        if st.session_state["deactivatedStocks"]:
            st.subheader("Sold Stocks")
            for ds in st.session_state["deactivatedStocks"]:
                profitTotal = (ds["soldPrice"] - ds["info"][0]) * ds["info"][1]
                with st.expander(f"{getStockName(ds)} ({ds['ticker']}) - SOLD"):
                    st.write(f"Buy Price: {ds['info'][0]}")
                    st.write(f"Quantity: {ds['info'][1]}")
                    st.write(f"Date of Buy: {ds['info'][2]}")
                    st.write(f"Sold Price: {ds['soldPrice']}")
                    st.write(f"Realized Profit: {profitTotal:.2f}")

# ---------------- STOCK DASHBOARD ----------------
elif pageCurrent == "Stock Dashboard":
    if "userID" not in st.session_state:
        st.error("Sign Up Rascal")
    else:
        st.success(f"Welcome {st.session_state['userID']}")
        portfolio_tab, stocks_tab = st.tabs(["Portfolio", "Stocks"])

        # ---- Portfolio Tab ----
        with portfolio_tab:
            stocks = getStocks(st.session_state["userID"])

            rows = []
            total_invested_all = 0
            total_earned_all = 0

            for s in stocks:
                name = getStockName(s)
                valueBuy = s["info"][0]
                quantity = s["info"][1]
                dateBuy = s["info"][2]

                valueCurrent = getPrice(s["ticker"])
                totalInvested = valueBuy * quantity
                currentValue = valueCurrent * quantity

                profitPerShare = valueCurrent - valueBuy
                profitTotal = profitPerShare * quantity
                growth = ((valueCurrent - valueBuy) / valueBuy) * 100

                total_invested_all += totalInvested
                total_earned_all += currentValue

                rows.append({
                    "Ticker": name,
                    "Buy Price": valueBuy,
                    "Quantity": quantity,
                    "Date of Buy": dateBuy,
                    "Current Price": valueCurrent,
                    "Total Invested": totalInvested,
                    "Profit/Share": profitPerShare,
                    "Profit Total": profitTotal,
                    "Growth %": f"{growth:.2f}%"
                })

            df = pd.DataFrame(rows)
            st.dataframe(df)

            total_growth_all = ((total_earned_all - total_invested_all) / total_invested_all) * 100

            st.markdown("---")
            st.subheader("Portfolio Summary")
            st.write(f"**Total Invested:** {total_invested_all}")
            st.write(f"**Total Current Value (Earned):** {total_earned_all}")
            st.write(f"**Total Growth:** {total_growth_all:.2f}%")

            # Realized profit from sold stocks
            realized_profit = sum((ds["soldPrice"] - ds["info"][0]) * ds["info"][1] for ds in st.session_state["deactivatedStocks"])
            if st.session_state["deactivatedStocks"]:
                st.write(f"**Realized Profit (Sold Stocks):** {realized_profit:.2f}")

            st.markdown("---")
            st.subheader("Visual Analysis")
            st.subheader("Portfolio Allocation (Invested)")
            st.pyplot(df.set_index("Ticker")["Total Invested"].plot.pie(autopct="%1.1f%%").figure)

            st.subheader("Profit/Loss per Stock")
            st.bar_chart(df.set_index("Ticker")["Profit Total"])

            portfolio_history = None
            for s in stocks:
                ticker = s["ticker"]
                quantity = s["info"][1]
                hist = yf.Ticker(ticker).history(period="6mo")["Close"] * quantity
                portfolio_history = hist if portfolio_history is None else portfolio_history.add(hist, fill_value=0)

            st.subheader("Total Portfolio Value Over Time")
            st.line_chart(portfolio_history)

            df_plot = df[["Ticker", "Total Invested"]].copy()
            df_plot["Current Value"] = df["Current Price"] * df["Quantity"]
            st.subheader("Invested vs Current Value")
            st.bar_chart(df_plot.set_index("Ticker"))

            growth_values = df["Growth %"].str.replace("%", "").astype(float)
            st.subheader("Growth Percentage Distribution")
            fig, ax = plt.subplots()
            sns.histplot(growth_values, bins=[-50, -25, -10, 0, 10, 20, 30, 50, 100, 150, 200], ax=ax)
            st.pyplot(fig)

        # ---- Stocks Tab ----
        with stocks_tab:
            for s in stocks:
                ticker = s["ticker"]
                valueBuy = s["info"][0]
                quantity = s["info"][1]
                dateBuy = s["info"][2]

                data = getStockData(ticker)

                with st.expander(f"{data['name']} ({ticker})"):
                    st.write(f"**Buy Price:** {valueBuy}")
                    st.write(f"**Quantity:** {quantity}")
                    st.write(f"**Date of Buy:** {dateBuy}")
                    st.write("---")
                    st.write(f"**Current Price:** {data['currentPrice']}")
                    st.write(f"**Previous Close:** {data['previousClose']}")
                    st.write(f"**Open:** {data['open']}")
                    st.write(f"**Day High/Low:** {data['dayHigh']} / {data['dayLow']}")
                    st.write(f"**Volume:** {data['volume']}")
                    st.write(f"**Sector:** {data['sector']}")
                    st.write(f"**Market Cap:** {data['marketCap']}")
