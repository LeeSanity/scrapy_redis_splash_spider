#-*-coding:utf-8-*-
import cStringIO
from w3lib.encoding import html_body_declared_encoding, to_unicode
from w3lib.html import get_meta_refresh
from chardet.universaldetector import UniversalDetector

def find_response_encoding(response):
	"""
	如果html的body中有charset声明的话，就会
	返回相应的内容.如果没有发现，就是用chardet来估算出网页所使用的字符编码
	"""	
	r = response.body
	encoding = html_body_declared_encoding(r)
	if encoding:
		return encoding
	else:
		my_stringio = cStringIO.StringIO(r)
		my_detector = UniversalDetector()
		for x in my_stringio:
			my_detector.feed(x)
			if my_detector.done:
				break
		my_detector.close()
		return my_detector.result['encoding']


def get_html_meta_refresh(response):
	"""
	text::response.text
	获取html网页中meta refresh中的重定向url, 返回的是元组对::(interval, url)
	interval是一个整数，表示重定向的延迟。如果不存在就为0
	如果不存在这个标签，就返回(None, None)
	"""
	text = html_to_unicode(response)
	result = get_meta_refresh(text)
	return result[1]


def bytes_to_unicode(bytes, encoding):
	"""
	将给定的bytes，通过encoding转换成unicode
	"""
	return to_unicode(bytes, encoding)


def html_to_unicode(response):
	"""
	将html转换成unicode
	"""
	encoding = find_response_encoding(response)
	return bytes_to_unicode(response.body, encoding)