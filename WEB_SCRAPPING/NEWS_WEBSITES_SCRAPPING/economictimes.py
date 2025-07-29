#economictimes
import requests
from bs4 import BeautifulSoup

url = 'https://economictimes.indiatimes.com/prime/economy-and-policy/flames-below-deck-the-silent-threat-lurking-in-cargo-holds/primearticleshow/121891425.cms?source=homepage&medium=prime_exclusives_header&campaign=prime_discovery'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

main_content = soup.find("div",class_="clearfix main_container prel prt_cnt layout_mm")
con=soup.find("div",class_="artText")

p_tags = main_content.find_all('p')
h1_tags=main_content.find("h1")
print(h1_tags.text)
print(con.text)
