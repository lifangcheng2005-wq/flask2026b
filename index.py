from flask import Flask, render_template, request
from datetime import datetime
app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入程莉芳的網站</h1>"
    link += "<a href='/mis'>課程</a><hr>"
    link += "<a href='/today'>現在日期時間</a><hr>"
    link += "<a href='/me'>關於我</a><hr>"
    link += "<a href='/welcome?u=莉芳&d=靜宜資管'>Get傳值</a><hr>"
    link += "<a href='/account'>POST傳值</a><br>"
    link += "<a href='/math'>次方與根號</a><br>"
    return link

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