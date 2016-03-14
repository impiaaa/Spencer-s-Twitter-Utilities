#!/usr/bin/env python

import webapp2
import logging
from base import *

class MainHandler(BaseHandler):
    def get(self):
        logging.debug("Test")
        self.write_response("index.html")

from requests_oauthlib import OAuth1Session

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'

class LoginHandler(BaseHandler):
    def get(self):
        if "denied" in self.request.params:
            # client denied access
            self.response.status = 302
            self.response.location = "/"
        elif "oauth_token" in self.request.GET or "oauth_verifier" in self.request.GET:
            # client redirected after logging in
            self.do_verify()
        else:
            # client clicked "log in"
            self.do_login()
    
    def do_login(self):
        oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret, callback_uri=self.request.host_url+'/login')
        try:
            resp = oauth_client.fetch_request_token(REQUEST_TOKEN_URL)
        except ValueError, e:
            self.do_error('Invalid response from Twitter requesting temp token: %s' % e)
            return
        self.response.location = oauth_client.authorization_url(SIGNIN_URL)
        self.response.status = 302
        self.session["oauth_token"] = resp.get('oauth_token')
        self.session["oauth_token_secret"] = resp.get('oauth_token_secret')
    
    def do_verify(self):
        if "oauth_token" not in self.request.GET:
            self.do_error("Invalid response from Twitter: No OAuth token")
            return
        if "oauth_verifier" not in self.request.GET:
            self.do_error("Invalid response from Twitter: No OAuth verifier")
            return
        if self.session["oauth_token"] != self.request.GET["oauth_token"]:
            self.do_error('Invalid OAuth token: %s' % self.request.GET["oauth_token"])
            return
        oauth_client = OAuth1Session(consumer_key, client_secret=consumer_secret,
                                 resource_owner_key=self.session["oauth_token"],
                                 resource_owner_secret=self.session["oauth_token_secret"],
                                 verifier=self.request.GET["oauth_verifier"]
        )
        try:
            resp = oauth_client.fetch_access_token(ACCESS_TOKEN_URL)
        except ValueError, e:
            self.do_error('Invalid response from Twitter requesting access token: %s' % e)
            return
        self.session["oauth_token"] = resp.get('oauth_token')
        self.session["oauth_token_secret"] = resp.get('oauth_token_secret')
        try:
            self.session["user"] = self.api.VerifyCredentials()
        except ValueError, e:
            self.do_error("Error verifying Twitter login: %s"%e)
            return
        self.response.status = 302
        self.response.location = "/"
    
class LogoutHandler(BaseHandler):
    def get(self):
        if "oauth_token" in self.session: del self.session["oauth_token"]
        if "oauth_token_secret" in self.session: del self.session["oauth_token_secret"]
        if "user" in self.session: del self.session["user"]
        self.response.status = 302
        self.response.location = "/"

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/login', LoginHandler),
    ('/logout', LogoutHandler)
], config=config)
