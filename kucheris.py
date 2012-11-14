import urllib2
import calendar
from bs4 import BeautifulSoup

PAGE_URL = 'http://kutcheris.com/schedule.php'
months = [x[:3] for x in calendar.month_name[1:]]

class KuchIterator:
    def __init__(self):
        fp = urllib2.urlopen(PAGE_URL)
        body = fp.read()
        soup = BeautifulSoup(body)
        self.schedule = soup.find_all('table')[1]
        self.cur_row = self.schedule.tbody.tr

    def __iter__(self):
        return self

    def next(self):
        try:
            c = self.cur_row.children
        except AttributeError:
            raise StopIteration
        c.next()
        c.next()
        dt1 = c.next().string.split()
        self.day = int(dt1[1].rstrip('st').rstrip('nd').rstrip('rd').rstrip('th'))
        self.month = months.index(dt1[2]) + 1
        if len(dt1) > 3:
            self.year = int(dt1[3])
        start_time = c.next().string.split()
        c.next()
        #import pdb; pdb.set_trace()
        who = ""
        for w1 in c.next().children:
            if getattr(w1, 'name', None):
                # can be an <a>, <br>, or <i>
                if w1.name == 'a':
                    who += w1.string
                elif w1.name == 'br' and who:
                    who += ", "
            else:
                who += w1.string
        #who = c.next().get_text().replace(')', '), ').rstrip(', ')
        loc = ""
        for w1 in c.next().children:
            if getattr(w1, 'name', None):
                if w1.name == 'a' and w1.string:
                    loc += w1.string
                elif w1.name == 'br' and loc:
                    loc += ", "
            else:
                loc += w1.string
        #loc = c.next().get_text()
        self.cur_row = self.cur_row.next_sibling
        return self.year, self.month, self.day, start_time, who, loc


if __name__ == "__main__":
    r1 = KuchIterator()
    for x in r1:
        print x
