# -*- coding: utf-8 -*-

# Scrapy settings for allocinay project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
# http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'allocinay'

SPIDER_MODULES = ['allocinay.spiders']
NEWSPIDER_MODULE = 'allocinay.spiders'
COOKIE_ENABLED = False
DEPTH_LIMIT = 2
CONCURRENT_REQUESTS = 40  #UBERFAST MODE
FORCE = False
RESULT_LIMIT = 3  #20 items per page sorted by notation
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'allocinay (+http://www.yourdomain.com)'
