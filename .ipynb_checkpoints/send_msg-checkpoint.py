import telegram

def send_message(msg):
    chat_token = "1740739677:AAFjOUObIBcjKs3nKAuHn4m349jbZvl6N6o"
    chat = telegram.Bot(token = chat_token)
    updates = chat.getUpdates()

    for u in updates:
        chat_id = u.message['chat']['id']

    bot = telegram.Bot(token = chat_token)
    bot.sendMessage(chat_id = chat_id, text=msg)

send_message("test sending message!!")