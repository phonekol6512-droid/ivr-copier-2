import requests
import re
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://call2all.co.il"

# --- המודול המקורי שלך (ללא שינוי, תמיד עובד) ---
@app.route('/copy-module', methods=['GET', 'POST'])
def copy_module():
    system_src = request.values.get('system_src')
    pass_src = request.values.get('pass_src')
    ext_src = request.values.get('ext_src')
    system_dst = request.values.get('system_dst')
    pass_dst = request.values.get('pass_dst')
    ext_dst = request.values.get('ext_dst')

    if not system_src: return ym_read("system_src", "t-אנא הקישו את מספר מערכת המקור ובסיומה סולמית")
    if not pass_src:   return ym_read("pass_src", "t-אנא הקישו את סיסמת מערכת המקור ובסיומה סולמית")
    if not ext_src:    return ym_read("ext_src", "t-אנא הקישו את מספר השלוחה להעתקה ובסיומה סולמית")
    if not system_dst: return ym_read("system_dst", "t-אנא הקישו את מספר מערכת היעד ובסיומה סולמית")
    if not pass_dst:   return ym_read("pass_dst", "t-אנא הקישו את סיסמת מערכת היעד ובסיומה סולמית")
    if not ext_dst:    return ym_read("ext_dst", "t-אנא הקישו את שלוחת היעד החדשה ובסיומה סולמית")

    return run_copy_logic(system_src, pass_src, ext_src, system_dst, pass_dst, ext_dst)


# --- 🌟 המודול החכם והחסין באמת (על בסיס המידע הגולמי) 🌟 ---
@app.route('/copy-smart', methods=['GET', 'POST'])
def copy_module_smart():
    # שואבים את כל הטקסט הגולמי שנשלח בבקשה (הן מהקישור והן מגוף הבקשה)
    raw_data = request.query_string.decode('utf-8', errors='ignore') + "&" + request.get_data(as_text=True)
    
    # פונקציה פנימית לחילוץ ערכים באמצעות חיתוך טקסט ישיר (Regex) כדי לדלג על בעיות הפיצול
    def find_raw_param(name, fallback_var):
        # 1. בודקים אם המאזין כבר הקיש את זה בטלפון בשלב קודם
        if request.values.get(fallback_var):
            return request.values.get(fallback_var).strip()
            
        # 2. מחפשים בטקסט הגולמי את התבנית של המשתנה מה-ext.ini (למשל login1=ספרות)
        match = re.search(r'[\?&]api_add_\d+=' + name + r'=([^&]+)', raw_data)
        if not match:
            match = re.search(r'[\?&]' + name + r'=([^&]+)', raw_data)
        
        if match:
            return requests.utils.unquote(match.group(1)).strip()
        return None

    # שליפת המשתנים מהמידע הגולמי בצורה חסינה
    system_src = find_raw_param('login1', 'system_src')
    pass_src = find_raw_param('password1', 'pass_src')
    ext_src = find_raw_param('key1', 'ext_src')
    
    system_dst = find_raw_param('login2', 'system_dst')
    pass_dst = find_raw_param('password2', 'pass_dst')
    ext_dst = find_raw_param('key2', 'ext_dst')

    # הבדיקה החכמה: תשאל בטלפון רק את מה שלא חולץ בהצלחה מהקובץ
    if not system_src or system_src == "": return ym_read("system_src", "t-אנא הקישו את מספר מערכת המקור ובסיומה סולמית")
    if not pass_src or pass_src == "":   return ym_read("pass_src", "t-אנא הקישו את סיסמת מערכת המקור ובסיומה סולמית")
    if not ext_src or ext_src == "":    return ym_read("ext_src", "t-אנא הקישו את מספר השלוחה להעתקה ובסיומה סולמית")
    
    if not system_dst or system_dst == "": return ym_read("system_dst", "t-אנא הקישו את מספר מערכת היעד ובסיומה סולמית")
    if not pass_dst or pass_dst == "":   return ym_read("pass_dst", "t-אנא הקישו את סיסמת מערכת היעד ובסיומה סולמית")
    if not ext_dst or ext_dst == "":    return ym_read("ext_dst", "t-אנא הקישו את שלוחת היעד החדשה ובסיומה סולמית")

    return run_copy_logic(system_src, pass_src, ext_src, system_dst, pass_dst, ext_dst)


# --- לוגיקת ההעתקה המשותפת של המערכת ---
def run_copy_logic(system_src, pass_src, ext_src, system_dst, pass_dst, ext_dst):
    try:
        token_src = f"{system_src.strip()}:{pass_src.strip()}"
        token_dst = f"{system_dst.strip()}:{pass_dst.strip()}"
        
        clean_src = ext_src.strip().replace('*', '/').replace('-', '/').strip('/')
        clean_dst = ext_dst.strip().replace('*', '/').replace('-', '/').strip('/')
        
        path_src = f"ivr2:/{clean_src}/ext.ini"
        path_dst = f"ivr2:/{clean_dst}/ext.ini"

        # 1. הורדת הקובץ ממערכת המקור
        download_url = f"{YEMOT_API_URL}DownloadFile"
        src_response = requests.get(download_url, params={"token": token_src, "path": path_src})

        if src_response.status_code != 200 or "הסיסמא שגויה" in src_response.text or "לא נמצא" in src_response.text:
            return ym_say_and_hangup("t-שגיאה. נתוני מערכת המקור שגויים או שהשלוחה לא קיימת.")

        ini_content = src_response.text

        # הוספת שורת הקרדיט בסוף הקובץ המועתק
        ini_content += "\n\ntitle=שלוחה זאת הגדרה ע'י פון קול"

        # 2. העלאת הקובץ המשודרג למערכת היעד
        upload_url = f"{YEMOT_API_URL}UploadTextFile?token={token_dst}&what={path_dst}&contents={requests.utils.quote(ini_content)}"
        dst_response = requests.post(upload_url)

        if dst_response.status_code == 200 and '"responseStatus":"OK"' in dst_response.text:
            return ym_say_and_hangup("t-ההעתקה בוצעה בהצלחה. השלוחה הועתקה.")
        return ym_say_and_hangup("t-שגיאה בהעלאת הנתונים למערכת היעד.")

    except Exception as e:
        print(f"API Error: {str(e)}")
        return ym_say_and_hangup("t-התרחשה שגיאה בתקשורת עם השרתים.")

def ym_read(var_name, text):
    res = make_response(f"read={text}={var_name},4,12,1,Digits")
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

def ym_say_and_hangup(text):
    res = make_response(f"id_list_message={text}")
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

__all__ = ['app']
