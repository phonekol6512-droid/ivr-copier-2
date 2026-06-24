import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://www.call2all.co.il/ym/api/"

# --- המודול המקורי שלך (ללא שינוי, עובד פיקס) ---
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


# --- 🌟 המודול החכם והסופי שלך! 🌟 ---
@app.route('/copy-smart', methods=['GET', 'POST'])
def copy_module_smart():
    # חילוץ ישיר של הפרמטרים מימות המשיח (כולל גיבוי של api_add בשביל תאימות מלאה)
    system_src = request.values.get('login1') or request.values.get('api_add_0') or request.values.get('system_src')
    pass_src = request.values.get('password1') or request.values.get('api_add_1') or request.values.get('pass_src')
    ext_src = request.values.get('key1') or request.values.get('api_add_2') or request.values.get('ext_src')
    
    system_dst = request.values.get('login2') or request.values.get('api_add_3') or request.values.get('system_dst')
    pass_dst = request.values.get('password2') or request.values.get('api_add_4') or request.values.get('pass_dst')
    ext_dst = request.values.get('key2') or request.values.get('api_add_5') or request.values.get('ext_dst')

    # ניקוי לכלוך ושאריות "שווה" אם ימות המשיח שלחה אותם משורשרים בטעות
    if system_src and "login1=" in str(system_src): system_src = str(system_src).split("login1=")[1]
    if pass_src and "password1=" in str(pass_src): pass_src = str(pass_src).split("password1=")[1]
    if ext_src and "key1=" in str(ext_src): ext_src = str(ext_src).split("key1=")[1]
    if system_dst and "login2=" in str(system_dst): system_dst = str(system_dst).split("login2=")[1]
    if pass_dst and "password2=" in str(pass_dst): pass_dst = str(pass_dst).split("password2=")[1]
    if ext_dst and "key2=" in str(ext_dst): ext_dst = str(ext_dst).split("key2=")[1]

    # הבדיקה החכמה: המערכת תשאל בטלפון רק אם הנתון עדיין ריק לגמרי!
    if not system_src or str(system_src).strip() == "": 
        return ym_read("system_src", "t-אנא הקישו את מספר מערכת המקור ובסיומה סולמית")
    if not pass_src or str(pass_src).strip() == "": 
        return ym_read("pass_src", "t-אנא הקישו את סיסמת מערכת המקור ובסיומה סולמית")
    if not ext_src or str(ext_src).strip() == "": 
        return ym_read("ext_src", "t-אנא הקישו את מספר השלוחה להעתקה ובסיומה סולמית")
    
    if not system_dst or str(system_dst).strip() == "": 
        return ym_read("system_dst", "t-אנא הקישו את מספר מערכת היעד ובסיומה סולמית")
    if not pass_dst or str(pass_dst).strip() == "": 
        return ym_read("pass_dst", "t-אנא הקישו את סיסמת מערכת היעד ובסיומה סולמית")
    if not ext_dst or str(ext_dst).strip() == "": 
        return ym_read("ext_dst", "t-אנא הקישו את שלוחת היעד החדשה ובסיומה סולמית")

    return run_copy_logic(system_src, pass_src, ext_src, system_dst, pass_dst, ext_dst)


# --- לוגיקת ההעתקה המשותפת ---
def run_copy_logic(system_src, pass_src, ext_src, system_dst, pass_dst, ext_dst):
    try:
        token_src = f"{str(system_src).strip()}:{str(pass_src).strip()}"
        token_dst = f"{str(system_dst).strip()}:{str(pass_dst).strip()}"
        
        clean_src = str(ext_src).strip().replace('*', '/').replace('-', '/').strip('/')
        clean_dst = str(ext_dst).strip().replace('*', '/').replace('-', '/').strip('/')
        
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
    # הפורמט המנצח שלך שעובד פיקס!
    res = make_response(f"read={text}={var_name},4,12,1,Digits")
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

def ym_say_and_hangup(text):
    res = make_response(f"id_list_message={text}")
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

__all__ = ['app']
