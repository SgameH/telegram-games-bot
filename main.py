Import os 
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
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

    def __init__(self, chat_id, bot, from_user):
        self.chat_id = chat_id
        self._bot = bot
        self.from_user = from_user

    async def reply_text(self, text, **kwargs):
        return await self._bot.send_message(chat_id=self.chat_id, text=text, **kwargs)


class FakeUpdate:

    def __init__(self, chat_id, bot, user):
        self.message = FakeMessage(chat_id, bot, user)
        self.effective_user = user
        self.effective_chat = type('obj', (object,), {'id': chat_id})()


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
        "⚠️ **عذراً، لا يمكنك استخدام البوت قبل الاشتراك في قناة البوت الرسمية!**\n\n"
        "يرجى الاشتراك في القناة أولاً لتتمكن من اللعب واستخدام كافة الميزات:\n"
        f"🔗 {CHANNEL_URL}\n\n"
        "بعد الانضمام، اضغط على زر **'تحقق من الاشتراك 🔄'** أدناه."
    )
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_URL)],
        [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            pass
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")


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
    menu_text = f"🎮 **قائمة الألعاب المتاحة يا {user_name}:**\nاختر اللعبة لإنشاء رابط التحدي ومشاركته مع صديقك:"

    keyboard = [
        [InlineKeyboardButton("❌ لعبة اكس أو ⭕", callback_data="menu_ttt")],
        [InlineKeyboardButton("✊ حجر - ورقة - مقص", callback_data="menu_rps")],
        [InlineKeyboardButton("🏴‍☠️ جزيرة الكنوز والأموال", callback_data="menu_treasure")],
        [InlineKeyboardButton("💣 الصناديق المفخخة", callback_data="menu_traps")],
        [InlineKeyboardButton("⚓ السفن الحربية", callback_data="menu_battleship")],
        [InlineKeyboardButton("📖 تعليمات وشرح الألعاب", callback_data="show_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(menu_text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            pass
    else:
        await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode="Markdown")


async def show_help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    if user and not await check_subscription(user.id, context):
        await ask_to_subscribe(update)
        return

    help_text = (
        "📖 **دليل وتعليمات ألعاب البوت الجماعية:**\n\n"
        "1️⃣ **لعبة اكس أو (Tic Tac Toe):**\n"
        "• **الفكرة:** لعبة الكلاسيكية الشهيرة لترتيب 3 رموز متتالية (أفقياً، عمودياً، أو قطرياً).\n"
        "• **طريقة اللعب:** اختر اللعبة من القائمة لإنشاء رابط تحدٍ، أرسله لصديقك، وبمجرد دخوله ستبدأ المعركة التفاعلية وتبادلون الأدوار بالضغط على المربعات.\n\n"
        "2️⃣ **حجر - ورقة - مقص (Rock Paper Scissors):**\n"
        "• **الفكرة:** المواجهة السريعة المعروفة (الحجر يكسر المقَص، المقَص يقطع الورقة، الورقة تغلف الحجر).\n"
        "• **طريقة اللعب:** أنشئ رابط التحدي وأرسله لصديقك ليختار حركته سراً وتظهر النتيجة فوراً لتحديد الفائز.\n\n"
        "3️⃣ **جزيرة الكنوز والأموال (Treasure):**\n"
        "• **الفكرة:** مغامرة استكشاف والحفر للبحث عن الكنوز الثمينة وتجنب الخسارة.\n"
        "• **طريقة اللعب:** شارك رابط التحدي وتنافس مع صديقك في التنقيب واكتشاف أكبر قدر من الكنوز المخفية.\n\n"
        "4️⃣ **الصناديق المفخخة (Traps):**\n"
        "• **الفكرة:** اختبار حظ وتفكير بحت لتجنب الصناديق المفخخة.\n"
        "• **طريقة اللعب:** أنشئ التحدي وأرسله لصديقك، وكل لاعب يحاول اختيار الصناديق الآمنة والابتعاد عن الفخاخ حتى النهاية.\n\n"
        "5️⃣ **السفن الحربية (Battleship):**\n"
        "• **الفكرة:** معركة بحرية استراتيجية لتدمير أسطول الخصم.\n"
        "• **طريقة اللعب:** قم بدعوة صديقك عبر رابط التحدي وابدءا تبادل الضربات الاستراتيجية لإغراق سفن بعضكما البعض!"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 رجوع لقائمة الألعاب", callback_data="show_games_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        try:
            await update.callback_query.message.edit_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            pass


async def universal_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    user = query.from_user


    if data == "check_sub":
        is_subscribed = await check_subscription(user.id, context)
        if is_subscribed:
            await query.answer("✅ شكراً لاشتراكك! تم فتح البوت بنجاح.", show_alert=True)
            await games_command(update, context)
        else:

            await query.answer(
                "❌ عذراً، لم تقم بالاشتراك في القناة بعد!\nيرجى الضغط على زر 'اشترك في القناة' أولاً ثم حاول مرة أخرى.",
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

    fake_update = FakeUpdate(chat_id, context.bot, user)


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
        await rps_button_handler(update, context)
    elif data.startswith("gold_"):
        await treasure_button_handler(update, context)
    elif data.startswith("trap_"):
        await traps_button_handler(update, context)
    elif data.startswith("bs_"):
        await battleship_button_handler(update, context)


def main():

    if not TOKEN or TOKEN == "PASTE_YOUR_TOKEN_HERE":
        print("❌ خطأ: لم يتم العثور على التوكن. يرجى وضع التوكن في الكود أو في متغيرات البيئة.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", main_start))
    app.add_handler(CommandHandler("games", games_command))
    app.add_handler(CommandHandler("ttt", tictactoe_start))
    app.add_handler(CommandHandler("rps", rps_start))
    app.add_handler(CommandHandler("treasure", treasure_start))
    app.add_handler(CommandHandler("traps", traps_start))
    app.add_handler(CommandHandler("battleship", battleship_start))

    app.add_handler(CallbackQueryHandler(universal_callback_handler))

    print("🚀 البوت الشامل يعمل الآن بكفاءة تامة وجاهز لاستقبال اللاعبين...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
