import asyncio
import random
import time
from datetime import datetime, date
from telegram import Bot

# ===== CONFIG =====
BOT_TOKEN = "8099486001:AAGsySaCPmjE-HYx-yayraxPf-lueM-jC5E"
CHANNEL_ID = "@cruxitesting

WARNING_IMG = "https://i.postimg.cc/Y9zbMWG1/file-000000009af871f49d98a41cd04221cb.png"
BUY_IMG = "https://i.postimg.cc/3x984LsS/buy.png"
SELL_IMG = "https://i.postimg.cc/jqzrngNB/sell.png"

AUDIO_WARNING = "https://raw.github.com/cruxifeedsy/ai-voice-/main/ttsmaker-file-2026-2-10-6-58-53.mp3"

PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"]
EXPIRATION_OPTIONS = [2, 3, 5]

MIN_TRADES_PER_DAY = 30
MAX_TRADES_PER_DAY = 80

trade_count = 0
current_day = date.today()
BOT_START_TIME = time.time()

bot = Bot(token=BOT_TOKEN)

# ===== ACTIVE HOURS =====
def market_open():
    hour = datetime.utcnow().hour
    return 6 <= hour <= 20  # 6AM–8PM UTC

# ===== RANDOM SIGNAL ENGINE =====
def generate_random_signal():
    pair = random.choice(PAIRS)
    direction = random.choice(["BUY", "SELL"])
    score = random.randint(70, 95)
    expiration = random.choice(EXPIRATION_OPTIONS)

    reasons_list = [
        "Momentum breakout",
        "Liquidity sweep detected",
        "Institutional order flow",
        "EMA trend continuation",
        "RSI reversal zone",
        "MACD impulse",
        "Smart money activity",
        "Price rejection level",
        "High volatility breakout"
    ]

    reasons = ", ".join(random.sample(reasons_list, k=2))

    return pair, direction, score, expiration, reasons

# ===== WARNING =====
async def send_warning(pair):
    await bot.send_audio(chat_id=CHANNEL_ID, audio=AUDIO_WARNING)
    await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=WARNING_IMG,
        caption=f"⚠️ STRONG SIGNAL DETECTED\n\n💱 Pair: {pair}\n⏳ Entry in 60 seconds..."
    )

# ===== SEND SIGNAL =====
async def send_signal():
    global trade_count

    if trade_count >= MAX_TRADES_PER_DAY:
        return

    pair, direction, score, expiration, reasons = generate_random_signal()

    img = BUY_IMG if direction == "BUY" else SELL_IMG

    caption = f"""
🚨 VIP FOREX SIGNAL

💱 Pair: {pair}
📈 Direction: {direction}
🎯 Confidence: {score}%

⌛ Expiration: {expiration} MIN

🧠 Strategy Insight:
{reasons}

🔥 Premium Institutional Engine
"""

    await send_warning(pair)
    await asyncio.sleep(60)
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

            if trade_count < MAX_TRADES_PER_DAY:
                await send_signal()

            delay = random.randint(180, 360)  # 3–6 minutes
            await asyncio.sleep(delay)

        except Exception as e:
            print("ERROR:", e)
            await asyncio.sleep(10)

# ===== START =====
if __name__ == "__main__":
    print("🚀 RANDOM SIGNAL BOT LIVE")
    asyncio.run(main_loop())