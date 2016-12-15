import requests
from bs4 import BeautifulSoup as bs
import unittest
import xmlrunner
import re
from selenium import webdriver


base_url = "http://www.efax.com"



def dedupe(seq):
    """Deduplicate a list"""
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def collect_links(url):
    headers = {'User-Agent':
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) \
                AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 \
                Safari/537.36'}

    schemes = ["https", "http"]
    link_collection = []
    urlp = r"^((http[s]?|ftp):\/)?\/?([^:\/\s]+)((\/\w+)*\/)([\w\-\.]+[^#?\s]+)(.*)?(#[\w\-]+)?$"
    r = requests.get(url, headers=headers)
    soup = bs(r.content, "html.parser")

    for each_link in soup.findAll('a', href=re.compile(urlp)):
        if any(x in each_link['href'] for x in schemes):
            link_collection.append(each_link['href'])
        else:
            link_collection.append("{}{}".format(url, each_link['href']))



    return dedupe([x for x in  link_collection if url in x])


def compile_test_list(url):
    """Generates a nested list of elements to feed dynamicly generated tests"""
    test_vectors = []
    links = collect_links(url)
    for el in links:
        test_name = el.replace("http://", ""). \
                    replace("/", "_").replace(".", "_"). \
                    replace("-", "_")
        test_vectors.append(["{}".format(test_name), el, 200])
    return test_vectors

# creats single tests for each item return from compiled_test_list()


class CrawlerTests(type):
    def __new__(mcs, name, bases, dict):

        def gen_test(a, b):
            def test(self):
                """Testing {} for a response of 200""".format(a)
                r = requests.get(a)
                self.assertEqual(r.status_code, b)
            return test

        for tname, a, b in compile_test_list(base_url):
            test_name = "test_%s" % tname
            dict[test_name] = gen_test(a, b)
        return type.__new__(mcs, name, bases, dict)


class CrawlerTestSequence(unittest.TestCase):
    __metaclass__ = CrawlerTests

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'),
                  verbosity=2, failfast=False, buffer=False, catchbreak=False)
