import random
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

active_battleship_games = {}
TOTAL_SHIPS = 3
GRID_SIZE = 7 # تقليص الشبكة قليلاً لتناسب أزرار الشات بشكل أفضل


def create_empty_grid():
    return [["·" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]


def get_setup_keyboard(game_id, player_num):
    keyboard = []
    for r in range(GRID_SIZE):
        row = []
        for c in range(GRID_SIZE):
            row.append(InlineKeyboardButton("🟦", callback_data=f"bs_set_{game_id}_{player_num}_{r}_{c}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def get_game_board_keyboard(grid, game_id):
    keyboard = []
    for r in range(GRID_SIZE):
        row_buttons = []
        for c in range(GRID_SIZE):
            cell = grid[r][c]
            if cell == "·":
                text = "🎯"
                callback_data = f"bs_att_{game_id}_{r}_{c}"
            else:
                text = cell
                callback_data = "none"
            row_buttons.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(row_buttons)
    return InlineKeyboardMarkup(keyboard)


async def battleship_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id if update.effective_chat else None
    game_id = f"bs_inline_{chat_id}_{user.id}"

    active_battleship_games[game_id] = {
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

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚓ انضم والعب كـ منافس", callback_data=f"bs_join_{game_id}")]
    ])

    text = (
        f"⚓ **معركة السفن الحربية**\n\n"
        f"👤 أنشأ التحدي: **{user.first_name}**\n"
        f"⏳ في انتظار انضمام المنافس لبدء وضع السفن..."
    )

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def battleship_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    if data.startswith("bs_join_"):
        game_id = data.replace("bs_join_", "")
        if game_id not in active_battleship_games:
            await query.answer("انتهت صلاحية هذه اللعبة.", show_alert=True)
            return

        game = active_battleship_games[game_id]
        if game["player_1"] == user.id:
            await query.answer("لا يمكنك اللعب ضد نفسك!", show_alert=True)
            return

        if game["player_2"] is not None:
            await query.answer("اللعبة مكتملة اللاعبين بالفعل!", show_alert=True)
            return

        game["player_2"] = user.id
        game["name_2"] = user.first_name
        game["status"] = "setup_1_placing"

        # طلب من اللاعب الأول اختيار سفنه أولاً
        keyboard = get_setup_keyboard(game_id, 1)
        text = (
            f"⚓ **مرحلة توزيع السفن**\n\n"
            f"👤 دور اللاعب **{game['name_1']}** لإخفاء سفنه الـ {TOTAL_SHIPS} (الرجاء اختيار المربعات سرّاً):\n"
            f"تم وضع: (0/{TOTAL_SHIPS})"
        )
        try:
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception:
            pass

    elif data.startswith("bs_set_"):
        parts = data.split("_")
        r = int(parts[-2])
        c = int(parts[-1])
        p_num = int(parts[-3])
        game_id = "_".join(parts[2:-3])

        if game_id not in active_battleship_games:
            await query.answer("انتهت اللعبة.", show_alert=True)
            return

        game = active_battleship_games[game_id]
        
        # التأكد أن اللاعب الصحيح هو من يضغط
        if p_num == 1 and user.id != game["player_1"]:
            await query.answer("ليس دورك في توزيع السفن!", show_alert=True)
            return
        if p_num == 2 and user.id != game["player_2"]:
            await query.answer("ليس دورك في توزيع السفن!", show_alert=True)
            return

        ships_list = game["ships_1"] if p_num == 1 else game["ships_2"]

        if (r, c) in ships_list:
            await query.answer("لقد اخترت هذا المربع مسبقاً!", show_alert=True)
            return

        ships_list.append((r, c))
        current_count = len(ships_list)

        if current_count < TOTAL_SHIPS:
            keyboard = get_setup_keyboard(game_id, p_num)
            name = game["name_1"] if p_num == 1 else game["name_2"]
            text = (
                f"⚓ **مرحلة توزيع السفن**\n\n"
                f"👤 دور اللاعب **{name}** لإخفاء سفنه:\n"
                f"تم وضع: ({current_count}/{TOTAL_SHIPS})"
            )
            try:
                await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
            except Exception:
                pass
        else:
            # إذا انتهى اللاعب الأول، ننتقل للاعب الثاني
            if p_num == 1:
                keyboard = get_setup_keyboard(game_id, 2)
                text = (
                    f"⚓ **مرحلة توزيع السفن**\n\n"
                    f"✅ انتهى {game['name_1']} من وضع سفنه.\n"
                    f"👤 الآن دور اللاعب **{game['name_2']}** لإخفاء سفنه الـ {TOTAL_SHIPS}:"
                )
                try:
                    await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
                except Exception:
                    pass
            else:
                # انتهى الاثنان، تبدأ المعركة!
                game["status"] = "fighting"
                game["turn"] = game["player_1"]
                kb = get_game_board_keyboard(game["shared_grid"], game_id)
                text = (
                    f"🔥 **معركة السفن الحربية اشتعلت!**\n\n"
                    f"❌ {game['name_1']} ضد ⭕ {game['name_2']}\n\n"
                    f"🎯 دور اللاعب للهجوم: **{game['name_1']}**"
                )
                try:
                    await query.edit_message_text(text=text, reply_markup=kb, parse_mode="Markdown")
                except Exception:
                    pass

    elif data.startswith("bs_att_"):
        parts = data.split("_")
        r = int(parts[-2])
        c = int(parts[-1])
        game_id = "_".join(parts[2:-2])

        if game_id not in active_battleship_games:
            await query.answer("انتهت اللعبة.", show_alert=True)
            return

        game = active_battleship_games[game_id]
        if game["status"] != "fighting":
            return

        if game["turn"] != user.id:
            await query.answer("ليس دورك الآن في الهجوم!", show_alert=True)
            return

        is_p1 = (user.id == game["player_1"])
        my_ships = game["ships_1"] if is_p1 else game["ships_2"]
        target_ships = game["ships_2"] if is_p1 else game["ships_1"]

        if (r, c) in my_ships:
            await query.answer("⚠️ لا يمكنك قصف سفينتك الخاصة!", show_alert=True)
            return

        shared_grid = game["shared_grid"]
        if shared_grid[r][c] != "·":
            await query.answer("هذا المربع تم قصفه مسبقاً!", show_alert=True)
            return

        hit = ((r, c) in target_ships)

        if hit:
            shared_grid[r][c] = "💥"
            if (r, c) in target_ships:
                target_ships.remove((r, c))

            if len(target_ships) == 0:
                game["status"] = "over"
                winner_name = game["name_1"] if is_p1 else game["name_2"]
                text = f"🏆 **تهانينا! الفائز في المعركة هو: {winner_name}** 🎊\nتم تدمير كافة سفن العدو بنجاح!"
                try:
                    await query.edit_message_text(text=text, reply_markup=None, parse_mode="Markdown")
                except Exception:
                    pass
                return
            else:
                attacker_name = game["name_1"] if is_p1 else game["name_2"]
                kb = get_game_board_keyboard(shared_grid, game_id)
                text = (
                    f"🔥 **معركة السفن الحربية**\n\n"
                    f"🎯 إصابة ناجحة بواسطة **{attacker_name}**! 💥\n"
                    f"دور اللاعب للهجوم مستمر: **{attacker_name}**"
                )
                try:
                    await query.edit_message_text(text=text, reply_markup=kb, parse_mode="Markdown")
                except Exception:
                    pass
        else:
            shared_grid[r][c] = "❌"
            game["turn"] = game["player_2"] if is_p1 else game["player_1"]
            next_name = game["name_2"] if is_p1 else game["name_1"]

            kb = get_game_board_keyboard(shared_grid, game_id)
            text = (
                f"🔥 **معركة السفن الحربية**\n\n"
                f"❌ أخطأ الهدف!\n"
                f"⏳ دور اللاعب التالي للهجوم: **{next_name}**"
            )
            try:
                await query.edit_message_text(text=text, reply_markup=kb, parse_mode="Markdown")
            except Exception:
                pass
