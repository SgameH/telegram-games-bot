import logging
from google import genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)

# تخزين مؤقت للأسئلة وحالة اللعبة لكل شات
truth_active_games = {}
chat_history = {}
_gemini_client = None


def init_truth_game(api_key: str):
    """تهيئة مكتبة لعبة الصراحة والجرأة بمفتاح الـ API القادم من ملف الـ main"""
    global _gemini_client
    _gemini_client = genai.Client(api_key=api_key)


def generate_unique_question(category: str, chat_id: int) -> str:
    if chat_id not in chat_history:
        chat_history[chat_id] = []

    categories_desc = {
        "truth": "سؤال صراحة قوي وجريء وممتع للشباب (أسئلة شخصية وكشف أسرار).",
        "love": "سؤال حب رومانسية وعلاقات عاطفية وغزل ومشاعر للأحباب والمرتبطين.",
        "embarrassing": "سؤال إحراج ومواقف محرجة ومقالب قديمة وقع فيها الشخص.",
        "hot": "أسئلة جريئة جداً ومخصصة للكبار فقط (+18) وعلاقات خاصة وحميمة بجرأة عالية.",
    }

    category_prompt = categories_desc.get(category, categories_desc["truth"])
    previous = chat_history[chat_id]
    prompt = (
        f"أعطني سؤالاً واحداً فقط باللغة العربية ضمن التصنيف التالي: {category_prompt}."
        " اجعل السؤال مبتكراً، مشوقاً، وبدون أي مقدمات أو شرح، فقط السؤال نصاً."
    )

    if previous:
        prompt += f" تجنب تماماً وممنوع نهائياً استخدام أي من هذه الأسئلة التي سئلت مسبقاً: {previous[-15:]}"

    try:
        if not _gemini_client:
            return "⚠️ تنبيه: لم يتم تهيئة مفتاح الـ API الخاص بـ Gemini بشكل صحيح."

        response = _gemini_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        question = response.text.strip().replace('"', "")

        chat_history[chat_id].append(question)
        if len(chat_history[chat_id]) > 30:
            chat_history[chat_id].pop(0)

        return question
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        return "عذراً، حدث خطأ في استخراج السؤال، حاول مرة أخرى! 😅"


# 1. أمر البدء للعبة في الشات (بانتظار الانضمام مثل الـ XO)
async def truth_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    game_id = f"truth_{chat_id}_{user.id}"

    truth_active_games[game_id] = {
        "host_id": user.id,
        "host_name": user.first_name,
        "player_2_id": None,
        "player_2_name": "بانتظار لاعب...",
        "current_category": "truth",
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 انضم للعبة الصراحة والجرأة", callback_data=f"truth_join_{game_id}")]
    ])

    await update.message.reply_text(
        f"🎯 **تحدي جديد في لعبة الصراحة والجرأة**\n\n"
        f"👤 أنشأ التحدي: **{user.first_name}**\n"
        f"⏳ في انتظار انضمام المنافس لبدء الأسئلة...",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


# 2. معالجة الأزرار (الانضمام واختيار الأقسام) بشكل آمن
async def truth_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    # معالجة انضمام اللاعب الثاني
    if data.startswith("truth_join_"):
        game_id = data.replace("truth_join_", "")
        if game_id not in truth_active_games:
            await query.answer("انتهت صلاحية هذه اللعبة أو تم البدء بواحدة جديدة.", show_alert=True)
            return

        game = truth_active_games[game_id]

        if game["host_id"] == user.id:
            await query.answer("أنت من أنشأ التحدي، انتظر انضمام شخص آخر!", show_alert=True)
            return

        game["player_2_id"] = user.id
        game["player_2_name"] = user.first_name

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🟢 صراحة", callback_data=f"truth_cat_{game_id}_truth"),
                InlineKeyboardButton("❤️ حب وغرام", callback_data=f"truth_cat_{game_id}_love"),
            ],
            [
                InlineKeyboardButton("😳 مواقف محرجة", callback_data=f"truth_cat_{game_id}_embarrassing"),
                InlineKeyboardButton("🔥 +18 جرأة", callback_data=f"truth_cat_{game_id}_hot"),
            ],
        ])

        text = (
            f"🎯 **بدأت لعبة الصراحة والجرأة بنجاح!**\n\n"
            f"👤 المنشئ: **{game['host_name']}**\n"
            f"👤 المنافس: **{game['player_2_name']}**\n\n"
            f"👇 اختر القسم المناسب لطرح أول سؤال:"
        )

        try:
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception:
            pass
        return

    # معالجة اختيار الأقسام وتوليد الأسئلة
    if data.startswith("truth_cat_"):
        parts = data.replace("truth_cat_", "").split("_")
        category = parts[-1]
        game_id = "_".join(parts[:-1])

        if game_id not in truth_active_games:
            await query.answer("انتهت صلاحية هذه اللعبة.", show_alert=True)
            return

        game = truth_active_games[game_id]
        
        # استخراج chat_id بشكل آمن لمنع خطأ الإنلاين
        chat_id = query.message.chat_id if query.message else user.id

        cat_names = {
            "truth": "🟢 قسم الصراحة",
            "love": "❤️ قسم الحب والغرام",
            "embarrassing": "😳 قسم المواقف المحرجة",
            "hot": "🔥 قسم الجرأة (+18)",
        }

        new_question = generate_unique_question(category, chat_id)

        text = (
            f"🎯 **{cat_names.get(category, 'لعبة الصراحة')}**\n"
            f"👤 الدور على: **{user.first_name}**\n\n"
            f"❓ **السؤال:**\n`{new_question}`\n\n"
            "👇 اختر قسماً آخر أو اطلب سؤالاً جديداً:"
        )

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 سؤال جديد من نفس القسم", callback_data=f"truth_cat_{game_id}_{category}")],
            [
                InlineKeyboardButton("🟢 صراحة", callback_data=f"truth_cat_{game_id}_truth"),
                InlineKeyboardButton("❤️ حب", callback_data=f"truth_cat_{game_id}_love"),
            ],
            [
                InlineKeyboardButton("😳 إحراج", callback_data=f"truth_cat_{game_id}_embarrassing"),
                InlineKeyboardButton("🔥 +18", callback_data=f"truth_cat_{game_id}_hot"),
            ],
        ])

        try:
            await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            pass


# 3. دالة التسجيل الأساسية لملف الـ main
def setup_truth_handlers(application, gemini_api_key: str):
    init_truth_game(gemini_api_key)
    application.add_handler(CommandHandler("truth", truth_start))
    application.add_handler(CallbackQueryHandler(truth_button_handler, pattern="^truth_(cat|join)_"))
