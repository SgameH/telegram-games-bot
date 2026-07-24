import random
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

active_trap_games = {}
BOT_USERNAME = "SgameHbot"

# تعديل الأبعاد لتصبح 10 صفوف و 8 أعمدة (إجمالي 80 صندوقاً)
GRID_ROWS = 10                  
GRID_COLS = 8                  
TOTAL_BOXES = GRID_ROWS * GRID_COLS
TOTAL_TRAPS = 10                # إجمالي الصناديق المفخخة في الشبكة


def get_trap_board_keyboard(game_id, opened_safe, opened_traps):
    """إنشاء أزرار الصناديق بحجم 10 صفوف × 8 أعمدة مع استخدام علامة الصح ✅ للصناديق الآمنة"""
    keyboard = []
    for r in range(GRID_ROWS):
        row_buttons = []
        for c in range(GRID_COLS):
            box_idx = r * GRID_COLS + c
            
            if box_idx in opened_safe:
                text = "✅"
                callback_data = "none"
            elif box_idx in opened_traps:
                text = "💥"
                callback_data = "none"
            else:
                text = f"📦 {r+1},{c+1}"
                callback_data = f"trap_open_{game_id}_{box_idx}"
            
            row_buttons.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(row_buttons)
    return InlineKeyboardMarkup(keyboard)


async def traps_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    chat_id = update.effective_chat.id

    if args and args[0].startswith("trap_"):
        game_id = args[0]

        if game_id not in active_trap_games:
            # توزيع 10 فخوخ عشوائياً بين الـ 80 صندوقاً
            trap_indices = random.sample(range(TOTAL_BOXES), TOTAL_TRAPS)
            
            active_trap_games[game_id] = {
                "player_1": user.id,
                "chat_1": chat_id,
                "name_1": user.first_name,
                "player_2": None,
                "chat_2": None,
                "name_2": "بانتظار قرصان...",
                "trap_indices": trap_indices,
                "opened_safe": [],
                "opened_traps": [],
                "hits_1": 0,
                "hits_2": 0,
                "turn": None,
                "msg_id_1": None,
                "msg_id_2": None,
                "status": "playing"
            }
            await update.message.reply_text(
                f"🏴‍☠️ أهلاً بك يا كابتن {user.first_name} في تحدي الصناديق الكبرى !\n\n"
                f"🔗 شارك هذا الرابط مع صديقك ليدخل معك في التحدي:\n"
                f"https://t.me/{BOT_USERNAME}?start={game_id}"
            )
            return

        game = active_trap_games[game_id]

        if game["player_2"] is None and game["player_1"] != user.id:
            game["player_2"] = user.id
            game["chat_2"] = chat_id
            game["name_2"] = user.first_name
            game["turn"] = game["player_1"]

            kb = get_trap_board_keyboard(game_id, game["opened_safe"], game["opened_traps"])
            
            text_p1 = f"🏴‍☠️ **معركة الصناديق **\n👤 أنت: {game['name_1']} | تفجيراتك: {game['hits_1']}\n👤 خصمك: {game['name_2']} | تفجيراته: {game['hits_2']}\n\n🎯 **دورك الآن! اختر صندوقاً:**"
            text_p2 = f"🏴‍☠️ **معركة الصناديق **\n👤 أنت: {game['name_2']} | تفجيراتك: {game['hits_2']}\n👤 خصمك: {game['name_1']} | تفجيراته: {game['hits_1']}\n\n⏳ **دور خصمك {game['name_1']}، انتظر...**"

            try:
                msg_1 = await context.bot.send_message(chat_id=game["chat_1"], text=text_p1, reply_markup=kb, parse_mode="Markdown")
                game["msg_id_1"] = msg_1.message_id

                msg_2 = await context.bot.send_message(chat_id=game["chat_2"], text=text_p2, reply_markup=kb, parse_mode="Markdown")
                game["msg_id_2"] = msg_2.message_id
            except Exception:
                pass
            return

        elif game["player_1"] == user.id or game["player_2"] == user.id:
            await update.message.reply_text("أنت مشارك بالفعل في هذه اللعبة!")
            return
        else:
            await update.message.reply_text("عذراً، هذه المعركة مكتملة وقائمة بالفعل!")
            return

    game_id = f"trap_{user.id}"
    trap_indices = random.sample(range(TOTAL_BOXES), TOTAL_TRAPS)

    active_trap_games[game_id] = {
        "player_1": user.id,
        "chat_1": chat_id,
        "name_1": user.first_name,
        "player_2": None,
        "chat_2": None,
        "name_2": "بانتظار قرصان...",
        "trap_indices": trap_indices,
        "opened_safe": [],
        "opened_traps": [],
        "hits_1": 0,
        "hits_2": 0,
        "turn": None,
        "msg_id_1": None,
        "msg_id_2": None,
        "status": "playing"
    }

    invite_link = f"https://t.me/{BOT_USERNAME}?start={game_id}"
    await update.message.reply_text(
                f"💣 أهلاً بك يا {user.first_name} في تحدي الصناديق المفخخة!\n\n"
                f"لقد أنشأت جلسة جديدة خاصة بك.\n"
                f"🔗 رابط دعوة الصديق:\n"
                f"https://t.me/{BOT_USERNAME}?start={game_id}\n\n"
                f"قم بنسخ هذا الرابط وأرسله لصديقك، وبمجرد دخوله ستبدأ اللعبة تلقائياً!"
            )


async def traps_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if data == "none":
        return

    game_id = None
    box_idx = None

    if data.startswith("trap_open_"):
        parts = data.split("_")
        if len(parts) >= 4:
            box_idx = int(parts[-1])
            game_id = "_".join(parts[2:-1])

    if not game_id or game_id not in active_trap_games:
        await query.answer("انتهت صلاحية اللعبة أو أن البيانات غير صالحة.", show_alert=True)
        return

    game = active_trap_games[game_id]

    if game["status"] != "playing":
        return

    if game["turn"] != user.id:
        await query.answer("ليس دورك الآن لفتح صندوق!", show_alert=True)
        return

    if box_idx in game["opened_safe"] or box_idx in game["opened_traps"]:
        await query.answer("هذا الصندوق مفتوح مسبقاً!", show_alert=True)
        return

    is_p1 = (user.id == game["player_1"])
    current_name = game["name_1"] if is_p1 else game["name_2"]
    other_name = game["name_2"] if is_p1 else game["name_1"]

    hit_trap = (box_idx in game["trap_indices"])

    if hit_trap:
        game["opened_traps"].append(box_idx)
        if is_p1:
            game["hits_1"] += 1
        else:
            game["hits_2"] += 1
    else:
        game["opened_safe"].append(box_idx)

    if len(game["opened_traps"]) == TOTAL_TRAPS:
        game["status"] = "over"
        h1 = game["hits_1"]
        h2 = game["hits_2"]
        n1 = game["name_1"]
        n2 = game["name_2"]

        if h1 > h2:
            text_over = f"🏁 **انتهت اللعبة واكتشفت جميع الفخوخ العشرة!**\n📊 النتائج:\n- {n1}: {h1} تفجيرات\n- {n2}: {h2} تفجيرات\n\n🎉 الفوز من نصيب الكابتن **{n2}** (أقل تفجيرات)! 🏆"
        elif h2 > h1:
            text_over = f"🏁 **انتهت اللعبة واكتشفت جميع الفخوخ العشرة!**\n📊 النتائج:\n- {n1}: {h1} تفجيرات\n- {n2}: {h2} تفجيرات\n\n🎉 الفوز من نصيب الكابتن **{n1}** (أقل تفجيرات)! 🏆"
        else:
            text_over = f"🏁 **انتهت اللعبة واكتشفت جميع الفخوخ العشرة!**\n📊 النتائج:\n- {n1}: {h1} تفجيرات\n- {n2}: {h2} تفجيرات\n\n🤝 **تعادل تام بين القرصانين!** ⚓"

        kb = get_trap_board_keyboard(game_id, game["opened_safe"], game["opened_traps"])
        try:
            if game["msg_id_1"]:
                await context.bot.edit_message_text(chat_id=game["chat_1"], message_id=game["msg_id_1"], text=text_over, reply_markup=kb, parse_mode="Markdown")
            if game["msg_id_2"]:
                await context.bot.edit_message_text(chat_id=game["chat_2"], message_id=game["msg_id_2"], text=text_over, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass
        return
    else:
        game["turn"] = game["player_2"] if is_p1 else game["player_1"]
        kb = get_trap_board_keyboard(game_id, game["opened_safe"], game["opened_traps"])

        text_p1_info = f"🏴‍☠️ **معركة الصناديق **\n👤 أنت: {game['name_1']} | تفجيراتك: {game['hits_1']}\n👤 خصمك: {game['name_2']} | تفجيراته: {game['hits_2']}\n\n"
        text_p2_info = f"🏴‍☠️ **معركة الصناديق **\n👤 أنت: {game['name_2']} | تفجيراتك: {game['hits_2']}\n👤 خصمك: {game['name_1']} | تفجيراته: {game['hits_1']}\n\n"

        if hit_trap:
            text_current = f"💥 **يا للأسف!** وقعت في صندوق مفخخ!\n⏳ دور {other_name}، انتظر..."
            text_next = f"💥 **انفجار عند خصمك!** وقع في صندوق مفخخ.\n🎯 **دورك الآن لاختيار صندوق:**"
        else:
            text_current = f"✅ فتحت صندوقاً **آمناً**.\n⏳ دور {other_name}، انتظر..."
            text_next = f"✅ فتح {current_name} صندوقاً **آمناً**.\n🎯 **دورك الآن لاختيار صندوق:**"

        try:
            if game["msg_id_1"]:
                await context.bot.edit_message_text(chat_id=game["chat_1"], message_id=game["msg_id_1"], text=text_p1_info + (text_current if is_p1 else text_next), reply_markup=kb, parse_mode="Markdown")
            if game["msg_id_2"]:
                await context.bot.edit_message_text(chat_id=game["chat_2"], message_id=game["msg_id_2"], text=text_p2_info + (text_next if is_p1 else text_current), reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass
