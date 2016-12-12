# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from parsel import Selector
from scrapy.loader.processors import TakeFirst, Join

class MyspiderItem(scrapy.Item):
    # define the fields for your item here like:
    #关于这里使用的输入输出处理器，建议最好配合compose一起使用
    #首先调用scrapy内建的输入输出处理器函数，然后在调用自定义的函数
    #这样就可以得到较为精准的数据
    movie_name = scrapy.Field(input_processor=TakeFirst(),
    					  output_processor=Join(),)

    movie_type = scrapy.Field(input_processor=TakeFirst(),
    					  output_processor=Join(),)

    movie_rate = scrapy.Field(input_processor=TakeFirst(),
    					  output_processor=Join(),)

    movie_year = scrapy.Field(input_processor=TakeFirst(),
    					  output_processor=Join(),)

    url = scrapy.Field(output_processor=Join())


class LinkLoader(object):
	#自定义一个类，专门用来提取链接
	#text是unicode字符串
	def __init__(self, text, type='html'):
		self.sel = Selector(text, type=type)
		self.set = set()

	def add_xpath(self, xpath, re_patten=r'.'):
		#提取links
		links = self.sel.xpath(xpath).re(re_patten)
		self.set.update(links)

	def get(self):
		#得到最终的所有链接
		return list(self.set)
