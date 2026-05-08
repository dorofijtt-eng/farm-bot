import sqlite3
import random
import threading
import time
import sys
import subprocess
import os

# Авто-встановлення telebot
try:
    import telebot
except ModuleNotFoundError:
    print("Встановлюю бібліотеку...")
    subprocess.check_call([
        sys.executable,
        "-m",
        "pip",
        "install",
        "pyTelegramBotAPI"
    ])
    import telebot

TOKEN = "8696995833:AAGipKRpvVaZX1x788R8alV_Px7zxrFc0Lk"
CURRENCY = "€"
DB_NAME = "farm_data.db"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


def get_db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


# Збереження прогресу
if not os.path.exists(DB_NAME):
    print("🆕 Створюється нова база...")
else:
    print("💾 База знайдена, прогрес збережено.")


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stats(
        id INTEGER PRIMARY KEY,
        balance REAL,
        cows INTEGER,
        chickens INTEGER,
        sheeps INTEGER,
        pigs INTEGER,
        horses INTEGER,
        goats INTEGER,
        rabbits INTEGER,
        crop_ready INTEGER,
        bonus_time INTEGER,
        tractor INTEGER,
        xp INTEGER
    )
    """)

    cursor.execute("SELECT COUNT(*) FROM stats WHERE id=1")
    exists = cursor.fetchone()[0]

    if exists == 0:
        cursor.execute("""
        INSERT INTO stats VALUES(
            1,
            1000,
            1,
            5,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
        )
        """)
        print("✅ Новий профіль створено")
    else:
        print("✅ Дані гравця завантажені")

    conn.commit()
    conn.close()


init_db()

ANIMAL_CONFIG = {
    "chicken": {"price": 15, "name": "курча", "db_col": "chickens"},
    "cow": {"price": 150, "name": "корову", "db_col": "cows"},
    "sheep": {"price": 250, "name": "вівцю", "db_col": "sheeps"},
    "pig": {"price": 400, "name": "свиню", "db_col": "pigs"},
    "horse": {"price": 800, "name": "коня", "db_col": "horses"},
    "goat": {"price": 300, "name": "козу", "db_col": "goats"},
    "rabbit": {"price": 100, "name": "кролика", "db_col": "rabbits"}
}


@bot.message_handler(commands=["start"])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.add("💰 Мій баланс", "📊 Статистика")
    markup.add("🌾 Посадити урожай", "🥗 Продати врожай")
    markup.add("🎁 Щоденний бонус", "🎰 Казино")
    markup.add("🚜 Купити трактор(500€)")

    markup.add("🐤 Купити курча(15€)", "🐄 Купити корову(150€)")
    markup.add("🐑 Купити вівцю(250€)", "🐷 Купити свиню(400€)")
    markup.add("🐴 Купити коня(800€)", "🐐 Купити козу(300€)")
    markup.add("🐰 Купити кролика(100€)")

    bot.reply_to(
        message,
        "🚜 Ферма запущена!",
        reply_markup=markup
    )


@bot.message_handler(func=lambda m: True)
def handle(message):
    conn = get_db()
    cursor = conn.cursor()

    # баланс
    if message.text == "💰 Мій баланс":
        cursor.execute("SELECT balance FROM stats WHERE id=1")
        bal = cursor.fetchone()[0]
        bot.reply_to(message, f"💰 Баланс: {bal:.2f}{CURRENCY}")

    # казино
    elif message.text == "🎰 Казино":
        bet = 100

        cursor.execute("SELECT balance FROM stats WHERE id=1")
        bal = cursor.fetchone()[0]

        if bal < bet:
            bot.reply_to(message, "❌ Недостатньо грошей для казино")

        else:
            if random.randint(1, 100) <= 45:
                win = random.randint(150, 300)

                cursor.execute("""
                UPDATE stats
                SET balance = balance + ?
                WHERE id=1
                """, (win,))
                conn.commit()

                bot.reply_to(
                    message,
                    f"🎉 Ти виграв {win}{CURRENCY}"
                )
            else:
                cursor.execute("""
                UPDATE stats
                SET balance = balance - ?
                WHERE id=1
                """, (bet,))
                conn.commit()

                bot.reply_to(
                    message,
                    f"💀 Ти програв {bet}{CURRENCY}"
                )

    # посадити урожай
    elif message.text == "🌾 Посадити урожай":
        cursor.execute("SELECT tractor FROM stats WHERE id=1")
        tractor = cursor.fetchone()[0]

        if tractor:
            crop_time = int(time.time()) + 15
            text = "🚜 Трактор прискорив урожай! 15 сек."
        else:
            crop_time = int(time.time()) + 30
            text = "🌱 Урожай посаджено! 30 сек."

        cursor.execute("""
        UPDATE stats
        SET crop_ready=?
        WHERE id=1
        """, (crop_time,))
        conn.commit()

        bot.reply_to(message, text)

    # продати урожай
    elif message.text == "🥗 Продати врожай":
        cursor.execute("SELECT crop_ready FROM stats WHERE id=1")
        crop_ready = cursor.fetchone()[0]

        now = int(time.time())

        if crop_ready == 0:
            bot.reply_to(message, "❌ Ти нічого не посадив")

        elif now < crop_ready:
            remain = crop_ready - now
            bot.reply_to(
                message,
                f"⏳ Урожай ще росте: {remain} сек."
            )

        else:
            profit = random.randint(50, 200)

            cursor.execute("""
            UPDATE stats
            SET balance = balance + ?,
                crop_ready = 0,
                xp = xp + 25
            WHERE id=1
            """, (profit,))
            conn.commit()

            bot.reply_to(
                message,
                f"🥗 Урожай продано +{profit}{CURRENCY}\n⭐ +25 XP"
            )

    # бонус
    elif message.text == "🎁 Щоденний бонус":
        cursor.execute("SELECT bonus_time FROM stats WHERE id=1")
        last_bonus = cursor.fetchone()[0]

        now = int(time.time())

        if now - last_bonus >= 86400:
            bonus = random.randint(1000, 3000)

            cursor.execute("""
            UPDATE stats
            SET balance = balance + ?,
                bonus_time = ?
            WHERE id=1
            """, (bonus, now))
            conn.commit()

            bot.reply_to(
                message,
                f"🎁 Ти отримав {bonus}{CURRENCY}"
            )
        else:
            remain = 86400 - (now - last_bonus)
            bot.reply_to(
                message,
                f"⏳ Бонус через {remain} сек."
            )

    # трактор
    elif message.text == "🚜 Купити трактор(500€)":
        cursor.execute("""
        SELECT balance, tractor
        FROM stats WHERE id=1
        """)
        bal, tractor = cursor.fetchone()

        if tractor:
            bot.reply_to(message, "🚜 У тебе вже є трактор")

        elif bal >= 500:
            cursor.execute("""
            UPDATE stats
            SET balance = balance - 500,
                tractor = 1
            WHERE id=1
            """)
            conn.commit()

            bot.reply_to(message, "🚜 Трактор куплено!")
        else:
            bot.reply_to(message, "❌ Недостатньо грошей")

    # статистика
    elif message.text == "📊 Статистика":
        cursor.execute("""
        SELECT balance,cows,chickens,sheeps,
               pigs,horses,goats,rabbits,
               tractor,xp
        FROM stats WHERE id=1
        """)

        bal, cows, chickens, sheeps, pigs, horses, goats, rabbits, tractor, xp = cursor.fetchone()

        bot.reply_to(
            message,
            f"""
📊 Статистика

💰 Баланс: {bal:.2f}{CURRENCY}

🐤 Кури: {chickens}
🐄 Корови: {cows}
🐑 Вівці: {sheeps}
🐷 Свині: {pigs}
🐴 Коні: {horses}
🐐 Кози: {goats}
🐰 Кролики: {rabbits}

🚜 Трактор: {"Є" if tractor else "Немає"}

⭐ XP: {xp}
🏆 Рівень: {xp // 100}
"""
        )

    # купівля тварин
    elif message.text in [
        "🐤 Купити курча(15€)",
        "🐄 Купити корову(150€)",
        "🐑 Купити вівцю(250€)",
        "🐷 Купити свиню(400€)",
        "🐴 Купити коня(800€)",
        "🐐 Купити козу(300€)",
        "🐰 Купити кролика(100€)"
    ]:

        animal_map = {
            "🐤 Купити курча(15€)": "chicken",
            "🐄 Купити корову(150€)": "cow",
            "🐑 Купити вівцю(250€)": "sheep",
            "🐷 Купити свиню(400€)": "pig",
            "🐴 Купити коня(800€)": "horse",
            "🐐 Купити козу(300€)": "goat",
            "🐰 Купити кролика(100€)": "rabbit"
        }

        animal = animal_map[message.text]
        conf = ANIMAL_CONFIG[animal]

        cursor.execute("SELECT balance FROM stats WHERE id=1")
        bal = cursor.fetchone()[0]

        if bal >= conf["price"]:
            cursor.execute(f"""
            UPDATE stats
            SET balance = balance - ?,
                {conf['db_col']} = {conf['db_col']} + 1
            WHERE id=1
            """, (conf["price"],))
            conn.commit()

            bot.reply_to(
                message,
                f"✅ Куплено {conf['name']}"
            )
        else:
            bot.reply_to(
                message,
                "❌ Недостатньо грошей"
            )

    conn.close()


def passive_income():
    while True:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT cows,chickens,sheeps,pigs,
               horses,goats,rabbits,tractor
        FROM stats WHERE id=1
        """)

        cows, chickens, sheeps, pigs, horses, goats, rabbits, tractor = cursor.fetchone()

        income = (
            cows * 1.5 +
            chickens * 0.5 +
            sheeps *2.5 +
            pigs * 4 +
            horses * 6 +
            goats * 3 +
            rabbits * 1
        )

        if tractor:
            income *= 2

        cursor.execute("""
        UPDATE stats
        SET balance = balance + ?
        WHERE id=1
        """, (income,))
        conn.commit()

        conn.close()
        time.sleep(1)


if __name__ == "__main__":
    threading.Thread(
        target=passive_income,
        daemon=True
    ).start()

    print("🚜 Бот запущено...")
    bot.infinity_polling()