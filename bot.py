from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import pytesseract

# --- Configuración de entorno y Gemini ---
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
print("🔑 API Key cargada:", GEMINI_API_KEY)

# Ruta a Tesseract en Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Comandos básicos ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy Nutri Bot 🤖🥦\n\n"
        "Opciones disponibles:\n"
        "/menu - Menú del día\n"
        "/receta - Te sugiero un platillo con tus ingredientes\n"
        "/compras - Lista de compras desde un menú semanal o una imagen 📷"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¿Quieres un menú del día completo (desayuno, comida y cena) o solo un platillo? 🍽️")
    context.user_data["esperando_menu"] = True

async def receta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Escribe hasta 15 ingredientes separados por coma (,) 🍅🧀🥬")
    context.user_data["esperando_receta"] = True

async def compras(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Envíame el menú semanal (texto) o una imagen 📷 para generar tu lista de compras con cantidades.")
    context.user_data["esperando_menu_compras"] = True

# --- Procesar texto ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    if context.user_data.get("esperando_menu"):
        prompt = (
            f"Genera un menú {user_input.lower()} para una persona. "
            "Incluye nombre del platillo, descripción breve y resumen de macronutrientes."
        )
        try:
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            response = model.generate_content(prompt)
            await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text(f"❌ Ocurrió un error al generar el menú:\n\n{e}")
        context.user_data["esperando_menu"] = False

    elif context.user_data.get("esperando_receta"):
        ingredientes = [x.strip() for x in user_input.split(",")]
        if len(ingredientes) > 15:
            await update.message.reply_text("❌ Solo puedes ingresar hasta 15 ingredientes.")
            return

        prompt = (
            f"Tengo estos ingredientes: {', '.join(ingredientes)}. "
            "Sugiéreme una receta nutritiva y fácil de preparar con ellos. "
            "Incluye nombre, pasos, y nutrientes principales."
        )
        try:
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            response = model.generate_content(prompt)
            await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text(f"❌ Ocurrió un error al generar la receta:\n\n{e}")
        context.user_data["esperando_receta"] = False

    elif context.user_data.get("esperando_menu_compras"):
        await update.message.reply_text("👌 Generando lista de compras adaptada para supermercado...")

        prompt = (
            f"Tengo el siguiente menú para varios días:\n\n{user_input}\n\n"
            "Quiero que me des una lista de compras agrupada por categoría (verduras, frutas, carnes, etc.). "
            "Incluye **cantidades aproximadas en unidades reales de supermercado**, como:\n"
            "- '1 botella de aceite de oliva (1 litro)'\n"
            "- '3 piezas de pechuga de pollo'\n"
            "- '1 bolsa de espinacas (200 g)'\n"
            "- '500 g de arroz integral'\n\n"
            "Asume que es para 1 semana. Agrupa ingredientes repetidos y no pongas solo nombres, siempre incluye cantidades."
        )
        try:
            model = genai.GenerativeModel("models/gemini-1.5-flash")
            response = model.generate_content(prompt)
            await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text(f"❌ Ocurrió un error al generar la lista de compras:\n\n{e}")
        context.user_data["esperando_menu_compras"] = False

    else:
        await update.message.reply_text("Usa /menu, /receta o /compras para comenzar.")

# --- Procesar imágenes ---
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📷 Imagen recibida. Procesando texto...")

    photo_file = await update.message.photo[-1].get_file()
    photo_path = "temp_image.jpg"
    await photo_file.download_to_drive(photo_path)

    try:
        image = Image.open(photo_path)
        extracted_text = pytesseract.image_to_string(image)

        if not extracted_text.strip():
            await update.message.reply_text("❌ No pude leer ningún texto en la imagen.")
            return

        await update.message.reply_text("✅ Texto extraído. Generando lista de compras...")

        prompt = (
            f"A partir del siguiente menú extraído de una imagen:\n\n{extracted_text}\n\n"
            "Genera una lista de compras con cantidades reales, agrupadas por categoría (verduras, frutas, proteínas, etc). "
            "Incluye unidades como:\n"
            "- '1 litro de leche'\n"
            "- '500 g de arroz integral'\n"
            "- '1 botella de aceite de oliva (1 L)'\n"
            "Asume que el menú es para una semana completa. No repitas ingredientes."
        )

        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text)

    except Exception as e:
        await update.message.reply_text(f"❌ Error procesando la imagen:\n{e}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)

# --- Iniciar bot ---
from telegram.ext import ApplicationBuilder

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("receta", receta))
    app.add_handler(CommandHandler("compras", compras))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot en modo Webhook...")

    # Tu URL de Render
    WEBHOOK_URL = "https://bot-alimentos-2.onrender.com"

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f"{WEBHOOK_URL}/webhook"
    )

