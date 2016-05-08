#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#
# services.py
#
# Copyright (C) 2012 Lorenzo Carbonell
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
#
#
#

import requests
import json
import os
from urllib.parse import urlencode
import random
import time
from logindialog import LoginDialog
import mimetypes
import io
import comun


KEY = 'rlajhlfbdjlv7vq'
SECRET = '4hxohya6cyhvsdz'


class DropboxService(object):
    def __init__(self, token_file):
        self.session = requests.session()
        self.request_token_url = \
            'https://api.dropbox.com/1/oauth/request_token'
        self.authorize_url = 'https://www.dropbox.com/1/oauth/authorize'
        self.access_token_url = 'https://api.dropbox.com/1/oauth/access_token'
        self.key = KEY
        self.secret = SECRET
        self.token_file = token_file
        self.access_token = None
        self.refresh_token = None
        if os.path.exists(token_file):
            f = open(token_file, 'r')
            text = f.read()
            f.close()
            try:
                data = json.loads(text)
                self.oauth_token = data['oauth_token']
                self.oauth_token_secret = data['oauth_token_secret']
            except Exception as e:
                print('Error')
                print(e)

    def get_request_token(self):
        params = {}
        params['oauth_consumer_key'] = KEY
        params['oauth_timestamp'] = int(time.time())
        params['oauth_nonce'] = ''.join(
            [str(random.randint(0, 9)) for i in range(8)])
        params['oauth_version'] = '1.0'
        params['oauth_signature_method'] = 'PLAINTEXT'
        params['oauth_signature'] = '%s&' % SECRET
        response = self.session.request(
            'POST', self.request_token_url, params=params)
        if response.status_code == 200:
            oauth_token_secret, oauth_token = response.text.split('&')
            oauth_token_secret = oauth_token_secret.split('=')[1]
            self.ts = oauth_token_secret
            oauth_token = oauth_token.split('=')[1]
            return oauth_token, oauth_token_secret
        return None

    def get_authorize_url(self, oauth_token, oauth_token_secret):
        params = {}
        params['oauth_token'] = oauth_token
        params['oauth_callback'] = 'http://localhost'
        return 'https://www.dropbox.com/1/oauth/authorize?%s' %\
            (urlencode(params))

    def get_access_token(self, oauth_token, secret):
        params = {}
        params['oauth_consumer_key'] = KEY
        params['oauth_token'] = oauth_token
        params['oauth_timestamp'] = int(time.time())
        params['oauth_nonce'] = ''.join(
            [str(random.randint(0, 9)) for i in range(8)])
        params['oauth_version'] = '1.0'
        params['oauth_signature_method'] = 'PLAINTEXT'
        params['oauth_signature'] = '%s&%s' % (SECRET, secret)
        response = self.session.request(
            'POST', self.access_token_url, params=params)
        print(response, response.status_code, response.text)
        if response.status_code == 200:
            oauth_token_secret, oauth_token, uid = response.text.split('&')
            oauth_token_secret = oauth_token_secret.split('=')[1]
            oauth_token = oauth_token.split('=')[1]
            uid = uid.split('=')[1]
            self.oauth_token = oauth_token
            self.oauth_token_secret = oauth_token_secret
            f = open(self.token_file, 'w')
            f.write(json.dumps(
                {'oauth_token': oauth_token,
                 'oauth_token_secret': oauth_token_secret}))
            f.close()
            return uid, oauth_token, oauth_token_secret
        return None

    def get_account_info(self):
        ans = self.__do_request(
            'GET', 'https://api.dropbox.com/1/account/info')
        if ans.status_code == 200:
            return ans.text
        return None

    def get_files(self):
        url = 'https://api.dropbox.com/1/search/auto/'
        ans = self.__do_request('GET', url, addparams={"query": "."})
        if ans and ans.status_code == 200:
            return json.loads(ans.text)
        return None

    def get_file(self, afile):
        url = 'https://api-content.dropbox.com/1/files/auto/%s' % (afile)
        ans = self.__do_request('GET', url)
        if ans and ans.status_code == 200:
            return ans.text
        return None

    def put_file(self, afile):
        name = afile.split('/')[-1]
        print(name)
        url = 'https://api-content.dropbox.com/1/files_put/auto/%s' % (name)
        print(url)
        addparams = {}
        addparams['overwrite'] = True
        afilee = open(afile, 'rb')
        data = afilee.read()
        afilee.close()
        addheaders = {
            'Content-type': 'multipart/related;boundary="END_OF_PART"',
            'Content-length': str(len(data)),
            'MIME-version': '1.0'}
        ans = self.__do_request('POST', url, addheaders=addheaders,
                                addparams=addparams, data=data)
        if ans is not None:
            return ans.text

    def __do_request(self, method, url, addheaders=None, data=None,
                     addparams=None, first=True, files=None):
        params = {}
        params['oauth_consumer_key'] = KEY
        params['oauth_token'] = self.oauth_token
        params['oauth_timestamp'] = int(time.time())
        params['oauth_nonce'] = ''.join(
            [str(random.randint(0, 9)) for i in range(8)])
        params['oauth_version'] = '1.0'
        params['oauth_signature_method'] = 'PLAINTEXT'
        params['oauth_signature'] = '%s&%s' % (
            SECRET, self.oauth_token_secret)
        headers = None
        if headers is not None:
            headers.update(addheaders)
        else:
            headers = addheaders
        if addparams is not None:
            params.update(addparams)
        if data:
            response = self.session.request(method, url, data=data,
                                            headers=headers,
                                            params=params, files=files)
        else:
            response = self.session.request(method, url, headers=headers,
                                            params=params, files=files)
        print(response, response.status_code)
        if response.status_code == 200 or response.status_code == 201:
            return response
        elif (response.status_code == 401 or response.status_code == 403) \
                and first:
            pass
        return None

if __name__ == '__main__':
    ds = DropboxService(comun.TOKEN_FILE)
    if os.path.exists(comun.TOKEN_FILE):
        print(ds.get_account_info())
        print(ds.put_file('/home/atareao/Escritorio/remarkable2.md'))
        print(ds.get_files())
    else:
        oauth_token, oauth_token_secret = ds.get_request_token()
        authorize_url = ds.get_authorize_url(oauth_token, oauth_token_secret)
        ld = LoginDialog(1024, 600, authorize_url)
        ld.run()
        oauth_token = ld.code
        uid = ld.uid
        ld.destroy()
        if oauth_token is not None:
            print(oauth_token, uid)
            ans = ds.get_access_token(oauth_token, oauth_token_secret)
            print(ans)
            print(ds.get_account_info())

    '''
    print(ds.get_account_info())
    print(ds.get_file('data'))
    print(ds.put_file('/home/atareao/Escritorio/data'))
    '''
    exit(0)
