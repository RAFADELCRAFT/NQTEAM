from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    COMPROBANTE1_CONFIG,
    COMPROBANTE4_CONFIG,
    COMPROBANTE_MOVIMIENTO_CONFIG,
    COMPROBANTE_MOVIMIENTO2_CONFIG,
    COMPROBANTE_QR_CONFIG,
    COMPROBANTE_MOVIMIENTO3_CONFIG
)
from utils import generar_comprobante
from auth_system import AuthSystem
import os
import logging
from uuid import uuid4

# Configuration
ADMIN_ID = 7994105703  # Updated admin ID
ALLOWED_GROUP = -1002849576343
OWNER = "@Teampaz2"

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize authorization system
auth_system = AuthSystem(ADMIN_ID, ALLOWED_GROUP)
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        if not auth_system.can_use_bot(user_id, chat_id):
            await update.message.reply_text("🚫 Acceso denegado: No tienes permiso para usar este bot.")
            return
    
        keyboard = [
            [InlineKeyboardButton("💸 Nequi", callback_data="comprobante1")],
            [InlineKeyboardButton("🔄 Transfiya", callback_data="comprobante4")],
            [InlineKeyboardButton("📱 QR Comprobante", callback_data="comprobante_qr")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = (
            f"🎉 Bienvenido al Generador de Comprobantes\n"
            f"💎 Servicio gratuito de alta calidad\n"
            f"⚠️ Si pagaste por esto, contacta a {OWNER}\n"
            f"Selecciona una opción:"
        )
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    except Exception as e:
        logger.error(f"Error in start command for user {user_id} in chat {chat_id}: {str(e)}")
        await update.message.reply_text("⚠️ Error al iniciar el bot. Intenta de nuevo.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        chat_id = query.message.chat.id
        tipo = query.data or "default"

        if not auth_system.can_use_bot(user_id, chat_id):
            await query.message.reply_text("🚫 Acceso denegado: No tienes permiso para usar este bot.")
            return

        user_data_store[user_id] = {"step": 0, "tipo": tipo, "session_id": str(uuid4())}

        prompts = {
            "comprobante1": "👤 Ingresa el nombre completo:",
            "comprobante4": "📱 Ingresa el número de teléfono:",
            "comprobante_qr": "🏬 Nombre del negocio:",
        }

        await query.message.reply_text(
            prompts.get(tipo, "🔍 Por favor, inicia ingresando los datos requeridos:")
        )
    
    except Exception as e:
        logger.error(f"Error in button_handler for user {user_id} in chat {chat_id}: {str(e)}")
        await query.message.reply_text("⚠️ Error al procesar la selección. Intenta de nuevo.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()

    try:
        if not auth_system.can_use_bot(user_id, chat_id):
            await update.message.reply_text("🚫 Acceso denegado: No tienes permiso para usar este bot.")
            return

        if user_id not in user_data_store:
            await update.message.reply_text("🔄 Por favor, inicia con /start")
            return

        data = user_data_store[user_id]
        tipo = data["tipo"]
        step = data["step"]

        async def send_document(output_path: str, caption: str) -> bool:
            try:
                if not os.path.exists(output_path):
                    logger.error(f"Document not found: {output_path}")
                    await update.message.reply_text("⚠️ Error: No se pudo generar el comprobante.")
                    return False
                with open(output_path, "rb") as f:
                    await update.message.reply_document(document=f, caption=caption)
                os.remove(output_path)
                return True
            except Exception as e:
                logger.error(f"Error sending document: {str(e)}")
                await update.message.reply_text("⚠️ Error al enviar el comprobante.")
                return False

        # --- NEQUI ---
        if tipo == "comprobante1":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text("📱 Ingresa el número de teléfono (solo dígitos):")
            elif step == 1:
                if not text.isdigit():
                    await update.message.reply_text("⚠️ El número debe contener solo dígitos.")
                    return
                data["telefono"] = text
                data["step"] = 2
                await update.message.reply_text("💰 Ingresa el valor:")
            elif step == 2:
                if not text.replace("-", "", 1).isdigit():
                    await update.message.reply_text("⚠️ El valor debe ser numérico.")
                    return
                data["valor"] = int(text)
                
                output_path = generar_comprobante(data, COMPROBANTE1_CONFIG)
                if await send_document(output_path, f"✅ Comprobante Nequi generado por {OWNER}"):
                    # Movimiento negativo
                    data_mov = data.copy()
                    data_mov["nombre"] = data["nombre"].upper()
                    data_mov["valor"] = -abs(data["valor"])
                    output_path_mov = generar_comprobante(data_mov, COMPROBANTE_MOVIMIENTO_CONFIG)
                    await send_document(output_path_mov, f"📄 Movimiento generado por {OWNER}")

                del user_data_store[user_id]

        # --- TRANSFIYA ---
        elif tipo == "comprobante4":
            if step == 0:
                if not text.isdigit():
                    await update.message.reply_text("⚠️ El número debe contener solo dígitos.")
                    return
                data["telefono"] = text
                data["step"] = 1
                await update.message.reply_text("💰 Ingresa el valor:")
            elif step == 1:
                if not text.replace("-", "", 1).isdigit():
                    await update.message.reply_text("⚠️ El valor debe ser numérico.")
                    return
                data["valor"] = int(text)
                
                output_path = generar_comprobante(data, COMPROBANTE4_CONFIG)
                if await send_document(output_path, f"✅ Comprobante Transfiya generado por {OWNER}"):
                    # Movimiento negativo
                    data_mov2 = {
                        "telefono": data["telefono"],
                        "valor": -abs(data["valor"]),
                        "nombre": data["telefono"],
                    }
                    output_path_mov2 = generar_comprobante(data_mov2, COMPROBANTE_MOVIMIENTO2_CONFIG)
                    await send_document(output_path_mov2, f"📄 Movimiento generado por {OWNER}")

                del user_data_store[user_id]

        # --- QR COMPROBANTE ---
        elif tipo == "comprobante_qr":
            if step == 0:
                data["nombre"] = text
                data["step"] = 1
                await update.message.reply_text("💰 Ingresa el valor:")
            elif step == 1:
                if not text.replace("-", "", 1).isdigit():
                    await update.message.reply_text("⚠️ El valor debe ser numérico.")
                    return
                data["valor"] = int(text)

                output_path = generar_comprobante(data, COMPROBANTE_QR_CONFIG)
                if await send_document(output_path, f"✅ Comprobante QR generado por {OWNER}"):
                    # Movimiento adicional
                    data_mov_qr = {
                        "nombre": data["nombre"].upper(),
                        "valor": -abs(data["valor"])
                    }
                    output_path_movqr = generar_comprobante(data_mov_qr, COMPROBANTE_MOVIMIENTO3_CONFIG)
                    await send_document(output_path_movqr, f"📄 Movimiento QR generado por {OWNER}")

                del user_data_store[user_id]

    except Exception as e:
        logger.error(f"Error in handle_message for user {user_id} in chat {chat_id}: {str(e)}")
        await update.message.reply_text("⚠️ Error al procesar los datos. Intenta de nuevo.")

# Admin Commands
async def gratis_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        # Allow admin to use command in any chat
        if user_id == ADMIN_ID or auth_system.is_admin(user_id):
            logger.info(f"Admin {user_id} executed /gratis in chat {chat_id}")
            auth_system.set_gratis_mode(True)
            await update.message.reply_text("✅ Modo GRATIS activado: Todos pueden usar el bot.")
        else:
            # Non-admins must be in ALLOWED_GROUP
            if chat_id != ALLOWED_GROUP:
                logger.warning(f"Non-admin {user_id} tried /gratis in unauthorized chat {chat_id}")
                await update.message.reply_text("🚫 Este comando solo puede usarse en el grupo autorizado.")
                return
            if not auth_system.is_admin(user_id):
                logger.warning(f"Non-admin {user_id} tried /gratis")
                await update.message.reply_text("🚫 Solo el administrador puede usar este comando.")
                return
    
    except Exception as e:
        logger.error(f"Error in gratis_command for user {user_id} in chat {chat_id}: {str(e)}")
        await update.message.reply_text("⚠️ Error al activar modo gratis.")

async def off_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        # Allow admin to use command in any chat
        if user_id == ADMIN_ID or auth_system.is_admin(user_id):
            logger.info(f"Admin {user_id} executed /off in chat {chat_id}")
            auth_system.set_gratis_mode(False)
            await update.message.reply_text("✅ Modo OFF activado: Solo usuarios autorizados.")
        else:
            # Non-admins must be in ALLOWED_GROUP
            if chat_id != ALLOWED_GROUP:
                logger.warning(f"Non-admin {user_id} tried /off in unauthorized chat {chat_id}")
                await update.message.reply_text("🚫 Este comando solo puede usarse en el grupo autorizado.")
                return
            if not auth_system.is_admin(user_id):
                logger.warning(f"Non-admin {user_id} tried /off")
                await update.message.reply_text("🚫 Solo el administrador puede usar este comando.")
                return
    
    except Exception as e:
        logger.error(f"Error in off_command for user {user_id} in chat {chat_id}: {str(e)}")
        await update.message.reply_text("⚠️ Error al desactivar modo gratis.")

async def agregar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        # Allow admin to use command in any chat
        if user_id == ADMIN_ID or auth_system.is_admin(user_id):
            logger.info(f"Admin {user_id} executed /agregar in chat {chat_id}")
            if not context.args:
                await update.message.reply_text("❓ Uso: /agregar <id_usuario>")
                return
            target_user_id = int(context.args[0])
            auth_system.add_user(target_user_id)
            await update.message.reply_text(f"✅ Usuario {target_user_id} autorizado.")
        else:
            logger.warning(f"Non-admin {user_id} tried /agregar in chat {chat_id}")
            await update.message.reply_text("🚫 Solo el administrador puede usar este comando.")
    
    except ValueError:
        logger.error(f"Invalid user ID provided by {user_id} in chat {chat_id}")
        await update.message.reply_text("⚠️ ID de usuario inválido.")
    except Exception as e:
        logger.error(f"Error in agregar_command for user {user_id} in chat {chat_id}: {str(e)}")
        await update.message.reply_text("⚠️ Error al agregar usuario.")

async def eliminar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        # Allow admin to use command in any chat
        if user_id == ADMIN_ID or auth_system.is_admin(user_id):
            logger.info(f"Admin {user_id} executed /eliminar in chat {chat_id}")
            if not context.args:
                await update.message.reply_text("❓ Uso: /eliminar <id_usuario>")
                return
            target_user_id = int(context.args[0])
            if auth_system.remove_user(target_user_id):
                await update.message.reply_text(f"✅ Usuario {target_user_id} desautorizado.")
            else:
                await update.message.reply_text(f"⚠️ Usuario {target_user_id} no estaba autorizado.")
        else:
            logger.warning(f"Non-admin {user_id} tried /eliminar in chat {chat_id}")
            await update.message.reply_text("🚫 Solo el administrador puede usar este comando.")
    
    except ValueError:
        logger.error(f"Invalid user ID provided by {user_id} in chat {chat_id}")
        await update.message.reply_text("⚠️ ID de usuario inválido.")
    except Exception as e:
        logger.error(f"Error in eliminar_command for user {user_id} in chat {chat_id}: {str(e)}")
        await update.message.reply_text("⚠️ Error al eliminar usuario.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    try:
        # Allow admin to use command in any chat
        if user_id == ADMIN_ID or auth_system.is_admin(user_id):
            logger.info(f"Admin {user_id} executed /stats in chat {chat_id}")
            stats = auth_system.get_stats()
            authorized_users = auth_system.get_authorized_users()
            
            message = (
                f"📊 **Estadísticas del Bot**\n\n"
                f"👥 Usuarios autorizados: {stats['total_authorized']}\n"
                f"🆓 Modo gratis: {'Activado' if stats['gratis_mode'] else 'Desactivado'}\n"
                f"📱 Grupo permitido: {stats['allowed_group']}\n\n"
            )
            
            if authorized_users:
                message += "👤 Usuarios autorizados:\n" + "\n".join(f"  • {uid}" for uid in authorized_users)
            else:
                message += "❌ No hay usuarios autorizados."
            
            await update.message.reply_text(message)
        else:
            logger.warning(f"Non-admin {user_id} tried /stats in chat {chat_id}")
            await update.message.reply_text("🚫 Solo el administrador puede usar este comando.")
    
    except Exception as e:
        logger.error(f"Error in stats_command for user {user_id} in chat {chat_id}: {str(e)}")
        await update.message.reply_text("⚠️ Error al obtener estadísticas.")

def main() -> None:
    try:
        # Log admin ID and group ID for debugging
        logger.info(f"Initializing bot with admin ID: {ADMIN_ID}, allowed group: {ALLOWED_GROUP}")
        
        # Updated bot token
        bot_token = "8390219313:AAGayHwfK5uyOXS-YsGi4l7V9NyszhkZQJM"
        
        # Validate token format
        if not bot_token or ":" not in bot_token:
            logger.error("Invalid bot token provided")
            raise ValueError("Invalid bot token")

        # Initialize application
        app = Application.builder().token(bot_token).build()

        # Register handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("gratis", gratis_command))
        app.add_handler(CommandHandler("off", off_command))
        app.add_handler(CommandHandler("agregar", agregar_command))
        app.add_handler(CommandHandler("eliminar", eliminar_command))
        app.add_handler(CommandHandler("stats", stats_command))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("Bot handlers registered successfully")
        logger.info("Starting bot polling...")

        # Start polling
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()
