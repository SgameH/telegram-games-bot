import random
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

active_battleship_games = {}
BOT_USERNAME = "SgameHbot"
TOTAL_SHIPS = 3
GRID_SIZE = 7


def create_empty_grid():
    return [["·" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]


def get_setup_keyboard(game_id, player_num):
    keyboard = []
    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            row.append(InlineKeyboardButton("🟦 مربع", callback_data=f"bs_set_{game_id}_{player_num}_{r}_{c}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def get_game_board_keyboard(grid, game_id):
    keyboard = []
    for r in range(GRID_SIZE):
        row_buttons = []
        for c in range(GRID_SIZE):
            cell = grid[r][c]
            if cell == "·":
                text = "🎯 إطلاق"
                callback_data = f"bs_att_{game_id}_{r}_{c}"
            else:
                text = cell
                callback_data = "none"
            row_buttons.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(row_buttons)
    return InlineKeyboardMarkup(keyboard)


async def battleship_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    chat_id = update.effective_chat.id

    if args and args[0].startswith("bs_"):
        game_id = args[0]

        if game_id not in active_battleship_games:
            active_battleship_games[game_id] = {
                "player_1": user.id,
                "chat_1": chat_id,
                "name_1": user.first_name,
                "player_2": None,
                "chat_2": None,
                "name_2": "بانتظار لاعب...",
                "ships_1": [],
                "ships_2": [],
                "shared_grid": create_empty_grid(),
                "turn": None,
                "msg_id_1": None,
                "msg_id_2": None,
                "status": "setup"
            }
            await update.message.reply_text(
                f"⚓ أهلاً بك يا {user.first_name} في معركة السفن الحربية!\n\n"
                f"🔗 شارك هذا الرابط مع صديقك ليبدأ التحدي:\n"
                f"https://t.me/{BOT_USERNAME}?start={game_id}"
            )
            return

        game = active_battleship_games[game_id]

        if game["player_2"] is None and game["player_1"] != user.id:
            game["player_2"] = user.id
            game["chat_2"] = chat_id
            game["name_2"] = user.first_name

            await update.message.reply_text(
                f"⚓ انضممت بنجاح يا {user.first_name} ضد {game['name_1']}!\n"
                f"اختر أماكن {TOTAL_SHIPS} سفن خاصة بك على الشبكة:"
            )

            kb_1 = get_setup_keyboard(game_id, 1)
            kb_2 = get_setup_keyboard(game_id, 2)

            await context.bot.send_message(chat_id=game["chat_1"], text=f"اختر مكان السفينة (1 من {TOTAL_SHIPS}):", reply_markup=kb_1)
            await context.bot.send_message(chat_id=game["chat_2"], text=f"اختر مكان السفينة (1 من {TOTAL_SHIPS}):", reply_markup=kb_2)
            return

        elif game["player_1"] == user.id or game["player_2"] == user.id:
            await update.message.reply_text("أنت مشارك بالفعل في هذه اللعبة!")
            return
        else:
            await update.message.reply_text("عذراً، هذه اللعبة مكتملة!")
            return

    game_id = f"bs_{user.id}"
    active_battleship_games[game_id] = {
        "player_1": user.id,
        "chat_1": chat_id,
        "name_1": user.first_name,
        "player_2": None,
        "chat_2": None,
        "name_2": "بانتظار لاعب...",
        "ships_1": [],
        "ships_2": [],
        "shared_grid": create_empty_grid(),
        "turn": None,
        "msg_id_1": None,
        "msg_id_2": None,
        "status": "setup"
    }

    invite_link = f"https://t.me/{BOT_USERNAME}?start={game_id}"
    await update.message.reply_text(
                f"⚓ أهلاً بك يا {user.first_name} في معركة السفن الحربية!\n\n"
                f"لقد أنشأت جلسة جديدة خاصة بك.\n"
                f"🔗 رابط دعوة الصديق:\n"
                f"https://t.me/{BOT_USERNAME}?start={game_id}\n\n"
                f"قم بنسخ هذا الرابط وأرسله لصديقك، وبمجرد دخوله ستبدأ اللعبة تلقائياً!"
            )


async def battleship_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if data.startswith("bs_set_"):
        parts = data.split("_")
        r = int(parts[-2])
        c = int(parts[-1])
        p_num = int(parts[-3])
        game_id = "_".join(parts[2:-3])

        if game_id not in active_battleship_games:
            await query.edit_message_text("انتهت صلاحية اللعبة.")
            return

        game = active_battleship_games[game_id]
        ships_list = game["ships_1"] if p_num == 1 else game["ships_2"]

        pos = (r, c)
        if pos in ships_list:
            all_possible = [(row, col) for row in range(GRID_SIZE) for col in range(GRID_SIZE)]
            empty_spots = [p for p in all_possible if p not in ships_list]
            if empty_spots:
                pos = random.choice(empty_spots)

        ships_list.append(pos)
        current_count = len(ships_list)

        if current_count < TOTAL_SHIPS:
            try:
                await query.edit_message_text(
                    text=f"⚓ تم إخفاء السفينة ({current_count}/{TOTAL_SHIPS}).\nاختر مكان السفينة التالية:",
                    reply_markup=get_setup_keyboard(game_id, p_num)
                )
            except Exception:
                pass
        else:
            try:
                await query.edit_message_text(text=f"⚓ تم إخفاء جميع السفن الـ {TOTAL_SHIPS} بنجاح! انتظر الخصم...")
            except Exception:
                pass

        if len(game["ships_1"]) == TOTAL_SHIPS and len(game["ships_2"]) == TOTAL_SHIPS:
            game["status"] = "fighting"
            game["turn"] = game["player_1"]

            kb = get_game_board_keyboard(game["shared_grid"], game_id)
            try:
                msg_1 = await context.bot.send_message(
                    chat_id=game["chat_1"], 
                    text=f"🔥 **معركة السفن الحربية**\n👤 أنت: {game['name_1']} (رمز إصابتك: 💥)\n👤 خصمك: {game['name_2']} (رمز إصابته: 🔥)\n\n🎯 دورك للهجوم أولاً:", 
                    reply_markup=kb,
                    parse_mode="Markdown"
                )
                game["msg_id_1"] = msg_1.message_id

                msg_2 = await context.bot.send_message(
                    chat_id=game["chat_2"], 
                    text=f"🔥 **معركة السفن الحربية**\n👤 أنت: {game['name_2']} (رمز إصابتك: 🔥)\n👤 خصمك: {game['name_1']} (رمز إصابته: 💥)\n\n⏳ دور خصمك {game['name_1']}, انتظر...", 
                    reply_markup=kb,
                    parse_mode="Markdown"
                )
                game["msg_id_2"] = msg_2.message_id
            except Exception:
                pass

    elif data.startswith("bs_att_"):
        parts = data.split("_")
        r = int(parts[-2])
        c = int(parts[-1])
        game_id = "_".join(parts[2:-2])

        if game_id not in active_battleship_games:
            await query.edit_message_text("انتهت صلاحية اللعبة.")
            return

        game = active_battleship_games[game_id]

        if game["status"] != "fighting":
            return

        if game["turn"] != user.id:
            await query.answer("ليس دورك الآن في الهجوم!", show_alert=True)
            return

        is_p1 = (user.id == game["player_1"])
        my_ships = game["ships_1"] if is_p1 else game["ships_2"]
        
        if (r, c) in my_ships:
            await query.answer("⚠️ لا يمكنك قصف سفينتك الخاصة!", show_alert=True)
            return

        shared_grid = game["shared_grid"]
        if shared_grid[r][c] != "·":
            await query.answer("هذا المربع تم قصفه مسبقاً!", show_alert=True)
            return

        target_ships = game["ships_2"] if is_p1 else game["ships_1"]
        hit = ((r, c) in target_ships)

        if hit:
            shared_grid[r][c] = "💥" if is_p1 else "🔥"
            if (r, c) in target_ships:
                target_ships.remove((r, c))

            kb = get_game_board_keyboard(shared_grid, game_id)

            if len(target_ships) == 0:
                game["status"] = "over"
                winner_name = game["name_1"] if is_p1 else game["name_2"]
                text_win = f"🎉 تهانينا يا {winner_name} فزت بالمعركة ودمرت كافة سفن العدو! 🏆"
                try:
                    if game["msg_id_1"]:
                        await context.bot.edit_message_text(chat_id=game["chat_1"], message_id=game["msg_id_1"], text=text_win, reply_markup=kb)
                    if game["msg_id_2"]:
                        await context.bot.edit_message_text(chat_id=game["chat_2"], message_id=game["msg_id_2"], text=text_win, reply_markup=kb)
                except Exception:
                    pass
                return
            else:
                hit_symbol = "💥" if is_p1 else "🔥"
                text_p1 = f"🔥 **معركة السفن الحربية**\n👤 أنت: {game['name_1']} (رمز إصابتك: 💥)\n👤 خصمك: {game['name_2']} (رمز إصابته: 🔥)\n\n🎯 إصابة ناجحة! ({hit_symbol}) لقد أصبت هدفاً للعدو. الدور مستمر لك:"
                text_p2 = f"🔥 **معركة السفن الحربية**\n👤 أنت: {game['name_2']} (رمز إصابتك: 🔥)\n👤 خصمك: {game['name_1']} (رمز إصابته: 💥)\n\n🎯 إصابة ناجحة! ({hit_symbol}) أصاب خصمك أحد أهدافك. انتظر دورك:"
                try:
                    if game["msg_id_1"]:
                        await context.bot.edit_message_text(chat_id=game["chat_1"], message_id=game["msg_id_1"], text=text_p1 if is_p1 else text_p2, reply_markup=kb, parse_mode="Markdown")
                    if game["msg_id_2"]:
                        await context.bot.edit_message_text(chat_id=game["chat_2"], message_id=game["msg_id_2"], text=text_p2 if is_p1 else text_p1, reply_markup=kb, parse_mode="Markdown")
                except Exception:
                    pass
                return
        else:
            shared_grid[r][c] = "❌"
            game["turn"] = game["player_2"] if is_p1 else game["player_1"]

            next_name = game["name_2"] if is_p1 else game["name_1"]
            prev_name = game["name_1"] if is_p1 else game["name_2"]

            kb = get_game_board_keyboard(shared_grid, game_id)

            text_p1_info = f"🔥 **معركة السفن الحربية**\n👤 أنت: {game['name_1']} (رمز إصابتك: 💥)\n👤 خصمك: {game['name_2']} (رمز إصابته: 🔥)\n\n"
            text_p2_info = f"🔥 **معركة السفن الحربية**\n👤 أنت: {game['name_2']} (رمز إصابتك: 🔥)\n👤 خصمك: {game['name_1']} (رمز إصابته: 💥)\n\n"

            text_turn_current = f"❌ أخطأت الهدف.\n⏳ دور {next_name}، انتظر..."
            text_turn_next = f"⚠️ أخطأ {prev_name} في الهجوم.\n🎯 دورك للهجوم الآن:"

            try:
                if game["msg_id_1"]:
                    await context.bot.edit_message_text(
                        chat_id=game["chat_1"], 
                        message_id=game["msg_id_1"], 
                        text=text_p1_info + (text_turn_current if is_p1 else text_turn_next), 
                        reply_markup=kb,
                        parse_mode="Markdown"
                    )
                if game["msg_id_2"]:
                    await context.bot.edit_message_text(
                        chat_id=game["chat_2"], 
                        message_id=game["msg_id_2"], 
                        text=text_p2_info + (text_turn_next if is_p1 else text_turn_current), 
                        reply_markup=kb,
                        parse_mode="Markdown"
                    )
            except Exception:
                pass
