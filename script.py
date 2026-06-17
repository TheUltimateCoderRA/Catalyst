from supabase import create_client, Client
import yfinance as yf


url: str = "https://nrzccincmeotobbzhlwo.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5yemNjaW5jbWVvdG9iYnpobHdvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE3MDQwODgsImV4cCI6MjA5NzI4MDA4OH0.JZKARqEQeVxzuDeEAgQ0dpqyrkRE7mBzrFEBx2mhsIc"

supabase: Client = create_client(url, key)


# ---------------- AUTH ----------------
def signup(userID, name, password):
    data = {
        "user_id": userID,
        "name": name,
        "password": password,
        "stocks": []   # initialize empty list so it's never None
    }
    return supabase.table("users").insert(data).execute()

def login(userID, password):
    response = supabase.table("users").select("user_id").eq("user_id", userID).execute()
    if not response.data:
        return "Account does not exist"
    else:
        response = supabase.table("users").select("password").eq("user_id", userID).execute()
        passwordDB = response.data[0]["password"]
        if password == passwordDB:
            return "Logged in successfully", userID
        else:
            return "Incorrect Password"

# ---------------- STOCKS ----------------
def addStock(ticker, price, quantity, dateOfBuy, userID):
    # Ensure date is stored as string
    date_str = dateOfBuy if isinstance(dateOfBuy, str) else dateOfBuy.isoformat()

    response = supabase.table("users").select("stocks").eq("user_id", userID).execute()
    currentStocks = response.data[0]["stocks"] if response.data else []

    if currentStocks is None:
        currentStocks = []

    # Append as list: [buyPrice, quantity, dateString]
    currentStocks.append({
        "ticker": ticker,
        "info": [float(price), int(quantity), date_str]
    })

    return supabase.table("users").update({"stocks": currentStocks}).eq("user_id", userID).execute()

def getStocks(userID):
    response = supabase.table("users").select("stocks").eq("user_id", userID).execute()
    stocks = response.data[0]["stocks"] if response.data else []
    if stocks is None:
        stocks = []
    return stocks   # return full stock objects, not just tickers

def removeStock(ticker, userID):
    response = supabase.table("users").select("stocks").eq("user_id", userID).execute()
    stocks = response.data[0]["stocks"] if response.data else []
    if stocks is None:
        stocks = []
    updated = [s for s in stocks if s["ticker"] != ticker]
    return supabase.table("users").update({"stocks": updated}).eq("user_id", userID).execute()

# ---------------- YFINANCE HELPERS ----------------
def getPrice(ticker):
    stock = yf.Ticker(ticker)
    return stock.info.get("currentPrice")

def getStockName(s):
    # s is a stock dict from Supabase
    return s["ticker"]

def getStockData(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "name": info.get("shortName"),
        "sector": info.get("sector"),
        "marketCap": info.get("marketCap"),
        "currentPrice": info.get("currentPrice"),
        "previousClose": info.get("previousClose"),
        "open": info.get("open"),
        "dayHigh": info.get("dayHigh"),
        "dayLow": info.get("dayLow"),
        "volume": info.get("volume"),
    }
