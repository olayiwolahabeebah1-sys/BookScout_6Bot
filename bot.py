import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQueryResultArticle, InputTextMessageContent,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    InlineQueryHandler, ContextTypes,
)

from config import BOT_TOKEN
from books_api import search_google_books, search_gutenberg
import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Welcome to BookScout_6Bot!\n\n"
        "/search <title or author> - find books\n"
        "/gutenberg <title> - find free public-domain books\n"
        "/mylist - view your saved books\n"
        "/help - show this message"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /search <title or author>")
        return

    results = search_google_books(query)
    if not results:
        await update.message.reply_text("No books found. Try a different search.")
        return

    context.user_data["results"] = results
    await send_result(update.message, context, index=0)


async def send_result(message, context, index: int):
    results = context.user_data.get("results", [])
    if not results or index < 0 or index >= len(results):
        return

    book = results[index]
    caption = (
        f"*{book['title']}*\n"
        f"by {book['authors']}\n"
        f"Published: {book['published']}\n\n"
        f"{book['description'][:500]}"
    )

    nav = []
    if index > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"nav:{index-1}"))
    if index < len(results) - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"nav:{index+1}"))

    buttons = []
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("➕ Add to my list", callback_data=f"add:{index}")])
    if book.get("info_link"):
        buttons.append([InlineKeyboardButton("🔗 More info", url=book["info_link"])])

    markup = InlineKeyboardMarkup(buttons)

    if book.get("thumbnail"):
        await message.reply_photo(photo=book["thumbnail"], caption=caption, parse_mode="Markdown", reply_markup=markup)
    else:
        await message.reply_text(caption, parse_mode="Markdown", reply_markup=markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, _, value = query.data.partition(":")

    if action == "nav":
        await send_result(query.message, context, int(value))

    elif action == "add":
        results = context.user_data.get("results", [])
        index = int(value)
        if 0 <= index < len(results):
            book = results[index]
            db.add_book(query.from_user.id, book["id"], book["title"], book["authors"])
            await query.answer("Added to your list ✅")

    elif action == "remove":
        db.remove_book(query.from_user.id, value)
        await query.edit_message_text("Removed from your list.")


async def gutenberg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /gutenberg <title or author>")
        return

    results = search_gutenberg(query)
    lines = [
        f"📖 *{b['title']}* by {b['authors']}\n[Download]({b['download_url']})"
        for b in results if b["download_url"]
    ]
    if not lines:
        await update.message.reply_text("No downloadable public-domain matches found.")
        return

    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown", disable_web_page_preview=True)


async def my_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.get_list(update.effective_user.id)
    if not rows:
        await update.message.reply_text("Your list is empty. Use /search to find books to add.")
        return

    buttons = [[InlineKeyboardButton(f"❌ Remove: {title}", callback_data=f"remove:{book_id}")] for book_id, title, _ in rows]
    text = "\n".join(f"• {title} — {author}" for _, title, author in rows)
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def inline_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.inline_query.query
    if not query_text:
        return

    results = search_google_books(query_text, max_results=8)
    inline_results = [
        InlineQueryResultArticle(
            id=book["id"],
            title=book["title"],
            description=book["authors"],
            thumbnail_url=book.get("thumbnail"),
            input_message_content=InputTextMessageContent(
                f"📖 *{book['title']}*\nby {book['authors']}\n{book.get('info_link', '')}",
                parse_mode="Markdown",
            ),
        )
        for book in results
    ]
    await update.inline_query.answer(inline_results, cache_time=10)


def main():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("gutenberg", gutenberg))
    app.add_handler(CommandHandler("mylist", my_list))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(InlineQueryHandler(inline_search))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
