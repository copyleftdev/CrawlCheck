import requests
from bs4 import BeautifulSoup as bs
import unittest
import xmlrunner
import ConfigParser



# Settings are located in conf/settings.cfg
config = ConfigParser.RawConfigParser()
config.read('conf/settings.cfg')
base_url = config.get('target', 'server')


def dedupe(seq):
    """Deduplicate a list"""
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def collect_links(url):
    """Collect <a> hregs tags from a given url"""
    exclude_pattern = ['tel', 'javascript', 'google', 'youtube', 'j2global',
                       'linkedin', 'facebook', 'twitter' ,'backup']
    collected_links = []
    r = requests.get(url)
    soup = bs(r.content, "html.parser")
    page_links = soup.find_all('a')
    for l in page_links:
        if any(x in l['href'] for x in exclude_pattern):
            continue
        elif 'http' not in l['href']:
            collected_links.append('{}{}'.format(base_url, l['href']))
        else:
            collected_links.append(l['href'])
    return dedupe(collected_links)



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
                r = requests.get(a)
                self.assertEqual(r.status_code, b)
            return test

        for tname, a, b in compile_test_list(base_url):
            test_name = "test_%s" % tname
            dict[test_name] = gen_test(a,b)
        return type.__new__(mcs, name, bases, dict)

class CrawlerTestSequence(unittest.TestCase):
    __metaclass__ = CrawlerTests

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'),
                  verbosity=2, failfast=False, buffer=False, catchbreak=False)
