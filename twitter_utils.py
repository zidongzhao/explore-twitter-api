#!/usr/bin/env python3
"""
Created on Sun Dec 13 20:49:32 2020

@author: zhaoz
"""

import tweepy
import pandas as pd
import numpy as np
from textblob import TextBlob
import wordcloud
import re
import nltk
nltk.download('stopwords')
import pickle
import matplotlib.pyplot as plt
import string

class TwitterAuthenticater():
    '''
    handle twitter authentication
    '''

    def __init__(self):
        pass

    def authenticate_twitter_app(self):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(auth_key, auth_secret)
        return auth


class TwitterListener(tweepy.streaming.StreamListener):
    '''
    Very basic listener class that just prints shit to stdout
    '''

    def __init__(self, fetched_fname):
        self.fetched_fname = fetched_fname

    def on_data(self, data):
        # overwriting the inherited on_data method
        print(data)
        try:
            with open(self.fetched_fname, 'a') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print(f'Error on data: {e}')
        return True

    def on_error(self, status):
        # overwirting the inherited on_error method
        print(status)
        if status == 420:
            # kill the connection if reach rates limit
            return False


class TwitterClient():
    def __init__(self, user=None):
        authenticater = TwitterAuthenticater()
        self.auth = authenticater.authenticate_twitter_app()
        self.client = tweepy.API(self.auth, wait_on_rate_limit=True)
        self.user = user

    def get_client_api(self):
        return self.client

    def get_user_timeline_tweets(self, n_tweets):
        tweets = []
        for tweet in tweepy.Cursor(self.client.user_timeline, id=self.user).items(n_tweets):
            tweets.append(tweet)
        return tweets

    def get_friends_list(self, n_friends):
        friends = []
        for friend in tweepy.Cursor(self.client.friends, id=self.user).items(n_friends):
            friends.append(friend)
        return friends

    def get_home_feed_tweets(self, n_tweets):
        tweets = []
        for tweet in tweepy.Cursor(self.client.home_timeline).items(n_tweets):
            tweets.append(tweet)
        return tweets

    def search_past_tweets(self, query, n_tweets):
        tweets = []
        for tweet in tweepy.Cursor(self.client.search, q=query).items(n_tweets):
            tweets.append(tweet)
        return tweets


class TwitterStreamer():
    '''
    Class for streaming and processing live tweets
    '''

    def __init__(self):
        authenticater = TwitterAuthenticater()
        self.auth = authenticater.authenticate_twitter_app()

    def stream_tweets(self, fetched_fname, tracks):
        listener = TwitterListener(fetched_fname)
        stream = tweepy.Stream(self.auth, listener)
        stream.filter(track=tracks)


class TwitterAnalyzer():
    '''
    Functions for analyzing and categorizing tweets
    '''

    def __init__(self):
        pass

    def tweets_to_df(self, tweets):
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['text'])
        df['id'] = [tweet.id for tweet in tweets]
        # etc
        return df

    def unicode2ascii(self, text):
        # courtesy
        better_text = (text.str.
                       replace('\\xe2\\x80\\x99', "'").
                       replace('\\xe2\\x80\\x90', '-').
                       replace('\\xe2\\x80\\x91', '-').
                       replace('\\xe2\\x80\\x92', '-').
                       replace('\\xe2\\x80\\x93', '-').
                       replace('\\xe2\\x80\\x94', '-').
                       replace('\\xe2\\x80\\x94', '-').
                       replace('\\xe2\\x80\\x98', "'").
                       replace('\\xe2\\x80\\x9b', "'").
                       replace('\\xe2\\x80\\x9c', '"').
                       replace('\\xe2\\x80\\x9c', '"').
                       replace('\\xe2\\x80\\x9d', '"').
                       replace('\\xe2\\x80\\x9e', '"').
                       replace('\\xe2\\x80\\x9f', '"').
                       replace('\\xe2\\x80\\xa6', '...').
                       replace('\\xe2\\x80\\xb2', "'").
                       replace('\\xe2\\x80\\xb3', "'").
                       replace('\\xe2\\x80\\xb4', "'").
                       replace('\\xe2\\x80\\xb5', "'").
                       replace('\\xe2\\x80\\xb6', "'").
                       replace('\\xe2\\x80\\xb7', "'").
                       replace('\\xe2\\x81\\xba', "+").
                       replace('\\xe2\\x81\\xbb', "-").
                       replace('\\xe2\\x81\\xbc', "=").
                       replace('\\xe2\\x81\\xbd', "(").
                       replace('\\xe2\\x81\\xbe', ")").
                       replace('\\\\xf0\\\\x9f\\\\x..\\\\x..', '',regex = True).
                       replace('\\\\x..\\\\x..\\\\..','',regex = True).
                       replace('\\n', ' ').
                       replace('&amp;', '&')
                       )
        return better_text

    def clean_tweet(self, tweet):
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def process_tweet_text(self, tweets):
        '''
        takes in a collection of tweet texts, clean by converting unicode and removing frills
        '''
        tw_ascii = self.unicode2ascii(tweets)
        tw_precl = [self.clean_tweet(t) for t in tw_ascii]
        tw_clean = [t[2:].lower() for t in tw_precl]  # remove leading 'b ' from each string
        return tw_clean

    def remove_tracked_words(self, tweets, tracks):
        # only handles Series for now
        try:
            patterns = '|'.join(tracks)
            tw_clean = tweets.str.replace(patterns, '')
            return tw_clean
        except:
            print('tweets must be pandas Series')

    def get_tweet_polarity(self, tweet):
        blob = TextBlob(tweet)
        pol = blob.sentiment.polarity
        return pol

    def get_tweet_subjectivity(self, tweet):
        blob = TextBlob(tweet)
        sub = blob.sentiment.subjectivity
        return sub

    def make_word_cloud(self, text, plot=True):
        if isinstance(text, pd.core.series.Series):
            s = ''
            for t in text:
                s += ' ' + t
            text = s
        sw = list(string.ascii_letters) + nltk.corpus.stopwords.words() + ['amp']
        wc = wordcloud.WordCloud(stopwords = sw, height = 600, width = 600).generate(text)
        if plot:
            plt.imshow(wc, interpolation="bilinear")
            plt.axis("off")
            plt.show()
        return wc

if __name__ == '__main__':
    # pass
    with open('api_tokens.pkl', 'rb') as f:
        [consumer_key, consumer_secret, auth_key, auth_secret] = \
            pickle.load(f)

    client = TwitterClient()
    api = client.get_client_api()
    tweets = api.user_timeline(screen_name='jaboukie', count=5)
    analyzer = TwitterAnalyzer()
