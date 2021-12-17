# Python libs import
import json

# Telebot imports
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Class imports
from Constants import *
from BotUser import *


# Admin variables
admin = False


# User variables
UserStates = {}


# Load credentials
credentialsFile = open(DataDirectory + "Credentials.json", "r")
credentials = json.load(credentialsFile)
credentialsFile.close()

# Create bot
bot = TeleBot(credentials["token"])


# Helper Functions
def SendMessage(user, message, reply_markup = None):
    bot.send_message(user, message, reply_markup=reply_markup)

def FetchUser(id) -> BotUser:
    if id not in UserStates:
        UserStates[id] = BotUser(id)
    return UserStates[id]


# User Commands
@bot.message_handler(commands=["start"])
def Start_Command(m):
    SendMessage(m.chat.id, "Send your questions in the chat, it'll be answered shortly. Spammers will be ignored.")


# Admin Commands
@bot.message_handler(commands=["login"])
def Login_Command(m):
    # Fetch user
    user = FetchUser(m.chat.id)

    # Check user is locked
    if user.Role == ROLE_LOCKED:
        SendMessage(user.ID, "Unable to login")
    else:
        # Check user is admin
        if user.Role != ROLE_ADMIN:
            # Split command message to get password
            split = m.text.split(" ")
            if len(split) > 1 and split[1] == credentials["password"]:
                # Update user role to admin upon login
                user.Role = ROLE_ADMIN
                SendMessage(user.ID, "Login successful")
            else:
                # Incorrect password entered
                user.AttemptLoginFail()
                SendMessage(user.ID, "Incorrect password entered, try again.")
        else:
            SendMessage(user.ID, "You are already logged in.")
            
    # Delete login command message for security
    bot.delete_message(user.ID, m.message_id)