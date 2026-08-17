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
    payload = {
        "chat_id": TELEGRAM_CHAT_ID, 
        "text": message, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True
    }
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
    # Doctor of Credit Bank Bonus RSS Feed
    url = "https://www.doctorofcredit.com/category/bank-account-bonuses/feed/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.content, 'xml')
        items = soup.find_all('item')
        
        count = 0
        for item in items:
            title = item.find('title').get_text().strip() if item.find('title') else ""
            link = item.find('link').get_text().strip() if item.find('link') else ""
            pub_date = item.find('pubDate').get_text().strip() if item.find('pubDate') else ""
            description = item.find('description').get_text().strip() if item.find('description') else ""
            
            combined_text = (title + " " + description).lower()
            
            # 1. Strict Expiry Filter
            if any(exp in combined_text for exp in ['expired', 'expired deal', 'expired bonus', '[expired]']):
                continue
                
            # 2. Meta/General Page Title Filter
            if any(meta in title.lower() for meta in ['best bank account bonuses', 'q1', 'q2', 'q3', 'q4', 'august 2026', 'july 2026']):
                continue
            
            # 3. No Deposit / Easy Requirement Filter
            if any(req in combined_text for req in ['no direct deposit', 'no deposit', '$0 deposit', 'no dd required', 'easy bonus', 'without direct deposit']):
                clean_date = pub_date[:16] if pub_date else "সাম্প্রতিক"
                count += 1
                
                bn_title = translate_to_bangla(title)
                bn_date = translate_to_bangla(clean_date)
                
                doc_results.append(f"{count}. *{bn_title}*\n📅 তারিখ: {bn_date}\n🔗 [আর্টিকেল লিংক]({link})")
                if count >= 3:
                    break
    except Exception as e:
        doc_results.append(f"Doctor of Credit স্ক্র্যাপ করতে এরর: {e}")
    return doc_results

def scrape_bankbonus():
    bb_results = []
    url = "https://bankbonus.com/best/bank-promotions-without-direct-deposit/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        headings = soup.find_all(['h2', 'h3'])
        
        count = 0
        for h in headings:
            title = h.get_text().strip()
            title_lower = title.lower()
            
            # 1. Expiry Check
            if any(exp in title_lower for exp in ['expired', 'ended', 'closed']):
                continue
                
            # 2. Filter specific bank deals (Must have $ amount and ignore generic section titles)
            if '$' in title and not any(gen in title_lower for gen in ['best bank', 'promotions without', 'bonus offers for', 'best checking']):
                link_tag = h.find('a')
                link = link_tag['href'] if link_tag and link_tag.has_attr('href') else url
                if link.startswith('/'):
                    link = "https://bankbonus.com" + link
                
                count += 1
                bn_title = translate_to_bangla(title)
                
                bb_results.append(f"{count}. *{bn_title}*\n📅 অফার টাইপ: সক্রিয় (No Direct Deposit)\n🔗 [আর্টিকেল লিংক]({link})")
                if count >= 3:
                    break
    except Exception as e:
        bb_results.append(f"BankBonus স্ক্র্যাপ করতে এরর: {e}")
    return bb_results

def run_scraper():
    today = datetime.now().strftime("%d %B, %Y")
    msgs = [f"🔔 *আজকের ফিল্টারকৃত লেটেস্ট ব্যাংক বোনাস* ({today})\n"]
    
    msgs.append("📌 *Doctor of Credit (সক্রিয় ও নতুন আর্টিকেল):*")
    doc_data = scrape_doc()
    msgs.extend(doc_data if doc_data else ["বর্তমানে নতুন কোনো সক্রিয় 'No Deposit' অফারের আর্টিকেল নেই।"])
    
    msgs.append("\n" + "="*30 + "\n")
    
    msgs.append("📌 *BankBonus.com (সক্রিয় প্রমোশনসমূহ):*")
    bb_data = scrape_bankbonus()
    msgs.extend(bb_data if bb_data else ["কোনো নির্দিষ্ট সক্রিয় অফার পাওয়া যায়নি।"])
    
    full_text = "\n\n".join(msgs)
    send_telegram_msg(full_text)

if __name__ == "__main__":
    run_scraper()
