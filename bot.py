import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN tidak ditemukan!")

def get_trending():
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        r = requests.get(url, timeout=12)
        data = r.json()
        text = "🔥 <b>TRENDING COINS</b>\n\n"
        for i, coin in enumerate(data.get("coins", [])[:10], 1):
            item = coin["item"]
            name = item["name"]
            symbol = item["symbol"].upper()
            rank = item.get("market_cap_rank", "-")
            text += f"{i}. <b>{name}</b> ({symbol})\n   Rank: #{rank}\n\n"
        return text
    except Exception as e:
        logger.error(f"Error trending: {e}")
        return "❌ Gagal mengambil data trending."

def get_top_volume():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "volume_desc",
            "per_page": 10,
            "page": 1,
            "sparkline": "false"
        }
        r = requests.get(url, params=params, timeout=12)
        data = r.json()
        text = "📊 <b>TOP VOLUME 24 JAM</b>\n\n"
        for i, coin in enumerate(data, 1):
            name = coin["name"]
            symbol = coin["symbol"].upper()
            price = coin.get("current_price", 0)
            vol = coin.get("total_volume", 0)
            change = coin.get("price_change_percentage_24h") or 0
            emoji = "🟢" if change >= 0 else "🔴"
            text += (
                f"{i}. <b>{name}</b> ({symbol})\n"
                f"   Harga: ${price:,.4f}\n"
                f"   Volume: ${vol:,.0f}\n"
                f"   {emoji} {change:+.2f}%\n\n"
            )
        return text
    except Exception as e:
        logger.error(f"Error volume: {e}")
        return "❌ Gagal mengambil data volume."

def get_top_gainers():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "price_change_percentage_24h_desc",
            "per_page": 10,
            "page": 1,
            "sparkline": "false"
        }
        r = requests.get(url, params=params, timeout=12)
        data = r.json()
        text = "🚀 <b>TOP GAINERS 24 JAM</b>\n\n"
        for i, coin in enumerate(data, 1):
            name = coin["name"]
            symbol = coin["symbol"].upper()
            price = coin.get("current_price", 0)
            change = coin.get("price_change_percentage_24h") or 0
            vol = coin.get("total_volume", 0)
            text += (
                f"{i}. <b>{name}</b> ({symbol})\n"
                f"   Harga: ${price:,.6f}\n"
                f"   📈 {change:+.2f}%\n"
                f"   Vol: ${vol:,.0f}\n\n"
            )
        return text
    except Exception as e:
        logger.error(f"Error gainers: {e}")
        return "❌ Gagal mengambil data gainers."

def get_binance_hot():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        r = requests.get(url, timeout=12)
        data = r.json()
        usdt_pairs = [x for x in data if x["symbol"].endswith("USDT")]
        usdt_pairs.sort(key=lambda x: float(x["quoteVolume"]), reverse=True)
        text = "⚡ <b>BINANCE HOT PAIRS</b>\n\n"
        for i, pair in enumerate(usdt_pairs[:10], 1):
            symbol = pair["symbol"]
            price = float(pair["lastPrice"])
            change = float(pair["priceChangePercent"])
            vol = float(pair["quoteVolume"])
            emoji = "🟢" if change >= 0 else "🔴"
            text += (
                f"{i}. <b>{symbol}</b>\n"
                f"   Harga: ${price:,.4f}\n"
                f"   {emoji} {change:+.2f}%\n"
                f"   Vol: ${vol:,.0f}\n\n"
            )
        return text
    except Exception as e:
        logger.error(f"Error Binance: {e}")
        return "❌ Gagal mengambil data Binance."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Trending", callback_data="trending")],
        [InlineKeyboardButton("📊 Top Volume", callback_data="volume")],
        [InlineKeyboardButton("🚀 Top Gainers", callback_data="gainers")],
        [InlineKeyboardButton("⚡ Binance Hot", callback_data="binance")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 <b>Market Screener Bot</b>\n\n"
        "Pantau market yang sedang <b>trending</b> & <b>ramai transaksi</b>.\n\n"
        "Pilih menu di bawah:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏳ Sedang mengambil data...")

    if query.data == "trending":
        text = get_trending()
    elif query.data == "volume":
        text = get_top_volume()
    elif query.data == "gainers":
        text = get_top_gainers()
    elif query.data == "binance":
        text = get_binance_hot()
    else:
        text = "Perintah tidak dikenal"

    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data=query.data)],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🔥 Trending", callback_data="trending")],
        [InlineKeyboardButton("📊 Top Volume", callback_data="volume")],
        [InlineKeyboardButton("🚀 Top Gainers", callback_data="gainers")],
        [InlineKeyboardButton("⚡ Binance Hot", callback_data="binance")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "👋 <b>Market Screener Bot</b>\n\nPilih menu:",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(trending|volume|gainers|binance)$"))
    app.add_handler(CallbackQueryHandler(menu_handler, pattern="^menu$"))
    logger.info("Bot sedang berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
