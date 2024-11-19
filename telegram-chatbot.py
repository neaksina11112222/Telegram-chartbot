from tracemalloc import start
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CallbackContext
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
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()

        if data and 'meanings' in data[0]:
            meaning = data[0]['meanings'][0]['definitions'][0]['definition']
            part_of_speech = data[0]['meanings'][0].get('partOfSpeech', 'No part of speech available.')
            example = data[0]['meanings'][0]['definitions'][0].get('example', 'No example available.')

            return f"**Word**: {corrected_word.capitalize()}\n" \
                   f"**Part of Speech**: {part_of_speech.capitalize()}\n" \
                   f"**Definition**: {meaning}\n" \
                   f"**Example**: {example}\n" + (f"\n{correction_msg}" if correction_msg else "")
        else:
            return f"Sorry, I couldn't find detailed information for '{corrected_word}'. {correction_msg}"
    except requests.exceptions.RequestException as e:
        return f"An error occurred while fetching the definition: {str(e)}"

# Command handler for the bot
def definition_command(update: Update, context: CallbackContext) -> None: # type: ignore
    # Get the word from the user's message
    word = ' '.join(context.args)
    if not word:
        update.message.reply_text("Please provide a word to look up.")
        return
    
    # Fetch the definition
    result = get_definition(word)
    update.message.reply_text(result)

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
    # css
    elif "what is css?" in user_text:
        response = (
            "CSS (CSS stands for Cascading Style Sheets) describes how HTML elements are displayed on screen, paper, or in other media.\n"
            "CSS saves a lot of work. It can control the layout of multiple web pages all at once.\n"
            "External stylesheets are stored in CSS files."
        ) 
    elif "css?" in user_text:
        response = (
            "CSS (CSS stands for Cascading Style Sheets) describes how HTML elements are displayed on screen, paper, or in other media.\n"
            "CSS saves a lot of work. It can control the layout of multiple web pages all at once.\n"
            "External stylesheets are stored in CSS files."
        ) 
    elif "types of selectors" in user_text:
        response = (
            "1. Universal Selector (*) : This selector is used to select all elements on the page.\n"
            "2. Type Selector : This selects all elements of a specific type (tag name).\n"
            "3. Class Selector : This selects elements with a specific class.\n"
            "4. ID Selector : This selects a single element with a specific ID.\n"
            "5. Attribute Selector : This selects elements with a specific attribute.\n"
            "6. Pseudo-class Selector : This selects elements in a specific state.\n"
            "7. Pseudo-element Selector : This styles a specific part of an element.\n"
            "8. Descendant Selector : This selects all elements inside another element.\n"
            "9. Child Selector : This selects direct children of an element.\n"
            "10. Adjacent Sibling Selector : This selects an element that is immediately after another element.\n"
            "11. General Sibling Selector : This selects all elements that are siblings after another element."
        )    
    elif "what is box model in css?" in user_text or "box model in css" in user_text:
        response = (
            "Border: property defines a boundary around an element, separating the content area from the surrounding space (including padding and margin). It is placed between the padding and margin.\n"
            "Margin: property defines the space outside the border of an element, pushing the element away from other surrounding elements. It is the outermost area of the box model.\n"
            "Padding: property defines the space inside the border of an element, between the border and the content. It pushes the content away from the border.\n"
            "Content: content of the box, where text and images appear."
        )    
    elif "what is text color?" in user_text:
        response = (
            "The text color property is used to set the color of the text. The color is specified."
        )    
    elif "how many font types in css?" in user_text or "font types in css" in user_text:
        response = (
            "Serif fonts: have a small stroke at the edges of each letter. They create a sense of formality and elegance.\n"
            "Sans-serif fonts: have clean lines (no small strokes attached). They create a modern and minimalistic look.\n"
            "Monospace fonts: here all the letters have the same fixed width. They create a mechanical look.\n"
            "Cursive fonts imitate human handwriting.\n"
            "Fantasy fonts are decorative/playful fonts."
        )    
    elif "type of css" in user_text or "font types in css" in user_text:
        response = (
            "Serif fonts: have a small stroke at the edges of each letter. They create a sense of formality and elegance.\n"
            "Sans-serif fonts: have clean lines (no small strokes attached). They create a modern and minimalistic look.\n"
            "Monospace fonts: here all the letters have the same fixed width. They create a mechanical look.\n"
            "Cursive fonts imitate human handwriting.\n"
            "Fantasy fonts are decorative/playful fonts."
        )    
    elif "how to add icon" in user_text or "add icon in css" in user_text:
        response = (
            "The simplest way to add an icon to your HTML page, is with an icon library, such as Font Awesome. Add the name of the specified icon class to any inline HTML element (like <i> or <span>). All the icons in the icon libraries below, are scalable vectors that can be customized with CSS (size, color, shadow, etc.)\n"
            "To use the Font Awesome icons, go to fontawesome.com, sign in, and get a code to add in the <head> section of your HTML page."
        )    
    elif "list style in css?" in user_text or "what is list style in css?" in user_text:
        response = (
            "Unordered Lists: The list items are marked with bullets.\n"
            "Ordered Lists: The list items are marked with numbers or letters."
        )                
    elif "what is sass?" in user_text:
        response = (
            "Sass stands for Syntactically Awesome Stylesheets.\n"
            "Sass is an extension to CSS.\n"
            "Sass is a CSS pre-processor.\n"
            "Sass is completely compatible with all versions of CSS.\n"
            "Sass reduces repetition of CSS and therefore saves time.\n"
            "Sass was designed by Hampton Catlin and developed by Natalie Weizenbaum in 2006.\n"
            "Sass is free to download and use."
        )         
    elif "why use sass?" in user_text:
        response = (
            "Stylesheets are getting larger, more complex, and harder to maintain. This is where a CSS pre-processor can help.\n"
            "Sass lets you use features that do not exist in CSS, like variables, nested rules, mixins, imports, inheritance, built-in functions, and other stuff."
        )         
    elif "how does sass work?" in user_text:
        response = (
            "A browser does not understand Sass code. Therefore, you will need a Sass pre-processor to convert Sass code into standard CSS.\n"
            "This process is called transpiling. So, you need to give a transpiler (some kind of program) some Sass code and then get some CSS code back."
        )   
    elif "sass file type?" in user_text:
        response = (
            "Sass files have the .scss file extension."
        )
    elif "Sass string Functions?" in user_text or "string" in user_text:
        response = (
            "The string functions are used to manipulate and get information about strings.\n"
            "Sass strings are 1-based. The first character in a string is at index 1, not 0.\n"
            "The following table lists all string functions in Sass"
        )
    elif "The position property?" in user_text or "position" in user_text:
        response = (
            "The string functions are used to manipulate and get information about strings.\n"
            "The position property specifies the type of positioning method used for an element (static, relative, fixed, absolute or sticky).\n"          
            "The position property specifies the type of positioning method used for an element.\n"
            "There are five different position values:\n"   
            "static\n"
            "relative\n"
            "fixed\n"
            "absolute\n"
            "sticky\n"
        )
    elif"position" in user_text:
        response = (
            "The string functions are used to manipulate and get information about strings.\n"
            "The position property specifies the type of positioning method used for an element (static, relative, fixed, absolute or sticky).\n"          
            "The position property specifies the type of positioning method used for an element.\n"
            "There are five different position values:\n"   
            "static\n"
            "relative\n"
            "fixed\n"
            "absolute\n"
            "sticky\n"
        )
    elif "z-index Property" in user_text or "z-index" in user_text:
        response = (
            "The z-index property specifies the stack order of an element.\n"
            "When elements are positioned, they can overlap other elements.\n"          
            "The z-index property specifies the stack order of an element (which element should be placed in front of, or behind, the others).\n"
            "Example : \n"   
            "img {\n"
            " position: absolute;\n"
            "left: 0px;\n"
            "top: 0px;\n"
            "z-index: -1;\n"
            "}\n"
        )
    elif "what is overflow?" or "overflow" in user_text:
        response = (
            "The CSS overflow property controls what happens to content that is too big to fit into an area.\n"
            "Example : overflow: scroll;\n"
            "The overflow property has the following values :/n"
            "visible - Default. The overflow is not clipped. The content renders outside the element's box\n"
            "hidden - The overflow is clipped, and the rest of the content will be invisible\n"
            "scroll - The overflow is clipped, and a scrollbar is added to see the rest of the content\n"
            "auto - Similar to scroll, but it adds scrollbars only when necessary"
        )
    elif "what is inline-block"  or "inline-block"in user_text:
        response = (
            "1,Compared to display: inline, the major difference is that display: inline-block allows to set a width and height on the element.\n"
            "2,Also, with display: inline-block, the top and bottom margins/paddings are respected, but with display: inline they are not.\n"
            "3,Compared to display: block, the major difference is that display: inline-block does not add a line-break after the element, so the element can sit next to other elements./n"
            "4,The following example shows the different behavior of display: inline, display: inline-block and display: block"
        )
    elif "flex property?" in user_text or "what is flex Property?" in user_text:
        response = (
            "flex-grow\n"
            "flex basis\n"
            "flex-shrink\n"
        )
    elif "flex-wrap?" in user_text or "what is flex-wrap?" in user_text:
        response = (
            "The flex-wrap property specifies whether the flexible items should wrap or not.\n"
            "Note: If the elements are not flexible items, the flex-wrap property has no effect.\n"
        )
    elif "grid property?" in user_text or "what is grid property?" in user_text:
        response = (
            "The grid property is a shorthand property for:\n"
            "1. grid-template-rows\n"
            "2. grid-template-columns\n"
            "3. grid-template-areas\n"
            "4. grid-auto-rows\n"
            "5. grid-auto-columns\n"
            "6. grid-auto-flow"
        )
    elif "Box sizing?" in user_text or "what is box Sizing?" in user_text:
        response = (
            "The CSS box-sizing property allows us to include the padding and border in an element's total width and height.\n"
        )
    elif "box-shadow?" in user_text or "what is box-shadow?" in user_text:
        response = (
            "The box-shadow property attaches one or more shadows to an element.\n"
        )
    elif "flex-direction?" in user_text or "what is flex-direction?" in user_text:
        response = (
            "The flex-direction property specifies the direction of the flexible items.\n"
            "Note: If the element is not a flexible item, the flex-direction property has no effect.\n"
        )
    elif "width property?" in user_text or "what is width property?" in user_text:
        response = (
            "The width property sets the width of an element.\n"
            "The width of an element does not include padding, borders, or margins!\n"
            "Note: The min-width and max-width properties override the width property.\n"
        )
    # py  
    elif "what is python?" in user_text:
        response = (
            "Python is a high-level, interpreted, general-purpose programming language.\n"
            "It was created by Guido van Rossum in 1991.\n"
            "Python features dynamic typing, interpreted nature, and a large standard library.\n"
            "Example: print('Hello, World!')"
        )
    elif "how to use a function" in user_text:
        response = (
            "To use a function, you need to define it first.\n"
            "You can define a function using the 'def' keyword.\n"
            "Example: def greet(name):\n"
            "    print('Hello,', name)"
        )
        
    elif "Hello" in user_text:
        response = (
            "Hello, I'm a simple Python bot that responds to basic greetings and basic programming questions."
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
    elif "thanks" in user_text:
        response = (
        "You're welcome! 😊 If you have any more questions or run into any issues, feel fre.\n"
        )
    elif "loop" in user_text:
        response = (
            "Looping in Python is done using the 'for' loop or the 'while' loop.\n"
            "The 'for' loop is used to iterate over a sequence (like a list or string).\n"
            "Example: for item in ['apple', 'banana', 'cherry']: print(item)"
        )
    elif "function" in user_text:
        response = (
            "A function is a block of code that performs a specific task.\n"
            "Functions can be reused, making the code more modular and easier to manage.\n"
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
    application = ApplicationBuilder().token("7316188795:AAEi0o-hFR8jv9uZqcbPYpYpdyCnVmWqoOU").build()

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