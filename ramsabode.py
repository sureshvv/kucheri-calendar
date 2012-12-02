#!/usr/bin/python
#
# Copyright (C) 2009 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import datetime
import calendar
import urllib2
import atom
from subprocess import Popen, PIPE
from calendarExample import CalendarExample 
from google_pw import username, userpass
import gdata.calendar
import gdata.calendar.service
import Levenshtein

PAGE_URL = 'http://ramsabode.wordpress.com/concerts-in-chennai'

CALENDAR_NAME = 'default'
#CALENDAR_NAME = 'admin@rasikas.org'

months = calendar.month_name[1:]

class RamIterator:
    def __init__(self):
        fp = urllib2.urlopen(PAGE_URL)
        self.skip_data(fp)
        self.myiter = iter(fp)

    def __iter__(self):
        return self

    def next(self):
        while True:
            line = self.myiter.next()
            line = line.strip()
            line = line.replace('\xc2\xa0', '')
	    if line.find('text-decoration:underline') != -1:
                line = self.remove_tags(line)
                line = line.strip()
                if not line:
                    # month being underlined
                    continue
                line = line.split()
                if line[1] not in months:
                    if line[0].capitalize() in months:
                        continue
                    raise StopIteration
                self.year = int(line[2])
                self.day = line[0]
                assert(self.day.endswith('st') or self.day.endswith('nd') or \
                       self.day.endswith('rd') or self.day.endswith('th'))
                self.day = int(self.day[:-2])
                self.month = months.index(line[1]) + 1
            else:
                if line.find('@') != -1:
                    line = line.split('@')
                    loc = line[1].strip()
                    line0 = self.remove_tags(line[0])
                    line0 = line0.replace('&#8211;', '-')
                    line0 = line0.replace('\xe2\x80\x93', '-')
                    line0 = line0.replace('\xe2\x80\x99', "'")
                    line0 = line0.split('-', 1)
                    data = line0[0].split()
                    if len(data) == 4:
                        if data[1] != 'to':
                            continue
                        data = [data[0], data[3]]
                    if len(data) != 2:
                        continue
                    dict1 = {}
                    try:
                        dict1['hour'] = int(data[0].split(':')[0])
                    except ValueError:
                        import pdb; pdb.set_trace()
                    assert dict1['hour'] <= 12
                    try:
                        dict1['min'] = int(data[0].split(':')[1])
                    except (IndexError, ValueError):
                        dict1['min'] = 0
                    assert dict1['min'] < 60
                    data[1] = data[1].upper()
                    assert data[1] in ['AM', 'PM']
                    if data[1] == 'PM':
                        if dict1['hour'] < 12:
                            dict1['hour'] += 12
                    #if dict1['min'] >= 30:
                    #    dict1['hour'] -= 5
                    #    dict1['min'] -= 30
                    #else:
                    #    dict1['hour'] -= 6
                    #    dict1['min'] += 30
                    dict1['what'] = line0[1].strip()
                    dict1['where'] = line[-1].strip()
                    dict1['year'] = self.year
                    dict1['month'] = self.month
                    dict1['day'] = self.day
                    dict1['content'] = 'ramsabode %s' % datetime.datetime.now()
                    return dict1


    def skip_data(self, fp):
        for line in fp:
            line = line.strip()
            line = self.remove_tags(line)
            line = line.split()
            if len(line) == 2 and line[0].capitalize() in months:
                return True
        return False

    def remove_tags(self, line):
        while 1:
            pos = line.find('<')
            if pos == -1:
                break
            pos1 = line.find('>', pos)
            if pos1 == -1:
                break
            line = line[:pos] + line[pos1+1:]
        return line

if __name__ == "__main__":
    r1 = RamIterator()
    for x in r1:
        print x
