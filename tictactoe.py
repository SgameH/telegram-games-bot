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
    chat_id = update.effective_chat.id
    
    # إنشاء معرف فريد للعبة يعتمد على المحادثة أو الوقت لتبقى الرسالة في نفس الشات
    game_id = f"tictactoe_{chat_id}_{user.id}"

    active_games[game_id] = {
        "player_X": user.id,
        "chat_X": chat_id,
        "name_X": user.first_name,
        "player_O": None,
        "chat_O": chat_id,
        "name_O": "بانتظار لاعب...",
        "board": create_board(),
        "turn": user.id,
        "msg_id": None
    }

    # زر انضمام يضغط عليه اللاعب الثاني مباشرة في نفس الشات
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 انضم والعب كـ ⭕", callback_data=f"join_{game_id}")]
    ])

    msg = await update.message.reply_text(
        f"🎮 **تحدي جديد في لعبة XO**\n\n"
        f"👤 أنشأ التحدي: **{user.first_name}** (❌)\n"
        f"⏳ في انتظار انضمام المنافس...",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    active_games[game_id]["msg_id"] = msg.message_id


async def tictactoe_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    # معالجة انضمام اللاعب الثاني مباشرة من نفس الرسالة
    if data.startswith("join_"):
        game_id = data.replace("join_", "")
        if game_id not in active_games:
            await query.answer("انتهت صلاحية هذه اللعبة.", show_alert=True)
            return

        game = active_games[game_id]

        if game["player_X"] == user.id:
            await query.answer("لا يمكنك اللعب ضد نفسك!", show_alert=True)
            return

        if game["player_O"] is not None:
            await query.answer("اللعبة مكتملة اللاعبين بالفعل!", show_alert=True)
            return

        game["player_O"] = user.id
        game["name_O"] = user.first_name
        game["turn"] = game["player_X"]

        keyboard = get_board_keyboard(game["board"], game_id)
        text = (
            f"⚔️ **لعبة XO قائمة الآن**\n"
            f"❌ {game['name_X']} ضد ⭕ {game['name_O']}\n\n"
            f"دور اللاعب: ❌ {game['name_X']}"
        )

        try:
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception:
            pass
        return

    # معالجة ضغطات مربعات اللعب داخل الشات
    if data.startswith("play_"):
        parts = data.split("_")
        r = int(parts[-2])
        c = int(parts[-1])
        game_id = "_".join(parts[1:-2])

        if game_id not in active_games:
            await query.answer("انتهت صلاحية هذه اللعبة أو تم حذفها.", show_alert=True)
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
                text = f"🤝 **تعادل الفريقان!**\n\n❌ {game['name_X']} ضد ⭕ {game['name_O']}"
            else:
                winner_name = game["name_X"] if winner == "❌" else game["name_O"]
                text = f"🏆 **انتهت اللعبة!**\nالفائز هو: {winner} {winner_name} 🎊"
            
            try:
                await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
            except Exception:
                pass
            return

        game["turn"] = game["player_O"] if game["turn"] == game["player_X"] else game["player_X"]
        next_name = game["name_X"] if game["turn"] == game["player_X"] else game["name_O"]
        next_symbol = "❌" if game["turn"] == game["player_X"] else "⭕"

        keyboard = get_board_keyboard(game["board"], game_id)
        text = (
            f"⚔️ **لعبة XO قائمة الآن**\n"
            f"❌ {game['name_X']} ضد ⭕ {game['name_O']}\n\n"
            f"دور اللاعب: {next_symbol} {next_name}"
        )

        try:
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
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
                f"🔄 **بدأت مباراة جديدة!**\n"
                f"❌ {game['name_X']} ضد ⭕ {game['name_O']}\n\n"
                f"دور اللاعب: ❌ {game['name_X']}"
            )

            try:
                await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
            except Exception:
                pass
