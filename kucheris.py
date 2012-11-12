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
        #import pdb; pdb.set_trace()
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
        who = c.next().get_text().replace(')', '), ').rstrip(', ')
        loc = c.next().get_text()
        self.cur_row = self.cur_row.next_sibling
        return self.year, self.month, self.day, start_time, who, loc


if __name__ == "__main__":
    r1 = KuchIterator()
    for x in r1:
        print x

"""
Pdb) p list(self.cur_row.children)[0]
<td><div class="unstarred" id="8755" onclick="toggleStar(this);"></div></td>
(Pdb) p list(self.cur_row.children)[1]
u' '
(Pdb) p list(self.cur_row.children)[2]
<td>Wednesday 14th Nov 2012</td>
(Pdb) p list(self.cur_row.children)[3]
<td>7:00 PM</td>
(Pdb) p list(self.cur_row.children)[4]
u'\n'
(Pdb) p list(self.cur_row.children)[5]
<td><a href="artist.php?id=1390">R. Arjun Sambasivan</a> (Keyboard)<br/><a href="artist.php?id=1391">R. Narayanan</a> (Keyboard)<br/><a href="artist.php?id=1823">Nagerkoil Anand</a> (Violin)<br/><a href="artist.php?id=1129">S. Sathyanarayanan</a> (Mrdangam)<br/><a href="artist.php?id=51">S. Hariharasubramaniam</a> (Ghatam)<br/></td>
(Pdb) p list(self.cur_row.children)[6]
<td><a href="organization.php?id=339">Tambaram Asthika Sabha</a><br/><a href="venues.php?vid=52">Sitadevi Garodia Hindu Senior Secondary School (Chennai)</a></td>
(Pdb) p list(self.cur_row.children)[7
*** SyntaxError: SyntaxError('unexpected EOF while parsing', ('<string>', 1, 29, 'list(self.cur_row.children)[7'))
(Pdb) p list(self.cur_row.children)[7]
<td style="text-align:center;vertical-align:middle;"><a href="event.php?id=8755"><img src="images/icons/arrow-right.png"/></a></td>
"""

