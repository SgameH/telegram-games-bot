import os
import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
)

from tictactoe import tictactoe_start, tictactoe_button_handler
from rps import rps_start, rps_button_handler
from treasure import treasure_start, treasure_button_handler
from traps import traps_start, traps_button_handler
from battleship import battleship_start, battleship_button_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
CHANNEL_USERNAME = "@SgameH"
CHANNEL_URL = "https://t.me/SgameH"

class FakeMessage:
    def __init__(self, chat_id, bot, from_user, message_id=None):
        self.chat_id = chat_id
        self._bot = bot
        self.from_user = from_user
        self.message_id = message_id

    async def reply_text(self, text, **kwargs):
        return await self._bot.send_message(chat_id=self.chat_id, text=text, **kwargs)

    async def edit_text(self, text, **kwargs):
        if self.message_id:
            return await self._bot.edit_message_text(chat_id=self.chat_id, message_id=self.message_id, text=text, **kwargs)
        return await self.reply_text(text, **kwargs)

class FakeUpdate:
    def __init__(self, chat_id, bot, user, message_id=None, callback_query=None):
        self.message = FakeMessage(chat_id, bot, user, message_id)
        self.effective_user = user
        self.effective_chat = type('obj', (object,), {'id': chat_id})()
        self.callback_query = callback_query

async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception as e:
        logger.error(f"خطأ أثناء التحقق من الاشتراك: {e}")
        return False
    return False

async def ask_to_subscribe(update: Update):
    text = (
        "عذراً، لا يمكنك استخدام البوت قبل الاشتراك في قناة البوت الرسمية!\n\n"
        "يرجى الاشتراك في القناة أولاً لتتمكن من اللعب واستخدام كافة الميزات:\n"
        f"{CHANNEL_URL}\n\n"
        "بعد الانضمام، اضغط على زر 'تحقق من الاشتراك'."
    )
    keyboard = [
        [InlineKeyboardButton("اشترك في القناة", url=CHANNEL_URL)],
        [InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        except Exception:
            pass
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user and not await check_subscription(user.id, context):
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="يجب الاشتراك بالقناة أولاً للعب!",
                description="اضغط هنا للاشتراك في قناة البوت الرسمية.",
                input_message_content=InputTextMessageContent(
                    message_text=f"عذراً، لا يمكنك استخدام البوت قبل الاشتراك في قناة البوت الرسمية:\n{CHANNEL_URL}"
                ),
            )
        ]
        await update.inline_query.answer(results, cache_time=0)
        return

    results = [
        InlineQueryResultArticle(
            id="ttt_game",
            title="لعبة اكس أو (Tic Tac Toe)",
            description="تحدى صديقك في لعبة اكس أو الشهيرة داخل المحادثة!",
            input_message_content=InputTextMessageContent(
                message_text="تم إنشاء تحدي جديد في لعبة اكس أو!\nاضغط على الزر أدناه للدخول والبدء باللعب معاً:"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ابدأ التحدي الآن", callback_data="menu_ttt")]
            ])
        ),
        InlineQueryResultArticle(
            id="rps_game",
            title="حجر - ورقة - مقص",
            description="تحدى صديقك في لعبة المواجهة السريعة.",
            input_message_content=InputTextMessageContent(
                message_text="تحدي حجر - ورقة - مقص:\nاضغط على الزر أدناه للدخول واختيار حركتك:"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ابدأ التحدي الآن", callback_data="menu_rps")]
            ])
        ),
        InlineQueryResultArticle(
            id="treasure_game",
            title="جزيرة الكنوز والأموال",
            description="تنافس مع صديقك في التنقيب عن الكنوز.",
            input_message_content=InputTextMessageContent(
                message_text="تحدي جزيرة الكنوز:\nاضغط على الزر أدناه لاختبار حظك والتنقيب:"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ابدأ التحدي الآن", callback_data="menu_treasure")]
            ])
        ),
        InlineQueryResultArticle(
            id="traps_game",
            title="الصناديق المفخخة",
            description="تجنب الفخاخ واكتشف الصناديق الآمنة.",
            input_message_content=InputTextMessageContent(
                message_text="تحدي الصناديق المفخخة:\nاضغط على الزر أدناه للبدء بحذر:"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ابدأ التحدي الآن", callback_data="menu_traps")]
            ])
        ),
        InlineQueryResultArticle(
            id="battleship_game",
            title="السفن الحربية",
            description="معركة بحرية استراتيجية لتدمير أسطول الخصم.",
            input_message_content=InputTextMessageContent(
                message_text="تحدي السفن الحربية:\nاضغط على الزر أدناه لبدء المعركة الاستراتيجية:"
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ابدأ التحدي الآن", callback_data="menu_battleship")]
            ])
        )
    ]
    await update.inline_query.answer(results, cache_time=5)

async def main_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return

    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        await ask_to_subscribe(update)
        return

    args = context.args
    if args and len(args) > 0:
        payload = args[0]
        if payload.startswith("game_"):
            await tictactoe_start(update, context)
            return
        elif payload.startswith("rps_"):
            await rps_start(update, context)
            return
        elif payload.startswith("gold_"):
            await treasure_start(update, context)
            return
        elif payload.startswith("trap_"):
            await traps_start(update, context)
            return
        elif payload.startswith("bs_"):
            await battleship_start(update, context)
            return

    await games_command(update, context)

async def games_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user and not await check_subscription(user.id, context):
        await ask_to_subscribe(update)
        return

    user_name = user.first_name if user else "صديقي"
    menu_text = f"قائمة الألعاب المتاحة يا {user_name}:\nاختر اللعبة لإنشاء رابط التحدي ومشاركته مع صديقك:"

    keyboard = [
        [InlineKeyboardButton("لعبة اكس أو", callback_data="menu_ttt")],
        [InlineKeyboardButton("حجر - ورقة - مقص", callback_data="menu_rps")],
        [InlineKeyboardButton("جزيرة الكنوز والأموال", callback_data="menu_treasure")],
        [InlineKeyboardButton("الصناديق المفخخة", callback_data="menu_traps")],
        [InlineKeyboardButton("السفن الحربية", callback_data="menu_battleship")],
        [InlineKeyboardButton("تعليمات وشرح الألعاب", callback_data="show_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query and update.callback_query.message:
        try:
            await update.callback_query.message.edit_text(menu_text, reply_markup=reply_markup)
        except Exception:
            pass
    else:
        await update.message.reply_text(menu_text, reply_markup=reply_markup)

async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user and not await check_subscription(user.id, context):
        await ask_to_subscribe(update)
        return

    help_text = (
        "دليل وتعليمات ألعاب البوت الجماعية:\n\n"
        "1. لعبة اكس أو (Tic Tac Toe):\n"
        "• الفكرة: لعبة الكلاسيكية الشهيرة لترتيب 3 رموز متتالية.\n"
        "• طريقة اللعب: اختر اللعبة وتبادل الأدوار بالضغط على المربعات.\n\n"
        "2. حجر - ورقة - مقص:\n"
        "• الفكرة: المواجهة السريعة المعروفة لتحديد الفائز.\n\n"
        "3. جزيرة الكنوز والأموال:\n"
        "• الفكرة: مغامرة استكشاف للبحث عن الكنوز الثمينة.\n\n"
        "4. الصناديق المفخخة:\n"
        "• الفكرة: اختبار حظ وتفكير لتجنب الصناديق المفخخة.\n\n"
        "5. السفن الحربية:\n"
        "• الفكرة: معركة بحرية استراتيجية لتدمير أسطول الخصم."
    )

    keyboard = [
        [InlineKeyboardButton("رجوع لقائمة الألعاب", callback_data="show_games_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query and update.callback_query.message:
        try:
            await update.callback_query.message.edit_text(help_text, reply_markup=reply_markup)
        except Exception:
            pass

async def universal_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    data = query.data
    user = query.from_user
    message = query.message
    
    # الحل الآمن لاستخراج معرف المحادثة بدقة تامة
    chat_id = None
    if message and hasattr(message, "chat_id") and message.chat_id:
        chat_id = message.chat_id
    elif update.effective_chat:
        chat_id = update.effective_chat.id

    if data == "check_sub":
        is_subscribed = await check_subscription(user.id, context)
        if is_subscribed:
            await query.answer("شكراً لاشتراكك! تم فتح البوت بنجاح.", show_alert=True)
            await games_command(update, context)
        else:
            await query.answer(
                "عذراً، لم تقم بالاشتراك في القناة بعد!\nيرجى الضغط على زر 'اشترك في القناة' أولاً.",
                show_alert=True
            )
        return

    if not await check_subscription(user.id, context):
        await query.answer()
        await ask_to_subscribe(update)
        return

    await query.answer()

    if data == "show_games_menu":
        await games_command(update, context)
        return
    elif data == "show_help":
        await show_help_menu(update, context)
        return

    if not chat_id:
        return

    message_id = message.id if message else None
    fake_update = FakeUpdate(chat_id, context.bot, user, message_id, query)

    if data == "menu_ttt":
        context.args = []
        await tictactoe_start(fake_update, context)
        return
    elif data == "menu_rps":
        context.args = []
        await rps_start(fake_update, context)
        return
    elif data == "menu_treasure":
        context.args = []
        await treasure_start(fake_update, context)
        return
    elif data == "menu_traps":
        context.args = []
        await traps_start(fake_update, context)
        return
    elif data == "menu_battleship":
        context.args = []
        await battleship_start(fake_update, context)
        return

    if data.startswith("play_") or data.startswith("restart_"):
        await tictactoe_button_handler(update, context)
    elif data.startswith("rps_"):
        data_parts = data.split("_")
        if len(data_parts) > 1 and data_parts[1] == "start":
            await rps_start(fake_update, context)
        else:
            await rps_button_handler(update, context)
    elif data.startswith("gold_"):
        data_parts = data.split("_")
        if len(data_parts) > 1 and data_parts[1] == "start":
            await treasure_start(fake_update, context)
        else:
            await treasure_button_handler(update, context)
    elif data.startswith("trap_"):
        data_parts = data.split("_")
        if len(data_parts) > 1 and data_parts[1] == "start":
            await traps_start(fake_update, context)
        else:
            await traps_button_handler(update, context)
    elif data.startswith("bs_"):
        data_parts = data.split("_")
        if len(data_parts) > 1 and data_parts[1] == "start":
            await battleship_start(fake_update, context)
        else:
            await battleship_button_handler(update, context)

def main():
    if not TOKEN or TOKEN == "PASTE_YOUR_TOKEN_HERE":
        print("خطأ: لم يتم العثور على التوكن.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", main_start))
    app.add_handler(CommandHandler("games", games_command))
    app.add_handler(CommandHandler("ttt", tictactoe_start))
    app.add_handler(CommandHandler("rps", rps_start))
    app.add_handler(CommandHandler("treasure", treasure_start))
    app.add_handler(CommandHandler("traps", traps_start))
    app.add_handler(CommandHandler("battleship", battleship_start))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(universal_callback_handler))

    print("البوت الشامل يعمل الآن بكفاءة تامة...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
