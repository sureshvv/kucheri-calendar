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
import calendar, time
import urllib2
import atom
from subprocess import Popen, PIPE
from calendarExample import CalendarExample 
from google_pw import username, userpass
import gdata.calendar
import gdata.service
import gdata.calendar.service
import Levenshtein

from kucheris import KuchIterator
from ramsabode import RamIterator

CALENDAR_NAME = 'default'
#CALENDAR_NAME = 'admin@rasikas.org'

def google_login(email, password):
    cal_client = gdata.calendar.service.CalendarService()
    cal_client.email = email
    cal_client.password = password
    cal_client.source = 'Google-Calendar_Python_Sample-1.0'
    cal_client.ProgrammaticLogin()
    return cal_client

last_info = {'date': None, 'feed': None, 'len': 0 }

def same_string(str1, str2):
    if not str1 or not str2:
        return True
    str1 = str1.encode('utf-8') if type(str1) == type(u'a') else str1
    str2 = str2.encode('utf-8') if type(str2) == type(u'a') else str2
    print '++++', str1, str2
    ratio = Levenshtein.ratio(str1, str2)
    return ratio > 0.9

def chk_event(cal_client, event):
    global last_info
    new_date = '%d-%02d-%02d' % (event['year'], event['month'], event['day'])
    if last_info['date'] != new_date:
        query = gdata.calendar.service.CalendarEventQuery(CALENDAR_NAME, 'private', 'full')
        query.start_min = new_date
        st1 = datetime.date(event['year'], event['month'], event['day']) + datetime.timedelta(days=1)
        query.start_max = '%d-%02d-%02d' % (st1.year, st1.month, st1.day)
        query.max_results = 1000
        feed = cal_client.CalendarQuery(query)
        last_info['feed'] = feed
        last_info['date'] = new_date
        last_info['len'] = len(feed.entry)
    else:
        feed = last_info['feed']
        assert len(feed.entry) == last_info['len']
    matches = []
    for an_event in feed.entry:
      if an_event.title.text and same_string(an_event.title.text, event['what']):
          for a_when in an_event.when:
              start = a_when.start_time.split('T')[1].split(':')
              start_hour = int(start[0])
              start_min = int(start[1])
              if start_hour == event['hour'] and start_min == event['min']:
                  matches.append(an_event)
    return matches

def add_event(cal_client, event):
    ev1 = gdata.calendar.CalendarEventEntry()
    ev1.title = atom.Title(text=event['what'])
    ev1.content = atom.Content(text=event['content'])
    ev1.where.append(gdata.calendar.Where(value_string=event['where']))

    st1 = "%d-%02d-%02dT%02d:%02d:00.000+05:30" % (event['year'], event['month'],
        event['day'], event['hour'], event['min'])
    st2 = "%d-%02d-%02dT%02d:%02d:00.000+05:30" % (event['year'], event['month'],
        event['day'], event['hour']+2, event['min'])
    ev1.when.append(gdata.calendar.When(start_time=st1, end_time=st2))
    for ntries in range(5):
        try:
            new_event = cal_client.InsertEvent(ev1, '/calendar/feeds/' + CALENDAR_NAME + '/private/full')
        except gdata.service.RequestError as inst:
            print '++++', 'Retrying...', ntries, inst[0]['status']
            time.sleep(5)
            new_event = None
        else:
            break
    return new_event

def delete_duplicate_events(start_date, n_days):
    global last_info
    ex1 = google_login(username, userpass)
    start_date = start_date.split('-')
    if len(start_date) != 3:
        start_date = datetime.date.today()
        start_year = start_date.year
        start_month = start_date.month
        start_day = start_date.day
    else:
        start_year = int(start_date[0])
        start_month = int(start_date[1])
        start_day = int(start_date[2])
    for cnt in range(int(n_days)):
        st1 = datetime.date(start_year, start_month, start_day) + datetime.timedelta(days=cnt)
        event = {'day': st1.day, 'month': st1.month, 'year': st1.year, 'what': 'junk' }
        print 'processing ', event['year'], event['month'], event['day']
        chk_event(ex1, event)
        events = list(last_info['feed'].entry)
        events.sort(lambda x, y: ((x.title.text < y.title.text and -1) or
                                  (x.title.text > y.title.text and 1) or
                                  (x.when[0].start_time < y.when[0].start_time and -1) or
                                  (x.when[0].start_time > y.when[0].start_time and 1) or
                                  0
                                 )
                   )
        #import pdb; pdb.set_trace()
        last_event = None
        for ev in events:
            if last_event and last_event.when[0].start_time == ev.when[0].start_time:
                if last_event.title.text in ev.title.text:
                    print '... deleting ', last_event.title.text, ' at ', last_event.when[0].start_time
                    ex1.DeleteEvent(last_event.GetEditLink().href)
                    last_event = None
                elif ev.title.text in last_event.title.text or same_string(last_event.title.text, ev.title.text):
                    print '... deleting ', ev.title.text, ' at ', ev.when[0].start_time
                    ex1.DeleteEvent(ev.GetEditLink().href)
            else:
                last_event = ev
        last_info = {'date': None, 'feed': None, 'len': 0 }


def process_data():
    today = datetime.date.today()
    ex1 = google_login(username, userpass)
    r1 = KuchIterator()
    #r1 = RamIterator()
    for x in r1:
        if x['year'] < today.year:
            print 'passing over ', x['year']
            continue
        if x['year'] == today.year and x['month'] < today.month:
            print 'passing over %s-%02d' % (x['year'], x['month'])
            continue
        if x['year'] == today.year and x['month'] == today.month and x['day'] < today.day:
            print 'passing over %s-%02d-%02d' % (x['year'], x['month'], x['day'])
            continue
        if not x['what'].strip():
            print 'passing over -%s-' % (x['what'], )
            continue
        if chk_event(ex1, x):
            #print 'passing over ', x['what'], ' on ', '%s-%02d-%02d' % (x['year'], x['month'], x['day'])
            continue
        add_event(ex1, x)
        print 'adding ', x['what'], ' on ', '%s-%02d-%02d' % (x['year'], x['month'], x['day'])

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--dups':
        start_date = datetime.datetime.today().strftime('%Y-%m-%d')
        n_days = 100
        if len(sys.argv) > 2:
            start_date = sys.argv[2]
        if len(sys.argv) > 3:
            n_days = sys.argv[3]
        delete_duplicate_events(start_date, n_days)
    else:
        process_data()
