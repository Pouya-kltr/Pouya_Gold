import os
import time
import requests
from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler, JobQueue

# خواندن متغیرهای محیطی از رندر
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
MIN_PRICE = int(os.getenv('MIN_PRICE', 0))  # مقدار پیش‌فرض 0 اگه خالی باشه
MAX_PRICE = int(os.getenv('MAX_PRICE', 0))  # مقدار پیش‌فرض 0 اگه خالی باشه
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))  # فاصله چک کردن (ثانیه)، پیش‌فرض 5 دقیقه

def get_gold_price():
    url = "https://milli.gold"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # تلاش برای پیدا کردن قیمت از تگ موردنظر (ممکنه نیاز به تنظیم داشته باشه)
        price_element = soup.find("span", {"class": "info-price"})  # حدس تگ، ممکنه تغییر کنه
        if price_element:
            price_text = price_element.text.strip().replace("ریال", "").replace(",", "")
            price = int(price_text) / 10  # تبدیل ریال به تومان (فرض 1 تومان = 10 ریال)
            return price
        else:
            raise Exception("قیمت طلا در سایت میلی یافت نشد")
    except Exception as e:
        print(f"خطا در دریافت قیمت: {e}")
        return None

def send_alert(context):
    price = context.job.context
    if price is None:
        return
    bot = context.bot
    if price < MIN_PRICE:
        msg = f"📉 قیمت طلا از پایین بازه خارج شده!\nقیمت فعلی: {price:,} تومان\nبازه: {MIN_PRICE:,} تا {MAX_PRICE:,}"
    elif price > MAX_PRICE:
        msg = f"📈 قیمت طلا از بالای بازه خارج شده!\nقیمت فعلی: {price:,} تومان\nبازه: {MIN_PRICE:,} تا {MAX_PRICE:,}"
    else:
        return  # اگه تو بازه باشه، پیام نمی‌فرسته
    bot.send_message(chat_id=CHAT_ID, text=msg)

def check_price(context):
    price = get_gold_price()
    if price:
        print(f"قیمت فعلی: {price:,} تومان در {time.ctime()}")
        context.job_queue.run_once(send_alert, 1, context=price)  # ارسال هشدار با تأخیر 1 ثانیه

def start(update, context):
    update.message.reply_text(f"ربات فعال است!\nبازه فعلی: {MIN_PRICE:,} تا {MAX_PRICE:,} تومان\nچک کردن هر {CHECK_INTERVAL} ثانیه.")

def main():
    if not all([BOT_TOKEN, CHAT_ID, MIN_PRICE, MAX_PRICE]):
        raise ValueError("یکی از متغیرهای محیطی (BOT_TOKEN, CHAT_ID, MIN_PRICE, MAX_PRICE) تنظیم نشده است!")
    
    updater = Updater(BOT_TOKEN, use_context=True)
    jq = updater.job_queue

    # چک کردن قیمت با فاصله مشخص
    jq.run_repeating(check_price, interval=CHECK_INTERVAL, first=10)

    # اضافه کردن دستور /start
    updater.dispatcher.add_handler(CommandHandler("start", start))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()