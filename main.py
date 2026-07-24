import logging
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ContextTypes,
)

# استيراد دوال الألعاب الخمسة (بما فيها السفن الحربية باسمها الصحيح battleship)
from rps import rps_start, rps_button_handler, active_rps_games
from tictactoe import tictactoe_start, tictactoe_button_handler, active_games, create_board
from traps import traps_start, traps_button_handler, active_trap_games
from treasure import treasure_start, treasure_button_handler, active_gold_games
from battleship import battleship_start, battleship_button_handler, active_battleship_games  # 🚢 السفن الحربية

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_USERNAME = "SgameHbot"

# 📌 يوزر قناة الاشتراك الإجباري
CHANNEL_USERNAME = "@SgameH" 


# ================= دالة التحقق من الاشتراك الإجباري =================
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return True


async def show_subscription_required(update: Update):
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة هنا", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("🔄 تحقق من الاشتراك", callback_data="check_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        f"⚠️ **عذراً، يجب عليك الاشتراك في قناة البوت أولاً لكي تتمكن من استخدامه واللعب!**\n\n"
        f"📌 قناة البوت: {CHANNEL_USERNAME}\n\n"
        f"بعد الانضمام، اضغط على زر **(تحقق من الاشتراك)** بالأسفل ⬇️"
    )

    if update.callback_query:
        try:
            await update.callback_query.answer("يجب عليك الاشتراك في القناة أولاً!", show_alert=True)
            await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            pass
    elif update.message:
        try:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            pass


# ================= دالة البداية الرئيسية (تعليمات وبدون أزرار داخلية) =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        return await show_subscription_required(update)

    args = context.args

    if args:
        payload = args[0]
        if payload.startswith("rps_"):
            return await rps_start(update, context)
        elif payload.startswith("game_") or payload.startswith("tictactoe_"):
            return await tictactoe_start(update, context)
        elif payload.startswith("trap_"):
            return await traps_start(update, context)
        elif payload.startswith("gold_"):
            return await treasure_start(update, context)
        elif payload.startswith("bs_"):
            return await battleship_start(update, context)

    # رسالة الترحيب الإرشادية تشرح الألعاب وطريقة اللعب بدون أزرار داخلية
    instructions = (
        f"👋 أهلاً بك يا **{user.first_name}** في بوت الألعاب التنافسية الاحترافي!\n\n"
        f"🎮 **الألعاب الـ 5 المتاحة في البوت:**\n"
        f"1️⃣ لعبة XO (إكس أو)\n"
        f"2️⃣ لعبة حجر ورقة مقص\n"
        f"3️⃣ لعبة الصناديق المفخخة\n"
        f"4️⃣ مغامرة جزيرة الكنز والأموال\n"
        f"5️⃣ لعبة السفن الحربية 🚢\n\n"
        f"📖 **طريقة اللعب مع أصدقائك (في أي محادثة أو مجموعة):**\n"
        f"• افتح أي محادثة خاصة أو مجموعة.\n"
        f"• اكتب يوزر البوت هكذا: `@{BOT_USERNAME}`\n"
        f"• ستظهر لك قائمة الألعاب الخمسة، اختر اللعبة التي تعجبك.\n"
        f"• سيتم إرسال اللعبة في الشات، وكل ما على صديقك إلا الضغط على زر **(انضمام)** ليبدأ التحدي مباشرة بينكم!"
    )

    if update.message:
        await update.message.reply_text(instructions, parse_mode="Markdown")


# ================= دالة البحث المباشر (إظهار الألعاب الـ 5 بالإنلاين) =================
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    user = query.from_user
    
    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        results = [
            InlineQueryResultArticle(
                id="not_subscribed",
                title="⚠️ تنبيه: اشتراك إجباري مطلوب",
                description="يجب عليك الاشتراك في قناة البوت لاستخدام الألعاب عبر الإنلاين.",
                input_message_content=InputTextMessageContent(
                    message_text=f"⚠️ عذراً يا {user.first_name}، يجب عليك الاشتراك في قناة البوت {CHANNEL_USERNAME} أولاً لتتمكن من اللعب عبر الإنلاين!",
                    parse_mode="Markdown"
                )
            )
        ]
        return await update.inline_query.answer(results, cache_time=1)

    # 1. إعداد لعبة XO
    tictactoe_id = f"tictactoe_inline_{user.id}_{query.id[:5]}"
    active_games[tictactoe_id] = {
        "player_X": user.id,
        "chat_X": None,
        "name_X": user.first_name,
        "player_O": None,
        "chat_O": None,
        "name_O": "بانتظار لاعب...",
        "board": create_board(),
        "turn": user.id,
        "msg_id": None
    }

    # 2. إعداد لعبة حجر ورقة مقص
    rps_id = f"rps_inline_{user.id}_{query.id[:5]}"
    active_rps_games[rps_id] = {
        "player_1": user.id,
        "name_1": user.first_name,
        "player_2": None,
        "name_2": "بانتظار لاعب...",
        "choice_1": None,
        "choice_2": None,
        "status": "waiting"
    }

    # 3. إعداد لعبة الصناديق المفخخة
    trap_id = f"trap_inline_{user.id}_{query.id[:5]}"
    TOTAL_BOXES = 30
    TOTAL_TRAPS = 6
    trap_indices = random.sample(range(TOTAL_BOXES), TOTAL_TRAPS)
    active_trap_games[trap_id] = {
        "player_1": user.id,
        "name_1": user.first_name,
        "player_2": None,
        "name_2": "بانتظار قرصان...",
        "trap_indices": trap_indices,
        "opened_safe": [],
        "opened_traps": [],
        "hits_1": 0,
        "hits_2": 0,
        "turn": None,
        "msg_id": None,
        "status": "waiting"
    }

    # 4. إعداد لعبة جزيرة الكنز
    gold_id = f"gold_inline_{user.id}_{query.id[:5]}"
    cells = list(range(30))
    random.shuffle(cells)
    empty_count = 3
    remaining_cells = cells[empty_count:]
    n = len(remaining_cells)
    silver_count = int(n * 0.25)
    gold_count = int(n * 0.25)
    cash_count = int(n * 0.25)
    active_gold_games[gold_id] = {
        "player_1": user.id,
        "name_1": user.first_name,
        "player_2": None,
        "name_2": "بانتظار منافس...",
        "empty_cells": set(cells[:empty_count]),
        "silver_cells": set(remaining_cells[:silver_count]),
        "gold_cells": set(remaining_cells[silver_count:silver_count+gold_count]),
        "cash_cells": set(remaining_cells[silver_count+gold_count:silver_count+gold_count+cash_count]),
        "coins_cells": set(remaining_cells[silver_count+gold_count+cash_count:]),
        "board_state": {},
        "collected_1": {"silver": 0, "gold": 0, "cash": 0, "coins": 0, "empty": 0},
        "collected_2": {"silver": 0, "gold": 0, "cash": 0, "coins": 0, "empty": 0},
        "turn": None,
        "msg_id": None,
        "status": "waiting"
    }

    # 5. إعداد لعبة السفن الحربية (Battleship)
    from battleship import create_empty_grid, GRID_SIZE
    bs_id = f"bs_inline_{user.id}_{query.id[:5]}"
    active_battleship_games[bs_id] = {
        "player_1": user.id,
        "name_1": user.first_name,
        "player_2": None,
        "name_2": "بانتظار لاعب...",
        "ships_1": [],
        "ships_2": [],
        "shared_grid": create_empty_grid(),
        "turn": None,
        "status": "setup_1"
    }

    results = [
        InlineQueryResultArticle(
            id=tictactoe_id,
            title="🎮 لعبة XO (إكس أو)",
            description="انقر لإرسال لعبة XO وابدأ التحدي مع صديقك في الشات",
            thumbnail_url="https://l.top4top.io/p_38579s38j0.png",
            input_message_content=InputTextMessageContent(
                message_text=f"🎮 **تحدي جديد في لعبة XO**\n\n👤 أنشأ التحدي: **{user.first_name}** (❌)\n⏳ في انتظار انضمام المنافس...",
                parse_mode="Markdown"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 انضم والعب كـ ⭕", callback_data=f"join_{tictactoe_id}")]])
        ),
        InlineQueryResultArticle(
            id=rps_id,
            title="✊ لعبة حجر ورقة مقص",
            description="انقر لإرسال تحدي حجر ورقة مقص وابدأ اللعب",
            thumbnail_url="https://i.top4top.io/p_385725ev60.png",
            input_message_content=InputTextMessageContent(
                message_text=f"✊ **تحدي حجر ورقة مقص**\n\n👤 أنشأ التحدي: **{user.first_name}**\n⏳ اضغط أدناه للانضمام والمنافسة:",
                parse_mode="Markdown"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎮 انضم للتحدي", callback_data=f"rps_join_{rps_id}")]])
        ),
        InlineQueryResultArticle(
            id=trap_id,
            title="💣 لعبة الصناديق المفخخة",
            description="انقر لإرسال لعبة الصناديق المفخخة وابدأ التحدي",
            thumbnail_url="https://a.top4top.io/p_3857irrvz0.png",
            input_message_content=InputTextMessageContent(
                message_text=f"💣 **تحدي الصناديق المفخخة**\n\n👤 أنشأ التحدي: **{user.first_name}**\n⏳ في انتظار انضمام المنافس...",
                parse_mode="Markdown"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏴‍☠️ انضم لتحدي الصناديق كـ منافس", callback_data=f"trap_join_{trap_id}")]])
        ),
        InlineQueryResultArticle(
            id=gold_id,
            title="🏴‍☠️ مغامرة جزيرة الكنز والأموال",
            description="انقر لإرسال مغامرة جزيرة الكنز وابدأ التحدي",
            thumbnail_url="https://e.top4top.io/p_3857v3rga0.png",
            input_message_content=InputTextMessageContent(
                message_text=f"🏴‍☠️ **مغامرة جزيرة الكنز والأموال**\n\n👤 أنشأ التحدي: **{user.first_name}**\n⏳ في انتظار انضمام المنافس...",
                parse_mode="Markdown"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 انضم إلى مغامرة الكنز كـ منافس", callback_data=f"gold_join_{gold_id}")]])
        ),
        InlineQueryResultArticle(
            id=bs_id,
            title="🚢 لعبة السفن الحربية",
            description="انقر لإرسال معركة السفن الحربية وابدأ التحدي",
            thumbnail_url="https://a.top4top.io/p_3857qjg8x0.png",
            input_message_content=InputTextMessageContent(
                message_text=f"⚓ **معركة السفن الحربية**\n\n👤 أنشأ التحدي: **{user.first_name}**\n⏳ في انتظار انضمام المنافس لبدء وضع السفن...",
                parse_mode="Markdown"
            ),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚓ انضم والعب كـ منافس", callback_data=f"bs_join_{bs_id}")]])
        ),
    ]
    await update.inline_query.answer(results, cache_time=1)


# ================= موجه الأزرار مع الحماية =================
async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = query.data

    if data == "check_sub":
        is_subscribed = await check_subscription(user.id, context)
        if is_subscribed:
            await query.answer("✅ تم التحقق بنجاح! يمكنك الآن اللعب بحرية.", show_alert=True)
            instructions = (
                f"🎉 أهلاً بك يا **{user.first_name}** مرة أخرى!\n\n"
                f"📖 **طريقة اللعب مع أصدقائك:**\n"
                f"• افتح أي محادثة أو مجموعة واكتب يوزر البوت: `@{BOT_USERNAME}`\n"
                f"• اختر إحدى الألعاب الخمسة من القائمة.\n"
                f"• اجعل صديقك يضغط على زر الانضمام المرفق مع الرسالة لتبدأ المنافسة!"
            )
            try:
                await query.edit_message_text(instructions, parse_mode="Markdown")
            except Exception:
                pass
        else:
            await query.answer("❌ عذراً، لم تقم بالاشتراك في القناة بعد!", show_alert=True)
        return

    is_subscribed = await check_subscription(user.id, context)
    if not is_subscribed:
        return await show_subscription_required(update)

    if data.startswith("rps_"):
        return await rps_button_handler(update, context)
    elif data.startswith("play_") or data.startswith("restart_") or data.startswith("join_") or data.startswith("tictactoe_"):
        return await tictactoe_button_handler(update, context)
    elif data.startswith("trap_"):
        return await traps_button_handler(update, context)
    elif data.startswith("gold_"):
        return await treasure_button_handler(update, context)
    elif data.startswith("bs_"):
        return await battleship_button_handler(update, context)


def main():
    TOKEN = os.getenv("TOKEN")

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(InlineQueryHandler(inline_query_handler))
    application.add_handler(CallbackQueryHandler(button_router))

    logger.info("Bot is running with all 5 games (XO, RPS, Traps, Treasure, Battleship)...")
    application.run_polling()


if __name__ == "__main__":
    main()
