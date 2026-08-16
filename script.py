import os
import requests
from bs4 import BeautifulSoup
from googletrans import Translator
from datetime import datetime

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
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": True}
    requests.post(url, data=payload)

def translate_to_bangla(text):
    if not text:
        return ""
    try:
        return translator.translate(text, dest='bn').text
    except Exception:
        return text

def scrape_doc():
    doc_results = []
    url = "https://www.doctorofcredit.com/category/bank-account-bonuses/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        posts = soup.find_all('div', class_='post')
        
        count = 0
        for post in posts:
            title_tag = post.find(['h2', 'h3'])
            if not title_tag: continue
            
            title = title_tag.get_text().strip()
            link_tag = title_tag.find('a')
            link = link_tag['href'] if link_tag else url
            
            # Extract Date
            date_tag = post.find('time') or post.find('span', class_='date')
            date_str = date_tag.get_text().strip() if date_tag else "সাম্প্রতিক"
            
            if any(k in title.lower() for k in ['no direct deposit', 'no deposit', '$0 deposit', 'easy bonus', 'checking', 'bonus']):
                count += 1
                bn_title = translate_to_bangla(title)
                bn_date = translate_to_bangla(date_str)
                doc_results.append(f"{count}. *{bn_title}*\n📅 তারিখ: {bn_date}\n🔗 [আর্টিকেল লিংক]({link})")
                if count >= 3: break
    except Exception as e:
        doc_results.append(f"Doctor of Credit এরর: {e}")
    return doc_results

def scrape_bankbonus():
    bb_results = []
    url = "https://bankbonus.com/promotions/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        headings = soup.find_all(['h2', 'h3'])
        
        count = 0
        for h in headings:
            title = h.get_text().strip()
            if any(char in title for char in ['$', 'Bonus', 'Checking', 'Savings']):
                link_tag = h.find('a')
                link = link_tag['href'] if link_tag and link_tag.has_attr('href') else url
                if link.startswith('/'): link = "https://bankbonus.com" + link
                
                count += 1
                bn_title = translate_to_bangla(title)
                bb_results.append(f"{count}. *{bn_title}*\n📅 তারিখ: আপডেট অফার\n🔗 [আর্টিকেল লিংক]({link})")
                if count >= 3: break
    except Exception as e:
        bb_results.append(f"BankBonus এরর: {e}")
    return bb_results

def run_scraper():
    today = datetime.now().strftime("%d %B, %Y")
    msgs = [f"🔔 *আজকের সর্বশেষ ব্যাংক বোনাস আপডেট* ({today})\n"]
    
    msgs.append("📌 *Doctor of Credit (সর্বশেষ খবর):*")
    doc_data = scrape_doc()
    msgs.extend(doc_data if doc_data else ["কোনো নতুন পোস্ট পাওয়া যায়নি।"])
    
    msgs.append("\n" + "="*30 + "\n")
    
    msgs.append("📌 *BankBonus.com (সর্বশেষ অফার):*")
    bb_data = scrape_bankbonus()
    msgs.extend(bb_data if bb_data else ["কোনো নতুন অফার পাওয়া যায়নি।"])
    
    full_text = "\n\n".join(msgs)
    send_telegram_msg(full_text)

if __name__ == "__main__":
    run_scraper()
