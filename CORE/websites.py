from rss_functions import all_rss, economictimes_rss,prnewswire_rss,ndtvprofit_latest_rss,ndtvprofit_trending_rss,ndtv_top_stories_rss,moneycontrol_rss,livemint_rss,thehindu_Industry_rss,thehindu_Economy_rss
from rss_functions import thehindu_business_rss,thehindu_markets_rss,zeenews_rss,hindustantimes_rss,indiatoday_rss,indiatvnews_rss,timesofindia_business_rss,timesofindia_topstories_rss,cnbc_rss,etnow_latest_rss
from rss_functions import etnow_standard_rss,indianexpress_rss,economictimes_default_rss,economictimes_markets_rss,economictimes_industry_rss




rss_websites = {
    "prnews_manufacturing": "https://www.prnewswire.com/rss/heavy-industry-manufacturing-latest-news/heavy-industry-manufacturing-latest-news-list.rss",
    "economictimes_industry": "https://manufacturing.economictimes.indiatimes.com/rss/industry",
    # "economictimes_markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    # "economictimes_industry": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
    # "livemint_market": "https://www.livemint.com/rss/markets",
    # "livemint_companies": "https://www.livemint.com/rss/companies",
    # "thehindu_Industry": "https://www.thehindu.com/business/Industry/feeder/default.rss",
    # "thehindu_Economy": "https://www.thehindu.com/business/economy/feeder/default.rss",
    # "thehindu_markets": "https://www.thehindu.com/business/markets/feeder/default.rss",
    # "thehindu_business": "https://www.thehindu.com/business/feeder/default.rss",
    # "znews_business": "http://zeenews.india.com/rss/business.xml",
    # "hindustantimes_business": "https://www.hindustantimes.com/feeds/rss/business/rssfeed.xml",
    # "indiatoday_economics": "https://www.indiatoday.in/rss/1206513",
    # "indiatvnews_business": "https://www.indiatvnews.com/rssnews/topstory-business.xml",
    # "timesofindia_business": "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
    # "etnow_infrastructure": "https://www.etnownews.com/feeds/gns-etn-infrastructure.xml",
    # "etnow_realestate": "https://www.etnownews.com/feeds/gns-etn-real-estate.xml",
    # "etnow_companies": "https://www.etnownews.com/feeds/gns-etn-companies.xml",
    # "etnow_market": "https://www.etnownews.com/feeds/gns-etn-markets.xml",
    # "indianexpress_companies": "https://indianexpress.com/section/business/companies/feed/",
    # "indianexpress_business": "https://indianexpress.com/section/business/feed/",
    # "indiatimes_economy": "https://cfo.economictimes.indiatimes.com/rss/economy"
}


rss_functions = {
    "prnews_manufacturing": prnewswire_rss,
    "economictimes":economictimes_rss,
    "economictimes_markets":economictimes_markets_rss,
    "economictimes_industry":economictimes_industry_rss,
    "livemint_market":livemint_rss,
    "livemint_companies": livemint_rss,
    "thehindu_Industry":thehindu_Industry_rss,
    "thehindu_Economy":thehindu_Economy_rss,
    "thehindu_markets":thehindu_markets_rss,
    "thehindu_business":thehindu_business_rss,
    "znews_business":zeenews_rss,
    "hindustantimes_business":hindustantimes_rss,
    "indiatoday_economics":indiatoday_rss,
    "indiatvnews_business":indiatvnews_rss,
    "timesofindia_business":timesofindia_business_rss,
    "indianexpress_companies":indianexpress_rss,
    "indianexpress_business":indianexpress_rss,
    "all_rss": all_rss
}

