import os
import time
import talib  # Aggiungi in requirements.txt
from threading import Thread
from flask import Flask
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET

app = Flask(__name__)

@app.route("/")
def index():
    return "🚀 Bot TRADING ATTIVO - RSI+EMA su BTCUSDT TESTNET!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# API Keys da Render
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
if not API_KEY or not API_SECRET:
    raise Exception("❌ API keys mancanti su Render!")

client = Client(API_KEY, API_SECRET, testnet=True)
SYMBOL = "BTCUSDT"
ORDER_USDT = 5.0
SLEEP_SECONDS = 60  # 1 minuto

holding_btc = False  # Traccia posizione

def get_price():
    ticker = client.get_symbol_ticker(symbol=SYMBOL)
    return float(ticker["price"])

def calc_quantity(usdt_amount):
    price = get_price()
    qty = usdt_amount / price
    return round(qty, 6)

def buy_testnet(usdt_amount):
    global holding_btc
    qty = calc_quantity(usdt_amount)
    print(f"🟢 BUY {qty:.6f} BTC (~{usdt_amount}$)")
    order = client.create_order(
        symbol=SYMBOL, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=str(qty))
    print(f"✅ BUY #{order['orderId']}")
    holding_btc = True

def sell_all_btc():
    global holding_btc
    balance = float(client.get_asset_balance(asset='BTC')['free'])
    if balance > 0.0001:
        print(f"🔴 SELL {balance:.6f} BTC")
        order = client.create_order(
            symbol=SYMBOL, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=str(balance))
        print(f"✅ SELL #{order['orderId']}")
        holding_btc = False

def rsi_ema_signals():
    klines = client.get_klines(SYMBOL, Client.KLINE_INTERVAL_5MINUTE, limit=50)
    closes = [float(k[4]) for k in klines]
    
    rsi = talib.RSI(np.array(closes), timeperiod=14)[-1]
    ema_fast = talib.EMA(np.array(closes), timeperiod=9)[-1]
    ema_slow = talib.EMA(np.array(closes), timeperiod=21)[-1]
    
    price = get_price()
    print(f"📊 Prezzo: {price:.2f} | RSI: {rsi:.1f} | EMA9: {ema_fast:.2f} | EMA21: {ema_slow:.2f}")
    
    # BUY: RSI oversold + EMA crossover up
    if rsi < 35 and ema_fast > ema_slow and not holding_btc:
        buy_testnet(ORDER_USDT)
    
    # SELL: RSI overbought + EMA crossover down
    elif rsi > 65 and ema_fast < ema_slow and holding_btc:
        sell_all_btc()

def bot_loop():
    print("🚀 Bot TRADING avviato!")
    while True:
        try:
            rsi_ema_signals()
            time.sleep(SLEEP_SECONDS)
        except Exception as e:
            print(f"❌ Errore: {e}")
            time.sleep(30)

if __name__ == "__main__":
    print("Inizializzo bot TRADING...")
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot_loop()



