import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request,make_response, jsonify
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
    link = "<h1>歡迎進入程莉芳的網站20260514</h1>"
    link += "<a href='/mis'>課程</a><hr>"
    link += "<a href='/today'>現在日期時間</a><hr>"
    link += "<a href='/me'>關於我</a><hr>"
    link += "<a href='/welcome?u=莉芳&d=靜宜資管'>Get傳值</a><hr>"
    link += "<a href='/account'>POST傳值</a><hr>"
    link += "<a href='/math'>次方與根號</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/teacher>靜宜資管老師查詢</a><hr>"
    link += "<a href=/spider>爬取子青老師本學期課程</a><hr>"
    link += "<a href=/movie1>爬取即將上映電影</a><hr>"
    link += "<a href=/movie2>輸入片名關鍵字查詢電影</a><hr>"
    link += "<a href=/spiderMovie>爬取即將上映電影到資料庫</a><hr>"
    link += "<a href='/searchMovie'>資料庫電影查詢關鍵字</a><hr>"
    link += "<a href='/road'>台中市十大肇事路口</a><hr>"
    link += "<a href='/weather'>查詢縣市目前天氣及降雨機率</a><hr>"
    link += "<a href='/rate'>本週新片進DB</a><br>"
    return link


@app.route("/webhook", methods=["POST"])
def webhook():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action =  req["queryResult"]["action"]
    info = ""
    #msg =  req["queryResult"]["queryText"]
    #info = "我是程莉芳設計的機器人,動作：" + action + "； 查詢內容：" + msg

    if (action == "rateChoice"):
        rate =  req["queryResult"]["parameters"]["rate"]
        #info = "我是程莉芳設計的機器人,您選擇的電影分級是：" + rate
        info = "我是程莉芳開發的電影聊天機器人,您選擇的電影分級是：" + rate + "，相關電影：\n"

    db = firestore.client()
    collection_ref = db.collection("電影含分級")
    docs = collection_ref.get()
    result = ""
    for doc in docs:
        dict = doc.to_dict()
        if rate in dict["rate"]:
            result += "片名：" + dict["title"] + "\n"
            result += "介紹：" + dict["hyperlink"] + "\n\n"

    if not result:
            result = "抱歉，找不到該分級的電影。"

        info += result

    return make_response(jsonify({"fulfillmentText": info}))


@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/weather")
def weather():
    # 1. 建立輸入框介面
    R = '<form>請輸入縣市：<input name="city"><button>查詢</button></form><hr>'
    
    # 2. 取得使用者輸入的縣市 (如果沒有輸入就停止)
    city = request.args.get("city")
    if not city:
        return R + "請輸入縣市名稱（例如：臺中市）<br>"

    # 3. 處理名稱與抓取資料
    city = city.replace("台", "臺")
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=rdec-key-123-45678-011121314&locationName={city}"
    
    try:
        Data = requests.get(url)
        JsonData = json.loads(Data.text)
        
        # 4. 解析資料並存入 R
        location = JsonData["records"]["location"][0]
        weather_state = location["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
        rain_chance = location["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
        
        # 累加結果到 R
        R += f"<h3>{city} 最新預報</h3>"
        R += f"目前天氣：{weather_state}<br>"
        R += f"降雨機率：{rain_chance}%"
        
    except:
        R += "查詢失敗，請輸入完整的縣市名稱（如：彰化縣）。"
    R += "<br><a href='/'>返回首頁</a>"

    return R

if __name__ == "__main__":
    app.run(debug=True)


@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口(113年10月)作者：程莉芳</h1><br>"
    
    url = "https://newdatacenter.taichung.gov.tw/api/v1/no-auth/resource.download?rid=a1b899c0-511f-4e3d-b22b-814982a97e41"
    Data = requests.get(url)
    JsonData = json.loads(Data.text)
    for item in JsonData:
        R += item["路口名稱"] + ",原因：" + item["主要肇因"] + ",件數：" + item["總件數"] + "<br>"


    return R

@app.route("/searchMovie", methods=["GET"])
def searchMovie():
    keyword = request.args.get("q")
    
    R = """
        <form action="/searchMovie" method="GET">
            <h3>電影資料庫關鍵字查詢</h3>
            <input type="text" name="q" placeholder="請輸入片名關鍵字">
            <button type="submit">查詢</button>
        </form>
        <hr>
    """
    
    if keyword:
        db = firestore.client()
        collection_ref = db.collection("電影2B")
        docs = collection_ref.get()
        
        found = False
        count = 0
        for doc in docs:
            movie_data = doc.to_dict()
            title = movie_data.get("title", "")
            
            if keyword in title:
                found = True
                count += 1
                movie_id = doc.id
                picture = movie_data.get("picture")
                hyperlink = movie_data.get("hyperlink")
                showDate = movie_data.get("showDate")
                
                R += f"<b>編號：</b>{movie_id}<br>"
                R += f"<b>片名：</b>{title}<br>"
                R += f"<b>上映日期：</b>{showDate}<br>"
                R += f"<a href='{hyperlink}' target='_blank'>查看電影介紹</a><br>"
                R += f"<img src='{picture}' width='150' style='margin-top:10px;'><br><hr>"
        
        if found:
            R = f"<h4>找到 {count} 部符合「{keyword}」的電影：</h4>" + R
        else:
            R += f"抱歉，資料庫中找不到包含「{keyword}」的電影。"
    
    R += "<br><a href='/'>返回首頁</a>"
    return R

@app.route("/spiderMovie")
def spiderMovie():
    R = ""
    
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"

    sp = BeautifulSoup(Data.text, "html.parser")

    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間：" , "")
    result=sp.select(".filmListAllX li")
    db = firestore.client()
    total = 0

    for item in result:
      total += 1
      movie_id = item.find("a").get("href").replace("/movie/" , "").replace("/" , "")
      title = item.find(class_="filmtitle").text
      picture = "http://www.atmovies.com.tw" + item.find("img").get("src")
      hyperlink = "http://www.atmovies.com.tw" + item.find("a").get("href")
      showDate = item.find(class_="runtime").text[5:15]

      doc = {
          "title": title,
          "picture": picture,
          "hyperlink": hyperlink,
          "showDate": showDate,
          "lastUpdate": lastUpdate
      }

      doc_ref = db.collection("電影2B").document(movie_id)
      doc_ref.set(doc)

      R = "網站最近更新日期:" + lastUpdate + "<br>"
      R += "總共爬取" + str(total) + "部電影到資料庫" + "<br>"

      R += "<br><a href='/'>返回首頁</a>"

    return R

@app.route("/movie1")
def movie1():
    R = ""
    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    #print(Data.text)
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".filmListAllX li")
    for item in result:
        introduce = "https://www.atmovies.com.tw" + item.find("a").get("href")
        R += "<a href=" + introduce + ">" + item.find("img").get("alt") + "</a><br>"
        R += "https://www.atmovies.com.tw" + item.find("img").get("src") + "<br><br>"
    return R

@app.route("/movie2", methods=["GET"])
def movie2():
    keyword = request.args.get("q")
    
    # 建立查詢表單
    R = """
        <form action="/movie2" method="GET">
            <h3>電影關鍵字查詢</h3>
            <input type="text" name="q" placeholder="請輸入片名關鍵字">
            <button type="submit">查詢</button>
        </form>
        <hr>
    """
    
    if keyword:
        url = "https://www.atmovies.com.tw/movie/next/"
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        
        found = False
        for item in result:
            title = item.find("img").get("alt")
            if keyword in title:
                found = True
                link = "https://www.atmovies.com.tw" + item.find("a").get("href")
                img_src = "https://www.atmovies.com.tw" + item.find("img").get("src")
                R += f"<b>{title}</b><br>"
                R += f"<a href='{link}'>查看詳情</a><br>"
                R += f"<img src='{img_src}' width='150'><br><br>"
        
        if not found:
            R += f"找不到包含「{keyword}」的電影。"
    
    R += "<br><a href='/'>返回首頁</a>"
    return R

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