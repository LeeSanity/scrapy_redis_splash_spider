# -*- coding: utf-8 -*-
import re
import logging
import scrapy
import urlparse
from scrapy import signals
from scrapy.http import Request
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy.linkextractors import LinkExtractor
from scrapy_redis.spiders import RedisSpider
from scrapy.utils.log import configure_logging
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
from twisted.internet.error import TCPTimedOutError
from scrapy.spidermiddlewares.httperror import HttpError
from w3lib.url import canonicalize_url
from ..items import MyspiderItem, LinkLoader
from .. import html

class MySpider(RedisSpider):
    """
    在使用scrapy_redis时，初始url需要手动添加到待抓取的队列中

    scrapy_redis中最起码有三个队列：
    1.保存所有看过的request对象信息指纹的队列，这个队列用于去重.队列的名称为'[spider.name]:dupefilter'------->'splashspider:dupefilter'
      这个队列里会保存所有看过的request对象的指纹

    2.保存等待抓取的request的队列，默认使用的是redis的有序集合，根据request对象的priority属性进行排序。
      队列的名称为'[spider.name]:requests'----->'splashspider:requests'
      
    3.保存item的队列，队列名称为'[spider.name]:items'---->'splashspider:items'
    
    scrapy-redis原理:
        1.spider解析下载器下载下来的response,返回item或者是links
        2.item或者links经过spidermiddleware的process_spider_out()方法，交给engine。
        3.engine将item交给itempipeline,将links交给调度器
        4.在调度器中，先将request对象利用scrapy内置的指纹函数，生成一个指纹对象
        5.如果request对象中的dont_filter参数设置为False,并且该request对象的指纹不在信息指纹的队列中，那么就把该request对象放到优先级的队列中
        6.从优先级队列中获取request对象，交给engine
        7.engine将request对象交给下载器下载，期间会通过downloadmiddleware的process_request()方法
        8.下载器完成下载，获得response对象，将该对象交给engine,期间会通过downloadmiddleware的process_response()方法
        9.engine将获得的response对象交给spider进行解析，期间会经过spidermiddleware的process_spider_input()方法
        10.从第一步开始循环
    """
    name = "splashspider"   
    #初始url所在的队列，一定要手动的往这个队列中加入初始url
    redis_key = 'splashspider:start_urls'
    allowed_domains = ["movie.douban.com"]

    #这里的*args, **kwargs是通过scrapy的命令行传递的
    #命令行的指令是scrapy crawl splashspider -a *args **kwargs
    #就可以通过这个命令行来动态的指定一些参数，比如allowed_domain
    def __init__(self, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        #匹配需要提取item的url
        self.item_url = re.compile(r'/subject/[0-9]+/$')

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        #这个from_crawler方法一定要返回当前类的实例
        #这个类方法的crawler对象是进入scrapy核心api的入口
        #可以定义非常多的功能，比如接受信号等
        #该方法最好继承父类的方法，要不然会报错
        spider = super(MySpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.stats = crawler.stats
        #spider.splash_meta = crawler.settings.get('SPLASH_META')
        return spider

    def parse(self, response):
        #如果没有给request对象显示的指定回调函数
        #那么就会使用parse作为默认的回调函数
        if self.item_url.search(response.url):
            return self._extract_item(response)            
        else:
           return self._parse_links(response)
            
    def _extract_item(self, response):
        #提取结构化数据
        l = ItemLoader(response=response, item=MyspiderItem(), type='html')
        l.add_xpath('movie_name', '//h1/span[@property="v:itemreviewed"]/text()')
        l.add_xpath('movie_year', '//span[@property="v:initialReleaseDate"]/text()')
        l.add_xpath('movie_type', '//span[@property="v:genre"]/text()')
        l.add_xpath('movie_rate', '//strong[@class="ll rating_num"]/text()')
        l.add_value('url', response.url)
        #这里转换为字典的原因是，load_item()返回的是scrapy.Item对象
        #而scrapy-redis，采用了json将item序列化并上传到redis的item队列中
        #可是json只能序列化python内建的数据结构，所以这里将item转换成字典
        return dict(l.load_item())

    def _parse_links(self, response):
        #提取网页中的链接
        #并把相对url补全为完整的url
        l = LinkLoader(html.html_to_unicode(response))
        l.add_xpath(xpath='//a/@href', re_patten=r'/subject/[0-9]+/$|/tag/.*')
        #如果需要提取多个不同的规则的链接就调用多次
        #l.add_xpath(xpath, re_patten)
        #l.add_xpath(xpath, re_patten)
        #最后调用get()方法就可以获取到相应的所有的链接，返回的是一个包含url的列表
        links = l.get()

        base = urlparse.urlparse(response.url)
        domain = '://'.join((base.scheme, base.netloc))
        for url in links:
            #其实下面这些部分scrapy内置link extrackor实现了
            #也可以放到中间件中去实现将相对url补全为完整的url
            component = urlparse.urlparse(url)
            #这一步是去除url中的host与response的url的host不相同的url
            #然后scrapy默认的offsite spider中间件就可以保证抓取到的不会抓取不该抓取的url
            if (component.netloc) and (component.netloc != base.netloc):
                continue                 
            #这一步判断url是否为完整的url
            if domain not in url:
                url = urlparse.urljoin(domain, url)
            #将url规范化,比如去除url中的#号等等
            url = canonicalize_url(url)
            #设置request抓取的优先级
            priority = 5 if self.item_url.search(url) else 0
            #遇到了如果没有显示的指定callback，而就单单指定一个
            #errback就会报错的情况
            yield Request(url=url, callback=self.parse, errback=self.error_back,
                          priority=priority)
            
    def error_back(self, failure):
        #request对象中的error_back
        #当下载器在下载request对象引发的错误时，就会调用这个方法
        #对于请求超时和dns解析超时的请求
        #可以将请求对象重新放到redis的优先级队列中
        if failure.check(HttpError):
            #这里记录非200响应的错误
            response = failure.value.response
            self.logger.error('[%s] GET [%d]', response.url, response.status)

        if failure.check(DNSLookupError):
            #dns查询错误
            request = failure.request
            self.logger.error('[%s] DNSLookupError', request.url)

        if failure.check(TimeoutError, TCPTimedOutError):
            #请求超时
            request = failure.request
            self.logger.error('[%s] TimeoutError', request.url)

