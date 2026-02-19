import os
import sqlite3
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

TYPE, COLOR, QTY = range(3)

def db():
    conn = sqlite3.connect("pla.db")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS pla(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user TEXT,
        filament TEXT,
        color TEXT,
        qty INTEGER
    )
    """)
    return conn

# ---------- ADD FLOW ----------

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧵 Tipo filamento?")
    return TYPE

async def type_received(update: Update, context):
    context.user_data["filament"] = update.message.text
    await update.message.reply_text("🎨 Colore?")
    return COLOR

async def color_received(update: Update, context):
    context.user_data["color"] = update.message.text
    await update.message.reply_text("📦 Quante bobine?")
    return QTY

async def qty_received(update: Update, context):
    qty = int(update.message.text)

    filament = context.user_data["filament"]
    color = context.user_data["color"]
    user = update.effective_user.first_name
    chat_id = update.effective_chat.id

    conn = db()
    conn.execute(
        "INSERT INTO pla(chat_id,user,filament,color,qty) VALUES(?,?,?,?,?)",
        (chat_id, user, filament, color, qty),
    )
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Aggiunto:\n{filament} {color} — {qty} bobine"
    )

    return ConversationHandler.END

# ---------- LIST ----------

async def list_pla(update: Update, context):
    chat_id = update.effective_chat.id

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT filament,color,SUM(qty)
        FROM pla
        WHERE chat_id=?
        GROUP BY filament,color
    """,(chat_id,))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Lista vuota 🙂")
        return

    text = "📦 ORDINE PLA\n\n"

    for f,c,q in rows:
        text += f"• {f} {c} → {q} bobine\n"

    await update.message.reply_text(text)

# ---------- CANCEL ----------

async def cancel(update: Update, context):
    await update.message.reply_text("Operazione annullata.")
    return ConversationHandler.END

# ---------- MAIN ----------

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, type_received)],
            COLOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, color_received)],
            QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, qty_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("list", list_pla))

    app.run_polling()

if __
