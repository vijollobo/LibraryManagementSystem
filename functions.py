import mysql.connector
import hashlib
from email.message import EmailMessage
import ssl
import smtplib
import re
import streamlit as st
from datetime import date
import random, string, math
import os
from dotenv import load_dotenv
load_dotenv()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306))
    )
#cur=get_connection().cursor()
def tuples2list(tuplelist : tuple) -> list:
    resultlist = [element for tup in tuplelist for element in tup]
    return resultlist

def isint(num:str)->bool: #checks if given string is a float or not
    try:
        int(num)
        return True
    except ValueError:
        return False

def valid_isbn(isbn):
    return isint(isbn) and len(isbn)==13

def generate_code(length=5, cur=None, table=None, column=None):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not (cur and table and column):
            return code

        cur.execute(f"SELECT 1 FROM {table} WHERE {column}=%s LIMIT 1", (code,))
        if not cur.fetchone():
            return code


def send_email(email_receiver, subject, body, isHTML=False):
    email_sender = os.getenv("EMAIL_ID")
    email_password = os.getenv("EMAIL_PASS")

    context = ssl.create_default_context()

    msg = EmailMessage()
    msg["From"] = email_sender
    msg["To"] = email_receiver
    msg["Subject"] = subject

    if isHTML:
        # Plain-text fallback (important for email clients)
        msg.set_content("This email contains HTML content. Please use an HTML-compatible email client.")
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.send_message(msg)


def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_regex, email):
        return True
    return False

def table_parameter_exists(table,parameter, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM {table} WHERE {parameter}=%s", (value,))
    res = cur.fetchone()
    conn.close()
    return res is not None

def calculate_cost(
    book_cost: float,
    issue_date: date,
    due_date: date,
    return_date: date,
    base_daily_rate: float = 1.0,
    late_fee_base: float = 2.0
):
    """
    Calculates total cost incurred for a library book.

    Parameters
    ----------
    book_price : float
        MRP or valuation of the book
    issue_date : date
    due_date : date
    return_date : date
    base_daily_rate : float
        Base cost per day before subsidy
    late_fee_base : float
        Base multiplier for late fees

    Returns
    -------
    dict
        Detailed cost breakdown
    """

    # 1. DAY CALCULATIONS (+1 LOGIC)
    total_days = (return_date - issue_date).days + 1
    allowed_days = (due_date - issue_date).days + 1
    late_days = max(0, (return_date - due_date).days)

    # 2. SUBSIDY FACTOR k (LOG SCALE)
    # k ∈ [0.27, 0.55]
    min_price = 100
    max_price = 5000

    normalized_price = max(min(book_cost, max_price), min_price)

    k = 0.27 + (0.55 - 0.27) * (
        math.log(normalized_price / min_price) /
        math.log(max_price / min_price)
    )

    # 3. BASE COST (SUBSIDIZED)
    effective_daily_rate = base_daily_rate * (1 - k)
    base_cost = total_days * effective_daily_rate

    # 4. LATE FEES (QUADRATIC GROWTH)
    late_fee = 0
    if late_days > 0:
        late_fee = late_fee_base * (late_days ** 2)

    # 5. FINAL COST
    total_cost = max(2,round(base_cost + late_fee, 2))

    return {
        "total_days": total_days,
        "allowed_days": allowed_days,
        "late_days": late_days,
        "base_cost": round(base_cost, 2),
        "late_fee": round(late_fee, 2),
        "total_cost": total_cost
    }

def numSuffix(n):
    suffix = ("ᵗʰ","ˢᵗ","ⁿᵈ","ʳᵈ")
    if n%10 in {1, 2, 3} and n not in {11,12,13}:
        return suffix[n % 10]
    else:
        return suffix[0]
    
date2string = lambda Date: Date.strftime("%A")+", "+str(int(Date.strftime("%d")))+numSuffix(int(Date.strftime("%d")))+" "+Date.strftime("%B")+" "+Date.strftime("%Y") #takes date and converts it into common format

calculateAge = lambda birthdate: date.today().year - birthdate.year - ((date.today().month, date.today().day) < (birthdate.month, birthdate.day))

def num2words(n):
        if len(str(n))>=1 and len(str(n))<=5:
            single_digits = ("", "one", "two", "three","four", "five", "six", "seven", "eight", "nine")
            two_digits = ("", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen")
            tens_multiple = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy","eighty","ninety")
            ten_power=('','hundred')
            def dig1or2(n):
                if n>=0 and n<=9:
                    word = single_digits[n]
                elif n>=10 and n<=19:
                    word=two_digits[n-9]
                elif n in range(20,91,10):
                    word=tens_multiple[(int(str(n)[0]))]
                elif n>20 and n<=99:
                    word1,word2=tens_multiple[(int(str(n)[0]))],single_digits[n%10]; word=word1+'-'+word2
                return word
            if n==0:
                word='Zero'
            elif n>0 and n<100:
                word=dig1or2(n)
            elif n>=100 and n<1000:
                word1=(single_digits[int(str(n)[0])])
                word=single_digits[int(str(n)[0])]+" hundred "+dig1or2(n%100)
            elif n>=1000 and n<10000:
                word=single_digits[int(str(n)[0])]+' thousand '+ single_digits[int(str(n)[1])]+' '+ten_power[0 if str(n)[1]=='0' else 1]+' '+ dig1or2(n%100)
            elif n>=10000 and n<=99999:
                word=dig1or2(n//1000)+ ' thousand '+single_digits[int(str(n)[2])]+' '+ten_power[0 if str(n)[2]=='0' else 1]+' '+ dig1or2(n%100)
            return word
        else:
            return None

def cost2word(n:float) -> str: #converts cost in float into words with proper rupees and paise
    costdivl=str(round(n,2)).split('.') #list with two strings, one of numbers before decimal and second with after
    if int(costdivl[0])<100000:
        if len(costdivl)==1:
            word = 'One rupee' if int(costdivl[0])==1 else num2words(int(costdivl[0]))+' rupees'
        elif len(costdivl)==2:
            if costdivl[1]=='0':
                word= 'One rupee' if int(costdivl[0])==1 else num2words(int(costdivl[0]))+' rupees'
            else:
                paisa=int(costdivl[1])*10 if len(costdivl[1])==1 else int(costdivl[1])
                word= ('One rupee and ' if int(costdivl[0])==1 else '' if int(costdivl[0])==0 else num2words(int(costdivl[0]))+' rupees and ')+ ('one paisa' if paisa==1 else num2words(paisa)+' paise')
        return word[0].upper()+word[1:]
    else: return None

def getISBN(label="Select a book"):
    """
    Displays a dropdown with 'Book Name (ISBN)'
    Returns the selected ISBN only
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ISBN, name FROM books ORDER BY name")
    books = cur.fetchall()
    conn.close()

    if not books:
        st.warning("No books available in the library.")
        return None

    book_map = {
        f"{isbn}  —  {name}": isbn
        for isbn, name in books
    }

    selected = st.selectbox(label, book_map.keys())

    return book_map[selected]

def getUserName(label="Select User"):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT username, name 
        FROM users 
        ORDER BY name
    """)
    users = cur.fetchall()
    conn.close()

    if not users:
        st.warning("No users found")
        return None

    options = {
        f"{u['username']} — {u['name']}": u['username']
        for u in users
    }

    choice = st.selectbox(label, list(options.keys()))
    return options.get(choice)

nativeLang= {
    "Konkani": "कोंकणी / ಕೊಂಕಣಿ / കൊങ്കണി",
    "Bangla": "বাংলা",
    "Marathi": "मराठी / 𑘦𑘨𑘰𑘙𑘲",
    "Maithili":"𑒧𑒻𑒟𑒱𑒪𑒲", 
    "Assamese": "অসমীয়া",
    "Axomiya": "অসমীয়া",
    "Kannada": "ಕನ್ನಡ",
    "Tamil": "தமிழ்",
    "Telugu": "తెలుగు",
    "Malayalam": "മലയാളം",
    "Gujarati": "ગુજરાતી",
    "Punjabi": "ਪੰਜਾਬੀ / پنجابی",
    "Urdu": "اردو",
    "Odia": "ଓଡ଼ିଆ",
    "Awadhi":"𑂃𑂫𑂡𑂲",
    'Angika':'अंगिका',
    "Bhojpuri": "𑂦𑂷𑂔𑂣𑂳𑂩𑂲",
    "Magahi":"𑂧𑂏𑂯𑂲",
    "Nepali": "नेपाली",
    "Sindhi": "सिन्धी",
    "Hindustani": "हिन्दुस्तानी / ہندوستانی",
    "Sanskrit": "संस्कृतम्",
    "Bodo":"बड़ो",
    "Dogri":"𑠖𑠵𑠌𑠤𑠮",
    "Koshur":"𑆑𑆳𑆯𑆶𑆫𑇀",
    "Kashmiri":"𑆑𑆳𑆯𑆶𑆫𑇀",
    "Manipuri":"ꯃꯅꯤꯄꯨꯔꯤ / মণিপুরী",
    'Santali':'ᱥᱟᱱᱛᱟᱲᱤ',
    'Sindhi':"سِنڌِي‎ / सिन्धी",
    "French": "français",
    "Spanish": "español",
    "German": "Deutsch",
    "Russian": "русский",
    "Chinese": "中文",
    "Japanese": "日本語",
    "Korean": "한국어",
    "Hindi": "हिन्दी",
    "Arabic": "العربية",
    "Persian": "فارسی",
    "Hebrew": "עברית",
    "Greek": "Ελληνικά",
    "Italian": "italiano",
    "Portuguese": "português",
    "Swedish": "svenska",
    "Dutch": "Nederlands",
    "Turkish": "Türkçe",
    "Vietnamese": "Tiếng Việt",
    "Thai": "ไทย",
    "Hungarian": "magyar",
    "Czech": "čeština",
    "Polish": "polski",
    "Romanian": "română",
    "Ukrainian": "українська",
    "Serbian": "српски",
    "Croatian": "hrvatski",
    "Bulgarian": "български",
    "Finnish": "suomi",
    "Norwegian": "norsk",
    "Danish": "dansk",
    "Icelandic": "íslenska",
    "Irish": "Gaeilge",
    "Welsh": "Cymraeg",
    "Scottish Gaelic": "Gàidhlig",
    'Divehi':'ދިވެހި',
    'Amharic':'አማርኛ',
}