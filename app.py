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


# --- המודול החכם והחסין שלך (תואם פורמט PHP שעבד לך!) ---
@app.route('/copy-smart', methods=['GET', 'POST'])
def copy_module_smart():
    extracted = {}

    for key, value in request.values.items():
        key_str = str(key).strip()
        val_str = str(value).strip()

        if "login1" in key_str or "login1" in val_str:
            extracted['login1'] = val_str.split('=')[-1] if '=' in val_str else val_str
        if "password1" in key_str or "password1" in val_str:
            extracted['password1'] = val_str.split('=')[-1] if '=' in val_str else val_str
        if "key1" in key_str or "key1" in val_str:
            extracted['key1'] = val_str.split('=')[-1] if '=' in val_str else val_str
            
        if "login2" in key_str or "login2" in val_str:
            extracted['login2'] = val_str.split('=')[-1] if '=' in val_str else val_str
        if "password2" in key_str or "password2" in val_str:
            extracted['password2'] = val_str.split('=')[-1] if '=' in val_str else val_str
        if "key2" in key_str or "key2" in val_str:
            extracted['key2'] = val_str.split('=')[-1] if '=' in val_str else val_str

    system_src = extracted.get('login1') or request.values.get('system_src')
    pass_src = extracted.get('password1') or request.values.get('pass_src')
    ext_src = extracted.get('key1') or request.values.get('ext_src')
    
    system_dst = extracted.get('login2') or request.values.get('system_dst')
    pass_dst = extracted.get('password2') or request.values.get('pass_dst')
    ext_dst = extracted.get('key2') or request.values.get('ext_dst')

    if not system_src or str(system_src).strip() == "": return ym_read("system_src", "t-אנא הקישו את מספר מערכת המקור ובסיומה סולמית")
    if not pass_src or str(pass_src).strip() == "":   return ym_read("pass_src", "t-אנא הקישו את סיסמת מערכת המקור ובסיומה סולמית")
    if not ext_src or str(ext_src).strip() == "":    return ym_read("ext_src", "t-אנא הקישו את מספר השלוחה להעתקה ובסיומה סולמית")
    
    if not system_dst or str(system_dst).strip() == "": return ym_read("system_dst", "t-אנא הקישו את מספר מערכת היעד ובסיומה סולמית")
    if not pass_dst or str(pass_dst).strip() == "":   return ym_read("pass_dst", "t-אנא הקישו את סיסמת מערכת היעד ובסיומה סולמית")
    if not ext_dst or str(ext_dst).strip() == "":    return ym_read("ext_dst", "t-אנא הקישו את שלוחת היעד החדשה ובסיומה סולמית")

    return run_copy_logic(system_src, pass_src, ext_src, system_dst, pass_dst, ext_dst)


# --- לוגיקת ההעתקה המקורית והמנצחת שלך ---
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

        ini_content = src_response.text

        # 🌟 השורה האחת והיחידה שהתווספה לקוד המקורי שלך! 🌟
        ini_content += "\n\ntitle=שלוחה זאת הגדרה ע'י פון קול"

        # העלאה המקורית והמדויקת שעבדה לך פיקס!
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
