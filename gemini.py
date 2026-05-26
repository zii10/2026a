from google import genai

client = genai.Client(api_key='AIzaSyDY8Z8uYJ2dNKfcx8aU2Tq0C1T_cvzKUtU')

# 直接體驗最新一代的 3.5 Flash 
response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents='打上你要問的問題',
)

print(response.text)
