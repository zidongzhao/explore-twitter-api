#!/usr/bin/env python3
"""
@author: z
"""
import tweepy
import pandas as pd
import numpy as np
import pickle
import textblob

####
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
        super().__init__()
        self.fetched_fname = fetched_fname
        # init storage df
        self.df = pd.DataFrame(
            data = None,
            columns = [
                'text','tweet_id','author_id','author_screen_name','time',
                'source','coord_x','coord_y','place_name','place_type',
                'place_country_code','place_bounding'
            ],
        )

    def text_parser(self, status):
        # handle extended mode, full_text etc
        if hasattr(status, 'extended_tweet'):
            text = status.extended_tweet['full_text']
        else:
            text = status.text
        text = text.encode('utf-8')
        return text

    def coords_parser(self, coordinates):
        if coordinates is not None:
            coords = coordinates.coordinates
        else:
            coords = [None, None]
        return coords

    def place_parser(self,place):
        if place is not None:
            name = place.name
            type = place.place_type
            cc = place.country_code
            box = place.bounding_box.coordinates[0]
            place_stuff = [name, type, cc, box]
        else:
            place_stuff = [None, None, None, None]
        return place_stuff

    def on_status(self, status):
        # overwriting the inherited on_status method
        # exclude all retweets and quote tweets, could adjust
        if not hasattr(status, 'retweeted_status') and not status.is_quote_status:
            try:
                basics = [
                    self.text_parser(status), status.id, status.author.id,
                    status.author.screen_name, status.created_at, status.source
                ]
                coords = self.coords_parser(status.coordinates)
                place = self.place_parser(status.place)
                newrow = np.concatenate((basics, coords, place))
                self.df.loc[self.df.shape[0]] = newrow # append in place
                # print to file every 10 tweets
                if self.df.shape[0] % 10 == 0:
                    self.df.to_csv(fetched_fname)
                return True
            except BaseException as e:
                print(f'Error on error: {e}')
                return True

    def on_error(self, status):
        # overwirting the inherited on_error method
        print(status)
        if status == 420:
            # kill the connection if reach rates limit
            return False

class TwitterStreamer():
    '''
    Class for streaming and processing live tweets
    '''
    def __init__(self):
        authenticater = TwitterAuthenticater()
        self.auth = authenticater.authenticate_twitter_app()

    def stream_tweets(self, fetched_fname, tracks):
        listener = TwitterListener(fetched_fname)
        stream = tweepy.Stream(self.auth, listener, tweet_mode='extended')
        stream.filter(track=tracks)

if __name__ == '__main__':
    # load in api credentials
    with open('api_tokens.pkl','rb') as f:
        [consumer_key, consumer_secret, auth_key, auth_secret] = \
            pickle.load(f)

    # define streamer params
    tracks = ['mitch mcconnell', 'mitchmcconnell', 'elaine chao', 'elainechao']
    fetched_fname = 'elaine_mitch.csv'
    # set up streaming
    moscowstream = TwitterStreamer()
    moscowstream.stream_tweets(fetched_fname, tracks)
