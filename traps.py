import random
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

active_trap_games = {}

GRID_ROWS = 10                  # تقليص الشبكة قليلاً لتناسب أزرار الشات بشكل ممتاز
GRID_COLS = 8                  
TOTAL_BOXES = GRID_ROWS * GRID_COLS
TOTAL_TRAPS = 10                


def get_trap_board_keyboard(game_id, opened_safe, opened_traps):
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
                text = "📦"
                callback_data = f"trap_open_{game_id}_{box_idx}"
            
            row_buttons.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(row_buttons)
    return InlineKeyboardMarkup(keyboard)


async def traps_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id if update.effective_chat else None
    
    # معرف فريد متوافق مع نظام الإنلاين المباشر داخل الشات
    game_id = f"trap_inline_{chat_id}_{user.id}"
    trap_indices = random.sample(range(TOTAL_BOXES), TOTAL_TRAPS)

    active_trap_games[game_id] = {
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

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏴‍☠️ انضم لتحدي الصناديق كـ منافس", callback_data=f"trap_join_{game_id}")]
    ])

    text = (
        f"💣 **تحدي الصناديق المفخخة**\n\n"
        f"👤 أنشأ التحدي: **{user.first_name}**\n"
        f"⏳ في انتظار انضمام المنافس..."
    )

    if update.message:
        msg = await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
        active_trap_games[game_id]["msg_id"] = msg.message_id


async def traps_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if data == "none":
        return

    # معالجة انضمام اللاعب الثاني مباشرة في نفس الرسالة
    if data.startswith("trap_join_"):
        game_id = data.replace("trap_join_", "")
        if game_id not in active_trap_games:
            await query.answer("انتهت صلاحية هذه اللعبة.", show_alert=True)
            return

        game = active_trap_games[game_id]

        if game["player_1"] == user.id:
            await query.answer("لا يمكنك اللعب ضد نفسك!", show_alert=True)
            return

        if game["player_2"] is not None:
            await query.answer("اللعبة مكتملة اللاعبين بالفعل!", show_alert=True)
            return

        game["player_2"] = user.id
        game["name_2"] = user.first_name
        game["turn"] = game["player_1"]
        game["status"] = "playing"

        kb = get_trap_board_keyboard(game_id, game["opened_safe"], game["opened_traps"])
        text = (
            f"🏴‍☠️ **معركة الصناديق المفخخة**\n\n"
            f"👤 {game['name_1']} (تفجيرات: {game['hits_1']}) ضد 👤 {game['name_2']} (تفجيرات: {game['hits_2']})\n\n"
            f"🎯 **دور اللاعب للهجوم:** {game['name_1']}"
        )

        try:
            await query.edit_message_text(text=text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass
        return

    # معالجة فتح الصناديق
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

    # التحقق من نهاية اللعبة (عند اكتشاف جميع الفخوخ أو نهايتها)
    if len(game["opened_traps"]) == TOTAL_TRAPS:
        game["status"] = "over"
        h1 = game["hits_1"]
        h2 = game["hits_2"]
        n1 = game["name_1"]
        n2 = game["name_2"]

        if h1 < h2:
            winner_name = n1
        elif h2 < h1:
            winner_name = n2
        else:
            winner_name = None

        if winner_name:
            text_over = f"🏁 **انتهت المعركة وتم كشف كافة الفخوخ!**\n\n📊 النتائج:\n- {n1}: {h1} تفجيرات\n- {n2}: {h2} تفجيرات\n\n🎉 **الفائز هو الكابتن {winner_name}** (أقل تفجيرات)! 🏆"
        else:
            text_over = f"🏁 **انتهت المعركة وتم كشف كافة الفخوخ!**\n\n📊 النتائج:\n- {n1}: {h1} تفجيرات\n- {n2}: {h2} تفجيرات\n\n🤝 **تعادل تام بين القرصانين!** ⚓"

        kb = get_trap_board_keyboard(game_id, game["opened_safe"], game["opened_traps"])
        try:
            await query.edit_message_text(text=text_over, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass
        return
    else:
        game["turn"] = game["player_2"] if is_p1 else game["player_1"]
        kb = get_trap_board_keyboard(game_id, game["opened_safe"], game["opened_traps"])

        status_msg = f"💥 وقع في فخ!" if hit_trap else f"✅ فتح صندوقاً آمناً."
        text = (
            f"🏴‍☠️ **معركة الصناديق المفخخة**\n\n"
            f"👤 {game['name_1']} (تفجيرات: {game['hits_1']}) ضد 👤 {game['name_2']} (تفجيرات: {game['hits_2']})\n\n"
            f"آخر حدث: {current_name} {status_msg}\n"
            f"🎯 **دور اللاعب للهجوم:** {other_name}"
        )

        try:
            await query.edit_message_text(text=text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass
