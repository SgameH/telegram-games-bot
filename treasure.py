import random
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

active_gold_games = {}

GRID_ROWS = 10                  
GRID_COLS = 8                  
TOTAL_CELLS = GRID_ROWS * GRID_COLS

VALUES = {
    "silver": 20,    
    "gold": 50,      
    "cash": 35,      
    "coins": 40,     
    "empty": 0       
}


def calculate_score(collected_dict):
    return (
        (collected_dict["silver"] * VALUES["silver"]) + 
        (collected_dict["gold"] * VALUES["gold"]) + 
        (collected_dict["cash"] * VALUES["cash"]) +
        (collected_dict["coins"] * VALUES["coins"])
    )


def get_board_kb(game_id, board_state):
    keyboard = []
    for r in range(GRID_ROWS):
        row_buttons = []
        for c in range(GRID_COLS):
            cell_idx = r * GRID_COLS + c
            if cell_idx in board_state:
                val = board_state[cell_idx]
                if val == "silver":
                    text = "🥈"
                elif val == "gold":
                    text = "🪙"
                elif val == "cash":
                    text = "💵"
                elif val == "coins":
                    text = "💰"
                elif val == "empty":
                    text = "📭"
                callback_data = "none"
            else:
                text = "🎁"  
                callback_data = f"gold_open_{game_id}_{cell_idx}"
            row_buttons.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(row_buttons)
    return InlineKeyboardMarkup(keyboard)


async def treasure_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id if update.effective_chat else None
    
    game_id = f"gold_inline_{chat_id}_{user.id}"
    
    cells = list(range(TOTAL_CELLS))
    random.shuffle(cells)
    
    # تحديد 3 صناديق فارغة بدقة والباقي للكنوز عشوائياً
    empty_cells = set(cells[:3])
    remaining_cells = cells[3:]
    
    # خلط الباقي عشوائياً لتوزيع الكنوز بشكل عشوائي تام
    random.shuffle(remaining_cells)
    
    n = len(remaining_cells)
    part = n // 4
    
    silver_cells = set(remaining_cells[:part])
    gold_cells = set(remaining_cells[part:part*2])
    cash_cells = set(remaining_cells[part*2:part*3])
    coins_cells = set(remaining_cells[part*3:])

    active_gold_games[game_id] = {
        "player_1": user.id,
        "name_1": user.first_name,
        "player_2": None,
        "name_2": "بانتظار منافس...",
        "empty_cells": empty_cells,
        "silver_cells": silver_cells,
        "gold_cells": gold_cells,
        "cash_cells": cash_cells,
        "coins_cells": coins_cells,
        "board_state": {},
        "collected_1": {"silver": 0, "gold": 0, "cash": 0, "coins": 0, "empty": 0},
        "collected_2": {"silver": 0, "gold": 0, "cash": 0, "coins": 0, "empty": 0},
        "turn": None,
        "msg_id": None,
        "status": "waiting"
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 انضم إلى مغامرة الكنز كـ منافس", callback_data=f"gold_join_{game_id}")]
    ])

    text = (
        f"🏴‍☠️ **مغامرة جزيرة الكنز والأموال**\n\n"
        f"👤 أنشأ التحدي: **{user.first_name}**\n"
        f"⏳ في انتظار انضمام المنافس..."
    )

    if update.message:
        msg = await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
        active_gold_games[game_id]["msg_id"] = msg.message_id


async def treasure_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if data == "none":
        return

    if data.startswith("gold_join_"):
        game_id = data.replace("gold_join_", "")
        if game_id not in active_gold_games:
            await query.answer("انتهت صلاحية هذه اللعبة.", show_alert=True)
            return

        game = active_gold_games[game_id]

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

        kb = get_board_kb(game_id, game["board_state"])
        score_1 = calculate_score(game["collected_1"])
        score_2 = calculate_score(game["collected_2"])
        c1 = game["collected_1"]
        c2 = game["collected_2"]

        status_header = (
            f"💎 **جزيرة الكنوز والأموال** 💎\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **{game['name_1']}** ⟵ النقاط: **{score_1}** ⭐ (🥈:{c1['silver']} | 🪙:{c1['gold']} | 💵:{c1['cash']} | 💰:{c1['coins']})\n"
            f"👤 **{game['name_2']}** ⟵ النقاط: **{score_2}** ⭐ (🥈:{c2['silver']} | 🪙:{c2['gold']} | 💵:{c2['cash']} | 💰:{c2['coins']})\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
        )
        text = status_header + f"🎯 **دور اللاعب الآن:** {game['name_1']} (اختر صندوق كنز 🎁)"

        try:
            await query.edit_message_text(text=text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass
        return

    game_id = None
    cell_idx = None

    if data.startswith("gold_open_"):
        parts = data.split("_")
        if len(parts) >= 4:
            cell_idx = int(parts[-1])
            game_id = "_".join(parts[2:-1])

    if not game_id or game_id not in active_gold_games:
        await query.answer("انتهت صلاحية اللعبة أو أن البيانات غير صالحة.", show_alert=True)
        return

    game = active_gold_games[game_id]

    if game["status"] != "playing":
        return

    if game["turn"] != user.id:
        await query.answer("ليس دورك الآن!", show_alert=True)
        return

    if cell_idx in game["board_state"]:
        await query.answer("تم فتح صندوق الكنز هذا مسبقاً!", show_alert=True)
        return

    is_p1 = (user.id == game["player_1"])
    current_name = game["name_1"] if is_p1 else game["name_2"]
    other_name = game["name_2"] if is_p1 else game["name_1"]

    if cell_idx in game["empty_cells"]:
        cell_type = "empty"
    elif cell_idx in game["silver_cells"]:
        cell_type = "silver"
    elif cell_idx in game["gold_cells"]:
        cell_type = "gold"
    elif cell_idx in game["cash_cells"]:
        cell_type = "cash"
    else:
        cell_type = "coins"

    game["board_state"][cell_idx] = cell_type

    target_collected = game["collected_1"] if is_p1 else game["collected_2"]
    target_collected[cell_type] += 1

    score_1 = calculate_score(game["collected_1"])
    score_2 = calculate_score(game["collected_2"])
    c1 = game["collected_1"]
    c2 = game["collected_2"]

    if len(game["board_state"]) >= TOTAL_CELLS:
        game["status"] = "over"
        n1 = game["name_1"]
        n2 = game["name_2"]

        text_over = (
            f"🏆 **انتهت معركة فتح كافة الصناديق!** 🏆\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 **{n1}** ⟵ إجمالي النقاط: **{score_1}** ⭐\n"
            f"👤 **{n2}** ⟵ إجمالي النقاط: **{score_2}** ⭐\n\n"
        )

        if score_1 > score_2:
            text_over += f"🎉 **الفائز هو الكابتن {n1}** لإحرازه أعلى نقاط! 👑"
        elif score_2 > score_1:
            text_over += f"🎉 **الفائز هو الكابتن {n2}** لإحرازه أعلى نقاط! 👑"
        else:
            text_over += f"🤝 **تعادل تام في النقاط بين الطرفين!**"

        kb = get_board_kb(game_id, game["board_state"])
        try:
            await query.edit_message_text(text=text_over, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass
        return
    else:
        game["turn"] = game["player_2"] if is_p1 else game["player_1"]
        kb = get_board_kb(game_id, game["board_state"])

        status_header = (
            f"💎 **جزيرة الكنوز والأموال** 💎\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **{game['name_1']}** ⟵ النقاط: **{score_1}** ⭐ (🥈:{c1['silver']} | 🪙:{c1['gold']} | 💵:{c1['cash']} | 💰:{c1['coins']})\n"
            f"👤 **{game['name_2']}** ⟵ النقاط: **{score_2}** ⭐ (🥈:{c2['silver']} | 🪙:{c2['gold']} | 💵:{c2['cash']} | 💰:{c2['coins']})\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
        )

        if cell_type == "silver":
            action_desc = f"🥈 وجد {current_name} فضة (+20 نقطة)."
        elif cell_type == "gold":
            action_desc = f"🪙 وجد {current_name} ذهباً رائعاً (+50 نقطة)."
        elif cell_type == "cash":
            action_desc = f"💵 وجد {current_name} أموالاً (+35 نقطة)."
        elif cell_type == "coins":
            action_desc = f"💰 وجد {current_name} عملات معدنية (+40 نقطة)."
        else:
            action_desc = f"📭 كنز فارغ وقع فيه {current_name}!"

        text = status_header + f"آخر حدث: {action_desc}\n🎯 **دور اللاعب الآن:** {other_name} (اختر صندوق كنز 🎁)"

        try:
            await query.edit_message_text(text=text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass
