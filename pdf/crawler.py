#! /usr/bin/env python3
# -*- coding: utf-8 -*-
'''
This crawler is used to crawl a
web site and change it to pdf
'''

__author__ = 'ly'

from urllib import request
from urllib import parse
from urllib import error
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pdfkit
import time, os, re, logging

from PyPDF2 import PdfFileMerger

class Crawler(object):
    '''
    爬虫基类，所有爬虫都应该继承此类
    '''
    name = None
    # 需要在body中添加自己的内容
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
    
    </body>
    </html>
    '''
    # css的模板样式，自己添加需要的href
    css_template = '<link rel="stylesheet" type="text/css">'

    def __init__(self, name, start_url):
        '''
        初始化
        ：param name: 保存PDF文件名，不需要后缀名
        : param start_url: 爬虫入口url
        '''
        self.name = name
        self.start_url = start_url
        self.domain = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(self.start_url))

    def crawl(self, url):
        '''
        return url
        '''
        return request.urlopen(url)

    def parse_menu(self, response):
        '''
        解析目录结构
        '''
        raise NotImplementedError

    def parse_body(self, response):
        '''
        解析正文
        '''
        raise NotImplementedError
    def parse_css(self, response):
        '''
        解析css(注： 整个网页都是一样的css文件，可以有多个css文件，但是大家都要是一样的)
        '''
        return None

    def run(self):
        '''
        run method
        '''
        start = time.time()
        css_list = self.parse_css(self.crawl(self.start_url))
        menu_list = self.parse_menu(self.crawl(self.start_url))
        if not menu_list:
            logging.error('在起始url没有找到目录，程序返回', exc_info=True)
            return None
        # 对html、css等文件的出来
        # try except finally 方法
        html_template = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
        '''
        for css in css_list:
            html_template = html_template + '\n <link rel="stylesheet" href="{}">'.format(css)
        html_template = html_template + '\n</head>\n<body>'
        with open('final.html', 'wb') as f_html:
            f_html.write(html_template.encode('utf-8'))
            for url in menu_list:
                cur_html = self.parse_body(self.crawl(url))
                print('抓取 {} 完成， 正在写入文件'.format(str(cur_html.h1)))
                f_html.write(cur_html.encode('utf-8'))
            f_html.write('\n</body>\n</html>'.encode('utf-8'))

        print('translate to "final.pdf"!!')
        try:
            pdfkit.from_file('final.html', self.name + ".pdf")
            #os.remove('final.html')
        except Exception as e:
            logging.error('转化为pdf失败！\n', exc_info=True)
        total_time = time.time() - start
        print(u'总计耗时： %f 秒' % total_time)

class WebCrawler(Crawler):
    '''
    廖雪峰python3教程
    '''

    def parse_menu(self, response):
        '''
        解析目录结构
        '''
        bs_obj = BeautifulSoup(response, 'lxml')
        nav_div = bs_obj.find('div', class_='x-sidebar-left-content')
        link_list = nav_div.findAll('a', {'href' : re.compile('/wiki/')})
        for alist in link_list:
            src = alist['href']
            if not src.startswith('http'):
                src = urljoin(self.start_url, src)
            yield src

    def parse_css(self, response):
        '''
        解析css文件
        '''
        bs_obj = BeautifulSoup(response, 'lxml')
        css_label = bs_obj.head.findAll('link', {'href' : re.compile(r'.*?\.css')})
        css_list = []
        for alabel in css_label:
            css_list.append(urljoin(self.start_url, alabel['href']))
        return css_list
        #return css_list if Not len(css_list) else None


    def parse_body(self, response):
        '''
        解析正文
        '''
        try:
            bs_obj = BeautifulSoup(response, 'lxml')
            title = bs_obj.h4.get_text()
            main_page = bs_obj.find('div', class_='x-wiki-content')

            new_center = bs_obj.new_tag('center')
            new_title = bs_obj.new_tag('h1')
            new_title.string = title
            new_center.insert(1, new_title)
            main_page.insert(1, new_center)

            for img in main_page.findAll('img', {'src' : re.compile('^(?!http)')}):
                img['src'] = urljoin(self.start_url, img['src'])

            return main_page
            #html = BeautifulSoup(self.html_template, 'lxml')
            #html.body.insert(1, main_page)
            #return (html.encode('utf-8'), title)
        except Exception as e:
            logging.error('解析错误!\n', exc_info=True)

if __name__ == '__main__':
    start_url = 'http://www.liaoxuefeng.com/wiki/0014316089557264a6b348958f449949df42a6d3a2e542c000'
    crawler = WebCrawler('python3', start_url)
    crawler.run()
