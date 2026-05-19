import requests
from bs4 import BeautifulSoup
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

if not firebase_admin._apps:
    if os.path.exists('serviceAccountKey.json'):
        # 本地環境
        cred = credentials.Certificate('serviceAccountKey.json')
    else:
        # 雲端環境 (Vercel)
        firebase_config = os.getenv('FIREBASE_CONFIG')
        if firebase_config:
            try:
                cred_dict = json.loads(firebase_config)
                cred = credentials.Certificate(cred_dict)
            except Exception as e:
                print(f"JSON 解析錯誤: {e}")
        else:
            print("找不到環境變數 FIREBASE_CONFIG")
    
    # 執行初始化
    try:
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase 初始化失敗: {e}")


from flask import Flask, render_template, request
from datetime import datetime
import random

app = Flask(__name__)

@app.route("/")
def index():
    homepage = "<h1>歡迎來到周子洋Python網頁</h1>"
    homepage += "<a href=/mis>MIS</a><br>"
    homepage += "<a href=/today>顯示日期時間</a><br>"
    homepage += "<a href=/welcome?nick=子洋>傳送使用者暱稱</a><br>"
    homepage += "<a href=/account>網頁表單傳值</a><br>"
    homepage += "<a href=/about>子洋簡介網頁</a><br>"
    homepage += "<br><a href=/read>讀取Firestore資料</a><br>"
    homepage += "<a href=/search>老師查詢</a><br>"
    homepage += "<a href=/sp1>爬蟲結果</a><br>"
    homepage += "<a href=/movie>查詢即將上映電影</a><br>"
    homepage += "<a href=/movie2>爬取電影進資料庫</a><br>"
    homepage += "<a href=/movie3>查詢電影資料庫</a><br>"
    homepage += "<a href=/road>查詢易肇事路口資訊</a><br>"
    homepage += "<a href=/weather>查詢天氣</a><br>"
    homepage += "<a href=/rate>本周新片進口</a><br>"
    homepage += "<a href=/demo>聊天機器人</a><br>"
    return homepage


@app.route("/webhook", methods=["POST"])
def webhook():
    # build a request object
    req = request.get_json(force=True)
    # fetch queryResult from json
    action =  req["queryResult"]["action"]
    #msg =  req["queryResult"]["queryText"]
    #info = "我是楊子青設計的電影聊天機器人, 動作：" + action + "； 查詢內容：" + msg
    if (action == "rateChoice"):
        rate =  req["queryResult"]["parameters"]["rate"]
        info = "我是楊子青設計的電影聊天機器人,您選擇的電影分級是：" + rate + "，相關電影：\n"

        db = firestore.client()
        collection_ref = db.collection("本週新片含分級")
        docs = collection_ref.get()
        result = ""
        for doc in docs:
            dict = doc.to_dict()
            if rate in dict["rate"]:
                result += "片名：" + dict["title"] + ";\n"
                result += "連結：" + dict["hyperlink"] + "\n\n"

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

@app.route("/weather", methods=["GET", "POST"])
def weather_query():
    result_text = ""
    if request.method == "POST":
        city = request.form.get("city", "")
        if city:
            city = city.replace("台", "臺")
            
            # 氣象署 API
            url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=rdec-key-123-45678-011121314&format=JSON&locationName={city}"
            
            try:
                response = requests.get(url, verify=False)
                data = json.loads(response.text)
                
                if data["records"]["location"]:
                    weather_element = data["records"]["location"][0]["weatherElement"]
                    weather = weather_element[0]["time"][0]["parameter"]["parameterName"]
                    rain = weather_element[1]["time"][0]["parameter"]["parameterName"]
                    
                    # 這是你要的 R 字串
                    result_text = f"{city} 目前天氣預報：<br>{weather}，降雨機率：{rain}%"
                else:
                    result_text = "找不到該縣市，請輸入正確名稱（如：臺中市）。"
            except Exception as e:
                result_text = f"連線錯誤：{e}"
                
    return render_template("weather.html", result=result_text)

@app.route("/road")
def road():
    R = ""
    url = "https://newdatacenter.taichung.gov.tw/api/v1/no-auth/resource.download?rid=a1b899c0-511f-4e3d-b22b-814982a97e41"
    Data = requests.get(url, verify=False)
    #print(Data.text)

    JsonData = json.loads(Data.text)
    for item in JsonData:
        R += item["路口名稱"] + ",總共發生" + item["總件數"] + "件事故<br>"
    return R

@app.route("/movie3", methods=["GET", "POST"])
def movie3():
    db = firestore.client()
    results = []
    keyword = ""
    
    if request.method == "POST":
        keyword = request.form.get("keyword")
        collection_ref = db.collection("電影2A")
        docs = collection_ref.get()

        for doc in docs:
            movie = doc.to_dict()
            if keyword in movie["title"]:
                results.append({
                    "title":  movie["title"],
                    "picture": movie["picture"],
                    "hyperlink": movie["hyperlink"],
                    "showDate": movie["showDate"],
                    "showLength": movie["showLength"],
                    "lastUpdate": movie["lastUpdate"]
                })

    return render_template("movie3.html", results=results, keyword=keyword)


@app.route("/movie2")
def movie2():
  url = "http://www.atmovies.com.tw/movie/next/"
  Data = requests.get(url)
  Data.encoding = "utf-8"
  sp = BeautifulSoup(Data.text, "html.parser")
  result=sp.select(".filmListAllX li")
  lastUpdate = sp.find("div", class_="smaller09").text[5:]

  for item in result:
    picture = item.find("img").get("src").replace(" ", "")
    title = item.find("div", class_="filmtitle").text
    movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
    hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")
    show = item.find("div", class_="runtime").text.replace("上映日期：", "")
    show = show.replace("片長：", "")
    show = show.replace("分", "")
    showDate = show[0:10]
    showLength = show[13:]

    doc = {
        "title": title,
        "picture": picture,
        "hyperlink": hyperlink,
        "showDate": showDate,
        "showLength": showLength,
        "lastUpdate": lastUpdate
      }

    db = firestore.client()
    doc_ref = db.collection("電影2A").document(movie_id)
    doc_ref.set(doc)    
  return "近期上映電影已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate 

@app.route("/sp1")
def sp1():
    R = "<h1>爬蟲結果</h1>"
    url = "https://vercel.com/zii10s-projects/2026a"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    #print(Data.text)
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select("td a")

    for item in result:
        R += item.text + "<br>" + item.get("href")+"<br><br>"
    return R

@app.route("/movie")
def movie():
    url = "http://www.atmovies.com.tw/movie/next/"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    Data = requests.get(url, headers=headers)
    Data.encoding = "utf-8"
    
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    R = "<h1>近期上映電影</h1>"

    for item in result:
        img_tag = item.find("img")
        title = img_tag.get("alt") if img_tag else "無標題"

        a_tag = item.find("a")
        href = a_tag.get("href") if a_tag else "#"
        link = "http://www.atmovies.com.tw" + href if not href.startswith("http") else href
        
        R += f"<a href='{link}' target='_blank'>{title}</a><br>"

    return R

@app.route("/search", methods=["GET", "POST"])
def search():
    db = firestore.client()
    results = []
    keyword = ""
    
    if request.method == "POST":
        keyword = request.form.get("keyword")
        collection_ref = db.collection("靜宜資管")
        docs = collection_ref.get()

        for doc in docs:
            user = doc.to_dict()
            if keyword in user["name"]:
                results.append({
                    "name": user["name"],
                    "lab": user["lab"]
                })

    return render_template("search.html", results=results, keyword=keyword)

@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.get()    
    for doc in docs:         
        Result += "文件內容：{}".format(doc.to_dict()) + "<br>"    
    return Result

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1>"
    
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/welcome", methods=["GET"])
def welcome():
    x=request.values.get("u")
    y=request.values.get("dep")
    return render_template("welcome.html", name=x,dep=y)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")




if __name__ == "__main__":
    app.run()
