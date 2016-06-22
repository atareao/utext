#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of utext
#
# Copyright (C) 2012-2016 Lorenzo Carbonell
# lorenzo.carbonell.cerezo@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from services import GoogleService
from logindialog import LoginDialog
from urllib.parse import quote, urlencode, parse_qs
import os
import json
import io
import comun
import datetime
import dateutil
import dateutil.rrule
import time
import uuid
import dateutil
import rfc3339

OAUTH2_URL = 'https://accounts.google.com/o/oauth2/'
AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
REDIRECT_URI = 'http://localhost'
CLIENT_ID='906536899599-93lne5t3cb0keptl8fh0o8ghpmt447ls.apps.googleusercontent.com'
CLIENT_SECRET='x_QgZkRfUJ_08lWvCw4EIK3U'
SCOPE='https://www.googleapis.com/auth/calendar'
ITEMS_PER_PAGE = 10

CALENDAR_LIST_URL = 'https://www.googleapis.com/calendar/v3/users/me/calendarList'
EVENT_LIST_URL = 'https://www.googleapis.com/calendar/v3/calendars/%s/events'

FREQUENCE_SECONDLY = 'SECONDLY'
FREQUENCE_MINUTELY = 'MINUTELY'
FREQUENCE_HOURLY = 'HOURLY'
FREQUENCE_DAILY = 'DAILY'
FREQUENCE_WEEKLY = 'WEEKLY'
FREQUENCE_MONTHLY = 'MONTHLY'
FREQUENCE_YEARLY = 'YEARLY'

def add_time(minutes=0,hours=0,days=0):
	return datetime.timedelta(days,0,0,0,minutes,hours,0)

def is_Bisiesto(year):
	if year % 400 == 0:
		bisiesto = True
	elif year % 100 == 0:
		bisiesto = False
	elif year % 4 == 0:
		bisiesto = True
	else:
		bisiesto = False
	return bisiesto

def get_utc_offset(date):
	if date.year < 1970:
		# We use 1972 because 1970 doesn't have a leap day (feb 29)
		t = time.mktime(date.replace(year=1972).timetuple())
	else:
		t = time.mktime(date.timetuple())
	if time.localtime(t).tm_isdst: # pragma: no cover
		utc_offset = -time.altzone
	else:
		utc_offset = -time.timezone
	hours = abs(utc_offset) // 3600
	minutes = abs(utc_offset) % 3600 // 60
	sign = (utc_offset < 0 and '-') or '+'
	return '%c%02d:%02d' % (sign, hours, minutes)

def addOneYear(start_date):
	if start_date.month == 2 and start_date.day == 29 and is_Bisiesto(start_date.year):
		end_date = datetime.date(start_date.year+1,start_date.month+1,1)
	else:
		end_date = datetime.date(start_date.year+1,start_date.month,start_date.day)
	return end_date

class LocalTZ(datetime.tzinfo):
	"""Fixed offset in minutes east from UTC."""
	def __init__(self):
		date = datetime.datetime.now()
		if date.year < 1970:
			# We use 1972 because 1970 doesn't have a leap day (feb 29)
			t = time.mktime(date.replace(year=1972).timetuple())
		else:
			t = time.mktime(date.timetuple())
		if time.localtime(t).tm_isdst: # pragma: no cover
			utc_offset = -time.altzone
		else:
			utc_offset = -time.timezone
		minutes = abs(utc_offset) // 60
		self.__offset = datetime.timedelta(minutes = minutes)

	def utcoffset(self, dt):
		return self.__offset

	def tzname(self, dt):
		return 'Local'

	def dst(self, dt):
		return datetime.timedelta(0)


class RecurrenceRule(object):
	def __init__(self,frequence,interval = 0):
		self.frequence = frequence
		self.interval = interval
	def get_rrule(self):
		rrule = 'RRULE:FREQ=%s'%(self.frequence)
		if self.interval > 0:
			rrule += ';INTERVAL=%s'%(self.interval)
		return rrule

class Event(dict):
	def __init__(self,entry=None):
		self.set_from_entry(entry)

	def set_from_entry(self,entry):
		if entry:
			self.update(entry)

	def __str__(self):
		ans = ''
		for key in self.keys():
			ans += '%s: %s\n'%(key,self[key])
		return ans

	def _get_date(self,typeofdate):
		daybefore = datetime.datetime.now(LocalTZ())
		if 'recurrence' in self.keys():
			rset = dateutil.rrule.rruleset()
			for el in self['recurrence']:
				if el.find('DTSTART') == -1:
					if 'date' in self[typeofdate].keys():
						dtstart = self[typeofdate]['date']+'T00:00:00'+ get_utc_offset(daybefore)
						print(self[typeofdate]['date'])
					elif 'dateTime' in self[typeofdate].keys():
						dtstart = self[typeofdate]['dateTime']
						print(self[typeofdate]['dateTime'])
					print(1,dtstart)
					dtstart = rfc3339.parse_datetime(dtstart)
					print(2,dtstart)
					if el.find('UNTIL') != -1:
						elements = el.split(';')
						ans = ''
						for element in elements:
							if element.startswith('UNTIL='):
								s,e=element.split("=")
								if len(e) == 8:
									e += 'T000000'+ get_utc_offset(daybefore).replace(':','')
								elif len(e) == 17:
									e += get_utc_offset(daybefore)
								element = s+'='+e
							ans += element+';'
						if ans.endswith(';'):
							ans = ans[:-1]
						el = ans
						print(3,el)
					el = 'DTSTART:%s%s\n'%(dtstart.strftime('%Y%m%dT%H%M'),get_utc_offset(daybefore))+el
					print(el)
					try:
						rrule = dateutil.rrule.rrulestr(el)
						rset.rrule(rrule)
					except Exception as e:
						print(e)
				try:
					ans = rset.after(daybefore,inc=True)
				except Exception as e:
					print(e)
					ans = None
				if ans is not None:
					return ans
		if typeofdate in self.keys():
			if 'date' in self[typeofdate].keys():
				dtstart = self[typeofdate]['date']+'T00:00:00'+ get_utc_offset(daybefore)
				return rfc3339.parse_datetime(dtstart)
			elif 'dateTime' in self[typeofdate].keys():
				dtstart = self[typeofdate]['dateTime']
				return rfc3339.parse_datetime(dtstart)
		return None

	def get_start_date(self):
		return self._get_date('start')

	def get_end_date(self):
		return self._get_date('end')

	def get_start_date_string(self):
		adate = self.get_start_date()
		if 'date' in self['start'].keys():
			return adate.strftime('%x')
		else:
			return adate.strftime('%x')+' - '+adate.strftime('%H:%M')

	def __eq__(self,other):
		for key in self.keys():
			if key in other.keys():
				if self[key] != other[key]:
					return False
			else:
				return False
		return True

	def __ne__(self,other):
		return not self.__eq__(other)

	def __lt__(self,other):
		return self.get_start_date() < other.get_start_date()

	def __le__(self,other):
		return self.get_start_date() <= other.get_start_date()

	def __gt__(self,other):
		return self.get_start_date() > other.get_start_date()

	def __ge__(self,other):
		return self.get_start_date() >= other.get_start_date()

class Calendar(dict):
	def __init__(self,entry=None):
		self.set_from_entry(entry)
		self['events'] = {}

	def set_from_entry(self,entry):
		if entry:
			self.update(entry)

	def set_events(self,events):
		self['events'] = events

	def __str__(self):
		ans = ''
		for key in self.keys():
			ans += '%s: %s\n'%(key,self[key])
		return ans

class GoogleCalendar(GoogleService):
	def __init__(self,token_file):
		GoogleService.__init__(self,auth_url=AUTH_URL,token_url=TOKEN_URL,redirect_uri=REDIRECT_URI,scope=SCOPE,client_id=CLIENT_ID,client_secret=CLIENT_SECRET,token_file=comun.TOKEN_FILE)
		self.calendars = {}

	def read(self):
		self.calendars = self.get_calendars_and_events()

	def __do_request(self,method,url,addheaders=None,data=None,params=None,first=True):
		headers ={'Authorization':'OAuth %s'%self.access_token}
		if addheaders:
			headers.update(addheaders)
		print(headers)
		if data:
			if params:
				response = self.session.request(method,url,data=data,headers=headers,params=params)
			else:
				response = self.session.request(method,url,data=data,headers=headers)
		else:
			if params:
				response = self.session.request(method,url,headers=headers,params=params)
			else:
				response = self.session.request(method,url,headers=headers)
		print(response)
		if response.status_code == 200 or response.status_code == 201 or response.status_code == 204:
			return response
		elif (response.status_code == 401 or response.status_code == 403) and first:
			ans = self.do_refresh_authorization()
			print(ans)
			if ans:
				return self.__do_request(method,url,addheaders,data,params,first=False)
		return None

	def add_calendar(self,summary):
		url = 'https://www.googleapis.com/calendar/v3/calendars'
		data = {'kind':'calendar#calendar','summary':summary}
		body = json.dumps(data).encode('utf-8')
		addheaders={'Content-type':'application/json'}
		response = self.__do_request('POST',url,addheaders=addheaders,data = body)
		if response and response.text:
			try:
				return Calendar(json.loads(response.text))
			except Exception as e:
				print(e)
		return None

	def remove_calendar(self,calendar_id):
		url = 'https://www.googleapis.com/calendar/v3/calendars/%s'%(calendar_id)
		params = {'calendarId':calendar_id}
		response = self.__do_request('DELETE',url,params = params)
		return (response is not None)

	def remove_event(self,calendar_id,event_id):
		url = 'https://www.googleapis.com/calendar/v3/calendars/%s/events/%s'%(calendar_id,event_id)
		params = {'calendarId':calendar_id,'eventId':event_id}
		response = self.__do_request('DELETE',url,params = params)
		return (response is not None)

	def add_event(self,calendar_id,summary,start_date,end_date,description=None,reminder=False,reminder_minutes=15,rrule=None):
		url = 'https://www.googleapis.com/calendar/v3/calendars/%s/events'%(calendar_id)
		params = {'calendarId':calendar_id}
		if type(start_date) == datetime.date:
			start_value = {'date':start_date.strftime('%Y-%m-%d')}
		else:
			start_value = {'dateTime':start_date.strftime('%Y-%m-%dT%H:%M:%S')+get_utc_offset(start_date)}
		if type(end_date) == datetime.date:
			end_value = {'date':end_date.strftime('%Y-%m-%d')}
		else:
			end_value = {'dateTime':end_date.strftime('%Y-%m-%dT%H:%M:%S')+get_utc_offset(end_date)}
		data = {
			'kind':'calendar#event',
			'summary':summary,
			'start': start_value,
			'end': end_value
		}
		if description is not None:
			data['description'] = description
		if reminder:
			data['reminders'] = {
				'useDefault': False,
				'overrides': [
					{
					'method': 'email',
					'minutes': reminder_minutes
					}
				]
			}
		if rrule is not None:
			data['recurrence'] = [rrule.get_rrule()]
		body = json.dumps(data).encode('utf-8')
		addheaders={'Content-type':'application/json'}
		response = self.__do_request('POST',url,addheaders=addheaders,params = params, data = body)
		if response and response.text:
			try:
				aevent = Event(json.loads(response.text))
				aevent['calendar_id'] = calendar_id
				return aevent
			except Exception as e:
				print(e)
		return None

	def edit_event(self,calendar_id,event_id,summary,start_date,end_date,description=None,reminder=False,reminder_minutes=15,rrule=None):
		url = 'https://www.googleapis.com/calendar/v3/calendars/%s/events/%s'%(calendar_id,event_id)
		params = {'calendarId':calendar_id,'eventId':event_id}
		if type(start_date) == datetime.date:
			start_value = {'date':start_date.strftime('%Y-%m-%d')}
		else:
			start_value = {'dateTime':start_date.strftime('%Y-%m-%dT%H:%M:%S')+get_utc_offset(start_date)}
		if type(end_date) == datetime.date:
			end_value = {'date':end_date.strftime('%Y-%m-%d')}
		else:
			end_value = {'dateTime':end_date.strftime('%Y-%m-%dT%H:%M:%S')+get_utc_offset(end_date)}
		data = {
			'kind':'calendar#event',
			'summary':summary,
			'start': start_value,
			'end': end_value
		}
		if description is not None:
			data['description'] = description
		if reminder:
			data['reminders'] = {
				'useDefault': False,
				'overrides': [
					{
					'method': 'email',
					'minutes': reminder_minutes
					}
				]
			}
		if rrule is not None:
			data['recurrence'] = [rrule.get_rrule()]
		body = json.dumps(data).encode('utf-8')
		addheaders={'Content-type':'application/json'}
		response = self.__do_request('PUT',url,addheaders=addheaders,params = params, data = body)
		if response and response.text:
			try:
				aevent = Event(json.loads(response.text))
				aevent['calendar_id'] = calendar_id
				return aevent
			except Exception as e:
				print(e)
		return None

	def get_calendars_and_events(self):
		calendars = {}
		response = self.__do_request('GET',CALENDAR_LIST_URL)
		if response and response.text:
			try:
				answer = json.loads(response.text)
				if 'items' in answer.keys():
					for item in answer['items']:
						acalendar = Calendar(item)
						acalendar['events'] = self.get_events(acalendar['id'])
						calendars[acalendar['id']] = acalendar
			except:
				pass
		return calendars

	def get_calendars(self):
		calendars = {}
		response = self.__do_request('GET',CALENDAR_LIST_URL)
		if response and response.text:
			try:
				answer = json.loads(response.text)
				if 'items' in answer.keys():
					for item in answer['items']:
						acalendar = Calendar(item)
						calendars[acalendar['id']] = acalendar
			except:
				pass
		return calendars

	def get_events(self,calendar_id):
		events = {}
		params = {'calendarId':calendar_id,'maxResults':1000000}
		response = self.__do_request('GET',EVENT_LIST_URL%calendar_id,params = params)
		if response and response.text:
			try:
				answer = json.loads(response.text)
				if 'items' in answer.keys():
					for item in answer['items']:
						aevent = Event(item)
						aevent['calendar_id'] = calendar_id
						events[aevent['id']] = aevent
			except Exception as e:
				print(e)
		return events

	def backup(self):
		f = open(comun.BACKUP_FILE,'w')
		f.write(json.dumps(self.calendars))
		f.close()

	def restore(self):
		f = open(comun.BACKUP_FILE,'r')
		data = f.read()
		f.close()
		midata = json.loads(data)
		self.calendars = {}
		for key in midata.keys():
			acalendar = Calendar(midata[key])
			events = {}
			for event in midata[key]['events'].values():
				aevent = Event(event)
				events[aevent['id']] = aevent
			acalendar['events'] = events
			self.calendars[key] = acalendar

	def getNextTenEvents(self,calendar_ids):
		events = []
		lookinevents = []
		adatetime = datetime.datetime.now(LocalTZ())
		for calendar_id in calendar_ids:
			some_events = self.calendars[calendar_id]['events'].values()
			if some_events:
				lookinevents.extend(some_events)
		for event in lookinevents:
			sd = event.get_start_date()
			#print(event.get_start_date())
			if sd is not None and sd > adatetime:
				events.append({'date':sd,'event':event})
		sortedlist = sorted(events, key=lambda x: x['date'])
		ans = []
		for val in sortedlist:
			ans.append(val['event'])
			if len(ans) > 9:
				break
		print('--------------------------------------------------------')
		print(ans)
		print('--------------------------------------------------------')
		return ans

	def getAllEventsInCalendar(self,calendar):
		return calendar['events'].values()

	def getAllCalendars(self):
		return self.calendars.values()

	def getAllEvents(self):
		events = []
		for calendar in self.calendars.values():
			events.extend(calendar['events'].values())
		return events

	def getAllEventsOnMonth(self,date,calendars=[]):
		lookinevents = []
		for calendar_id in calendars:
			print([calendar_id])
			some_events = self.calendars[calendar_id]['events'].values()
			if some_events:
				lookinevents.extend(some_events)

		search = date.strftime('%Y-%m')
		firstdayofmonth = datetime.datetime(date.year,date.month,1,0,0,0)
		month = date.month + 1
		if month > 12:
			month = 1
		ldom = datetime.datetime(date.year,month,1)-datetime.timedelta(days=1)
		lastdayofmonth = datetime.datetime(date.year,date.month,ldom.day,23,59,59)
		sortedevents = {}
		iteratorday = firstdayofmonth
		while(iteratorday<=lastdayofmonth):
			sortedevents[iteratorday.date()] = []
			iteratorday += datetime.timedelta(days=1)
		for event in lookinevents:
			if 'recurrence' in event.keys():
				rset = dateutil.rrule.rruleset()
				for el in event['recurrence']:
					if el.find('DTSTART') == -1:
						if 'date' in event['start'].keys():
							dtstart = event['start']['date'].replace('-','').replace(':','')
						elif 'dateTime' in event['start'].keys():
							dtstart = event['start']['dateTime'].replace('-','').replace(':','')
						if dtstart.find('.')>-1:
							dtstart = dtstart[:dtstart.find('.')]
						if dtstart.find('+')>-1:
							dtstart = dtstart[:dtstart.find('+')]
						if dtstart.find('-')>-1:
							dtstart = dtstart[:dtstart.find('-')]
						el = 'DTSTART:%s\n'%dtstart+el
					print(event['summary'],el)
					el = el.replace('Z','')
					try:
						rrule = dateutil.rrule.rrulestr(el,ignoretz=True)
						rset.rrule(rrule)
					except Exception as e:
						print(e)
				try:
					recurrenceevents = list(rset.between(firstdayofmonth,lastdayofmonth,inc=True))
					for arecurrenceevent in recurrenceevents:
						sortedevents[arecurrenceevent.date()].append(event)
				except Exception as e:
					print(e)
			elif 'start' in event.keys() and 'date' in event['start'].keys():
				if event['start']['date'].startswith(search):
					adate = event.get_start_date().date()
					sortedevents[adate].append(event)
			elif 'start' in event.keys() and 'dateTime' in event['start'].keys():
				if event['start']['dateTime'].startswith(search):
					adate = event.get_start_date().date()
					sortedevents[adate].append(event)
		return sortedevents

if __name__ == '__main__':
	#gc = GoogleCalendar(token_file = comun.TOKEN_FILE)
	'''
	print(gc.do_refresh_authorization())
	if True and gc.access_token == None or gc.refresh_token == None:
		authorize_url = gc.get_authorize_url()
		print(authorize_url)
		ld = LoginDialog(authorize_url)
		ld.run()
		temporary_token = ld.code
		ld.destroy()
		print(temporary_token)
		#webbrowser.open(authorize_url)
		#temporary_token = input('Introduce the token: ')
		print(gc.get_authorization(temporary_token))
	'''
	'''
	for calendar in gc.get_calendars():
		print('########################################################')
		print(calendar.params['id'])
		print(calendar.params['summary'])
		for event in gc.get_events(calendar.params['id']):
			print(event.params['summary'],event.params['description'] if 'description' in event.params.keys() else '')
		#print gca.get_events(calendar['id'])
	'''
	#gc.backup()
	#gc.restore()
	#print(gc.getAllEventsOnMonth())
	'''
	gc.read_from_google_calendar()
	print(gc.calendars)
	#print(gc.getAllEventsOnMonth())
	'''
	'''
	calendar = gc.add_calendar('la prueba del cañón')
	print(calendar)
	gc.add_event(calendar['id'],'cañón',datetime.date.today(),datetime.date.today(),rrule=RecurrenceRule(frequence=FREQUENCE_MONTHLY))
	ahora = datetime.datetime.now()
	luego = ahora + add_time(minutes=50,hours=7)
	gc.add_event(calendar['id'],'prueba2',ahora,luego,True)
	mievent = gc.add_event(calendar['id'],'recurrente',ahora,luego,False)
	print(mievent)
	gc.edit_event(calendar['id'],mievent['id'],'editando',datetime.datetime.now()+add_time(hours=7),datetime.datetime.now()+add_time(hours=8))
	#gc.remove_event(calendar['id'],mievent['id'])
	#print(gc.remove_calendar(calendar['id']))
	'''
	'''
	md = '2009-10-01T11:00:00-02:00'
	md = '2009-10-01'
	print(datetime.datetime.now())
	print(get_utc_offset(datetime.datetime.now()))
	'''
	gc = GoogleCalendar(token_file = comun.TOKEN_FILE)
	#gc.read()
	#for calendar in gc.calendars.values():
	#	print(calendar['id'],calendar['summary'],calendar['etag'])
	#gc.backup()
	#gc.restore()
	adate = datetime.datetime.now()
	firstdayofmonth = datetime.datetime(adate.year,adate.month,1,0,0,0)
	month = adate.month + 1
	if month > 12:
		month = 1
	ldom = datetime.datetime(adate.year,month,1)-datetime.timedelta(days=1)
	lastdayofmonth = datetime.datetime(adate.year,adate.month,ldom.day,23,59,59)
	'''
	now = datetime.datetime.now()
	nowplus = now +datetime.timedelta(days=30)
	for event in gc.getAllEvents():
		if 'recurrence' in event.keys():
			for el in event['recurrence']:
				if el.find('DTSTART') == -1:
					if 'date' in event['start'].keys():
						dtstart = event['start']['date'].replace('-','').replace(':','')+'T000000'
					elif 'dateTime' in event['start'].keys():
						dtstart = event['start']['dateTime'].replace('-','').replace(':','')
						if dtstart.find('.')>-1:
							dtstart = dtstart[:dtstart.find('.')]
						if dtstart.find('+')>-1:
							dtstart = dtstart[:dtstart.find('+')]
						if dtstart.find('-')>-1:
							dtstart = dtstart[:dtstart.find('-')]
					el = 'DTSTART:%s\n'%dtstart+el
					if dtstart[4:6] == '12':
						print('#######################################')
						print(dtstart,event['summary'])
				arrule = dateutil.rrule.rrulestr(el)
				occurrences = arrule.between(firstdayofmonth,lastdayofmonth,True)
			#for aocurrence in occurrences:
			#	print(aocurrence,event['summary'],event['recurrence'][0])
	print(firstdayofmonth,lastdayofmonth)
	#for aevent in gc.getNextTenEvents():
	#	print(aevent['id'],aevent['summary'])
	#for event in gc.getNextTenEvents():
	#	print(event.get_start_date(),event['summary'])
	#ans = gc.getAllEventsOnMonth(datetime.datetime.now())
	#print(ans)
	for calendar in gc.getAllCalendars():
		print(calendar['id'],calendar['summary'])
	'''
	#eventos = (gc.calendars['bjb6gcqkjte62savct9odgqtk0@group.calendar.google.com']['events'].values())
	eventos = gc.get_events('bjb6gcqkjte62savct9odgqtk0@group.calendar.google.com')
	#print(eventos)
	f = open('temporal','w')
	f.write(json.dumps(eventos, sort_keys=True, indent=4))
	f.close()
	for event in eventos.values():
		if 'recurrence' in event.keys():
			for el in event['recurrence']:
				if el.find('TZID')!=-1:
					print(el)
				if el.find('DTSTART') == -1:
					if 'date' in event['start'].keys():
						dtstart = event['start']['date'].replace('-','').replace(':','')+'T000000'
					elif 'dateTime' in event['start'].keys():
						dtstart = event['start']['dateTime'].replace('-','').replace(':','')
						if dtstart.find('.')>-1:
							dtstart = dtstart[:dtstart.find('.')]
						if dtstart.find('+')>-1:
							dtstart = dtstart[:dtstart.find('+')]
						if dtstart.find('-')>-1:
							dtstart = dtstart[:dtstart.find('-')]
					el = 'DTSTART:%s\n'%dtstart+el
				arrule = dateutil.rrule.rrulestr(el)
				occurrences = arrule.between(firstdayofmonth,lastdayofmonth,True)
	print(firstdayofmonth,lastdayofmonth)
	exit(0)
