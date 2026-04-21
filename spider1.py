import requests
from bs4 import BeautifulSoup

url = "https://atomovies.com.tw/movie/next/"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select(".filmListAllX li")

info = ""
for item in result:
    print(item.find("img").get("alt"))
    print("http://www.atmovies.com.tw" + item.find("a").get("href"))
    print()