#-*-coding:utf-8-*-
from scrapy_redis.dupefilter import RFPDupeFilter
from scrapy_splash.dupefilter import splash_request_fingerprint

class MyRFPDupeFilter(RFPDupeFilter):
	"""
	使用scrapy-splash的信息指纹结合scrapy-redis的指纹去重来过滤request
	这个自定义的RFPDupeFilter用于使用splash渲染js页面，使得request对象
	可以永久保存在redis队列中，只是简简单单的重写了scrapy_redis的过滤器中
	的request_seen和request_fingerprint方法
	"""
	def request_seen(self, request):
		fp = self.request_fingerprint(request)
		added = self.server.sadd(self.key, fp)
		return added == 0

	def request_fingerprint(self, request):
		return splash_request_fingerprint(request)