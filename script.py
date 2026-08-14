import os
import requests
from bs4 import BeautifulSoup
from googletrans import Translator

# Telegram Credentials from Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

translator = Translator()

def send_telegram_msg(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram Token or Chat ID is missing!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

def translate_to_bangla(text):
    if not text:
        return ""
    try:
        return translator.translate(text, dest='bn').text
    except Exception:
        return text

def run_scraper():
    output_msgs = ["🔔 *আজকের ব্যাংক বোনাস আপডেট (No Direct Deposit)*\n"]
    
    # 1. Doctor of Credit
    doc_url = "https://www.doctorofcredit.com/best-bank-account-bonuses/"
    try:
        res = requests.get(doc_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        posts = soup.find_all(['h2', 'h3'])
        
        count = 0
        output_msgs.append("📌 *Doctor of Credit:*")
        for post in posts:
            text_content = post.get_text()
            if any(k in text_content.lower() for k in ['no direct deposit', 'no deposit', '$0 deposit']):
                link_tag = post.find('a') or post.find_parent('a')
                link = link_tag['href'] if link_tag and link_tag.has_attr('href') else doc_url
                
                count += 1
                bn_title = translate_to_bangla(text_content.strip())
                output_msgs.append(f"\n{count}. {bn_title}\n🔗 [লিংক দেখুন]({link})")
                if count >= 3: break
        if count == 0:
            output_msgs.append("কোনো নতুন অফার পাওয়া যায়নি।")
    except Exception as e:
        output_msgs.append(f"DoC এরর: {e}")

    output_msgs.append("\n" + "="*30 + "\n")

    # 2. BankBonus
    bb_url = "https://bankbonus.com/best/bank-promotions-without-direct-deposit/"
    try:
        res = requests.get(bb_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        headings = soup.find_all(['h2', 'h3'])
        
        count = 0
        output_msgs.append("📌 *BankBonus.com:*")
        for h in headings:
            title = h.get_text().strip()
            if any(char in title for char in ['$', 'Bonus', 'Checking', 'Savings']):
                link_tag = h.find('a')
                link = link_tag['href'] if link_tag and link_tag.has_attr('href') else bb_url
                if link.startswith('/'): link = "https://bankbonus.com" + link
                
                count += 1
                bn_title = translate_to_bangla(title)
                output_msgs.append(f"\n{count}. {bn_title}\n🔗 [লিংক দেখুন]({link})")
                if count >= 3: break
    except Exception as e:
        output_msgs.append(f"BankBonus এরর: {e}")

    # Send final report to Telegram
    full_text = "\n".join(output_msgs)
    send_telegram_msg(full_text)

if __name__ == "__main__":
    run_scraper()
