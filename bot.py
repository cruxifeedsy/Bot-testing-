import asyncio
import requests
import time
import random
from datetime import datetime, date
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from telegram import Bot

# ===== CONFIG =====
BOT_TOKEN = "8099486001:AAHeA5vquwefKsegpTwXhf74CYhzxsx1zqQ"
CHANNEL_ID = "@cruxitesting"

PRIMARY_API = "https://api.exchangerate.host/timeseries"
BACKUP_API = "https://open.er-api.com/v6/latest/USD"

WARNING_IMG = "https://i.postimg.cc/Y9zbMWG1/file-000000009af871f49d98a41cd04221cb.png"
BUY_IMG = "https://i.postimg.cc/3x984LsS/buy.png"
SELL_IMG = "https://i.postimg.cc/jqzrngNB/sell.png"

AUDIO_WARNING = "https://raw.github.com/cruxifeedsy/ai-voice-/main/ttsmaker-file-2026-2-10-6-58-53.mp3"

PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]

MAX_TRADES_PER_DAY = 5
MARKET_SCAN_SECONDS = 180  # every 3 minutes
EXPIRATION_OPTIONS = [2, 3, 5]  # minutes

trade_count = 0
current_day = date.today()

bot = Bot(token=BOT_TOKEN)

# ===== ACTIVE HOURS =====
def market_open():
    hour = datetime.utcnow().hour
    return 6 <= hour <= 20  # 6AM–8PM

# ===== MARKET DATA =====
def get_market_data(pair):
    base = pair[:3]
    quote = pair[3:]

    try:
        url = f"{PRIMARY_API}?base={base}&symbols={quote}&start_date=2024-01-01&end_date=2024-12-31"
        r = requests.get(url, timeout=10).json()

        prices = list(r["rates"].values())[-250:]
        closes = [list(p.values())[0] for p in prices]
        return pd.DataFrame({"close": closes})

    except:
        try:
            r = requests.get(BACKUP_API, timeout=10).json()
            base_price = r["rates"].get(quote)
            closes = [base_price] * 250
            return pd.DataFrame({"close": closes})
        except:
            return None

# ===== STRONG SIGNAL ENGINE =====
def analyze_signal(df):
    if df is None or len(df) < 60:
        return None, 0, None

    df["rsi"] = RSIIndicator(df["close"], window=14).rsi()
    df["ema9"] = EMAIndicator(df["close"], window=9).ema_indicator()
    df["ema21"] = EMAIndicator(df["close"], window=21).ema_indicator()

    macd = MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    direction = None
    reasons = []

    # Trend filter
    if abs(latest["ema9"] - latest["ema21"]) < 0.00005:
        return None, 0, None

    # EMA Cross
    if latest["ema9"] > latest["ema21"] and prev["ema9"] <= prev["ema21"]:
        direction = "BUY"
        score += 40
        reasons.append("EMA bullish cross")

    if latest["ema9"] < latest["ema21"] and prev["ema9"] >= prev["ema21"]:
        direction = "SELL"
        score += 40
        reasons.append("EMA bearish cross")

    if not direction:
        return None, 0, None

    # RSI
    if direction == "BUY" and latest["rsi"] < 50:
        score += 20
        reasons.append("RSI recovery")

    if direction == "SELL" and latest["rsi"] > 50:
        score += 20
        reasons.append("RSI rejection")

    # MACD
    if direction == "BUY" and latest["macd"] > latest["macd_signal"]:
        score += 20
        reasons.append("MACD bullish")

    if direction == "SELL" and latest["macd"] < latest["macd_signal"]:
        score += 20
        reasons.append("MACD bearish")

    return direction, score, ", ".join(reasons)

# ===== WARNING =====
async def send_warning(pair):
    await bot.send_audio(chat_id=CHANNEL_ID, audio=AUDIO_WARNING)
    await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=WARNING_IMG,
        caption=f"⚠️ STRONG SIGNAL\n\n💱 Pair: {pair}\n⏳ Entry in 60 seconds..."
    )

# ===== SEND SIGNAL =====
async def send_signal(pair, direction, score, reasons):
    global trade_count

    if trade_count >= MAX_TRADES_PER_DAY:
        return

    img = BUY_IMG if direction == "BUY" else SELL_IMG
    expiration = random.choice(EXPIRATION_OPTIONS)

    caption = f"""
🚨 HIGH-CONFIDENCE TRADE

💱 Pair: {pair}
📈 Direction: {direction}
🎯 Confidence: {score}%

⌛ Expiration: {expiration} MIN

🧠 Strategy:
{reasons}

🔥 Institutional Signal Engine
"""

    await bot.send_photo(chat_id=CHANNEL_ID, photo=img, caption=caption)

    trade_count += 1

# ===== MAIN LOOP =====
async def main_loop():
    global trade_count, current_day

    while True:
        try:
            if date.today() != current_day:
                trade_count = 0
                current_day = date.today()

            if not market_open():
                await asyncio.sleep(300)
                continue

            for pair in PAIRS:
                df = get_market_data(pair)
                direction, score, reasons = analyze_signal(df)

                if direction and score >= 85:
                    await send_warning(pair)
                    await asyncio.sleep(60)
                    await send_signal(pair, direction, score, reasons)

                await asyncio.sleep(2)

            await asyncio.sleep(MARKET_SCAN_SECONDS)

        except Exception as e:
            print("ERROR:", e)
            await asyncio.sleep(10)

# ===== START =====
if __name__ == "__main__":
    print("🚀 TELEGRAM FOREX BOT LIVE")
    asyncio.run(main_loop())