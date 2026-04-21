import requests
from bs4 import BeautifulSoup
import urllib3
# 關閉不安全連線的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://atomovies.com.tw/movie/next/"
Data = requests.get(url, verify=False)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select(".filmListAllX li")

for item in result:
    print(item.text)
    print(item.get("href"))
    print()