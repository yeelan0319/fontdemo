import jinja2
import json
import logging
import re
import os
import webapp2
import urllib2

from bs4 import BeautifulSoup
from urlparse import urlparse
from google.appengine.api import urlfetch

urlfetch.set_default_fetch_deadline(200)


JINJA_ENVIRONMENT = jinja2.Environment(
  loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions=['jinja2.ext.autoescape'],
  trim_blocks=True
)
ROOT_URL = ("http://localhost:8000" if
  os.environ['SERVER_SOFTWARE'].startswith('Development') else
  "https://mlfont-demo.googleplex.com/")

FONT_SLICES_CSS = "https://fonts.sandbox.google.com/earlyaccess/notosansscsliced.css"
NATIVE_FONT_CSS = "https://fonts.googleapis.com/earlyaccess/notosanssc.css"

FONT_SLICES_FAMILY = "Noto Sans SC Sliced"
NATIVE_FONT_FAMILY = "Noto Sans SC"



class MainHandler(webapp2.RequestHandler):
  """Web editor app entry point.
  """
  def get(self):
    self.response.set_status(200)
    self.response.headers['Content-Type'] = 'text/html'
    tmpl = JINJA_ENVIRONMENT.get_template('public/index.html')
    self.response.out.write(tmpl.render())


class HackyFrameHandler(webapp2.RequestHandler):
  def get(self):
    url = self.request.GET['url']
    use_font_slices = True if self.request.GET['slice']=='True' else False

    html = urllib2.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')
    ExtractAssetsMarkup(soup)
    InsertBaseurl(soup, url)
    InsertFontRule(soup, use_font_slices)
    PrintHTMLStatistics(soup)
    self.response.set_status(200)
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(unicode(soup))


class HackyPageHandler(webapp2.RequestHandler):
  def get(self):
    url = self.request.GET['url']
    use_font_slices = True if self.request.GET['slice']=='True' else False

    html = urllib2.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')
    InsertBaseurl(soup, url)
    InsertFontRule(soup, use_font_slices)
    PrintHTMLStatistics(soup)
    self.response.set_status(200)
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(unicode(soup))


def InsertBaseurl(soup, url):
  parsed_url = urlparse(url)
  baseurl = ''
  if parsed_url.scheme:
    baseurl = '{}:'.format(parsed_url.scheme)
  baseurl = '{}//{}'.format(baseurl, parsed_url.netloc)
  if parsed_url.path:
    baseurl = '{}/{}'.format(baseurl, parsed_url.path.rsplit('/', 1)[0])
  # Append BaseUrl
  soup.head.insert(0, soup.new_tag('base', href=baseurl))


def InsertFontRule(soup, use_font_slices):
  # Append font CSS
  font_url = FONT_SLICES_CSS if use_font_slices else NATIVE_FONT_CSS
  font_family = FONT_SLICES_FAMILY if use_font_slices else NATIVE_FONT_FAMILY
  soup.head.append(soup.new_tag('link', href=font_url, rel='stylesheet'))
  # Append font family
  soup.head.append(soup.new_tag('style', type='text/css'))
  soup.head.style.append('* {{font-family: "{}", serif !important;}}'.format(font_family))


def ExtractAssetsMarkup(soup):
  targetMarkup = ['script', 'style', 'link', 'img', 'iframe']
  for script in soup(targetMarkup):
    script.extract()
  for element in soup.find_all(style=re.compile('background')):
    element['style'] = ''


def PrintHTMLStatistics(soup):
  # Output how many unique unicode point the page has
  logging.info(len(set(re.sub(r'\s', '', soup.body.getText()))))

urls = [
  webapp2.Route(r'/frame', HackyFrameHandler),
  webapp2.Route(r'/page', HackyPageHandler),
  ('/.*', MainHandler),
]

app = webapp2.WSGIApplication(urls, debug=True)

