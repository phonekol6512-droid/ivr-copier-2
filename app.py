import requests
from flask import Flask, request, make_response

app = Flask(__name__)

YEMOT_API_URL = "https://call2all.co.il"

# 🌟 כאן אתה מגדיר את נתוני המקור הקבועים שלך! (החלף את הנתונים שבתוך המרכאות)
SYSTEM_SRC_STATIC = "0773016512"  # מספר מערכת המקור הקבועה
PASS_SRC_STATIC = "132580"          # סיסמת מערכת המקור הקבועה
EXT_SRC_STATIC = "0123*123"              # מספר השלוחה שממנה תמיד מעתיקים (למשל שלוחה 5, או 1*2 לשלוחה פנימית)

@app.route('/copy-module', methods=['GET', 'POST'])
def copy_module_static():
    system_dst = request.values.get('system_dst')
    pass_dst = request.values.get('pass_dst')
    ext_dst = request.values.get('ext_dst')

    # המערכת תבקש מהמאזין רק את פרטי היעד!
    if not system_dst: return ym_read("system_dst", "t-אנא הקישו את מספר מערכת היעד ובסיומה סולמית")
    if not pass_dst:   return ym_read("pass_dst", "t-אנא הקישו את סיסמת מערכת היעד ובסיומה סולמית")
    if not ext_dst:    return ym_read("ext_dst", "t-אנא הקישו את שלוחת היעד החדשה ובסיומה סולמית")

    try:
        token_src = f"{SYSTEM_SRC_STATIC.strip()}:{PASS_SRC_STATIC.strip()}"
        token_dst = f"{system_dst.strip()}:{pass_dst.strip()}"
        
        clean_src = EXT_SRC_STATIC.strip().replace('*', '/').replace('-', '/').strip('/')
        clean_dst = ext_dst.strip().replace('*', '/').replace('-', '/').strip('/')
        
        path_src = f"ivr2:/{clean_src}/ext.ini"
        path_dst = f"ivr2:/{clean_dst}/ext.ini"

        # 1. הורדת הקובץ ממערכת המקור הקבועה
        download_url = f"{YEMOT_API_URL}DownloadFile"
        src_response = requests.get(download_url, params={"token": token_src, "path": path_src})

        if src_response.status_code != 200 or "הסיסמא שגויה" in src_response.text or "לא נמצא" in src_response.text:
            return ym_say_and_hangup("t-שגיאה. נתוני מערכת המקור הקבועה שגויים או שהשלוחה לא קיימת.")

        ini_content = src_response.text

        # 2. העלאת הקובץ למערכת היעד שהקיש המאזין
        upload_url = f"{YEMOT_API_URL}UploadTextFile?token={token_dst}&what={path_dst}&contents={requests.utils.quote(ini_content)}"
        dst_response = requests.post(upload_url)

        if dst_response.status_code == 200 and '"responseStatus":"OK"' in dst_response.text:
            return ym_say_and_hangup("t-ההעתקה בוצעה בהצלחה. השלוחה הועתקה.")
        else:
            return ym_say_and_hangup("t-שגיאה בהעלאת הנתונים למערכת היעד.")

    except Exception as e:
        print(f"API Error: {str(e)}")
        return ym_say_and_hangup("t-התרחשה שגיאה בתקשורת עם השרתים.")

def ym_read(var_name, text):
    # הפורמט המנצח והבדוק שלך במאה אחוז!
    res = make_response(f"read={text}={var_name},4,12,1,Digits")
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

def ym_say_and_hangup(text):
    res = make_response(f"id_list_message={text}")
    res.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return res

__all__ = ['app']
