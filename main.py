import os
import time
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET

from keep_alive import keep_alive

# 1) Avvia piccola web app per tenere vivo il Repl
keep_alive()

# 2) Leggi le chiavi API dai Secrets di Replit
API_KEY = os.getenv("XqXdbxb8siH1FfwPmrjiPxexfgUI2cwJPnv8BwnzuhuGt806Zbk5pWy3p9jH6y16")
API_SECRET = os.getenv("ggwsB8Xt0YMVCwPLNwkQHccKRy8ARbvsJQxDi4IH2esMHq3bf7ak9WPjZ3U5h4aD")

if not API_KEY or not API_SECRET:
    raise Exception("Manca BINANCE_API_KEY o BINANCE_API_SECRET nei Secrets di Replit.")

# 3) Crea client Binance in modalità TESTNET Spot
client = Client(API_KEY, API_SECRET, testnet=True)

# 4) Parametri base bot
SYMBOL = "BTCUSDT"
BASE_ORDER_USDT = 5      # quanti USDT usare per trade di test
SLEEP_SECONDS = 30       # ogni quanti secondi controllare

def get_price(symbol: str) -> float:
    """Restituisce il last price del simbolo su testnet."""
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker["price"])

def calc_quantity_usdt(symbol: str, usdt_amount: float) -> float:
    """Calcola approx quantità BTC da comprare con usdt_amount."""
    price = get_price(symbol)
    qty = usdt_amount / price
    # Arrotonda a 6 decimali per stare entro i limiti di molte coppie BTCUSDT
    return float(f"{qty:.6f}")

def buy_market(usdt_amount: float):
    """Ordine market BUY usando un certo ammontare in USDT."""
    qty = calc_quantity_usdt(SYMBOL, usdt_amount)
    print(f"Provo a comprare {qty} BTC ({usdt_amount} USDT) su {SYMBOL} (TESTNET)...")
    order = client.create_order(
        symbol=SYMBOL,
        side=SIDE_BUY,
        type=ORDER_TYPE_MARKET,
        quantity=qty
    )
    print("Ordine BUY eseguito (TESTNET):", order)

def sell_all_btc():
    """Vende TUTTO il BTC disponibile sul wallet spot testnet per questo simbolo."""
    account_info = client.get_account()
    btc_balance = 0.0
    for asset in account_info["balances"]:
        if asset["asset"] == "BTC":
            btc_balance = float(asset["free"])
            break

    if btc_balance <= 0:
        print("Nessun BTC libero da vendere.")
        return

    qty = float(f"{btc_balance:.6f}")
    print(f"Provo a vendere {qty} BTC su {SYMBOL} (TESTNET)...")
    order = client.create_order(
        symbol=SYMBOL,
        side=SIDE_SELL,
        type=ORDER_TYPE_MARKET,
        quantity=qty
    )
    print("Ordine SELL eseguito (TESTNET):", order)

def main_loop():
    """
    Loop base:
    - stampa il prezzo di BTCUSDT su testnet
    - (per ora) solo dimostrativo: se BOT_ON è True fa un ordine di test all'avvio,
      poi si limita a loggare i prezzi.
    """
    BOT_ON = True   # per ora ON fisso; dopo puoi collegarlo a una strategia

    already_bought = False

    while True:
        try:
            price = get_price(SYMBOL)
            print(f"[TESTNET] Prezzo {SYMBOL}: {price} USDT")

            if BOT_ON and not already_bought:
                # Esempio: fai UN solo ordine buy di test all'avvio
                buy_market(BASE_ORDER_USDT)
                already_bought = True

            # Se vuoi testare anche la vendita automatica dopo, ad esempio:
            # if BOT_ON and already_bought:
            #     sell_all_btc()
            #     already_bought = False

        except Exception as e:
            print("Errore nel loop:", e)

        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    print("Bot Binance TESTNET avviato su Replit.")
    main_loop()
