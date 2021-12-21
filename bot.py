# Python libs import
import json
import time

# Telebot imports
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Class imports
from Constants import *
from BotUser import *
from Messages import Messages, MongoDB, Upsert, WriteIntoDB


# User variables
UserStates = {}


# Load credentials
credentialsFile = open(DataDirectory + "Credentials.json", "r")
credentials = json.load(credentialsFile)
credentialsFile.close()

# Update MongoDB credentials
MongoDB.Connect(credentials["atlas"])
Messages.Connect()

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
@bot.message_handler(commands=["start", "help"])
def Start_Command(m):
    SendMessage(m.chat.id, "Send your questions in the chat, it'll be answered shortly. Spammers will be ignored.\n\n*All engagements will be kept anonymous.\n*By using this bot, you consent to your data being used for research and analysis purposes.")

# Capture all text messages that are not commands
@bot.message_handler(func=lambda m : not m.text.startswith("/"), content_types=["text"])
def AnyTextMessage(m):
    # Fetch user
    user = FetchUser(m.chat.id)
    now = time.time()
    if user.PreviousSendTime == None or now > user.PreviousSendTime + SENDING_INTERVAL_MS:
        user.PreviousSendTime = now
        WriteIntoDB(m.chat.id, m.chat.username, m.text)
        print(f"{m.chat.username} ({m.chat.id}) asked \"{m.text}\"")
        SendMessage(m.chat.id, "Question registered, it'll be answered shortly.")
    else:
        SendMessage(m.chat.id, f"Please wait another {int(user.PreviousSendTime + SENDING_INTERVAL_MS - now)} seconds before asking a question.")


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

@bot.message_handler(commands=["logout"])
def Logout_Command(m):
    # Fetch user
    user = FetchUser(m.chat.id)
    
    if user.Role == ROLE_ADMIN:
        user.Role = ROLE_DEFAULT
        SendMessage(user.ID, "Logout successfully")
    else:
        SendMessage(user.ID, "Not logged in")

@bot.message_handler(commands=["reset"])
def Reset_Command(m):
    # Fetch user
    user = FetchUser(m.chat.id)
    user.CurrentChatID = user.CurrentMessageIndex = user.CurrentMessages = None

@bot.message_handler(commands=["list"])
def List_Command(m):
    # Fetch user
    user = FetchUser(m.chat.id)

    if user.Role != ROLE_ADMIN:
        return

    Reset_Command(m)
    messages = Messages.Collection.find()
    markup = InlineKeyboardMarkup()
    for message in messages:
        if not message["banned"]:
            markup.add(InlineKeyboardButton(message["id"], callback_data=message["id"]))
    SendMessage(user.ID, "All askers", markup)

@bot.message_handler(commands=["question"])
def Question_Command(m):
    # Fetch user
    user = FetchUser(m.chat.id)

    if user.Role != ROLE_ADMIN:
        return
    if user.CurrentMessages == None:
        SendMessage(user.ID, "No asker selected yet")
        return

    markup = InlineKeyboardMarkup()
    count = 0
    for q in user.CurrentMessages.questions:
        if user.CurrentMessages.answered[count] == "":
            markup.add(InlineKeyboardButton(f"Question #{count + 1}", callback_data=str(count)))
        else:
            markup.add(InlineKeyboardButton(f"[Answered] Question #{count + 1}", callback_data=str(count)))
        count += 1
    SendMessage(user.ID, f"All questions by {user.CurrentChatID}", markup)

@bot.message_handler(commands=["ban"])
def Ban_Command(m):
    # Fetch user
    user = FetchUser(m.chat.id)

    if user.Role != ROLE_ADMIN:
        return
    if user.CurrentMessages == None:
        SendMessage(user.ID, "No asker selected yet")

    user.CurrentMessages.banned = True
    Upsert({"id":user.CurrentChatID}, user.CurrentMessages)
    Reset_Command(m)

@bot.callback_query_handler(lambda query : query.data != "")
def Callback(query):
    # Fetch user
    user = FetchUser(query.message.chat.id)

    if user.Role != ROLE_ADMIN:
        return

    if user.CurrentChatID != None:
        # Question number
        user.CurrentMessageIndex = int(query.data)
        SendMessage(user.ID, f"Question: {user.CurrentMessages.questions[user.CurrentMessageIndex]}\n\nPlease type your answer below.")
        bot.register_next_step_handler_by_chat_id(user.ID, AnsweringQuestion)
    else:
        # Chat ID
        user.CurrentChatID = int(query.data)
        m = Messages.Collection.find_one({"id":user.CurrentChatID})
        if m == None:
            SendMessage(user.ID, "No such asker!")
            Reset_Command(query.message)
            return
        user.CurrentMessages = Messages().FromDict(m)
        user.CurrentMessageIndex = None
        Question_Command(query.message)
        #SendMessage(user.ID, "User ID Registered")

def AnsweringQuestion(m):
    user = FetchUser(m.chat.id)
    reply = f"Question: {user.CurrentMessages.questions[user.CurrentMessageIndex]}\n\n"
    if user.CurrentMessages.answered[user.CurrentMessageIndex] != "":
        reply += f"Old Answer: {user.CurrentMessages.answered[user.CurrentMessageIndex]}\n\nNew Answer: {m.text}"
    else:
        reply += f"Answer: {m.text}"
    SendMessage(user.CurrentChatID, reply)
    user.CurrentMessages.answered[user.CurrentMessageIndex] = m.text
    Upsert({"id":user.CurrentChatID}, user.CurrentMessages)
    SendMessage(user.ID, reply)
    user.CurrentMessageIndex = None
    Question_Command(m)


# Start polling for messages
bot.polling(none_stop=True)