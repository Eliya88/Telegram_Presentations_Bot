from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import psycopg2
from psycopg2 import OperationalError
from DataBaseManager import DatabaseManager
import os


TOKEN: Final = f"7096347082:{os.getenv('BOT_TOKEN')}"
BOT_USERNAME: Final = f"@{os.getenv('BOT_USERNAME')}"

# Initialize the DatabaseManager
db_manager = DatabaseManager()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command from the user.
    """
    # Fetch course names from the database
    course_names = db_manager.fetch_course_names()

    if course_names:
        # Create an inline keyboard with course names
        keyboard = [[InlineKeyboardButton(course, callback_data=f"course_{course}")] for course in course_names]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Please choose your course:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('No courses available at the moment.')


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the user's button clicks.
    """
    # Get the callback query
    query = update.callback_query
    await query.answer()

    data = query.data
    print(data)  # This will log the callback data for debugging purposes

    # User has selected a course
    if data.startswith('course_'):
        course_name = data.split('_')[1]
        presentation_numbers = db_manager.fetch_presentation_numbers(course_name)

        if presentation_numbers:
            keyboard = [[InlineKeyboardButton(f"Presentation {num}", callback_data=f"pres_{course_name}_{num}")] for num
                        in presentation_numbers]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Update the message with the presentation options
            await query.edit_message_text(text=f"Choose a presentation for {course_name}:", reply_markup=reply_markup)
        else:
            await query.edit_message_text(text="No presentations available for this course.")

    # User has selected a presentation
    elif data.startswith('pres_'):
        _, course_name, presentation_number = data.split('_')
        file_path = db_manager.get_presentation_path(course_name, presentation_number)
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as file:
                    await query.message.reply_document(document=file,
                                                       caption=f"Presentation {presentation_number} for {course_name}.")
            except Exception as e:
                await query.message.reply_text(f"Failed to send the file: {e}")
        else:
            await query.message.reply_text("File not found or inaccessible.")


def create_connection():
    """
    Creates and returns a new database connection using the psycopg2 library.
    """
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        # For debugging purposes
        print("Database connection established.")
        return connection

    except OperationalError as e:
        print(f"An error occurred: {e}")
        return None


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Logs errors caused by updates.
    """
    print(f"Update {update} caused error {context.error}")


# Main entry point for the bot application
if __name__ == '__main__':
    print('Bot is running...')

    # Create the application
    app = Application.builder().token(TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_error_handler(error)

    print('Polling...')
    app.run_polling()
