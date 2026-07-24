import random
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

active_gold_games = {}
BOT_USERNAME = "SgameHbot"

# أبعاد الشبكة: 10 صفوف × 8 أعمدة (إجمالي 80 صندوق كنز)
GRID_ROWS = 10                  
GRID_COLS = 8                  
TOTAL_CELLS = GRID_ROWS * GRID_COLS

# تحديد قيم النقاط لكل عنصر (فضة، ذهب، فلوس، عملات)
VALUES = {
    "silver": 20,    # 🥈 فضة
    "gold": 50,      # 🪙 ذهب
    "cash": 35,      # 💵 فلوس
    "coins": 40,     # 💰 عملات
    "empty": 0       # 📭 فارغ
}


def calculate_score(collected_dict):
    """حساب المجموع الكلي للنقاط بناءً على العناصر المجمعة"""
    return (
        (collected_dict["silver"] * VALUES["silver"]) + 
        (collected_dict["gold"] * VALUES["gold"]) + 
        (collected_dict["cash"] * VALUES["cash"]) +
        (collected_dict["coins"] * VALUES["coins"])
    )


def get_board_kb(game_id, board_state):
    """إنشاء لوحة الأزرار بحجم 10×8 مع صندوق كنز مغلق وشكل الأيموجي عند فتحه بدلاً من الكتابة"""
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
                text = "🎁"  # شكل الكنز المغلق
                callback_data = f"gold_open_{game_id}_{cell_idx}"
            row_buttons.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(row_buttons)
    return InlineKeyboardMarkup(keyboard)


async def treasure_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    chat_id = update.effective_chat.id

    if args and args[0].startswith("gold_"):
        game_id = args[0]

        if game_id not in active_gold_games:
            cells = list(range(TOTAL_CELLS))
            random.shuffle(cells)
            
            empty_count = 5
            empty_cells = set(cells[:empty_count])
            remaining_cells = cells[empty_count:]
            
            n = len(remaining_cells)
            silver_count = int(n * 0.25)
            gold_count = int(n * 0.25)
            cash_count = int(n * 0.25)
            
            silver_cells = set(remaining_cells[:silver_count])
            gold_cells = set(remaining_cells[silver_count:silver_count+gold_count])
            cash_cells = set(remaining_cells[silver_count+gold_count:silver_count+gold_count+cash_count])
            coins_cells = set(remaining_cells[silver_count+gold_count+cash_count:])
            
            active_gold_games[game_id] = {
                "player_1": user.id,
                "chat_1": chat_id,
                "name_1": user.first_name,
                "player_2": None,
                "chat_2": None,
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
                "msg_id_1": None,
                "msg_id_2": None,
                "status": "playing"
            }
            await update.message.reply_text(
                f"🏴‍☠️ أهلاً بك يا كابتن {user.first_name} في مغامرة جزيرة الكنز !\n\n"
                f"🔗 شارك هذا الرابط مع صديقك لتبدأ المعركة الثنائية:\n"
                f"https://t.me/{BOT_USERNAME}?start={game_id}"
            )
            return

        game = active_gold_games[game_id]

        if game["player_2"] is None and game["player_1"] != user.id:
            game["player_2"] = user.id
            game["chat_2"] = chat_id
            game["name_2"] = user.first_name
            game["turn"] = game["player_1"]

            kb = get_board_kb(game_id, game["board_state"])
            
            score_1 = calculate_score(game["collected_1"])
            score_2 = calculate_score(game["collected_2"])
            c1 = game["collected_1"]
            c2 = game["collected_2"]

            status_header = (
                f"💎 **جزيرة الكنوز والأموال ** 💎\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **{game['name_1']}** ⟵ إجمالي النقاط: **{score_1}** ⭐\n"
                f"🥈:{c1['silver']} | 🪙:{c1['gold']} | 💵:{c1['cash']} | 💰:{c1['coins']} | 📭:{c1['empty']}\n"
                f"-----------------------------------\n"
                f"👤 **{game['name_2']}** ⟵ إجمالي النقاط: **{score_2}** ⭐\n"
                f"🥈:{c2['silver']} | 🪙:{c2['gold']} | 💵:{c2['cash']} | 💰:{c2['coins']} | 📭:{c2['empty']}\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
            )
            
            text_p1 = status_header + f"🎯 **دورك الآن يا {game['name_1']}! اختر صندوق كنز 🎁:**"
            text_p2 = status_header + f"⏳ **دور خصمك {game['name_1']}، ترقب الحظ...**"

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

    game_id = f"gold_{user.id}"
    cells = list(range(TOTAL_CELLS))
    random.shuffle(cells)
    
    empty_count = 5
    empty_cells = set(cells[:empty_count])
    remaining_cells = cells[empty_count:]
    
    n = len(remaining_cells)
    silver_count = int(n * 0.25)
    gold_count = int(n * 0.25)
    cash_count = int(n * 0.25)
    
    silver_cells = set(remaining_cells[:silver_count])
    gold_cells = set(remaining_cells[silver_count:silver_count+gold_count])
    cash_cells = set(remaining_cells[silver_count+gold_count:silver_count+gold_count+cash_count])
    coins_cells = set(remaining_cells[silver_count+gold_count+cash_count:])

    active_gold_games[game_id] = {
        "player_1": user.id,
        "chat_1": chat_id,
        "name_1": user.first_name,
        "player_2": None,
        "chat_2": None,
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
        "msg_id_1": None,
        "msg_id_2": None,
        "status": "playing"
    }

    invite_link = f"https://t.me/{BOT_USERNAME}?start={game_id}"
    await update.message.reply_text(
        f"🏴‍☠️ أهلاً بك يا {user.first_name} في جزيرة الكنوز والأموال!\n\n"
        f"لقد أنشأت جلسة جديدة خاصة بك.\n"
        f"🔗 رابط دعوة الصديق:\n"
        f"https://t.me/{BOT_USERNAME}?start={game_id}\n\n"
        f"قم بنسخ هذا الرابط وأرسله لصديقك، وبمجرد دخوله ستبدأ اللعبة تلقائياً!"
    )


async def treasure_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if data == "none":
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

    if cell_idx in game["silver_cells"]:
        cell_type = "silver"
    elif cell_idx in game["gold_cells"]:
        cell_type = "gold"
    elif cell_idx in game["cash_cells"]:
        cell_type = "cash"
    elif cell_idx in game["coins_cells"]:
        cell_type = "coins"
    else:
        cell_type = "empty"

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
            f"🏆 **انتهت معركة فتح جميع الصناديق بالكامل!** 🏆\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 **تحليل نتائج الكابتن {n1}:**\n"
            f"• 🥈 فضة: {c1['silver']} (قيمتها: {c1['silver'] * VALUES['silver']} نقطة)\n"
            f"• 🪙 ذهب: {c1['gold']} (قيمتها: {c1['gold'] * VALUES['gold']} نقطة)\n"
            f"• 💵 فلوس: {c1['cash']} (قيمتها: {c1['cash'] * VALUES['cash']} نقطة)\n"
            f"• 💰 عملات: {c1['coins']} (قيمتها: {c1['coins'] * VALUES['coins']} نقطة)\n"
            f"• 📭 فارغ: {c1['empty']}\n"
            f"⭐ **إجمالي النقاط: {score_1} نقطة**\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **تحليل نتائج الكابتن {n2}:**\n"
            f"• 🥈 فضة: {c2['silver']} (قيمتها: {c2['silver'] * VALUES['silver']} نقطة)\n"
            f"• 🪙 ذهب: {c2['gold']} (قيمتها: {c2['gold'] * VALUES['gold']} نقطة)\n"
            f"• 💵 فلوس: {c2['cash']} (قيمتها: {c2['cash'] * VALUES['cash']} نقطة)\n"
            f"• 💰 عملات: {c2['coins']} (قيمتها: {c2['coins'] * VALUES['coins']} نقطة)\n"
            f"• 📭 فارغ: {c2['empty']}\n"
            f"⭐ **إجمالي النقاط: {score_2} نقطة**\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
        )

        if score_1 > score_2:
            text_over += f"🎉 **الفائز هو الكابتن {n1}** لإحرازه أعلى إجمالي نقاط في التحليل! 👑"
        elif score_2 > score_1:
            text_over += f"🎉 **الفائز هو الكابتن {n2}** لإحرازه أعلى إجمالي نقاط في التحليل! 👑"
        else:
            text_over += f"🤝 **تعادل تام في النقاط والإحصائيات بين الطرفين!**"

        kb = get_board_kb(game_id, game["board_state"])
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
        kb = get_board_kb(game_id, game["board_state"])

        status_header_p1 = (
            f"💎 **جزيرة الكنوز والأموال ** 💎\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 أنت (**{game['name_1']}**) ⟵ إجمالي النقاط: **{score_1}** ⭐\n"
            f"🥈:{c1['silver']} | 🪙:{c1['gold']} | 💵:{c1['cash']} | 💰:{c1['coins']} | 📭:{c1['empty']}\n"
            f"-----------------------------------\n"
            f"👤 خصمك (**{game['name_2']}**) ⟵ إجمالي النقاط: **{score_2}** ⭐\n"
            f"🥈:{c2['silver']} | 🪙:{c2['gold']} | 💵:{c2['cash']} | 💰:{c2['coins']} | 📭:{c2['empty']}\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
        )
        status_header_p2 = (
            f"💎 **جزيرة الكنوز والأموال ** 💎\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 أنت (**{game['name_2']}**) ⟵ إجمالي النقاط: **{score_2}** ⭐\n"
            f"🥈:{c2['silver']} | 🪙:{c2['gold']} | 💵:{c2['cash']} | 💰:{c2['coins']} | 📭:{c2['empty']}\n"
            f"-----------------------------------\n"
            f"👤 خصمك (**{game['name_1']}**) ⟵ إجمالي النقاط: **{score_1}** ⭐\n"
            f"🥈:{c1['silver']} | 🪙:{c1['gold']} | 💵:{c1['cash']} | 💰:{c1['coins']} | 📭:{c1['empty']}\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
        )

        if cell_type == "silver":
            msg_p1_action = f"🥈 **جيد!** وجدنت فضة (+20 نقطة).\n⏳ دور خصمك {other_name}، انتظر..." if is_p1 else f"🥈 وجد خصمك {current_name} فضة (+20 نقطة).\n🎯 **دورك لاختيار صندوق 🎁:**"
            msg_p2_action = f"🥈 وجد خصمك {current_name} فضة (+20 نقطة).\n🎯 **دورك لاختيار صندوق 🎁:**" if is_p1 else f"🥈 **جيد!** وجدنت فضة (+20 نقطة).\n⏳ دور خصمك {other_name}، انتظر..."
        elif cell_type == "gold":
            msg_p1_action = f"🪙 **رائع!** وجدت ذهباً (+50 نقطة).\n⏳ دور خصمك {other_name}، انتظر..." if is_p1 else f"🪙 وجد خصمك {current_name} ذهباً (+50 نقطة).\n🎯 **دورك لاختيار صندوق 🎁:**"
            msg_p2_action = f"🪙 وجد خصمك {current_name} ذهباً (+50 نقطة).\n🎯 **دورك لاختيار صندوق 🎁:**" if is_p1 else f"🪙 **رائع!** وجدت ذهباً (+50 نقطة).\n⏳ دور خصمك {other_name}، انتظر..."
        elif cell_type == "cash":
            msg_p1_action = f"💵 **ممتاز!** وجدت فلوساً (+35 نقطة).\n⏳ دور خصمك {other_name}، انتظر..." if is_p1 else f"💵 وجد خصمك {current_name} فلوساً (+35 نقطة).\n🎯 **دورك لاختيار صندوق 🎁:**"
            msg_p2_action = f"💵 وجد خصمك {current_name} فلوساً (+35 نقطة).\n🎯 **دورك لاختيار صندوق 🎁:**" if is_p1 else f"💵 **ممتاز!** وجدت فلوساً (+35 نقطة).\n⏳ دور خصمك {other_name}، انتظر..."
        elif cell_type == "coins":
            msg_p1_action = f"💰 **حظ عظيم!** وجدت عملات معدنية (+40 نقطة).\n⏳ دور خصمك {other_name}، انتظر..." if is_p1 else f"💰 وجد خصمك {current_name} عملات معدنية (+40 نقطة).\n🎯 **دورك لاختيار صندوق 🎁:**"
            msg_p2_action = f"💰 وجد خصمك {current_name} عملات معدنية (+40 نقطة).\n🎯 **دورك لاختيار صندوق 🎁:**" if is_p1 else f"💰 **حظ عظيم!** وجدت عملات معدنية (+40 نقطة).\n⏳ دور خصمك {other_name}، انتظر..."
        else:
            msg_p1_action = f"📭 عذراً، هذا الكنز كان فارغاً!\n⏳ دور خصمك {other_name}، انتظر..." if is_p1 else f"📭 وقع خصمك {current_name} في كنز فارغ.\n🎯 **دورك لاختيار صندوق 🎁:**"
            msg_p2_action = f"📭 وقع خصمك {current_name} في كنز فارغ.\n🎯 **دورك لاختيار صندوق 🎁:**" if is_p1 else f"📭 عذراً، هذا الكنز كان فارغاً!\n⏳ دور خصمك {other_name}، انتظر..."

        try:
            if game["msg_id_1"]:
                await context.bot.edit_message_text(chat_id=game["chat_1"], message_id=game["msg_id_1"], text=status_header_p1 + msg_p1_action, reply_markup=kb, parse_mode="Markdown")
            if game["msg_id_2"]:
                await context.bot.edit_message_text(chat_id=game["chat_2"], message_id=game["msg_id_2"], text=status_header_p2 + msg_p2_action, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass
