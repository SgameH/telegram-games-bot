import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

active_rps_games = {}


def get_rps_keyboard(game_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🪨 حجر", callback_data=f"rps_pick_{game_id}_rock"),
            InlineKeyboardButton("📄 ورقة", callback_data=f"rps_pick_{game_id}_paper"),
            InlineKeyboardButton("✂️ مقص", callback_data=f"rps_pick_{game_id}_scissors"),
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
    chat_id = update.effective_chat.id
    
    game_id = f"rps_{chat_id}_{user.id}"

    active_rps_games[game_id] = {
        "player_1": user.id,
        "chat_1": chat_id,
        "name_1": user.first_name,
        "player_2": None,
        "chat_2": chat_id,
        "name_2": "بانتظار لاعب...",
        "choice_1": None,
        "choice_2": None,
        "msg_id": None,
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 انضم وتحدَ اللاعب كـ ⭕", callback_data=f"rps_join_{game_id}")]
    ])

    text = (
        f"✊ **لعبة حجر - ورقة - مقص**\n\n"
        f"👤 أنشأ التحدي: **{user.first_name}**\n"
        f"⏳ في انتظار انضمام المنافس..."
    )

    if update.message:
        msg = await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")
        active_rps_games[game_id]["msg_id"] = msg.message_id


async def rps_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    # معالجة انضمام اللاعب الثاني مباشرة من نفس الرسالة
    if data.startswith("rps_join_"):
        game_id = data.replace("rps_join_", "")
        if game_id not in active_rps_games:
            await query.answer("انتهت صلاحية هذه اللعبة.", show_alert=True)
            return

        game = active_rps_games[game_id]

        if game["player_1"] == user.id:
            await query.answer("لا يمكنك اللعب ضد نفسك!", show_alert=True)
            return

        if game["player_2"] is not None:
            await query.answer("اللعبة مكتملة اللاعبين بالفعل!", show_alert=True)
            return

        game["player_2"] = user.id
        game["name_2"] = user.first_name

        keyboard = get_rps_keyboard(game_id)
        text = (
            f"✊ **معركة حجر 🪨 ورقة 📄 مقص ✂️**\n\n"
            f"⚔️ {game['name_1']} ضد {game['name_2']}\n"
            f"اختر حركتك سرياً عبر الأزرار أدناه:"
        )

        try:
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception:
            pass
        return

    # معالجة اختيار الحركات
    if data.startswith("rps_pick_"):
        parts = data.split("_")
        choice = parts[-1]
        game_id = "_".join(parts[2:-1])

        if game_id not in active_rps_games:
            await query.answer("انتهت صلاحية هذه اللعبة أو تم حذفها.", show_alert=True)
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

        # التحقق إذا اختار الاثنان معا
        if game["choice_1"] is not None and game["choice_2"] is not None:
            c1 = game["choice_1"]
            c2 = game["choice_2"]
            res = determine_winner(c1, c2)

            emoji_map = {"rock": "🪨 حجر", "paper": "📄 ورقة", "scissors": "✂️ مقص"}

            if res == "tie":
                result_text = "🤝 **تعادل الفريقان!**"
            elif res == "player1":
                result_text = f"🏆 **الفائز هو:** {game['name_1']} 🎊"
            else:
                result_text = f"🏆 **الفائز هو:** {game['name_2']} 🎊"

            text = (
                f"🎮 **نتائج لعبة حجر - ورقة - مقص**\n\n"
                f"👤 {game['name_1']} اختر: {emoji_map[c1]}\n"
                f"👤 {game['name_2']} اختر: {emoji_map[c2]}\n\n"
                f"{result_text}"
            )

            restart_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 إعادة التحدي", callback_data=f"rps_restart_{game_id}")]
            ])

            try:
                await query.edit_message_text(text=text, reply_markup=restart_kb, parse_mode="Markdown")
            except Exception:
                pass
        else:
            waiting_user = game["name_2"] if user.id == game["player_1"] else game["name_1"]
            current_picker = game["name_1"] if user.id == game["player_1"] else game["name_2"]
            try:
                await query.edit_message_text(
                    text=f"✊ **لعبة حجر - ورقة - مقص**\n\n✅ قام **{current_picker}** باختياره.\n⏳ بانتظار أن يقوم **{waiting_user}** باختياره...",
                    reply_markup=get_rps_keyboard(game_id),
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    elif data.startswith("rps_restart_"):
        parts = data.split("_")
        game_id = "_".join(parts[2:])

        if game_id in active_rps_games:
            game = active_rps_games[game_id]
            game["choice_1"] = None
            game["choice_2"] = None

            keyboard = get_rps_keyboard(game_id)
            text = (
                f"🔄 **جولة جديدة!**\n\n"
                f"⚔️ {game['name_1']} ضد {game['name_2']}\n"
                f"اختر حركتك الجديدة:"
            )

            try:
                await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
            except Exception:
                pass
