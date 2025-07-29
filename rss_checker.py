from rss_functions import all_rss, economictimes_rss,prnewswire_rss,ndtvprofit_latest_rss,ndtvprofit_trending_rss,ndtv_top_stories_rss,moneycontrol_rss,livemint_rss,thehindu_Industry_rss,thehindu_Economy_rss
from rss_functions import thehindu_business_rss,thehindu_markets_rss,zeenews_rss,hindustantimes_rss,indiatoday_rss,indiatvnews_rss,timesofindia_business_rss,timesofindia_topstories_rss,cnbc_rss,etnow_latest_rss
from rss_functions import etnow_standard_rss,indianexpress_rss,economictimes_default_rss,economictimes_markets_rss,economictimes_industry_rss
from proxy import proxy_content
from WEB_SCRAPPING.search_results import google_search_for_query
import requests
import time
import asyncio
from WEB_SCRAPPING.ADVANCE_SCRAPING.scrapy import run_advanced_text_scraper
def delay_ten_minutes():
    time.sleep(1* 30)

def loop():
    prnews=prnewswire_rss(proxy_content("https://www.prnewswire.com/rss/heavy-industry-manufacturing-latest-news/heavy-industry-manufacturing-latest-news-list.rss"))
    economics_t=economictimes_rss(proxy_content("https://manufacturing.economictimes.indiatimes.com/rss/industry"))

    # replce all recent news
    # ndtv_profit_latest=ndtvprofit_latest_rss(proxy_content("https://feeds.feedburner.com/ndtvprofit-latest"))
    # ndtv_profit_trending=ndtvprofit_trending_rss(proxy_content("https://feeds.feedburner.com/ndtvnews-trending-news"))
    # ndtv_top_stories=ndtv_top_stories_rss(proxy_content("https://feeds.feedburner.com/ndtvnews-top-stories"))

    # not updated
    # moneycontrol=moneycontrol_rss(proxy_content("https://www.moneycontrol.com/rss/latestnews.xml"))

    livemint=livemint_rss(proxy_content("https://www.livemint.com/rss/markets"))

    # # added
    livemint=livemint_rss(proxy_content("https://www.livemint.com/rss/companies"))
    thehindu_Industry=thehindu_Industry_rss(proxy_content("https://www.thehindu.com/business/Industry/feeder/default.rss"))
    thehindu_Economy=thehindu_Economy_rss(proxy_content("https://www.thehindu.com/business/economy/feeder/default.rss"))
    thehindu_markets=thehindu_markets_rss(proxy_content("https://www.thehindu.com/business/markets/feeder/default.rss"))
    thehindu_business=thehindu_business_rss(proxy_content("https://www.thehindu.com/business/feeder/default.rss"))
    znews=zeenews_rss(proxy_content("http://zeenews.india.com/rss/business.xml"))
    hindustantimes=hindustantimes_rss(proxy_content("https://www.hindustantimes.com/feeds/rss/business/rssfeed.xml"))
    indiatoday=indiatoday_rss(proxy_content("https://www.indiatoday.in/rss/1206513"))
    indiatvnews=indiatvnews_rss(proxy_content("https://www.indiatvnews.com/rssnews/topstory-business.xml"))
    timesofindia_business=timesofindia_business_rss(proxy_content("https://timesofindia.indiatimes.com/rssfeeds/1898055.cms"))
    # not important
    # timesofindia_topstories=timesofindia_topstories_rss(proxy_content("https://timesofindia.indiatimes.com/rssfeedstopstories.cms"))
    # cnbc=cnbc_rss(proxy_content("https://www.cnbc.com/id/100003114/device/rss/rss.html"))

    # added
    # cnn_company = all_rss(proxy_content("http://rss.cnn.com/rss/money_news_companies.rss"), "data/cnn_company.json", "log/cnn_company.csv", "cnn", "cnn_companies" )
    # cnn_market = all_rss(proxy_content("http://rss.cnn.com/rss/money_markets.rss"), "data/cnn_market.json", "log/cnn_market.csv", "cnn", "cnn_market")
    

    # # added
    etnow_infrastructure = all_rss(proxy_content("https://www.etnownews.com/feeds/gns-etn-infrastructure.xml"), "data/etnow_infrastructure.json", "log/etnow_infrastructure.csv", "etnow", "etnow_infrastructure")
    etnow_realestate= all_rss(proxy_content("https://www.etnownews.com/feeds/gns-etn-real-estate.xml"), "data/etnow_realestate.json", "log/etnow_realestate.csv", "etnow", "etnow_real-estate")
    etnow_companies =  all_rss(proxy_content("https://www.etnownews.com/feeds/gns-etn-companies.xml"), "data/etnow_companies.json", "log/etnow_companies.csv", "etnow", "etnow_companies")
    etnow_market = all_rss(proxy_content("https://www.etnownews.com/feeds/gns-etn-markets.xml"), "data/etnow_market.json", "log/etnow_market.csv", "etnow", "etnow_markets")

    # etnow_latest=etnow_latest_rss(proxy_content("https://www.etnownews.com/feeds/gns-etn-latest.xml"))
    # etnow_standard=etnow_standard_rss(proxy_content("https://www.etnownews.com/feeds/gns-etn-news.xml"))

    indian_express_companies =  all_rss(proxy_content("https://indianexpress.com/section/business/companies/feed/"), "data/indian_express_companies.json", "log/indian_express_companies.csv", "indian_express", "indian_express_companies")

    indianexpress=indianexpress_rss(proxy_content("https://indianexpress.com/section/business/feed/"))                
    # economictimes_default=economictimes_default_rss(proxy_content("https://economictimes.indiatimes.com/rssfeedsdefault.cms"))
    # added
    india_times_economy = all_rss(proxy_content("https://cfo.economictimes.indiatimes.com/rss/economy"), "data/india_times_economy.json", "log/india_times_economy.csv", "india_times", "india_times_economy")

    economictimes_markets=economictimes_markets_rss(proxy_content("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"))
    economictimes_industry=economictimes_industry_rss(proxy_content("https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms"))
    delay_ten_minutes()
def main():
    try:
        # while True:
        #     loop()
            asyncio.run(google_search_for_query())
            


    except KeyboardInterrupt:
        print("keyboard interrupt \n program complete")
        pass
if __name__=="__main__":
    main()