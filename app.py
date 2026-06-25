import requests
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


# --- 🌟 המודול החכם המעודכן (מותאם לפורמט ה-PHP של ימות המשיח) 🌟 ---
@app.route('/copy-smart', methods=['GET', 'POST'])
def copy_module_smart():
    # יצירת מילון שיחזיק את הפרמטרים שחולצו
    extracted = {}

    # סריקה יסודית של כל ה-api_add_X שימות המשיח שולחת מה-ext.ini
    for key, value in request.values.items():
        val_str = str(value).strip()
        # אם הערך מכיל סימן שווה (למשל: login1=0773016582)
        if "=" in val_str:
            parts = val_str.split('=', 1)
            param_name = parts[0].strip()   # למשל: login1
            param_value = parts[1].strip()  # למשל: 0773016582
            extracted[param_name] = param_value

    # שליפת המשתנים: עדיפות ראשונה למה שחולץ מה-ext.ini, עדיפות שנייה להקשת מאזין בטלפון
    system_src = extracted.get('login1') or request.values.get('system_src')
    pass_src = extracted.get('password1') or request.values.get('pass_src')
    ext_src = extracted.get('key1') or request.values.get('ext_src')
    
    system_dst = extracted.get('login2') or request.values.get('system_dst')
    pass_dst = extracted.get('password2') or request.values.get('pass_dst')
    ext_dst = extracted.get('key2') or request.values.get('ext_dst')

    # הבדיקה החכמה: ישאל בטלפון אך ורק אם המשתנה לא קיים בשום מקום (ריק)
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

        download_url = f"{YEMOT_API_URL}DownloadFile"
        src_response = requests.get(download_url, params={"token": token_src, "path": path_src})

        if src_response.status_code != 200 or "הסיסמא שגויה" in src_response.text or "לא נמצא" in src_response.text:
            return ym_say_and_hangup("t-שגיאה. נתוני מערכת המקור שגויים או שהשלוחה לא קיימת.")

        upload_url = f"{YEMOT_API_URL}UploadTextFile?token={token_dst}&what={path_dst}&contents={requests.utils.quote(src_response.text)}"
        dst_response = requests.post(upload_url)

        if dst_response.status_code == 200 and '"responseStatus":"OK"' in dst_response.text:
            return ym_say_and_hangup("t-ההעתקה בוצעה בהצלחה. השלוחה הועתקה.")
        return ym_say_and_hangup("t-שגיאה בהעלאת הנתונים למערכת היעד.")

    except Exception as e:
        print(f"API Error: {str(e)}")
        return ym_say_and_hangup("t-התרחשה שגיאה בתקשורת עם השרתים.")

def ym_read(var_name, text):
    # פורמט ההקשות המנצח והיציב שאתה פיצחת בעצמך!
    res = make_response(f"read={text}={var_name},4,12,1,Digits")
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

def ym_say_and_hangup(text):
    res = make_response(f"id_list_message={text}")
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

__all__ = ['app']
