import os
import time
from threading import Thread
from flask import Flask
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET

app


app = Flask(__name__)

@app.route("/")
def index():
    return "🚀 Bot TRADING RSI+EMA - LIVE!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# API Keys
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
client = Client(API_KEY, API_SECRET, testnet=True)

SYMBOL = "BTCUSDT"
ORDER_USDT = 5.0
SLEEP_SECONDS = 60

holding_btc = False

def get_price():
    return float(client.get_symbol_ticker(symbol=SYMBOL)["price"])

def calc_quantity(usdt_amount):
    return round(usdt_amount / get_price(), 6)

def buy_testnet(usdt_amount):
    global holding_btc
    qty = calc_quantity(usdt_amount)
    print(f"🟢 BUY {qty:.6f} BTC")
    order = client.create_order(symbol=SYMBOL, side=SIDE_BUY, 
                               type=ORDER_TYPE_MARKET, quantity=str(qty))
    print(f"✅ BUY #{order['orderId']}")
    holding_btc = True

def sell_all_btc():
    global holding_btc
    balance = float(client.get_asset_balance(asset='BTC')['free'])
    if balance > 0.0001:
        print(f"🔴 SELL {balance:.6f} BTC")
        order = client.create_order(symbol=SYMBOL, side=SIDE_SELL, 
                                   type=ORDER_TYPE_MARKET, quantity=str(balance))
        print(f"✅ SELL #{order['orderId']}")
        holding_btc = False

def simple_rsi(prices, period=14):
    deltas = np.diff(prices)
    gains = np.mean(deltas[-period:][deltas[-period:] > 0]) if len(deltas) >= period else 0
    losses = abs(np.mean(deltas[-period:][deltas[-period:] < 0])) if len(deltas) >= period else 0
    rs = gains / losses if losses != 0 else 100
    return 100 - (100 / (1 + rs))

def rsi_ema_signals():
    global holding_btc
    klines = client.get_klines(SYMBOL, Client.KLINE_INTERVAL_5MINUTE, limit=50)
    closes = np.array([float(k[4]) for k in klines])
    price = get_price()
    
    rsi = simple_rsi(closes)
    ema_fast = np.mean(closes[-9:])
    ema_slow = np.mean(closes[-21:])
    
    print(f"📊 {price:.2f}USDT | RSI:{rsi:.1f} | EMA9:{ema_fast:.2f} | EMA21:{ema_slow:.2f} | Hold:{holding_btc}")
    
    # BUY: RSI basso + EMA up
    if rsi < 40 and ema_fast > ema_slow and not holding_btc:
        buy_testnet(ORDER_USDT)
    
    # SELL: RSI alto + EMA down
    elif rsi > 60 and ema_fast < ema_slow and holding_btc:
        sell_all_btc()

def bot_loop():
    print("🚀 Bot TRADING H24 - RSI+EMA!")
    while True:
        try:
            rsi_ema_signals()
            time.sleep(SLEEP_SECONDS)
        except Exception as e:
            print(f"❌ {e}")
            time.sleep(30)

if __name__ == "__main__":
    print("🔥 Inizializzo BOT TRADING...")
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    bot_loop()







