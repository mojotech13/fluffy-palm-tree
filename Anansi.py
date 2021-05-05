import argparse
import logging
import logging.config
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import sys
from configparser import ConfigParser
import pprint
import tweepy as tweepy
from six import iteritems

''' 
    Anansi is an Akan folkstale Character that literally means spider. He often 
    takes the shape of a spider and is sometimes considered to be a god of all 
    knowledge of stories.
'''


class AnansiParseError(Exception):
    pass


class Anansi(object):

    def __init__(self, stock=None, twitter=False, twitter_id=None, archive=False):
        # create logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        plt.style.use('seaborn')
        # Create argument dictionary
        self.job_configs = {'stock': stock, 'twitter': twitter, 'twitter_id': twitter_id, 'archive': archive}
        self.results = {}

        # Start logging program info
        self.logger.info('Starting up the Anansi.....')
        self.logger.info('************************')
        self.logger.info('* Arguments to Execute *')
        self.logger.info('************************')
        for key, val in iteritems(self.job_configs):
            self.logger.info(str(key) + '=' + str(val))
        self.logger.info('************************')

        self.execute_job(self.read_config_file(self.job_configs))

    def read_config_file(self, job_configs):

        # Instantiate configparser and read .ini file
        self.job_configs = job_configs
        config = ConfigParser()
        config.read('palmtree.ini')

        if self.job_configs['twitter']:
            self.job_configs['consumer_key'] = config.get('Twitter Configs', 'consumer_key')
            self.job_configs['consumer_secret'] = config.get('Twitter Configs', 'consumer_secret')
            self.job_configs['access_token'] = config.get('Twitter Configs', 'access_token')
            self.job_configs['secret_token'] = config.get('Twitter Configs', 'secret_token')
            self.job_configs['bearer_token'] = config.get('Twitter Configs', 'bearer_token')

        return self.job_configs

    def execute_job(self, job_configs):

        self.job_configs = job_configs

        if self.job_configs['twitter'] and self.job_configs['twitter_id']:
            results = (self.twitter_api(self.job_configs))

            for key, value in results.items():

                if key == 'username':
                    self.job_configs['twitter_id'] = {value: results}
                    del (self.job_configs['twitter_id'][value]['username'])
                    break

        if self.job_configs['stock']:

            results = self.stock_lookup(self.job_configs)
            self.job_configs = results

        if self.job_configs['archive']:
            self.archive_results(self.job_configs)

        self.print_results(self.job_configs)

    def twitter_api(self, job_configs):

        self.job_configs = job_configs
        twitter_info = {}
        auth = tweepy.OAuthHandler(self.job_configs['consumer_key'], self.job_configs['consumer_secret'])
        auth.set_access_token(self.job_configs['access_token'], self.job_configs['secret_token'])
        api = tweepy.API(auth, wait_on_rate_limit=True)
        user = api.get_user(self.job_configs['twitter_id'])
        twitter_info['followers_count'] = user.followers_count
        twitter_info['username'] = user.name

        return twitter_info

    def stock_lookup(self, job_configs):

        self.job_configs = job_configs

        stock_info = {}
        buffet = ['marketCap', 'priceToSalesTrailing12Months', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'profitMargins',
                  'sharesOutstanding', 'bookValue', 'heldPercentInstitutions', 'netIncomeToCommon', 'priceToBook',
                  'heldPercentInsiders', 'enterpriseValue', 'regularMarketPrice', 'sharesShortPriorMonth',
                  'sharesShort',
                  'fullTimeEmployees']

        # Get Ticker Info
        ticker = self.job_configs['stock']
        yf_ticker = yf.Ticker(ticker)
        ticker_info = yf_ticker.info
        # Retrieve selected Ticker Info
        for buff in buffet:
            if buff not in ticker_info:
                self.logger.warning(f"{buff} Not found in Stock Info.")
            else:
                stock_info.update({buff: ticker_info[buff]})
                # self.job_configs['stock'] = {buff: stock_info}

        self.job_configs['stock'] = {ticker: stock_info}
        self.logger.debug(f'job_configs in stock_lookup: {self.job_configs}')
        return self.job_configs

    def print_results(self, results):
        self.results = results
        pprint.pprint(self.results)

    def archive_results(self, job_configs):
        pass


if __name__ == '__main__':

    # Commandline argument parsing
    parser = argparse.ArgumentParser(description='Process user input')
    parser.add_argument('-a', '--archive', action='store_true', default=False,
                        help='If True, results will be save in Database.')
    parser.add_argument('-s', '--stock', action='store', default=None,
                        help='Stock ticker to lookup.')
    group = parser.add_argument_group('twitter')
    group.add_argument('-t', '--twitter', action='store_true', default=False,
                       help='Connect to twitter and retrieve User info.')
    group.add_argument('-tid', '--twitter_id', action='store', default=None,
                       help='Twitter ID to look up')
    args = parser.parse_args()

    # Logger
    logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s: '
                               ' %(message)s', stream=sys.stderr)
    logger = logging.getLogger(__name__)
    logger.debug('Finished parsing commandline arguments')

    try:

        # Run Anansi...
        Anansi(stock=args.stock, twitter=args.twitter, twitter_id=args.twitter_id, archive=args.archive)

    except Exception as err:
        logger.error(err)
        sys.exit()
