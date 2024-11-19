from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import requests
import json
import os
from datetime import datetime
import pytz
from googleapiclient.discovery import build
from spellchecker import SpellChecker
# Bot Token
TOKEN = '7316188795:AAEi0o-hFR8jv9uZqcbPYpYpdyCnVmWqoOU'

# Initialize SpellChecker for word corrections
spell = SpellChecker()

# File for storing user preferences
PREFS_FILE = 'user_prefs.json'

# API Keys
YOUTUBE_API_KEY = 'AIzaSyDQSRsLtPIru--EJIg9MtX2eMjOxuvuddM'
WEATHER_API_KEY = '7f59948b973042e8bfd22815241211'


# --- Helper Functions --- #

def load_prefs():
    """Load user preferences from the file."""
    if os.path.exists(PREFS_FILE):
        with open(PREFS_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_prefs(prefs):
    """Save user preferences to the file."""
    with open(PREFS_FILE, 'w') as file:
        json.dump(prefs, file)

def get_definition(word):
    """Fetch definition of a word using an API and suggest corrections."""
    corrected_word = spell.correction(word)
    correction_msg = f"Did you mean '{corrected_word}'?" if corrected_word != word else ""

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{corrected_word}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        meaning = data[0]['meanings'][0]['definitions'][0]['definition']
        part_of_speech = data[0]['meanings'][0].get('partOfSpeech', 'No part of speech available.')
        example = data[0]['meanings'][0]['definitions'][0].get('example', 'No example available.')
        
        return f"**Word**: {corrected_word.capitalize()}\n" \
               f"**Part of Speech**: {part_of_speech.capitalize()}\n" \
               f"**Definition**: {meaning}\n" \
               f"**Example**: {example}\n" + correction_msg
    else:
        return f"Sorry, I couldn't find the definition for '{word}'. {correction_msg}"

# --- Command Handlers --- #

# /define command: Fetch word definition
async def define(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    word = ' '.join(context.args)
    if word:
        definition = get_definition(word)
        await update.message.reply_text(definition)
    else:
        await update.message.reply_text("Please provide a word to define. Example: /define example")

# /weather command: Fetch weather information for a city
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    city = 'Phnom Penh'
    if context.args:
        city = ' '.join(context.args)

    url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
    response = requests.get(url)
    data = response.json()

    if 'error' not in data:
        weather_data = f"Weather in {city}:\nTemperature: {data['current']['temp_c']}°C\nDescription: {data['current']['condition']['text']}"
    else:
        weather_data = "Sorry, I couldn't fetch the weather data."

    await update.message.reply_text(weather_data)

# /datetime command: Get the current date and time in Cambodia
async def datetime_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cambodia_timezone = pytz.timezone("Asia/Phnom_Penh")
    current_time = datetime.now(cambodia_timezone)
    formatted_time = current_time.strftime("%A, %Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"Current date and time in Cambodia: {formatted_time}")

# /youtube command: Search YouTube videos
async def youtube_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = ' '.join(context.args)
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    request = youtube.search().list(part="snippet", q=query, type="video", maxResults=3)
    response = request.execute()

    message = ""
    for item in response['items']:
        title = item['snippet']['title']
        video_id = item['id']['videoId']
        url = f"https://www.youtube.com/watch?v={video_id}"
        message += f"{title}\n{url}\n\n"

    await update.message.reply_text(message if message else "No results found.")


async def set_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    custom_response = ' '.join(context.args)
    prefs = load_prefs()

    if user_id not in prefs:
        prefs[user_id] = {}
    
    prefs[user_id]['custom_response'] = custom_response
    save_prefs(prefs)

    await update.message.reply_text(f"Custom response set to: {custom_response}")

# /help command: Show help message
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Commands:\n"
        "/start - Greet the user\n"
        "/help - Show help\n"
        "/weather - Get weather data\n"
        "/setresponse <response> - Set custom response\n"
        "/datetime - Get the current date and time in Cambodia\n"
        "/youtube <search term> - Search YouTube for videos\n"
        "/define <word> - Get the definition of a word"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Normalize user input
    user_text = update.message.text.strip().lower()  # Trim whitespace and convert to lowercase

    # Respond based on keywords
    if "What does html stand for?" in user_text:
        response = (
            "Hyper text makeup language."
        )
    elif "What does CSS stand for?" in user_text:
        response = (
            "Cascading style sheet\n"
        )
    elif "what is html" in user_text:
        response = (
            "HTML (HyperText Markup Language) is a standard markup language used for creating web pages.\n"
            "It defines the structure and content of a web document."
            "HTML tags are used to define different elements, such as headings, paragraphs, images, and links.\n"
            "Example: <h1>This is a heading</h1>"
        )
    elif "what is python?" in user_text:
        response = (
            "Python is a high-level, interpreted, general-purpose programming language.\n"
            "It was created by Guido van Rossum in 1991.\n"
            "Python features dynamic typing, interpreted nature, and a large standard library.\n"
            "Example: print('Hello, World!')"
        )
    elif "html" in user_text:
        response = (
            "HTML (HyperText Markup Language) is a standard markup language used for creating web pages.\n"
            "It defines the structure and content of a web document.\n"
            "HTML tags are used to define different elements, such as headings, paragraphs, images, and links.\n"
            "Example: <h1>This is a heading</h1>"
        )
    elif "what is python?" in user_text:
         response = (
            "Python is a high-level, interpreted, general-purpose programming language.\n"
            "It was created by Guido van Rossum in 1991.\n"
            "Python features dynamic typing, interpreted nature, and a large standard library.\n"
            "Example: print('Hello, World!')"
        )
    elif "python" in user_text:
         response = (
            "Python is a high-level, interpreted, general-purpose programming language.\n"
            "It was created by Guido van Rossum in 1991.\n"
            "Python features dynamic typing, interpreted nature, and a large standard library.\n"
            "Example: print('Hello, World!')"
        )
    elif "how to use a dictionary" in user_text:
        response = (
            "A dictionary is a data structure that stores key-value pairs.\n"
            "Keys are used to access and retrieve values.\n"
            "Example: {'name': 'John', 'age': 30}"
        )
    elif "dictionary" in user_text:
        response = (
            "A dictionary is a data structure that stores key-value pairs.\n"
            "Keys are used to access and retrieve values.\n"
            "Example: {'name': 'John', 'age': 30}"
        )
    elif "how to use a list" in user_text:
        response = (
            "A list is an ordered collection of items.\n"
            "Items in a list can be of different data types.\n"
            "Example: ['apple', 'banana', 'cherry']"
        )
    elif "list" in user_text:
        response = (
            "A list is an ordered collection of items.\n"
            "Items in a list can be of different data types.\n"
            "Example: ['apple', 'banana', 'cherry']"
        )
    elif "how to use loop in python" in user_text:
        response = (
            "Looping in Python is done using the 'for' loop or the 'while' loop.\n"
            "The 'for' loop is used to iterate over a sequence (like a list or string).\n"
            "Example: for item in ['apple', 'banana', 'cherry']: print(item)"
        )
    elif "loop" in user_text:
        response = (
            "Looping in Python is done using the 'for' loop or the 'while' loop.\n"
            "The 'for' loop is used to iterate over a sequence (like a list or string).\n"
            "Example: for item in ['apple', 'banana', 'cherry']: print(item)"
        )
    elif "what is mean of html?" in user_text:
        response = (
            "HTML is the standard markup language for creating Web pages.\n"
            "HTML describes the structure of a Web page.\n"
            "HTML elements tell the browser how to display the content."
        )
    elif "mean" in user_text:
        response = (
            "HTML is the standard markup language for creating Web pages.\n"
            "HTML describes the structure of a Web page.\n"
            "HTML elements tell the browser how to display the content."
        )
    elif "what does html stand for?" in user_text:
        response = (
            "Stand for hyper text makeup language."
        )
    elif "stand" in user_text:
        response = (
            "Stand for hyper text makeup language."
        )
    elif "What is an HTML element?" in user_text:
        response = (
            "An HTML element is defined by a start tag, some content, and an end tag."
            "Example : <tagname> Content goes here... </tagname>"
        )
    elif "element" in user_text:
        response = (
            "An HTML element is defined by a start tag, some content, and an end tag."
            "Example : <tagname> Content goes here... </tagname>"
        )
    elif "What are the 10 basic HTML tags?" in user_text:
        response = (
            "<html> … </html> — The root element."
            "<head> … </head> — The document head."
            "<title> … </title> — The page title."
            "<body> … </body> — The page's content."
            "<h1> … </h1> — A section heading."
            "<a> … </a> — A link"
            "<img> — An image."
        )
    elif "10 basic" in user_text:
        response = (
            "<html> … </html> — The root element.\n"
            "<head> … </head> — The document head.\n"
            "<title> … </title> — The page title.\n"
            "<body> … </body> — The page's content.\n"
            "<h1> … </h1> — A section heading.\n"
            "<a> … </a> — A link.\n"
            "<img> — An image."
        )
    elif "Why is HTML used?" in user_text:
        response = (
            "HTML is used to provide structure to a webpage and make it accessible to users of the internet through text, visual formatting and search factors."
        )
    elif "used" in user_text:
        response = (
            "HTML is used to provide structure to a webpage and make it accessible to users of the internet through text, visual formatting and search factors."
        )
    elif "What is a url in HTML?" in user_text:
        response = (
            "URL - Uniform Resource Locator"
        )
    elif "url" in user_text:
        response = (
            "URL : Uniform Resource Locator."
        )
    else:
        response = "I didn't quite get that. Could you please clarify?"

    # Send the response
    await update.message.reply_text(response)
# --- Inline Button Handlers --- #

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    action = {
        'weather': "Please type /weather <city> to get the weather.",
        'youtube': "Please type /youtube <search term> to search YouTube.",
        'datetime': "Please type /datetime to get the current date and time in Cambodia."
    }.get(query.data, "Unknown option selected.")
    
    await query.edit_message_text(action)

# --- Start Command --- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Weather", callback_data='weather')],
        [InlineKeyboardButton("YouTube Search", callback_data='youtube')],
        [InlineKeyboardButton("Date/Time", callback_data='datetime')],
        [InlineKeyboardButton("Dictionary", callback_data='define')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose an option:", reply_markup=reply_markup)

# --- Main Function --- #

def main():
    """Main entry point for the bot."""
    application = ApplicationBuilder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("weather", weather))
    application.add_handler(CommandHandler("datetime", datetime_command))
    application.add_handler(CommandHandler("setresponse", set_response))
    application.add_handler(CommandHandler("define", define))
    application.add_handler(CommandHandler("youtube", youtube_search))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start polling for updates
    application.run_polling()

if __name__ == '__main__':
    main()
