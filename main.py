import os
import time
from threading import Thread
from flask import Flask

from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot Binance TESTNET attivo su Render!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Chiavi API da Environment Variables di Render
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

if not API_KEY or not API_SECRET:
    print("ERRORE: Manca BINANCE_API_KEY o BINANCE_API_SECRET su Render!")
    raise Exception("API keys mancanti")

# Client Binance TESTNET Spot
client = Client(API_KEY, API_SECRET, testnet=True)

SYMBOL = "BTCUSDT"
BASE_ORDER_USDT = 5.0
SLEEP_SECONDS = 30

def get_price(symbol):
    """Prezzo corrente BTCUSDT su testnet."""
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker["price"])

def calc_quantity(symbol, usdt_amount):
    """Calcola quantità BTC da comprare con USDT."""
    price = get_price(symbol)
    qty = usdt_amount / price
    return round(qty, 6)

def buy_testnet(usdt_amount):
    """Esegue ordine BUY market su testnet."""
    qty = calc_quantity(SYMBOL, usdt_amount)
    print(f"🟢 BUY TESTNET: {qty} BTC (~{usdt_amount}$ USDT) su {SYMBOL}")
    order = client.create_order(
        symbol=SYMBOL,
        side=SIDE_BUY,
        type=ORDER_TYPE_MARKET,
        quantity=str(qty)
    )
    print("✅ Ordine BUY completato:", order["orderId"])

def bot_loop():
    """Loop principale del bot."""
    print("🚀 Bot avviato - monitoro BTCUSDT testnet...")
    already_bought = False
    
    while True:
        try:
            price = get_price(SYMBOL)
            print(f"📈 [{SYMBOL}] {price:.2f} USDT")
            
            if not already_bought:
                buy_testnet(BASE_ORDER_USDT)
                already_bought = True
            
        except Exception as e:
            print(f"❌ Errore: {e}")
        
        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    print("Inizializzo bot...")
    
    # Thread Flask per tenere sveglio Render
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Loop principale bot
    bot_loop()
