import urllib2
import calendar
import datetime
from bs4 import BeautifulSoup

PAGE_URL = 'http://kutcheris.com/schedule.php'
months = [x[:3] for x in calendar.month_name[1:]]

class KuchIterator:
    def __init__(self):
        fp = urllib2.urlopen(PAGE_URL)
        body = fp.read()
        body = body.replace("</br>", "")
        body = body.replace("<br>", "<br />")
        soup = BeautifulSoup(body)
        self.schedule = soup.find_all('table')[0]
        self.cur_row = self.schedule.tbody.tr

    def __iter__(self):
        return self

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
            c = self.cur_row.children
        except AttributeError:
            raise StopIteration
        junk = c.next()
        junk = c.next()
        junk = c.next()
        """ <td style="padding: 15px;">
              <span style="font-size:120%;margin-bottom: 7px;display: block;">
                <a href="artist.php?id=544">Dr. Subashini Parthasarathy</a> (Vocal),
                <a href="artist.php?id=328">Pakkala Ramadas</a> (Violin),
                <a href="artist.php?id=31">Poongulam Subramaniam</a> (Mrdangam),
                <a href="artist.php?id=15">V. Anirudh Athreya</a> (Kanjira)
                </br>
              </span>
              <span style="font-size:100%;">
                <img src="images/icons/datetime.png" height="12px"/>&nbspSunday, October 19th, 2014 at 6:15 PM</br>
                <img src="images/icons/sabha.png" height="12px"/>&nbsp<a href="organization.php?id=37">Nadopasana</a><br>
                <img src="images/icons/venue.png" height="12px"/>&nbsp<a href="venues.php?vid=6">Ragasudha Hall (Chennai)</a>
              </span>
            </td>
        """
        a3 = c.next()
        who = ', '.join(str(x.contents[0]) for x in a3.span('a'))
        dt1 = a3('span')[1].contents[1].split()[1:]
        self.day = int(dt1[1].rstrip('st,').rstrip('nd,').rstrip('rd,').rstrip('th,'))
        self.month = months.index(dt1[0][:3]) + 1
        self.year = int(dt1[2])
        start_time = [dt1[4], dt1[5]]
        loc = a3('span')[1].contents[-1].contents[0]
        self.cur_row = c.next()
        dict1 = {}
        dict1['hour'] = int(start_time[0].split(':')[0])
        assert dict1['hour'] <= 12
        try:
            dict1['min'] = int(start_time[0].split(':')[1])
        except (IndexError, ValueError):
            dict1['min'] = 0
        assert dict1['min'] < 60
        start_time[1] = start_time[1].upper()
        assert start_time[1] in ['AM', 'PM']
        if start_time[1] == 'PM':
                if dict1['hour'] < 12:
                    dict1['hour'] += 12
        #if dict1['min'] >= 30:
        #    dict1['hour'] -= 5
        #    dict1['min'] -= 30
        #else:
        #    dict1['hour'] -= 6
        #    dict1['min'] += 30
        dict1['what'] = who.encode('utf-8')
        dict1['where'] = loc.encode('utf-8')
        dict1['year'] = self.year
        dict1['month'] = self.month
        dict1['day'] = self.day
        dict1['content'] = 'kutcheris %s' % datetime.datetime.now()
        return dict1


if __name__ == "__main__":
    r1 = KuchIterator()
    for x in r1:
        print x
