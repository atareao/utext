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


import requests
import codecs
import json
import os
from urllib.parse import quote, unquote
from urllib.parse import urlencode
import random
import time
from logindialog import LoginDialog
import mimetypes
import io
import comun

OAUTH2_URL = 'https://accounts.google.com/o/oauth2/'
AUTH_URL = 'https://accounts.google.com/o/oauth2/auth'
TOKEN_URL = 'https://accounts.google.com/o/oauth2/token'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
REDIRECT_URI = 'http://localhost'
CLIENT_ID = \
    '504881553270-d8hv211u6gpthd1nrd6sgj3s57genjpt.apps.googleusercontent.com'
CLIENT_SECRET = 'YpgNcrHnECuPnJ9O0goot9Lv'
SCOPE = 'https://www.googleapis.com/auth/drive.file'
MAIN_URL = 'https://www.googleapis.com/'
GET_FILES_URL = MAIN_URL + 'drive/v3/files'
DELETE_URL = MAIN_URL + 'drive/v3/files/%s'
GET_URL = MAIN_URL + 'drive/v3/files/%s'
UPDATE_URL = MAIN_URL + 'upload/drive/v3/files/%s'
UPLOADURL = MAIN_URL + 'upload/drive/v3/files'


class GoogleService(object):

    def __init__(self, auth_url, token_url, redirect_uri, scope, client_id,
                 client_secret, token_file):
        self.session = requests.session()
        self.auth_url = auth_url
        self.token_url = token_url
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_file = token_file
        self.access_token = None
        self.refresh_token = None
        if os.path.exists(token_file):
            f = open(token_file, 'r')
            text = f.read()
            f.close()
            try:
                data = json.loads(text)
                self.access_token = data['access_token']
                self.refresh_token = data['refresh_token']
            except Exception as e:
                print('Error')
                print(e)

    def get_authorize_url(self):
        oauth_params = {'redirect_uri': self.redirect_uri,
                        'client_id': self.client_id,
                        'scope': self.scope,
                        'response_type': 'code'}
        authorize_url = "%s?%s" % (self.auth_url, urlencode(oauth_params))
        print('Authorization url: %s' % authorize_url)
        return authorize_url

    def get_authorization(self, temporary_token):
        data = {'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': temporary_token,
                'grant_type': 'authorization_code',
                'scope': self.scope}
        response = self.session.request('POST', self.token_url, data=data)
        if response.status_code == 200:
            ans = json.loads(response.text)
            self.access_token = ans['access_token']
            self.refresh_token = ans['refresh_token']
            f = open(self.token_file, 'w')
            f.write(json.dumps({'access_token': self.access_token,
                                'refresh_token': self.refresh_token}))
            f.close()
            print('Authorizate')
            return self.access_token, self.refresh_token
        return None

    def do_revoke_authorization(self):
        self.access_token = None
        self.refresh_token = None
        if os.path.exists(self.token_file):
            os.remove(self.token_file)

    def do_refresh_authorization(self):
        data = {'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'}
        response = self.session.request('POST', self.token_url, data=data)
        if response.status_code == 200:
            ans = json.loads(response.text)
            self.access_token = ans['access_token']
            f = open(self.token_file, 'w')
            f.write(json.dumps({'access_token': self.access_token,
                                'refresh_token': self.refresh_token}))
            f.close()
            print('Refresh Authorization')
            return self.access_token
        return None

    def do_request(self, method, url, addheaders, data=None, params=None,
                   first=True):
        headers = {'Authorization': 'OAuth %s' % self.access_token}
        if addheaders:
            headers.update(addheaders)
        print(headers)
        if data:
            if params:
                response = self.session.request(
                    method, url, data=data, headers=headers, params=params)
            else:
                response = self.session.request(
                    method, url, data=data, headers=headers)
        else:
            if params:
                response = self.session.request(
                    method, url, headers=headers, params=params)
            else:
                response = self.session.request(
                    method, url, headers=headers)
        print(response)
        if response.status_code == 200:
            return response
        elif response.status_code == 403 and first:
            ans = self.do_refresh_authorization()
            print(ans)
            if ans:
                return self.do_request(
                    method, url, addheaders, first=False)
        return None


class DriveService(GoogleService):

    def __init__(self, token_file):
        GoogleService.__init__(self, auth_url=AUTH_URL, token_url=TOKEN_URL,
                               redirect_uri=REDIRECT_URI,
                               scope=SCOPE, client_id=CLIENT_ID,
                               client_secret=CLIENT_SECRET,
                               token_file=comun.TOKEN_FILE_DRIVE)
        self.calendars = {}

    def read(self):
        self.calendars = self.get_calendars_and_events()

    def __do_request(self, method, url, addheaders=None, data=None,
                     params=None, first=True):
        headers = {'Authorization': 'OAuth %s' % self.access_token}
        if addheaders:
            headers.update(addheaders)
        print(headers)
        if data:
            if params:
                response = self.session.request(
                    method, url, data=data, headers=headers, params=params)
            else:
                response = self.session.request(
                    method, url, data=data, headers=headers)
        else:
            if params:
                response = self.session.request(
                    method, url, headers=headers, params=params)
            else:
                response = self.session.request(
                    method, url, headers=headers)
        print(response)
        if response.status_code == 200 or response.status_code == 201 or\
                response.status_code == 204:
            return response
        elif (response.status_code == 401 or response.status_code == 403) and\
                first:
            ans = self.do_refresh_authorization()
            print(ans)
            if ans:
                return self.__do_request(
                    method, url, addheaders, data, params, first=False)
        return None

    def get_files(self):
        ans = self.__do_request('GET', GET_FILES_URL)
        if ans and ans.status_code == 200:
            return json.loads(ans.text)
        return None

    def delete_file(self, fileId):
        ans = self.__do_request('DELETE', DELETE_URL % fileId)
        if ans and ans.status_code == 200:
            return json.loads(ans.text)
        return None

    def get_file(self, fileId):
        params = {}
        params['alt'] = 'media'
        params['fields'] = 'name,originalFilename'
        ans = self.__do_request('GET', GET_URL % fileId, params=params)
        if ans and ans.status_code == 200:
            return ans.text
        return None

    def update_file(self, fileId, filename, content):
        params = {}
        params['uploadType'] = 'multipart'
        data = '''
--foo_bar_baz
Content-Type: application/json; charset=UTF-8

{
  "name": "%s"
}

--foo_bar_baz
Content-Type: text/markdown; charset=UTF-8

%s
--foo_bar_baz--
''' % (filename, content)
        addheaders = {
            'Content-type': 'multipart/related; boundary=foo_bar_baz',
            'Content-length': str(len(data)),
            'MIME-version': '1.0'}
        ans = self.__do_request('PATCH', UPDATE_URL % fileId,
                                addheaders=addheaders,
                                params=params, data=data)
        if ans is not None and ans.status_code == 200:
            return json.loads(ans.text)
        return None

    def put_file(self, filename, content):
        params = {}
        params['uploadType'] = 'multipart'
        data = '''
--foo_bar_baz
Content-Type: application/json; charset=UTF-8

{
  "name": "%s"
}

--foo_bar_baz
Content-Type: text/markdown; charset=UTF-8

%s
--foo_bar_baz--
''' % (filename, content)
        addheaders = {
            'Content-type': 'multipart/related; boundary=foo_bar_baz',
            'Content-length': str(len(data)),
            'MIME-version': '1.0'}
        ans = self.__do_request('POST', UPLOADURL, addheaders=addheaders,
                                params=params, data=data)
        if ans is not None and ans.status_code == 200:
            return json.loads(ans.text)
        return None


if __name__ == '__main__':
    from pprint import pprint
    ds = DriveService(comun.TOKEN_FILE_DRIVE)
    if os.path.exists(comun.TOKEN_FILE_DRIVE):
        # print(ds.put_file('/home/atareao/Escritorio/remarkable2.md'))
        # pprint(ds.get_files())
        # pprint(ds.put_file('/home/lorenzo/CloudStation/Articulos/201305/20130512.md'))
        #pprint(ds.put_file('esto_es_una_prueba', 'Esto es una prueba de funcionamiento'))
        files = ds.get_files()
        pprint(files)
        for afile in ds.get_files():
            pprint(afile)
        pprint(ds.get_file('0B3WiYW6nOxJDdVNRNERlcmRwanM'))
        pprint(ds.update_file('0B3WiYW6nOxJDdVNRNERlcmRwanM','20130512.md', 'jejejjejej'))
        '''
        afilee = codecs.open('/home/lorenzo/CloudStation/Articulos/201305/20130512.md', 'r', 'utf-8')
        data = afilee.read()
        afilee.close()
        pprint(ds.put_file('otra_prueba', data))
        '''
        ans = ds.put_file(
            'esto_es_una_prueba', 'Esto es una prueba de funcionamiento')
        pprint(ans)
    else:
        print('======================= 1 =============================')
        authorize_url = ds.get_authorize_url()
        ld = LoginDialog(1024, 600, authorize_url, isgoogle=True)
        ld.run()
        temp_oauth_token = ld.code
        uid = ld.uid
        ld.destroy()
        if temp_oauth_token is not None:
            print(ds.get_authorization(temp_oauth_token))

    '''
    print(ds.get_account_info())
    print(ds.get_file('data'))
    print(ds.put_file('/home/atareao/Escritorio/data'))
    '''
    exit(0)
