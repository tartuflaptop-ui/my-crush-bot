# -*- coding: utf-8 -*-
"""
ربات کراشیابی علامه — نسخه اصلاح شده، فوق‌العاده سبک و سریع
"""

import json
from pathlib import Path
import requests
from flask import Flask, request, jsonify

BOT_TOKEN = "8626659367:AAG57AhbVrSNHASW2pohIdsvlHQY2EdFv_0"
OWNER_ID = 8913236534
WEBHOOK_SECRET = "krashsecret123"

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
DATA_FILE = Path(__file__).with_name("krash_bot_data.json")

app = Flask(__name__)

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {"blocked": [], "user_alias": {}, "next_alias": 1, "msg_map": {}}

def save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

def tg(method, payload):
    try:
        return requests.post(f"{API_URL}/{method}", json=payload, timeout=2.5).json()
    except:
        return {}

@app.route("/")
def health():
    return "OK"

@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    update = request.get_json(force=True, silent=True) or {}
    data = load_data()

    if "callback_query" in update:
        cq = update["callback_query"]
        if cq["from"]["id"] == OWNER_ID:
            _, target_str = cq["data"].split(":")
            uid = int(target_str)
            if uid not in data["blocked"]:
                data["blocked"].append(uid)
                save_data(data)
            tg("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "کاربر بلاک شد 🚫"})
            msg = cq.get("message", {})
            if msg:
                tg("editMessageReplyMarkup", {"chat_id": msg["chat"]["id"], "message_id": msg["message_id"], "reply_markup": {"inline_keyboard": []}})
            tg("sendMessage", {"chat_id": OWNER_ID, "text": "🚫 کاربر بلاک شد."})
            tg("sendMessage", {"chat_id": uid, "text": "❌ شما توسط ادمین بلاک شدید."})
        return jsonify(ok=True)

    message = update.get("message")
    if not message:
        return jsonify(ok=True)

    user = message["from"]
    user_id = user["id"]
    msg_id = message["message_id"]
    text = message.get("text", "")

    if user_id == OWNER_ID:
        if text == "/blocked":
            b_list = data.get("blocked", [])
            if not b_list:
                tg("sendMessage", {"chat_id": OWNER_ID, "text": "لیست بلاک خالی است."})
                return jsonify(ok=True)
            txt = "🚫 لیست بلاک‌شده‌ها:\n"
            for b in b_list:
                al = data.get("user_alias", {}).get(str(b), "?")
                txt += f"• #{al} (ID: {b})\n"
            tg("sendMessage", {"chat_id": OWNER_ID, "text": txt})
            return jsonify(ok=True)

        if text.startswith("/unblock"):
            parts = text.split()
            if len(parts) > 1 and parts[1].isdigit():
                target_alias = int(parts[1])
                uid_to_unblock = None
                for u_str, al in data.get("user_alias", {}).items():
                    if al == target_alias:
                        uid_to_unblock = int(u_str)
                        break
                if uid_to_unblock in data.get("blocked", []):
                    data["blocked"].remove(uid_to_unblock)
                    save_data(data)
                    tg("sendMessage", {"chat_id": OWNER_ID, "text": f"✅ کاربر #{target_alias} آنبلاک شد."})
                    tg("sendMessage", {"chat_id": uid_to_unblock, "text": "✅ شما آنبلاک شدید."})
            return jsonify(ok=True)

        reply_to = message.get("reply_to_message")
        if reply_to:
            t_info = data.get("msg_map", {}).get(str(reply_to.get("message_id")))
            if t_info:
                tg("sendMessage", {
                    "chat_id": t_info["user_id"],
                    "text": f"💌 پاسخ ادمین:\n\n{text}",
                    "reply_to_message_id": t_info["msg_id"]
                })
                tg("sendMessage", {"chat_id": OWNER_ID, "text": "✅ ارسال شد."})
        return jsonify(ok=True)

    if user_id in data.get("blocked", []):
        tg("sendMessage", {"chat_id": user_id, "text": "❌ شما بلاک هستید."})
        return jsonify(ok=True)

    if text == "/start":
        f_name = user.get("first_name", "")
        l_name = user.get("last_name", "")
        username = user.get("username")
        tg("sendMessage", {
            "chat_id": OWNER_ID,
            "text": f"🎯 کاربر جدید استارت کرد!\n- نام: {f_name} {l_name}\n- یوزرنیم: @{username if username else 'ندارد'}\n- آیدی: {user_id}"
        })
        tg("sendMessage", {"chat_id": user_id, "text": "✨ به ربات کراشیابی علامه خوش آمدید! پیام خود را بفرستید:"})
        return jsonify(ok=True)

    u_key = str(user_id)
    if u_key not in data.setdefault("user_alias", {}):
        data["user_alias"][u_key] = data.get("next_alias", 1)
        data["next_alias"] = data.get("next_alias", 1) + 1
        save_data(data)
    alias = data["user_alias"][u_key]

    f_name = user.get("first_name", "")
    l_name = user.get("last_name", "")
    username = user.get("username")

    sender_info = f"💌 پیام جدید (شماره #{alias})\n- نام: {f_name} {l_name}\n- یوزرنیم: @{username if username else 'ندارد'}\n- آیدی: {user_id}\n-------------------"
    keyboard = {"inline_keyboard": [[{"text": "🚫 بلاک کردن این کاربر", "callback_data": f"block:{user_id}"}]]}

    if text and not any(k in message for k in ["photo", "video", "document", "voice", "audio", "sticker", "animation"]):
        res = tg("sendMessage", {"chat_id": OWNER_ID, "text": f"{sender_info}\n{text}", "reply_markup": keyboard})
    else:
        tg("sendMessage", {"chat_id": OWNER_ID, "text": sender_info})
        res = tg("copyMessage", {"chat_id": OWNER_ID, "from_chat_id": user_id, "message_id": msg_id, "reply_markup": keyboard})

    if res.get("ok"):
        res_msg_id = res["result"].get("message_id")
        if res_msg_id:
            data.setdefault("msg_map", {})[str(res_msg_id)] = {"user_id": user_id, "msg_id": msg_id}
            save_data(data)
        tg("sendMessage", {"chat_id": user_id, "text": "✅ پیام شما ناشناس ارسال شد!"})

    return jsonify(ok=True)

if __name__ == "__main__":
    app.run(debug=True)