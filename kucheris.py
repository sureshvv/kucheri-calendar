import calendar
import time
import datetime
import bs4

PAGE_URL = 'http://www.musicrux.com/kutcheris'

from splinter import Browser

months = [x[:3] for x in calendar.month_name[1:]]

class KuchIterator:
    def __init__(self):
        self.browser = Browser('phantomjs')
        self.browser.visit(PAGE_URL)
        self.get_next_row()

    def __iter__(self):
        return self

    def get_next_row(self):
        soup = bs4.BeautifulSoup(self.browser.html)
        self.schedule = soup.find_all('table')[0]
        self.cur_row = self.schedule.tbody.tr

    def get_a_children(self, parent):
        out = ""
        for c1 in parent.children:
            if getattr(c1, 'name', None):
                if c1.name == 'a':
                    if c1.string:
                        out += c1.string
                elif c1.name in ['i', 'br']:
                    out += ", "
                    out += self.get_a_children(c1)
            else:
                if c1.string:
                    out += c1.string
        return out

    def next(self):
        try:
            c1 = self.cur_row.td
        except AttributeError:
            self.browser.find_link_by_partial_text('next').click()
            time.sleep(5)
            self.get_next_row()
            c1 = self.cur_row.td

        when1 = c1.span['content']
        c1 = c1.next_sibling
        who1 = c1.next_sibling.div.ul.li.contents[0]
        if not isinstance(who1, bs4.element.NavigableString):
            who1 = who1.contents[0]
        c1 = c1.next_sibling
        c1 = c1.next_sibling
        c1 = c1.next_sibling
        c1 = c1.next_sibling
        where1 = c1.next_sibling.a.contents[0]
        self.cur_row = self.cur_row.next_sibling
        self.cur_row = self.cur_row.next_sibling
        pos1 = when1.find('+')
        if pos1 != -1:
            when1 = when1[:pos1]
        date1 = datetime.datetime.strptime(when1, '%Y-%m-%dT%H:%M:%S')
        dict1 = {}
        dict1['year'] = date1.year
        dict1['month'] = date1.month
        dict1['day'] = date1.day
        dict1['hour'] = date1.hour
        dict1['min'] = date1.minute
        dict1['what'] = who1
        dict1['where'] = where1
        dict1['content'] = 'musicrux'
        return dict1


if __name__ == "__main__":
    r1 = KuchIterator()
    for x in r1:
        print x
