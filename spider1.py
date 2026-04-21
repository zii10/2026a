import requests
from bs4 import BeautifulSoup

url = "https://atomovies.com.tw/movie/next/"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select(".filmListAllX li")

for item in result:
    print(item)
    print()