# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http import Request
import json
import re
import os
import fnmatch
from allocinay.items import AllocinayItem
import json
import requests


def uniqlist(seq, idfun=None):
    # custom stuff
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


# Xpath for username : //div[@class="user-name"]/h1/span/text()
# XPath for media list : //li[@class=" collectionitem"]
# URL Pa : http://www.allocine.fr/ws_v7/get_my_collection_list.ashx?url=%2Fws_v7%2Fget_my_collection_list.ashx&userId=Z20110109223902893978946&routeName=myuserspace_collection&profile=private&sort=&order=&child=&page=1
# Series : http://www.allocine.fr/ws_v7/get_my_collection_list.ashx?url=%2Fws_v7%2Fget_my_collection_list.ashx&userId=Z20110109223902893978946&routeName=public_collection_series&profile=private&sort=&order=&child=&page=1
class UserprefSpider(CrawlSpider):
    name = 'userpref'
    allowed_domains = ['allocine.fr']
    #start_urls = ['http://www.allocine.fr/membre-Z20110109223902893978946/'] #BIG ACCOUNT
    #start_urls = ['http://www.allocine.fr/membre-Z20061201131733277259886/'] #MODERATOR ACC
    start_urls = ['http://www.allocine.fr/membre-Z20090218183830900976424/']  # LOW END
    rules = (
    )
    baseFolder = './result'
    try:
        os.mkdir(baseFolder)
    except:
        print("Folder already exists")
    dire = os.listdir('./result/')

    def get_set(self, type, id):
        page = 1
        list = []
        selectApi = {'cine': 'myuserspace_collection',
                     'series': 'public_collection_series',
                     'stars': 'public_collection_star'}
        while True:
            if page == 1 or page % (self.settings['RESULT_LIMIT'] // 3) == 0:
                self.log("Getting result of page " + str(page))
            if page > self.settings['RESULT_LIMIT']:
                self.log("Excessive Access, stoping for this user.")
                break
            r = requests.get(
                'http://www.allocine.fr/ws_v7/get_my_collection_list.ashx?url=%2Fws_v7%2Fget_my_collection_list.ashx&userId=' + str(
                    id) + '&routeName=' + selectApi[type] + '&profile=private&sort=3&order=1&child=&page=' + str(page))
            page += 1
            JS = r.json()
            htmlsnips = JS['hits']
            if len(htmlsnips) == 0:
                break
            for htmlcode in htmlsnips:
                select = scrapy.Selector(text=htmlcode['html'])
                note_select = select.xpath('//ul/li/span/text()').extract()
                notation = note_select[0] if len(note_select) else 'Interest'
                name = select.xpath('//a/text()').extract()[0].strip()
                list.append((name, notation))
        return list

    def parse_friends(self, url):
        toto = (url + '/suivis/', url + '/abonnes/')
        friends_list = []
        friends_urls = []
        # 'json.loads(response.xpath('//span[@class="title"]//@data-entities')[0].extract())['profileUrl']'
        for page_url in toto:
            page = scrapy.Selector(text=requests.get(page_url).text)
            friend_selectors = page.xpath('//span[@class="title"]//@data-entities').extract()
            for friend in friend_selectors:
                unicode_url = json.loads(friend)['profileUrl']
                Id = re.search('(?<=membre-)\w+(?=/)', unicode_url).group(0)
                friends_list.append(Id)
                friends_urls.append(Request('http://www.allocine.fr' + unicode_url, callback=self.parse_user))
        return uniqlist(friends_list), uniqlist(friends_urls)

    def parse_user(self, response):
        i = AllocinayItem()
        i['id'] = re.search(r'(?<=membre-)\w+', response.url).group(0)
        i['name'] = response.xpath('//title').re('(?<=Profil de ).*(?= sur Allo)')[0]
        self.log("Name of current scraped user : " + i['name'])
        self.log("RESPONSE DEPTH == " + str(response.meta['depth']))
        self.log("DEPTH_LIMIT = " + str(self.settings['DEPTH_LIMIT']))
        if response.meta['depth'] < self.settings['DEPTH_LIMIT']:
            i['friends'], reqs = self.parse_friends(response.url)
            self.log("Succesfully fetched " + str(len(i['friends'])) + " friends.")
        else:
            reqs = []
        try:
            if self.settings['FORCE']:
                for user in self.dire:
                    assert not fnmatch.fnmatch(user, '*' + i['id'] + '*')
            i['movieList'] = self.get_set('cine', i['id'])
            self.log("Succesfully fetched " + str(len(i['movieList'])) + " movies.")
            i['seriesList'] = self.get_set('series', i['id'])
            self.log("Succesfully fetched " + str(len(i['seriesList'])) + " shows.")
            i['starList'] = self.get_set('stars', i['id'])
            self.log("Succesfully fetched " + str(len(i['starList'])) + " stars.")
            self.log("Finished the user named " + i['name'] + ', dumping the result..')
            with open(self.baseFolder + '/' + i['name'] + ' - ' + i['id'] + '.json', 'wb') as f:
                f.write(json.JSONEncoder(dict(i)).encode(dict(i)))
            if i['movieList'] or i['seriesList'] or i['starList']:
                reqs.append(i)
        except AssertionError:
            self.log("Already Fetched this user, skipping")
        return reqs
    def parse_start_url(self, response):
        return self.parse_user(response)