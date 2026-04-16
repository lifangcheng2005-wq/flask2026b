import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request
from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)


app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入程莉芳的網站20260409</h1>"
    link += "<a href='/mis'>課程</a><hr>"
    link += "<a href='/today'>現在日期時間</a><hr>"
    link += "<a href='/me'>關於我</a><hr>"
    link += "<a href='/welcome?u=莉芳&d=靜宜資管'>Get傳值</a><hr>"
    link += "<a href='/account'>POST傳值</a><hr>"
    link += "<a href='/math'>次方與根號</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/teacher>靜宜資管老師查詢</a><hr>"
    link += "<a href=/spider>爬取子青老師本學期課程</a><br>"
    return link

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("chengMIS")    
    docs = collection_ref.order_by("lab",direction=firestore.Query.DESCENDING).get()    
    for doc in docs:         
        Result += "文件內容：{}".format(doc.to_dict()) + "<br>"    
    return Result

@app.route("/spider")
def spider():
    R = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".team-box a")

    for i in result:
        R += i.text + i.get("href") + "<br>"
    return R

@app.route("/teacher")
def teacher():
    keyword = request.args.get("keyword")
    
    form_html = """
        <form action="/teacher" method="GET">
            <h3>靜宜資管老師查詢</h3>
            請輸入老師姓名關鍵字：
            <input type="text" name="keyword" placeholder="例如：陳">
            <button type="submit">查詢</button>
        </form>
        <hr>
    """
    
    db = firestore.client()
    collection_ref = db.collection("chengMIS")
    
    result_text = ""
    if keyword:
        docs = collection_ref.get()
        found = False
        result_text += f"<h4>查詢結果 (關鍵字: {keyword})：</h4>"
        
        for doc in docs:
            teacher_data = doc.to_dict()
            name = teacher_data.get("name", "")
            if keyword in name:
                found = True
                result_text += f"<span style='color:blue'><b>{name}</b></span> 老師的研究室在 <b>{teacher_data.get('lab')}</b><br>"
        
        if not found:
            result_text = f"<h4>查詢結果：</h4> 抱歉，找不到姓名包含「{keyword}」的老師。"
    else:
        result_text = "<i>請輸入關鍵字進行查詢</i>"

    back_link = '<br><br><a href="/">返回首頁</a>'
    return form_html + result_text + back_link


@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href='/'>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/me")
def me():
    return render_template("mis2026b.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    # 修正：參數名稱從 nick 改為 u
    user = request.values.get("u")
    return render_template("welcome.html", name=user)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        try:
            x = int(request.form["x"])
            y = int(request.form["y"])
            opt = request.form["opt"]

            if opt == "^":
                result = x ** y
            elif opt == "√":  # 修正：刪除後方的字母 a
                if y == 0:
                    result = "數學不能開0次方根"
                else:
                    result = x ** (1/y)
            else:
                result = "請輸入^或√"

            # 修正：調整 return 的縮排，確保計算完畢後回傳結果
            return f"計算結果: {result}<br><br><a href='/math'>繼續計算</a> | <a href='/'>回首頁</a>"

        except ValueError:
            return "輸入格式錯誤，請確保 x 和 y 都是整數！<br><a href='/math'>返回重新計算</a>"
    else:
        return render_template("math.html")

if __name__ == "__main__":
    app.run(debug=True)