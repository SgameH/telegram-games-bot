import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


active_games = {}


BOT_USERNAME = "SgameHbot"


def create_board():

    return [[" " for _ in range(3)] for _ in range(3)]


def get_board_keyboard(board, game_id, game_over=False):

    keyboard = []
    for r_idx, row in enumerate(board):
        row_buttons = []
        for c_idx, cell in enumerate(row):
            text = cell if cell != " " else "▪️"
            callback_data = f"play_{game_id}_{r_idx}_{c_idx}" if not game_over else "none"
            row_buttons.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(row_buttons)

    if game_over:
        keyboard.append([InlineKeyboardButton("🔄 إعادة اللعبة", callback_data=f"restart_{game_id}")])

    return InlineKeyboardMarkup(keyboard)


def check_winner(board):

    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] != " ":
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] != " ":
            return board[0][i]

    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != " ":
        return board[0][2]

    if all(cell != " " for row in board for cell in row):
        return "Tie"

    return None


async def tictactoe_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    chat_id = update.effective_chat.id

    if args and args[0].startswith("game_"):
        game_id = args[0]

        if game_id not in active_games:
            active_games[game_id] = {
                "player_X": user.id,
                "chat_X": chat_id,
                "name_X": user.first_name,
                "player_O": None,
                "chat_O": None,
                "name_O": "بانتظار لاعب...",
                "board": create_board(),
                "turn": user.id,
            }
            await update.message.reply_text(
                f"🎮 أهلاً بك يا {user.first_name}!\n"
                f"أنشأت جلسة جديدة لهذه اللعبة.\n\n"
                f"🔗 شارك هذا الرابط مع صديقك ليبدأ التحدي:\n"
                f"https://t.me/{BOT_USERNAME}?start={game_id}"
            )
            return

        game = active_games[game_id]

        if game["player_O"] is None and game["player_X"] != user.id:
            game["player_O"] = user.id
            game["chat_O"] = chat_id
            game["name_O"] = user.first_name

            await update.message.reply_text(
                f"🎮 انضممت بنجاح يا {user.first_name} ضد {game['name_X']}!\n"
                f"دع المعركة تبدأ ❌ ضد ⭕!"
            )


            keyboard = get_board_keyboard(game["board"], game_id)
            
            text_x = (
                f"⚔️ لعبة XO بين:\n"
                f"❌ {game['name_X']} ضد ⭕ {game['name_O']}\n\n"
                f"دور اللاعب: ❌ {game['name_X']}"
            )
            text_o = text_x

            msg_x = await context.bot.send_message(chat_id=game["chat_X"], text=text_x, reply_markup=keyboard)
            game["msg_id_X"] = msg_x.message_id

            msg_o = await context.bot.send_message(chat_id=game["chat_O"], text=text_o, reply_markup=keyboard)
            game["msg_id_O"] = msg_o.message_id
            return

        elif game["player_X"] == user.id or game["player_O"] == user.id:
            await update.message.reply_text("أنت مشارك بالفعل في هذه اللعبة النشطة!")
            return
        else:
            await update.message.reply_text("عذراً، هذه اللعبة مكتملة اللاعبين بالفعل!")
            return

    game_id = f"game_{user.id}"
    active_games[game_id] = {
        "player_X": user.id,
        "chat_X": chat_id,
        "name_X": user.first_name,
        "player_O": None,
        "chat_O": None,
        "name_O": "بانتظار لاعب...",
        "board": create_board(),
        "turn": user.id,
    }

    invite_link = f"https://t.me/{BOT_USERNAME}?start={game_id}"

    await update.message.reply_text(
        f"👋 أهلاً بك يا {user.first_name} في لعبة XO الاحترافية!\n\n"
        f"لقد أنشأت جلسة جديدة خاصة بك.\n"
        f"🔗 رابط دعوة الصديق:\n{invite_link}\n\n"
        f"قم بنسخ هذا الرابط وأرسله لصديقك، وبمجرد دخوله ستبدأ اللعبة تلقائياً!"
    )


async def tictactoe_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if data.startswith("play_"):
        parts = data.split("_")
        r = int(parts[-2])
        c = int(parts[-1])
        game_id = "_".join(parts[1:-2])

        if game_id not in active_games:
            await query.edit_message_text("انتهت صلاحية هذه اللعبة أو تم حذفها.")
            return

        game = active_games[game_id]

        if game["player_O"] is None:
            await query.answer("يجب أن ينتظر انضمام لاعب ثانٍ أولاً!", show_alert=True)
            return

        if user.id not in [game["player_X"], game["player_O"]]:
            await query.answer("لست مشاركاً في هذه اللعبة!", show_alert=True)
            return

        if game["turn"] != user.id:
            await query.answer("ليس دورك الآن! انتظر دور خصمك.", show_alert=True)
            return

        if game["board"][r][c] != " ":
            await query.answer("هذه الخانة محجوزة مسبقاً!", show_alert=True)
            return

        symbol = "❌" if user.id == game["player_X"] else "⭕"
        game["board"][r][c] = symbol

        winner = check_winner(game["board"])

        if winner:
            game_over = True
            keyboard = get_board_keyboard(game["board"], game_id, game_over=True)
            if winner == "Tie":
                text = f"🤝 تعادل الفريقان!\n\n❌ {game['name_X']} ضد ⭕ {game['name_O']}"
            else:
                winner_name = game["name_X"] if winner == "❌" else game["name_O"]
                text = f"🏆 مبروك الفوز!\nالفائز هو: {winner} {winner_name} 🎊"
            
            try:
                await context.bot.edit_message_text(chat_id=game["chat_X"], message_id=game["msg_id_X"], text=text, reply_markup=keyboard)
            except Exception:
                pass
            try:
                await context.bot.edit_message_text(chat_id=game["chat_O"], message_id=game["msg_id_O"], text=text, reply_markup=keyboard)
            except Exception:
                pass
            return

        game["turn"] = game["player_O"] if game["turn"] == game["player_X"] else game["player_X"]
        next_name = game["name_X"] if game["turn"] == game["player_X"] else game["name_O"]
        next_symbol = "❌" if game["turn"] == game["player_X"] else "⭕"

        keyboard = get_board_keyboard(game["board"], game_id)
        text = (
            f"⚔️ لعبة XO بين:\n"
            f"❌ {game['name_X']} ضد ⭕ {game['name_O']}\n\n"
            f"دور اللاعب: {next_symbol} {next_name}"
        )

        try:
            await context.bot.edit_message_text(chat_id=game["chat_X"], message_id=game["msg_id_X"], text=text, reply_markup=keyboard)
        except Exception:
            pass
        try:
            await context.bot.edit_message_text(chat_id=game["chat_O"], message_id=game["msg_id_O"], text=text, reply_markup=keyboard)
        except Exception:
            pass

    elif data.startswith("restart_"):
        parts = data.split("_")
        game_id = "_".join(parts[1:])

        if game_id in active_games:
            game = active_games[game_id]
            game["board"] = create_board()
            game["turn"] = game["player_X"]

            keyboard = get_board_keyboard(game["board"], game_id)
            text = (
                f"🔄 بدأت مباراة جديدة!\n"
                f"❌ {game['name_X']} ضد ⭕ {game['name_O']}\n\n"
                f"دور اللاعب: ❌ {game['name_X']}"
            )

            try:
                await context.bot.edit_message_text(chat_id=game["chat_X"], message_id=game["msg_id_X"], text=text, reply_markup=keyboard)
            except Exception:
                pass
            try:
                await context.bot.edit_message_text(chat_id=game["chat_O"], message_id=game["msg_id_O"], text=text, reply_markup=keyboard)
            except Exception:
                pass
