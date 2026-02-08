# principale.py - BOT TRADING RSI+EMA Binance Testnet 24/24 su Render
import ccxt
import os
import time
import json
import logging
import pandas as pd
import numpy as np
from threading import Thread
from flask import Flask
import ta

# Setup logging per Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Config
SYMBOL = "BTCUSDT"
ORDER_USDT = 5.0  # Quantità USDT per trade
SLEEP_SECONDS = 60
STATE_FILE = 'trading_state.json'

# NUOVO - Anti-block + continua comunque:
API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")

import ccxt
exchange = ccxt.binance({
    'sandbox': True,
    'options': {'defaultType': 'spot'}
})
logger.info("✅ CCXT Binance Testnet OK")

# Stato globale persistente
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

def calc_quantity(usdt_amount):
    price = get_price()
    qty = round(usdt_amount / price, 6)
    logger.info(f"💰 Qty calcolata: {qty:.6f} BTC per {usdt_amount} USDT @ {price}")
    return qty

def buy_testnet(usdt_amount):
    global holding_btc, bought_price
    try:
        qty = calc_quantity(usdt_amount)
        order = client.create_order(
            symbol=SYMBOL,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quoteOrderQty=str(usdt_amount)  # Più preciso per USDT
        )
        bought_price = get_price()
        holding_btc = True
        save_state()
        logger.info(f"🟢 BUY #{order['orderId']} - {qty:.6f} BTC @ {bought_price:.2f}")
    except Exception as e:
        logger.error(f"❌ Errore BUY: {e}")

def sell_all_btc():
    global holding_btc, bought_price
    try:
        balance = float(client.get_asset_balance(asset='BTC')['free'])
        if balance > 0.0001:
            order = client.create_order(
                symbol=SYMBOL,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=str(balance)
            )
            profit_pct = ((get_price() - bought_price) / bought_price * 100) if bought_price > 0 else 0
            holding_btc = False
            bought_price = 0.0
            save_state()
            logger.info(f"🔴 SELL #{order['orderId']} - {balance:.6f} BTC @ {get_price():.2f} | P&L: {profit_pct:+.2f}%")
        else:
            logger.warning("⚠️ Balance BTC troppo basso per vendere")
    except Exception as e:
        logger.error(f"❌ Errore SELL: {e}")

def get_price():
    ticker = exchange.fetch_ticker('BTC/USDT')
    return ticker['last']

def rsi_ema_signals():
    klines = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=50)
    closes = [k[4] for k in klines]
    price = get_price()
    rsi = simple_rsi(closes)
    ema_fast = ta.trend.EMAIndicator(pd.Series(closes), window=9).ema_indicator().iloc[-1]
    ema_slow

        
                
        ema_fast = ta.trend.EMAIndicator(closes, window=9).ema_indicator().iloc[-1]
        ema_slow = ta.trend.EMAIndicator(closes, window=21).ema_indicator().iloc[-1]
        
        profit_pct = ((price - bought_price) / bought_price * 100) if bought_price > 0 else 0
        
        logger.info(f"📊 {price:.2f}USDT | RSI:{rsi:.1f} | EMA9:{ema_fast:.2f} | EMA21:{ema_slow:.2f} | Hold:{holding_btc} | P&L:{profit_pct:+.2f}%")
        
        # STOP LOSS 5%
        if holding_btc and profit_pct < -5:
            logger.warning("🛑 STOP LOSS attivato!")
            sell_all_btc()
            return
        
        # BUY: RSI oversold + EMA bullish
        if rsi < 40 and ema_fast > ema_slow and not holding_btc:
            logger.info("🟢 SEGNALE BUY!")
            buy_testnet(ORDER_USDT)
        
        # SELL: RSI overbought + EMA bearish O profitto >3%
        elif holding_btc and ( (rsi > 60 and ema_fast < ema_slow) or profit_pct > 3 ):
            logger.info("🔴 SEGNALE SELL!")
            sell_all_btc()
            
    except Exception as e:
        logger.error(f"❌ Errore indicatori: {e}")

@app.route("/")
def index():
    return "🚀 Bot TRADING RSI+EMA - LIVE su Binance Testnet!"

@app.route("/health")
def health():
    return {
        "status": "alive",
        "symbol": SYMBOL,
        "holding": holding_btc,
        "bought_price": bought_price,
        "price": get_price()
    }

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
    time.sleep(2)  # Attendi Flask
    bot_loop()




















