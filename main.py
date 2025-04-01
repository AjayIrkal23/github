import yfinance as yf
import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import StochasticOscillator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode  # Add this import
from FOStocks import filter_stocks
from flask import Flask, jsonify


app = Flask(__name__)

# Telegram Bot Token
TOKEN = '7620770060:AAEyIkyGnAJDxTF5kFM5Uiwdyp6yJd3_ocg'

# Debug print function
def debug_print(label, value):
    print(f"[DEBUG] {label}: {value}")

# EMA Calculation
def calculate_ema(data, period):
    """Calculates the Exponential Moving Average (EMA)"""
    try:
        debug_print("Calculating EMA", period)
        ema = EMAIndicator(close=data['Close'], window=period).ema_indicator()
        debug_print(f"EMA{period}", ema.tail())
        return ema
    except Exception as e:
        print(f"Error calculating EMA{period}: {e}")
        return pd.Series([None] * len(data))

# Stochastic Oscillator Calculation
def calculate_stochastic(high, low, close, period=14):
    """Calculates the Stochastic Oscillator"""
    try:
        debug_print("Calculating Stochastic", period)
        stoch = StochasticOscillator(high=high, low=low, close=close, window=period, smooth_window=3)
        debug_print("Stochastic %K", stoch.stoch().tail())
        debug_print("Stochastic %D", stoch.stoch_signal().tail())
        return stoch.stoch(), stoch.stoch_signal()
    except Exception as e:
        print(f"Error calculating stochastic: {e}")
        return pd.Series([0]), pd.Series([0])

# Fetching Stock Data
def get_stock_data(ticker, interval):
    """Fetches stock data from Yahoo Finance"""
    try:
        debug_print("Fetching Data", f"Ticker: {ticker}, Interval: {interval}")
        data = yf.download(ticker, period='6mo', interval=interval)

        # Flatten multi-index if necessary
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in data.columns]
            debug_print("Flattened Columns", data.columns)

        # Adjust column names to remove ticker suffix
        suffix = f"_{ticker}"
        adjusted_columns = {col: col.replace(suffix, "") for col in data.columns}
        data.rename(columns=adjusted_columns, inplace=True)
        debug_print("Adjusted Columns", data.columns)

        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# Finding Oversold/Overbought Stocks
def find_oversold_overbought(ticker, interval):
    """Identifies whether the stock is oversold or overbought"""
    data = get_stock_data(ticker, interval)
    if data is None or data.empty:
        return None

    # Calculate EMAs
    data['EMA20'] = calculate_ema(data, 20)
    data['EMA200'] = calculate_ema(data, 200)

    # Calculate Stochastic Oscillator
    data['%K'], data['%D'] = calculate_stochastic(data['High'], data['Low'], data['Close'])

    # Get the latest data point
    latest = data.iloc[-1]
    debug_print(f"Latest Data for {ticker} | {interval}", latest)

    # Categorize based on conditions
    result = {'ticker': ticker, 'interval': interval, 'ema_status': 'Neutral', 'stoch_status': 'Neutral', 'both_status': 'Neutral'}

    try:
        ema20 = latest['EMA20'] if pd.notna(latest['EMA20']) else 0
        ema200 = latest['EMA200'] if pd.notna(latest['EMA200']) else 0
        stochastic_k = latest['%K'] if pd.notna(latest['%K']) else 0

        if ema20 > ema200:
            result['ema_status'] = 'Overbought'
        elif ema20 < ema200:
            result['ema_status'] = 'Oversold'

        if stochastic_k > 90:
            result['stoch_status'] = 'Overbought'
        elif stochastic_k < 40:
            result['stoch_status'] = 'Oversold'

        if result['ema_status'] == 'Overbought' and result['stoch_status'] == 'Overbought':
            result['both_status'] = 'Overbought'
        elif result['ema_status'] == 'Oversold' and result['stoch_status'] == 'Oversold':
            result['both_status'] = 'Oversold'
    except Exception as e:
        print(f"Error extracting values: {e}")
    return result

def formatted_results():
    tickers = ['RELIANCE.NS', 'MARUTI.NS', 'KOTAKBANK.NS', 'INFY.NS', 'HDFCBANK.NS', 'TITAN.NS', 'TCS.NS', 'SBIN.NS', 'HINDUNILVR.NS', 'LT.NS']
    intervals = ['4h', '1d']
    results = {interval: {'EMA Overbought': [], 'Stoch Overbought': [], 'Both Overbought': [], 
                          'EMA Oversold': [], 'Stoch Oversold': [], 'Both Oversold': []} for interval in intervals}
    for ticker in tickers:
        for interval in intervals:
            result = find_oversold_overbought(ticker, interval)
            if result:
                if result['ema_status'] == 'Overbought':
                    results[interval]['EMA Overbought'].append(ticker)
                elif result['ema_status'] == 'Oversold':
                    results[interval]['EMA Oversold'].append(ticker)

                if result['stoch_status'] == 'Overbought':
                    results[interval]['Stoch Overbought'].append(ticker)
                elif result['stoch_status'] == 'Oversold':
                    results[interval]['Stoch Oversold'].append(ticker)

                if result['both_status'] == 'Overbought':
                    results[interval]['Both Overbought'].append(ticker)
                elif result['both_status'] == 'Oversold':
                    results[interval]['Both Oversold'].append(ticker)

    formatted = ""
    for interval in intervals:
        formatted += f"--- {interval.upper()} Results ---\n\n"
        for category, stocks in results[interval].items():
            formatted += f"**{category}:**\n"
            if stocks:
                for stock in stocks:
                    formatted += f"- {stock}\n"
            else:
                formatted += "- None\n"
            formatted += "\n"  # Add a line break between each section
        formatted += "\n"  # Add extra spacing between intervals
    return formatted



# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("OverBS Screener", callback_data='screen')],
        [InlineKeyboardButton("High Liq F&O", callback_data='high_liq')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to the Stock Screener Bot!", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'screen':
        result = formatted_results()
        await query.edit_message_text(text=result, parse_mode=ParseMode.MARKDOWN)
    elif query.data == 'high_liq':
        result = filter_stocks()
        await query.edit_message_text(text=result, parse_mode=ParseMode.MARKDOWN)
        

# Main Function
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

