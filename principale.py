import os
import time
import json
import numpy as np
from threading import Thread
from flask import Flask
import ccxt
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Config
SYMBOL = "BTCUSDT"
ORDER_USDT = 5.0
SLEEP_SECONDS = 60
STATE_FILE = 'trading_state.json'

# Binance Testnet CCXT
exchange = ccxt.binance({
    'apiKey': os.getenv("BINANCE_API_KEY", ""),
    'secret': os.getenv("BINANCE_API_SECRET", ""),
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})
exchange.set_sandbox_mode(True)
logger.info("✅ CCXT Binance Testnet configurato")

# Stato globale
holding_btc = False
bought_price = 0.0

def load_state():
    global holding_btc, bought_price
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                holding_btc = state.get('holding', False)
                bought_price = state.get('bought_price', 0.0)
            logger.info(f"📂 Stato caricato: holding={holding_btc}, price={bought_price}")
    except Exception as e:
        logger.warning(f"⚠️ Errore caricamento stato: {e}")

def save_state():
    state = {'holding': holding_btc, 'bought_price': bought_price}
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
        logger.info("💾 Stato salvato")
    except Exception as e:
        logger.error(f"❌ Errore salvataggio stato: {e}")

def get_price():
    ticker = exchange.fetch_ticker('BTC/USDT')
    return ticker['last']

def simple_rsi(prices, period=14):
    """Calcola RSI senza pandas"""
    prices = np.array(prices)
    deltas = np.diff(prices)
    gain = np.where(deltas > 0, deltas, 0)
    loss = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def simple_ema(prices, period):
    """Calcola EMA senza pandas"""
    prices = np.array(prices)
    ema = np.zeros_like(prices)
    ema[0] = prices[0]
    multiplier = 2 / (period + 1)
    
    for i in range(1, len(prices)):
        ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
    
    return ema[-1]

def buy_testnet(usdt_amount):
    global holding_btc, bought_price
    try:
        order = exchange.create_market_buy_order('BTC/USDT', None, {'quoteOrderQty': usdt_amount})
        bought_price = get_price()
        holding_btc = True
        save_state()
        logger.info(f"🟢 BUY - Order ID: {order['id']} @ {bought_price:.2f} USDT")
    except Exception as e:
        logger.error(f"❌ Errore BUY: {e}")

def sell_all_btc():
    global holding_btc, bought_price
    try:
        balance = exchange.fetch_balance()
        btc_free = balance['BTC']['free']
        
        if btc_free > 0.00001:
            order = exchange.create_market_sell_order('BTC/USDT', btc_free)
            current_price = get_price()
            profit_pct = ((current_price - bought_price) / bought_price * 100) if bought_price > 0 else 0
            holding_btc = False
            bought_price = 0.0
            save_state()
            logger.info(f"🔴 SELL - Order ID: {order['id']} @ {current_price:.2f} | P&L: {profit_pct:+.2f}%")
        else:
            logger.warning("⚠️ Balance BTC troppo basso per vendere")
    except Exception as e:
        logger.error(f"❌ Errore SELL: {e}")

def rsi_ema_signals():
    try:
        klines = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=50)
        closes = [k[4] for k in klines]
        price = get_price()
        
        rsi = simple_rsi(closes)
        ema_fast = simple_ema(closes, 9)
        ema_slow = simple_ema(closes, 21)
        
        profit_pct = ((price - bought_price) / bought_price * 100) if bought_price > 0 else 0
        
        logger.info(f"📊 {price:.2f} USDT | RSI:{rsi:.1f} | EMA9:{ema_fast:.2f} | EMA21:{ema_slow:.2f} | Hold:{holding_btc} | P&L:{profit_pct:+.2f}%")
        
        if holding_btc and profit_pct < -5:
            logger.warning("🛑 STOP LOSS attivato!")
            sell_all_btc()
            return
        
        if rsi < 40 and ema_fast > ema_slow and not holding_btc:
            logger.info("🟢 SEGNALE BUY!")
            buy_testnet(ORDER_USDT)
        
        elif holding_btc and ((rsi > 60 and ema_fast < ema_slow) or profit_pct > 3):
            logger.info("🔴 SEGNALE SELL!")
            sell_all_btc()
            
    except Exception as e:
        logger.error(f"❌ Errore indicatori: {e}")

@app.route("/")
def index():
    return "🚀 Bot TRADING RSI+EMA - LIVE su Binance Testnet!"

@app.route("/health")
def health():
    try:
        price = get_price()
        return {
            "status": "alive",
            "symbol": SYMBOL,
            "holding": holding_btc,
            "bought_price": bought_price,
            "current_price": price
        }
    except:
        return {"status": "error"}, 500

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

def bot_loop():
    logger.info("🚀 Bot TRADING H24 - RSI+EMA su TESTNET!")
    load_state()
    
    while True:
        try:
            rsi_ema_signals()
            time.sleep(SLEEP_SECONDS)
        except KeyboardInterrupt:
            logger.info("⏹️ Bot fermato dall'utente")
            save_state()
            break
        except Exception as e:
            logger.error(f"❌ Errore loop: {e}")
            time.sleep(30)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)
    bot_loop()

























