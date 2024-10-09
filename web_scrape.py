from pygooglenews import GoogleNews
import os
os.environ['https_proxy'] = 'http://http.proxy.fmr.com:8000'
os.environ['http_proxy'] = 'http://http.proxy.fmr.com:8000'
import warnings
warnings.filterwarnings('ignore')
from newspaper import Article
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from preprocess import process_date, process_text
import pandas as pd
import numpy as np

def scrape_news(vendor,duration,include_words=[],exclude_words=[]):
    gn = GoogleNews()
    query = advanced_search_query(vendor,include_words,exclude_words)
    if type(duration)==int:
        duration = str(duration)+'d'
    google_result = gn.search(query=query,when=duration)['entries']
    links = []
    titles = []
    sources = []
    dates = []
    bodies = []

    def scrape_article(r):
        try:
            if chr(8211) in r['title']:
                title = r['title'].split(' '+chr(8211)+' ')[0]
            elif '-' in r['title']:
                title = r['title'].split(' - ')[0]
        except:
            title = r['title']

        link = r['link']

        try:
            source = r['source']['title']
        except:
            s = r['title'].split(' '+chr(8211)+' ')
            if len(s)>1:
                source = s[-1]
            else:
                try:
                    source = r['source']['href']
                except:
                    source = None
        try:
            datetime = r['published']
        except:
            datetime = None

        body = get_news_from_article(link)
        if body==None:
            body_ = get_news_from_requests(link)
        elif len(body)<600:
            body_ = get_news_from_requests(link)
            if body_:
                body = body_ if len(body_)>len(body) else body
        if body:
            if len(body)<600:
                if vendor.lower() not in body.lower() or len(body)<300:
                    body = None

        return [title,body,link,source,datetime]

    with ThreadPoolExecutor() as executor:
        results = executor.map(scrape_article,google_result)
        for res in results:
            titles.append(res[0])
            bodies.append(res[1])
            links.append(res[2])
            sources.append(res[3])
            dates.append(res[4])

    df = pd.DataFrame(data = np.array([titles,bodies,links,sources,dates]).T,
                      columns=['title','content','link','source','date'])
    df['date'] = df['date'].apply(process_date)
    df['content'] = df['content'].apply(process_text)
    df['title'] = df['title'].apply(process_text)
    return df

def advanced_search_query(vendor,include_words,exclude_words):
    query = ''
    if include_words != []:
        query += ' AND '.join(include_words)
    query += ' "'+vendor+'"'
    if exclude_words != []:
        query += ' -'
        query += ' -'.join(exclude_words)
    return query

def get_news_from_requests(link):
    try:
        response = requests.get(link,timeout=15)
        soup = BeautifulSoup(response.text,'html.parser')
        body = ' '.join([p.get_text() for p in soup.find_all('p')])
    except:
        body=None
    return body

def get_news_from_article(link):
    try:
        article = Article(link)
        article.download()
        article.parse()
        body = article.text
    except:
        body = None
    return body