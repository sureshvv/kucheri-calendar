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
from subprocess import Popen, PIPE
from google_pw import username, userpass
import Levenshtein

PAGE_URL = 'http://ramsabode.wordpress.com/concerts-in-chennai'

CALENDAR_NAME = 'default'
#CALENDAR_NAME = 'admin@rasikas.org'

months = calendar.month_name[1:]
short_months = ['Nov', 'Dec', 'Jan']

class RamIterator:
    def __init__(self):
        self.fp = urllib2.urlopen(PAGE_URL)
        self.skip_data(self.fp)

    def __iter__(self):
        return self

    def next(self):
        dict1 = {}
        dict1['content'] = 'ramsabode'
        abbrs = [x for x in calendar.month_abbr]
        while True:
            line = self.fp.next().strip()
            line = self.remove_tags(line)
            line = line.split(' ', 5)
            try:
                dict1['month'] = abbrs.index(line[0])
                dict1['year'] = 2017 if dict1['month'] in (11, 12) else 2018
                dict1['day'] = int(line[1])
                hour_min = line[3].split(':')
                dict1['hour'] = int(hour_min[0])
                dict1['min'] = int(hour_min[1][:2])
                what_where = line[5].split('@')
                dict1['what'] = what_where[0]
                dict1['where'] = what_where[1]
            except (ValueError, IndexError):
                continue
            else:
                return dict1

    def skip_data(self, fp):
        count = 0
        for line in fp:
            line = line.strip()
            count += 1
            line = self.remove_tags(line)
            line = line.split()
            if line and line[0] in short_months:
                try:
                    date1 = int(line[1])
                except ValueError:
                    continue
                else:
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
