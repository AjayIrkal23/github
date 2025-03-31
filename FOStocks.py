import yfinance as yf
import pandas as pd
from tabulate import tabulate

def get_fo_stocks():
    """Returns a predefined list of F&O stocks."""
    return [
        'RELIANCE.NS', 'MARUTI.NS', 'KOTAKBANK.NS', 'INFY.NS', 
        'HDFCBANK.NS', 'TITAN.NS', 'TCS.NS', 'SBIN.NS', 
        'HINDUNILVR.NS', 'LT.NS'
    ]

def get_stock_data(ticker):
    """Fetches average volume and market cap from Yahoo Finance"""
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period='3mo')
        avg_volume = hist['Volume'].mean()
        market_cap = data.info.get('marketCap', 0)
        return avg_volume, market_cap
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None

def filter_stocks():
    """Filters high liquidity stocks based on given criteria"""
    fo_stocks = get_fo_stocks()
    high_liquidity_stocks = []

    for stock in fo_stocks:
        avg_volume, market_cap = get_stock_data(stock)

        # Criteria for high liquidity F&O stocks
        if avg_volume is not None and avg_volume > 1_000_000 and market_cap > 40_000_000_000:
            high_liquidity_stocks.append((stock, f"{avg_volume:,.0f}", f"{market_cap / 1e7:,.2f} Cr"))

    # Display results as a structured list
    if high_liquidity_stocks:
        formatted = f"\n**High Liquidity F&O Stocks:**\n  {"-" * 46}    \n"
        for stock, volume, cap in high_liquidity_stocks:
            formatted += f"- **{stock}**\n"
            formatted += f"- Avg Volume: {volume}\n"
            formatted += f"- Market Cap: {cap}\n"
            formatted += "-" * 46 + "\n"  # Separator line
        return formatted
    else:
        return "No high liquidity F&O stocks found."


if __name__ == "__main__":
    filter_stocks()
