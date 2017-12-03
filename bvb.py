import calendar
import time
import datetime
import re

BVB_FILE = 'kfa1.txt'

class BVBIterator:
    def __init__(self):
        self.fp = open(BVB_FILE)
        self.content = self.fp.next().strip()

    def __iter__(self):
        return self

    def next(self):
        line = self.fp.next().strip()
        if re.match('[0-9]*[0-9]\.[0-9][0-9]\.2*0*1[78]', line):
            line = line.split()[0]
            line = line.split('.')
            self.cur_date = line[:3]
            line = self.fp.next().strip()
        line = line.split(' ', 2)
        self.cur_time = line[0].split('.')
        dict1 = {}
        dict1['year'] = int(self.cur_date[2])
        if dict1['year'] in (17,18):
            dict1['year'] += 2000
        dict1['month'] = int(self.cur_date[1])
        dict1['day'] = int(self.cur_date[0])
        dict1['hour'] = int(self.cur_time[0])
        dict1['min'] = int(self.cur_time[1])
        if line[1].lower() == 'pm' and dict1['hour'] < 12:
            dict1['hour'] += 12
        dict1['what'] = line[2]
        dict1['where'] = self.content
        dict1['content'] = self.content
        return dict1


if __name__ == "__main__":
    r1 = BVBIterator()
    for x in r1:
        print x
