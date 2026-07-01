import os
import re
import json
import shutil
import argparse
import random
import telebot
from config import Config
from markov import MarkovChain

whitespace_regex = re.compile(r'\s+')

class MarkovTelegramBot:
    def __init__(self, token: str, data_path: str):
        self.token = token
        self.data_path = data_path
        self.my_id = None
        self.my_username = ""

        self.fun_levels = {}
        self.load_fun_levels()

    def run(self):
        bot = telebot.TeleBot(self.token)

        try:
            me = bot.get_me()
            self.my_id = me.id
            self.my_username = me.username
        except Exception as e:
            raise Exception("failed to retrieve bot's username/id") from e

        print(f"bot id = {self.my_id}")
        print(f"bot started")

        @bot.message_handler(func=lambda msg: True, content_types=['text', 'caption', 'new_chat_members', 'left_chat_member'])
        def handle_update(message):
            try:
                self.handle_message(bot, message)
            except Exception as e:
                import traceback
                print(f"exception caught in handle_update: {e}")
                traceback.print_exc()

        bot.infinity_polling()

    def handle_message(self, bot, message):
        if message.chat.type == 'private':
            return

        chat_id = str(message.chat.id)

        if message.new_chat_members:
            for member in message.new_chat_members:
                if member.id == self.my_id:
                    print(f"added to group {chat_id}")

        if message.left_chat_member:
            if message.left_chat_member.id == self.my_id:
                print(f"removed from group {chat_id}")
                try:
                    self.delete_chat(chat_id)
                except Exception:
                    pass

        if message.from_user and message.from_user.id == self.my_id:
            return

        text = message.text or message.caption
        if text is not None and message.from_user is not None:
            self.handle_message_text(bot, message, chat_id, message.from_user, text)

    def handle_message_text(self, bot, message, chat_id, from_user, text):
        should_analyze_message = True
        entities = message.entities or message.caption_entities

        if entities:
            e0 = entities[0]
            if e0.type == "bot_command" and e0.offset == 0:
                should_analyze_message = False
                command_text = text.split()[0].split('@')[0]

                if command_text in ["/fun", "/deletemessage", "/toglimess"]:
                    self.handle_admin_command(bot, message, chat_id, from_user, text, command_text)

        if should_analyze_message:
            self.analyze_message(chat_id, text)
            self.try_automatic_reply(bot, message, chat_id)

    def is_admin(self, bot, chat_id, user_id):
        try:
            admins = bot.get_chat_administrators(chat_id)
            return any(admin.user.id == user_id for admin in admins)
        except Exception:
            return False

    def handle_admin_command(self, bot, message, chat_id, from_user, text, command):
        if not self.is_admin(bot, message.chat.id, from_user.id):
            bot.send_message(message.chat.id, "solo amministratori")
            return

        bot.send_chat_action(int(chat_id), 'typing')

        if command == "/fun":
            args = whitespace_regex.split(text)
            if len(args) < 2:
                current = self.fun_levels.get(chat_id, 1)
                bot.send_message(message.chat.id, f"il divertimento è attualmente di {current}/10")
                return

            try:
                level = int(args[1])
                if level < 1 or level > 10:
                    raise ValueError()
            except ValueError:
                bot.send_message(message.chat.id, "inserisci un numero intero valido da 1 a 10")
                return

            self.fun_levels[chat_id] = level
            self.save_fun_levels()
            bot.send_message(message.chat.id, f"divertimento impostato a {level}/10!")

        elif command in ["/deletemessage", "/toglimess"]:
            reply_to_message = message.reply_to_message
            if reply_to_message is not None:
                target_text = reply_to_message.text or reply_to_message.caption or ""
                if target_text:
                    words = whitespace_regex.split(target_text)
                    path = self.get_total_markov_path(chat_id)

                    try:
                        markov_chain = MarkovChain.read(path)
                        markov_chain.remove(words)
                        markov_chain.write(path)
                        bot.send_message(message.chat.id, "messaggio rimosso dal dizionario!")
                    except Exception:
                        bot.send_message(message.chat.id, "nessun dizionario per questo gruppo!")
                else:
                    bot.send_message(message.chat.id, "il messaggio a cui hai risposto non contiene testo!")
            else:
                bot.send_message(message.chat.id, "devi rispondere al messaggio che vuoi rimuovere dal dizionario!")

    def try_automatic_reply(self, bot, message, chat_id):
        fun_level = self.fun_levels.get(chat_id, 1)

        if random.randint(1, 10) <= fun_level:
            bot.send_chat_action(int(chat_id), 'typing')

            try:
                chain = MarkovChain.read(self.get_total_markov_path(chat_id))
                gen = chain.generate()
                if gen:
                    sentence = " ".join(gen)
                    bot.send_message(message.chat.id, sentence.lower())
            except Exception:
                pass

    def analyze_message(self, chat_id, text):
        path = self.get_total_markov_path(chat_id)
        markov_chain = None
        try:
            markov_chain = MarkovChain.read(path)
        except Exception:
            pass

        if markov_chain is None:
            markov_chain = MarkovChain()

        words = whitespace_regex.split(text)
        markov_chain.add(words)
        markov_chain.write(path)

    def delete_chat(self, chat_id: str) -> bool:
        path = os.path.join(self.data_path, chat_id)
        if os.path.exists(path):
            shutil.rmtree(path)
            return True
        return False

    def get_total_markov_path(self, chat_id: str) -> str:
        return os.path.join(self.get_chat_path(chat_id), "total.json")

    def get_chat_path(self, chat_id: str) -> str:
        path = os.path.join(self.data_path, chat_id)
        os.makedirs(path, exist_ok=True)
        return path

    def get_fun_levels_path(self) -> str:
        return os.path.join(self.data_path, "fun_levels.json")

    def load_fun_levels(self):
        path = self.get_fun_levels_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.fun_levels = json.load(f)
            except Exception:
                self.fun_levels = {}

    def save_fun_levels(self):
        path = self.get_fun_levels_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.fun_levels, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"errore nel salvataggio di fun_levels: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.yaml", help="path al file yaml di configurazione")
    parser.add_argument("-d", "--data", default="./dati_bot", help="path alla cartella dei dati")
    args = parser.parse_args()

    config = Config.read(args.config)
    MarkovTelegramBot(config.telegram_bot_token, args.data).run()