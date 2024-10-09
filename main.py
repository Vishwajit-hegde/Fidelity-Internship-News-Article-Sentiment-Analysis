import streamlit as st
import pandas as pd
import numpy as np
import os 
os.environ['https_proxy'] = 'http://http.proxy.fmr.com:8000'
os.environ['http_proxy'] = 'http://http.proxy.fmr.com:8000'
from generate_report import PDF
from web_scrape import scrape_news
from summarize import summarize_all, overall_summary
from preprocess import get_entities
from sentiment_analysis import *
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(layout='wide')
st.markdown("<h1 style='text-align: center; color: black;'>Vendor's News Analysis</h1>",unsafe_allow_html=True)
c1,c2 = st.beta_columns((1,2))

with c1:
    vendor = st.text_input("Vendor's Name")
    duration = st.text_input("Number of Days") + 'd'

with c2:
    include_words = st.text_input("Include Words (separated by spaces)").split(' ')
    exclude_words = st.text_input("Exclude Words (separated by spaces)").split(' ')

if st.button('Perform Analysis'):
    st.text('Scraping...')
    df = scrape_news(vendor,duration,include_words,exclude_words)
    st.text('Scraping done. \n')

    st.text('Preprocessing...')
    df = get_entities(df,vendor)
    st.text('Preprocessing done. \n')

    st.text('Performing Summarization...')
    df = get_heading_sentiment(df)
    df = summarize_all(df)
    st.text('Summarization done. \n')

    st.text('Performing Sentiment Analysis...')
    df = get_articles_sentiment(df)
    df = get_neg_sents(df)
    df = get_summary_sentiment(df)
    df = get_overall_sentiment(df)
    summary = overall_summary(df)
    ent_dict = get_neg_ents(df)
    neg_ent_list = [k for k,v in sorted(ent_dict.items() , key=lambda item:item[1],reverse=True)][:min(15,len(ent_dict))]
    num_neg_refs = get_neg_refs(df,vendor)
    keyphrases = get_neg_phrases(df)
    num_neg_sents = df['num_neg_sents'].sum()
    num_neg_art = df[df['article sentiment']=='negative'].shape[0]
    st.text('Sentiment Analysis done. \n')

    pdf = PDF()
    pdf.add_page()
    pdf.add_input_details(vendor,duration=duration,
                          include_words=include_words,exclude_words=exclude_words)

    pdf.add_overall_details(summary,keyphrases,neg_ent_list,num_neg_sents,num_neg_art,num_neg_refs)

    j = 0
    index_order = df[df['article sentiment']=='negative'].sort_values(by='refs',ascending=False).index
    for i in index_order:
        if j%5 == 0:
            pdf.add_page()
        title = df['title'][i]
        summary = df['summary'][i]
        source = df['source'][i]
        date = df['date'][i]
        sentiment_score = df['heading sentiment score'][i]
        polarity = df['heading sentiment'][i]
        top_neg_entities = []
        num_neg_sents = df['num_neg_sents'][i]
        pdf.add_article_details(title,summary,date,source,sentiment_score,polarity,num_neg_sents,top_neg_entities)
        j += 1

    _ = pdf.output(vendor+' Report.pdf','F')
    cols = ['title', 'content', 'link', 'source', 'date', 'heading sentiment', 'summary', 'num_neg_sents',
            'article sentiment', 'summary sentiment', 'neg_para', 'heading sentiment score']
    df[cols].to_excel(vendor+' Analysis Data.xlsx')
    st.text('Analysis report and excel file have been created successfully!')