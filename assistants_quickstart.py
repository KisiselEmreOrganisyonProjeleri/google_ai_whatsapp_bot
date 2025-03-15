import os
import time
import shelve
from dotenv import find_dotenv, load_dotenv
import google.generativeai as genai

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)


# API anahtarını ve model adını al
API_KEY = os.getenv("API_KEY")  # Gemini için API anahtarı
GENAI_MODEL_NAME = os.getenv("GENAI_MODEL_NAME", "models/gemini-2.0-flash")  # Varsayılan model adı

instruction = """We are running a charity fund for constructing well's for supplying African region with clean water as various other (donations).

Your Role:
You are a helpful Assistant. Your task is to generate high-quality responses to given messages. You should always keep a friendly and kind tone as you have a conversation with these Users.

Instructions:
Greet Users kindly and thank them for their interest.
Never share IBAN number unless User agrees to donate.
Keep a close eye on the current state of the conversation.

Rules:
Users can only donate using IBAN number and transfer money. No creditcards or other options are available.

Output Format:
Meticulously crafted response to the sender of the following message.

IBAN: TR6700 0100 1910 9625 2909 5001

Now please reply responsibly folowing all the guideline above."""

# GenAI yapılandırmasını gerçekleştir
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(GENAI_MODEL_NAME, system_instruction=instruction)



# --------------------------------------------------------------
# Thread yönetimi (Gemini için sohbet geçmişini kullanma)
# --------------------------------------------------------------
def check_if_thread_exists(wa_id):
    # Belirtilen wa_id için bir sohbet geçmişi olup olmadığını kontrol et
    with shelve.open("gemini_chats_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, chat_history):
    # Belirtilen wa_id için sohbet geçmişini sakla
    with shelve.open("gemini_chats_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = chat_history


# --------------------------------------------------------------
# Yanıt oluştur
# --------------------------------------------------------------
def generate_response(message_body, wa_id, name):
    # wa_id için zaten bir thread_id (şimdi sohbet geçmişi) olup olmadığını kontrol et
    chat_history = check_if_thread_exists(wa_id)
    chat = None

    # Bir thread (sohbet geçmişi) yoksa, bir tane oluştur ve sakla
    if chat_history is None:
        print(f"wa_id {wa_id} olan {name} için yeni sohbet oluşturuluyor")
        chat = model.start_chat(history=[])
        store_thread(wa_id, chat.history)
        thread_id = wa_id # Basitlik için wa_id'yi thread_id olarak kullanma, gerekmiyorsa kaldırılabilir
    # Aksi takdirde, mevcut thread'i (sohbet geçmişi) al
    else:
        print(f"wa_id {wa_id} olan {name} için mevcut sohbet alınıyor")
        chat = model.start_chat(history=chat_history)

    # Yardımcıyı çalıştır ve yeni mesajı al
    new_message = run_assistant(chat, message_body)
    print(f"{name} kişisine:", new_message)
    return new_message


# --------------------------------------------------------------
# Yardımcıyı çalıştır
# --------------------------------------------------------------
def run_assistant(chat, message_body):
    # Yardımcıyı almana gerek yok, doğrudan modeli kullan
    response = chat.send_message(message_body)
    new_message = response.text
    print(f"Oluşturulan mesaj: {new_message}")
    return new_message


# --------------------------------------------------------------
# Yardımcıyı test et
# --------------------------------------------------------------

wa_id = input('Lütfen Telefon Kimliğini Giriniz: ')
name = input('Lütfen İsminizi Giriniz')

while True:
    user_message = input('Siz: ')
    if user_message.lower() == 'exit':
        print('Sohbet Sonlandırıldı')
        break
    response = generate_response(user_message, wa_id, name)
    print(f"Asistan: {response}")

