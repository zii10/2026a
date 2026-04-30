import requests
from bs4 import BeautifulSoup

url = "https://atomovies.com.tw/movie/next/"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.find(id="h2text")

print(result)