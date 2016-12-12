#-*-coding:utf-8-*-

from scrapy import signals
from twisted.internet import task

class MyCustomExtension(object):
	#结合signals, 可以使用extension来定义和收集scrapy的stats
	#并将收集到的stats输出，绘制成图形
	#也可以在其他的类中使用from_crawler这个方法。用来记录日志
	#log出现的error的次数。也可以记录response中多少个404页面等等

	def __init__(self, stats):
		self.stats = stats

	@classmethod
	def from_crawler(cls, crawler):
		instance = cls(crawler.stats)
		crawler.signals.connect(instance.item_dropped, 
								signal=signals.item_dropped)
		crawler.signals.connect(instance.item_scraped, 
								signal=signals.item_scraped)

		crawler.signals.connect(instance.response_received, 
								signal=signals.response_received)
		crawler.signals.connect(instance.response_downloaded, 
								signal=signals.response_downloaded)
		return instance

	def item_dropped(self, item, spider):
		#接受item在经过itempipeline时被丢弃是发出的信号		
		self.stats.inc_value('item/dropped', spider=spider)	

	def item_scraped(self, item, spider):
		#接受item成功通过所有itempipeline时发出的信号		
		self.stats.inc_value('item/scraped', spider=spider)		

	def response_received(self, response, spider):
		#接受engine接收到一个response时发送的信号	
		self.stats.inc_value('response/received', spider=spider)	

	def response_downloaded(self, response, spider):
		#接受下载器成功下载一个response时发送的信号		
		self.stats.inc_value('response/downloaded', spider=spider)


class MyCustomStatsExtension(object):
	"""
	这个extension专门用来定期搜集一次stats
	"""
	def __init__(self, stats):
		self.stats = stats
		self.time = 60.0

	@classmethod
	def from_crawler(cls, crawler, *args, **kwargs):
		return cls(crawler.stats)
		
	def open_spider(self):
		self.tsk = task.LoopingCall(self.collect)
		self.tsk.start(self.time, now=True)

	def close_spider(self):		
		if self.tsk.running:
			self.tsk.stop()

	def collect(self):
		#这里收集stats并写入相关的储存。
		#目前是输出到终端展示出来
		print u'将展示收集到的数据'
		print self.stats.get_stats()