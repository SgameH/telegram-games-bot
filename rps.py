import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


active_rps_games = {}


BOT_USERNAME = "SgameHbot"


def get_rps_keyboard(game_id, chosen=False):

    if chosen:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تم اختيارك بنجاح، بانتظار الخصم...", callback_data="none")]
        ])
    
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🪨 حجر", callback_data=f"rps_{game_id}_rock"),
            InlineKeyboardButton("📄 ورقة", callback_data=f"rps_{game_id}_paper"),
            InlineKeyboardButton("✂️ مقص", callback_data=f"rps_{game_id}_scissors"),
        ]
    ])


def determine_winner(choice1, choice2):

    if choice1 == choice2:
        return "tie"
    if (
        (choice1 == "rock" and choice2 == "scissors") or
        (choice1 == "paper" and choice2 == "rock") or
        (choice1 == "scissors" and choice2 == "paper")
    ):
        return "player1"
    return "player2"


async def rps_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    chat_id = update.effective_chat.id

    if args and args[0].startswith("rps_"):
        game_id = args[0]

        if game_id not in active_rps_games:
            active_rps_games[game_id] = {
                "player_1": user.id,
                "chat_1": chat_id,
                "name_1": user.first_name,
                "player_2": None,
                "chat_2": None,
                "name_2": "بانتظار لاعب...",
                "choice_1": None,
                "choice_2": None,
                "msg_id_1": None,
                "msg_id_2": None,
            }
            await update.message.reply_text(
                f"🎮 أهلاً بك يا {user.first_name} في تحدي حجر-ورقة-مقص!\n\n"
                f"🔗 شارك هذا الرابط مع صديقك ليبدأ التحدي:\n"
                f"https://t.me/{BOT_USERNAME}?start={game_id}"
            )
            return

        game = active_rps_games[game_id]

        if game["player_2"] is None and game["player_1"] != user.id:
            game["player_2"] = user.id
            game["chat_2"] = chat_id
            game["name_2"] = user.first_name

            await update.message.reply_text(
                f"🎮 انضممت بنجاح يا {user.first_name} ضد {game['name_1']}!\n"
                f"اختر حركتك سراً من الأسفل:"
            )


            keyboard_1 = get_rps_keyboard(game_id)
            keyboard_2 = get_rps_keyboard(game_id)

            msg_1 = await context.bot.send_message(
                chat_id=game["chat_1"],
                text=f"⚔️ معركة حجر 🪨 ورقة 📄 مقص ✂️\n\nضد: {game['name_2']}\nاختر حركتك:",
                reply_markup=keyboard_1
            )
            game["msg_id_1"] = msg_1.message_id

            msg_2 = await context.bot.send_message(
                chat_id=game["chat_2"],
                text=f"⚔️ معركة حجر 🪨 ورقة 📄 مقص ✂️\n\nضد: {game['name_1']}\nاختر حركتك:",
                reply_markup=keyboard_2
            )
            game["msg_id_2"] = msg_2.message_id
            return

        elif game["player_1"] == user.id or game["player_2"] == user.id:
            await update.message.reply_text("أنت مشارك بالفعل في هذه اللعبة النشطة!")
            return
        else:
            await update.message.reply_text("عذراً، هذه اللعبة مكتملة اللاعبين بالفعل!")
            return


    game_id = f"rps_{user.id}"
    active_rps_games[game_id] = {
        "player_1": user.id,
        "chat_1": chat_id,
        "name_1": user.first_name,
        "player_2": None,
        "chat_2": None,
        "name_2": "بانتظار لاعب...",
        "choice_1": None,
        "choice_2": None,
        "msg_id_1": None,
        "msg_id_2": None,
    }

    invite_link = f"https://t.me/{BOT_USERNAME}?start={game_id}"

    await update.message.reply_text(
        f"✊ أهلاً بك يا {user.first_name} في لعبة حجر - ورقة - مقص!\n\n"
        f"لقد أنشأت جلسة جديدة خاصة بك.\n"
        f"🔗 رابط دعوة الصديق:\n"
        f"https://t.me/{BOT_USERNAME}?start={game_id}\n\n"
        f"قم بنسخ هذا الرابط وأرسله لصديقك، وبمجرد دخوله ستبدأ اللعبة تلقائياً!"
    )


async def rps_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if data.startswith("rps_") and not data.startswith("rps_restart_"):
        parts = data.split("_")
        choice = parts[-1]
        game_id = "_".join(parts[1:-1])

        if game_id not in active_rps_games:
            await query.edit_message_text("انتهت صلاحية هذه اللعبة أو تم حذفها.")
            return

        game = active_rps_games[game_id]

        if user.id not in [game["player_1"], game["player_2"]]:
            await query.answer("لست مشاركاً في هذه اللعبة!", show_alert=True)
            return


        if user.id == game["player_1"]:
            if game["choice_1"] is not None:
                await query.answer("لقد اخترت مسبقاً! انتظر خصمك.", show_alert=True)
                return
            game["choice_1"] = choice
        else:
            if game["choice_2"] is not None:
                await query.answer("لقد اخترت مسبقاً! انتظر خصمك.", show_alert=True)
                return
            game["choice_2"] = choice


        try:
            current_msg_id = game["msg_id_1"] if user.id == game["player_1"] else game["msg_id_2"]
            current_chat_id = game["chat_1"] if user.id == game["player_1"] else game["chat_2"]
            await context.bot.edit_message_text(
                chat_id=current_chat_id,
                message_id=current_msg_id,
                text="✅ تم تسجيل اختيارك بنجاح. بانتظار أن يختار الخصم...",
                reply_markup=get_rps_keyboard(game_id, chosen=True)
            )
        except Exception:
            pass


        if game["choice_1"] is not None and game["choice_2"] is not None:
            c1 = game["choice_1"]
            c2 = game["choice_2"]
            res = determine_winner(c1, c2)

            emoji_map = {"rock": "🪨 حجر", "paper": "📄 ورقة", "scissors": "✂️ مقص"}

            if res == "tie":
                text_1 = f"🤝 تعادل!\nاختيارك: {emoji_map[c1]}\nاختيار خصمك: {emoji_map[c2]}"
                text_2 = f"🤝 تعادل!\nاختيارك: {emoji_map[c2]}\nاختيار خصمك: {emoji_map[c1]}"
            elif res == "player1":
                text_1 = f"🏆 مبروك، لقد فزت!\nاختيارك: {emoji_map[c1]}\nاختيار خصمك: {emoji_map[c2]}"
                text_2 = f"❌ هاردلك، لقد خسرت!\nاختيارك: {emoji_map[c2]}\nاختيار خصمك: {emoji_map[c1]}"
            else:
                text_1 = f"❌ هاردلك، لقد خسرت!\nاختيارك: {emoji_map[c1]}\nاختيار خصمك: {emoji_map[c2]}"
                text_2 = f"🏆 مبروك، لقد فزت!\nاختيارك: {emoji_map[c2]}\nاختيار خصمك: {emoji_map[c1]}"

            restart_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 إلعادة التحدي", callback_data=f"rps_restart_{game_id}")]
            ])

            try:
                await context.bot.edit_message_text(chat_id=game["chat_1"], message_id=game["msg_id_1"], text=text_1, reply_markup=restart_kb)
            except Exception:
                pass
            try:
                await context.bot.edit_message_text(chat_id=game["chat_2"], message_id=game["msg_id_2"], text=text_2, reply_markup=restart_kb)
            except Exception:
                pass

    elif data.startswith("rps_restart_"):
        parts = data.split("_")
        game_id = "_".join(parts[2:])

        if game_id in active_rps_games:
            game = active_rps_games[game_id]
            game["choice_1"] = None
            game["choice_2"] = None

            keyboard_1 = get_rps_keyboard(game_id)
            keyboard_2 = get_rps_keyboard(game_id)

            try:
                msg_1 = await context.bot.edit_message_text(
                    chat_id=game["chat_1"],
                    message_id=game["msg_id_1"],
                    text=f"🔄 جولة جديدة!\nضد: {game['name_2']}\nاختر حركتك:",
                    reply_markup=keyboard_1
                )
                game["msg_id_1"] = msg_1.message_id
            except Exception:
                pass

            try:
                msg_2 = await context.bot.edit_message_text(
                    chat_id=game["chat_2"],
                    message_id=game["msg_id_2"],
                    text=f"🔄 جولة جديدة!\nضد: {game['name_1']}\nاختر حركتك:",
                    reply_markup=keyboard_2
                )
                game["msg_id_2"] = msg_2.message_id
            except Exception:
                pass
