from bs4 import BeautifulSoup
import requests


def indiatoday_webscrap(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    main_content = soup.find('main', class_='main__content')
    p_tags = main_content.find_all('p')
    h1_tags=main_content.find("h1")
    title = ""
    content = ""
    for i in h1_tags:
        title+=i.text
    for tag in p_tags:
        content+=tag.text
    
    print("title",title)
    print("content", content)
    return {
        "title": title,
        "content": content
    }
url = 'https://www.indiatoday.in/business/personal-finance/story/hyderabad-real-estate-price-rise-80-percent-outpaces-delhi-mumbai-bengaluru-2742020-2025-06-17'
indiatoday_webscrap(url)