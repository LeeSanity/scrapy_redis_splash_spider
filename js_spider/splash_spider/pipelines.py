# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from .connection import BaseMiddlewareClass


#异步执行数据库操作的管道
class MyCustomMySQLPipeline(BaseMiddlewareClass):

	def process_item(self, item, spider):
		self.insert(item).addCallback(callback)
		return item

	def insert(self, item):
		cmd = 'INSERT INTO [tablename] (fieldname) VALUES (???)'
		return self.db.runQuery(cmd, item)

	def callback(self, value):
		self.logger.info()
