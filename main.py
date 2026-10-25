import os
import requests
from flask import Flask, request

TOKEN = "8622474758:AAFcIwB0EOHK1luEnYig6yxE4ZxmbU0XOxo"
ADMIN_ID = 1056007305
URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)


def send_message(chat_id, text, reply_markup=None):
  data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
  if reply_markup:
    data["reply_markup"] = reply_markup
  requests.post(f"{URL}/sendMessage", json=data)


@app.route("/", methods=["GET"])
def home():
  return "متجر العاقل يعمل بنجاح 24/7!", 200


@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
  update = request.json
  if "message" in update:
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    if text == "/start":
      web_app_url = "https://" + request.host + "/shop"
      keyboard = {
          "inline_keyboard": [[{
              "text": "🛍️ فتح متجر العاقل",
              "web_app": {"url": web_app_url},
          }]]
      }
      send_message(
          chat_id,
          "مرحباً بك في *متجر العاقل* للملفات العسكرية 🎖️\nاضغط بالأسفل لفتح"
          " المتجر:",
          keyboard,
      )

    elif text == "/admin":
      if chat_id != ADMIN_ID:
        send_message(chat_id, "عذراً، هذا الأمر خاص بالأدمن فقط.")
        return "OK", 200

      keyboard = {
          "inline_keyboard": [
              [
                  {
                      "text": "➕ إضافة منتج",
                      "callback_data": "add_product",
                  },
                  {
                      "text": "⚙️ إدارة المنتجات",
                      "callback_data": "manage_products",
                  },
              ],
              [{
                  "text": "📊 إحصائيات المتجر",
                  "callback_data": "stats",
              }],
          ]
      }
      send_message(chat_id, "لوحة تحكم الأدمن لمتجر العاقل:", keyboard)

  return "OK", 200


# مسار لفتح واجهة المتجر (Mini App)
@app.route("/shop", methods=["GET"])
def shop_page():
  # سنقرأ ملف index.html ونععرضه مباشرة
  if os.path.exists("index.html"):
    with open("index.html", "r", encoding="utf-8") as f:
      return f.read()
  return "مرحباً بك في متجر العاقل"


if __name__ == "__main__":
  # ربط الويب هوك تلقائياً عند التشغيل
  # (استبدل رابط ريندر الخاص بك هنا لاحقاً أو دعه يتحدث)
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
