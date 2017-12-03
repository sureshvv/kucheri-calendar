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
import httplib2
import Levenshtein
from argparse import Namespace
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client import tools
from oauth2client.client import OAuth2WebServerFlow
from google_pw import MY_CLIENT_ID, MY_CLIENT_SECRET, MY_CALENDAR_NAME 

SCOPE = 'https://www.googleapis.com/auth/calendar'

from kucheris import KuchIterator
from ramsabode import RamIterator
from bvb import BVBIterator

#CALENDAR_NAME = 'admin@rasikas.org'

def google_login():
    flags = Namespace(auth_host_name='localhost', auth_host_port=[8080, 8090],
                      logging_level='ERROR', noauth_local_webserver=False)
    flow = OAuth2WebServerFlow(MY_CLIENT_ID, MY_CLIENT_SECRET, SCOPE)
    storage = Storage('credentials.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, flags)
    http = httplib2.Http()
    http = credentials.authorize(http)
    service = build('calendar', 'v3', http=http)
    return service

init_last_info = {'date': None, 'feed': None, 'len': 0 }
last_info = init_last_info.copy()

def ignore_dot(str1):
    pos1 = str1.find(' at ')
    if pos1 != -1:
        str1 = str1[:pos1]
    str1 = str1.strip(', ')
    str1 = str1.replace('Dr', '')
    str1 = str1.replace('Sri', '')
    str1 = str1.replace('Smt', '')
    str1 = str1.replace('Ms', '')
    str1 = str1.replace('Vidwan', '')
    str1 = str1.replace('Carnatic', '')
    str1 = str1.replace('.', '')
    str1  = str1.replace('&amp;', '&')
    str1  = str1.replace('&#8217;', "'")
    str1 = str1.replace('(', '')
    str1 = str1.replace(')', '')
    return str1.strip()

def same_location(str1, str2):
    if str2 == 'BVB' and 'Bharatiya Vidya Bhavan' in str1:
        return True
    if str1 == 'BVB' and 'Bharatiya Vidya Bhavan' in str2:
        return True
    return same_string(str1, str2)

def same_string(str1, str2):
    if not str1 or not str2:
        return True
    str1 = str1.encode('utf-8') if type(str1) == type(u'a') else str1
    str2 = str2.encode('utf-8') if type(str2) == type(u'a') else str2
    #print '++++', str1, str2
    str1 = str1.lower()
    str2 = str2.lower()
    str1  = ignore_dot(str1)
    str2  = ignore_dot(str2)
    if len(str1) > len(str2):
        str1, str2 = str2, str1
    str2 = str2[:len(str1)]
    if str1 in str2 or str2 in str1:
        return True
    ratio = Levenshtein.ratio(str1, str2)
    return ratio >= 0.85

def same_time(time1, time2):
    pos1 = time1.find('+')
    pos2 = time2.find('+')
    if pos1 == -1 or pos2 == -1:
        return False
    dt1 = time1[:pos1]
    dt2 = time2[:pos2]
    dt1 = datetime.datetime.strptime(dt1, "%Y-%m-%dT%H:%M:%S")
    dt2 = datetime.datetime.strptime(dt2, "%Y-%m-%dT%H:%M:%S")
    diff1 = dt1 - dt2
    diff1 = abs(diff1.total_seconds())
    return diff1 < 1701

def chk_event(service, event, calendar_id=MY_CALENDAR_NAME):
    global last_info
    new_date = '%d-%02d-%02d' % (event['year'], event['month'], event['day'])
    if last_info['date'] != new_date:
        last_info['events'] = []
        last_info['date'] = new_date
        st1 = datetime.date(event['year'], event['month'], event['day']) - datetime.timedelta(hours=6)
        start_min = '%d-%02d-%02dT00:00:00+05:30' % (st1.year, st1.month, st1.day)
        st1 = datetime.date(event['year'], event['month'], event['day']) + datetime.timedelta(days=1)
        start_max = '%d-%02d-%02dT00:00:00+05:30' % (st1.year, st1.month, st1.day)
        request = service.events().list(calendarId=calendar_id,
            timeMax=start_max, timeMin=start_min)
        while request != None:
            # Get the next page.
            response = request.execute()
            # Accessing the response like a dict object with an 'items' key
            # returns a list of item objects (events).
            for an_event in response.get('items', []):
                # The event object is a dict object with a 'summary' key.
                if an_event.get('summary', ''):
                    last_info['events'].append(an_event)
            # Get the next request object by passing the previous request object to
            # the list_next method.
            request = service.events().list_next(request, response)
    matches = []
    for an_event in last_info['events']:
        if event.get('what','') and \
           same_string(an_event.get('summary'), event['what']) and \
           same_time(an_event.get('start').get('dateTime'),
               '%d-%02d-%02dT%02d:%02d:00+' % (event['year'],
                event['month'], event['day'], event['hour'], event['min'])):
           matches.append(an_event)
    return matches

def add_event(service, event):
    st1 = "%d-%02d-%02dT%02d:%02d:00.000+05:30" % (event['year'], event['month'],
        event['day'], event['hour'], event['min'])
    st2 = "%d-%02d-%02dT%02d:%02d:00.000+05:30" % (event['year'], event['month'],
        event['day'], event['hour']+1, event['min'])
    event = {
              'summary': event['what'],
              'location': event['where'],
              'start': { 'dateTime': st1, },
              'end': { 'dateTime': st2, },
              'description': event['content'],
          }

    new_event = service.events().insert(calendarId=MY_CALENDAR_NAME, body=event).execute()
    return new_event

def delete_primary_events(start_date, n_days):
    global last_info
    ex1 = google_login()
    start1 = start_date.split('-')
    start_year = int(start1[0])
    start_month = int(start1[1])
    start_day = int(start1[2])
    count = 0
    for cnt in range(int(n_days)):
        st1 = datetime.date(start_year, start_month, start_day) + datetime.timedelta(days=cnt)
        event = {'day': st1.day, 'month': st1.month, 'year': st1.year }
        print 'processing ', event['year'], event['month'], event['day']
        chk_event(ex1, event, 'primary')
        events = list(last_info['events'])
        for ev in events:
            if ev['description'].startswith('kutcheris '):
                ex1.events().delete(calendarId='primary', eventId=ev['id']).execute()
                count += 1
    last_info.update(init_last_info)
    print 'deleted ', count

def delete_duplicate_events(start_date, n_days):
    global last_info
    ex1 = google_login()
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
        event = {'day': st1.day, 'month': st1.month, 'year': st1.year }
        print 'processing ', event['year'], event['month'], event['day']
        chk_event(ex1, event)
        events = last_info['events']
        events.sort(lambda x, y: (
                                  (x['start']['dateTime'] < y['start']['dateTime'] and -1) or
                                  (x['start']['dateTime'] > y['start']['dateTime'] and 1) or
                                  (ignore_dot(x['summary']) < ignore_dot(y['summary']) and -1) or
                                  (ignore_dot(x['summary']) > ignore_dot(y['summary']) and 1) or
                                  0
                                 )
                   )
        last_event = None
        #import pdb; pdb.set_trace()
        for ev in events:
            if not last_event:
                last_event = ev
                continue
            if same_time(last_event['start']['dateTime'], ev['start']['dateTime']) and \
               same_location(last_event['location'], ev['location']):
                if ignore_dot(last_event['summary']) in ignore_dot(ev['summary']) or \
                       ignore_dot(ev['summary']) in ignore_dot(last_event['summary']) or \
                       same_string(last_event['summary'], ev['summary']):
                    last_event_updated = last_event['description'] and last_event['description'].split()[1:]
                    ev_updated = ev['description'] and ev['description'].split()[1:]
                    if not last_event_updated or \
                       (ev_updated and last_event_updated < ev_updated):
                        print '... deleting ', last_event['summary'], ' at ', last_event['start']['dateTime']
                        ex1.events().delete(calendarId=MY_CALENDAR_NAME, eventId=last_event['id']).execute()
                        last_event = ev
                    else:
                        print '... deleting ', ev['summary'], ' at ', ev['start']['dateTime']
                        ex1.events().delete(calendarId=MY_CALENDAR_NAME, eventId=ev['id']).execute()
                else:
                    last_event = ev
            else:
                last_event = ev
        last_info = {'date': None, 'events': []}

def adjust_end_time(start_date, n_days, del_overlap):
    global last_info
    ex1 = google_login()
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
        event = {'day': st1.day, 'month': st1.month, 'year': st1.year }
        #print 'processing ', event['year'], event['month'], event['day']
        chk_event(ex1, event)
        events = last_info['events']
        events = [ e for e in events if e['location'] ]
        events.sort(lambda x, y: (
                                  (x['location'].strip() < y['location'].strip() and -1) or
                                  (x['location'].strip() > y['location'].strip() and 1) or
                                  (x['location'] < y['location'] and -1) or
                                  (x['location'] > y['location'] and 1) or
                                  0
                                 )
                   )
        last_event = None
        #import pdb; pdb.set_trace()
        for ev in events:
            if not last_event:
                last_event = ev
                continue
            if last_event['location'] == ev['location']:
                if same_time(last_event['start']['dateTime'], ev['start']['dateTime']):
                    if del_overlap:
                        last_event_updated = last_event['summary'] and last_event['summary'].split()[1:]
                        ev_updated = ev['summary'] and ev['summary'].split()[1:]
                        if not last_event_updated or \
                           (ev_updated and last_event_updated < ev_updated):
                            print '... deleting ', last_event.title.text, ' at ', last_event.when[0].start_time
                            ex1.DeleteEvent(last_event.GetEditLink().href)
                            last_event = ev
                        else:
                            print '... deleting ', ev.title.text, ' at ', ev.when[0].start_time
                            ex1.DeleteEvent(ev.GetEditLink().href)
                    else:
                        print "Possible Overlap at ", last_event.where[0].value_string, last_event.when[0].start_time
                        print "    ", last_event.title.text, "\n    ", ev.title.text
                elif last_event['start']['dateTime'] > ev['start']['dateTime']:
                    if ev['start']['dateTime'] > last_event['start']['dateTime']:
                       last_event['start']['dateTime'] = ev['start']['dateTime']
                       ex1.UpdateEvent(last_event.GetEditLink().href, last_event)
                       print "Updated:", last_event['start']['dateTime'], last_event['start']['dateTime'], last_event['start']['dateTime']
                    else:
                        import pdb; pdb.set_trace()
                        print "++++ Possible SCREWUP at ", last_event.where[0].value_string, last_event.when[0].start_time
                        print "    ", last_event.title.text, "\n    ", ev.title.text
                        return
            last_event = ev
        last_info = {'date': None, 'feed': None, 'len': 0 }



def process_data(max_events):
    today = datetime.date.today()
    ex1 = google_login()
    r1 = RamIterator()
    # r1 = KuchIterator()
    # r1 = BVBIterator()
    added = 0
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
        #import pdb; pdb.set_trace()
        if not x['what'].strip():
            print 'passing over ----', x['what'], '---- on ', '%s-%02d-%02d %02d:%02d at %s' % (x['year'], x['month'], x['day'], x['hour'], x['min'], x['where'])
            continue
        if chk_event(ex1, x):
            #print 'passing over ', x['what'], ' on ', '%s-%02d-%02d' % (x['year'], x['month'], x['day'])
            continue
        add_event(ex1, x)
        print 'adding ', x['what'], ' on ', '%s-%02d-%02d' % (x['year'], x['month'], x['day'])
        added += 1
        if max_events and added >= max_events:
            break

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--adjust':
        start_date = datetime.datetime.today().strftime('%Y-%m-%d')
        n_days = 30
        if len(sys.argv) > 2:
            start_date = sys.argv[2]
        if len(sys.argv) > 3:
            n_days = sys.argv[3]
        del_overlap = False
        if len(sys.argv) > 4:
            del_overlap = sys.argv[4] == 'delete'
        adjust_end_time(start_date, n_days, del_overlap)
    elif len(sys.argv) > 1 and sys.argv[1] == '--dups':
        start_date = datetime.datetime.today().strftime('%Y-%m-%d')
        n_days = 30
        if len(sys.argv) > 2:
            start_date = sys.argv[2]
        if len(sys.argv) > 3:
            n_days = sys.argv[3]
        delete_duplicate_events(start_date, n_days)
    elif len(sys.argv) > 1 and sys.argv[1] == '--primary':
        start_date = datetime.datetime.today().strftime('%Y-%m-%d')
        n_days = 0
        #delete_primary_events(start_date, n_days)
    else:
        max_events = int(sys.argv[1]) if len(sys.argv) > 1 else 0
        process_data(max_events)
