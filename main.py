#!/usr/bin/env python

import jinja2
import webapp2
import os
import twitter
from webapp2_extras import sessions
from webapp2_extras import sessions_ndb
import logging

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class _GaeCache:  
  PYTHON_TWITTER_NAMESPACE="python-twitter-cache"

  def __init__(self,root_directory=None):
    return None

  def Get(self,key):
    return memcache.get(key=key,namespace=self.PYTHON_TWITTER_NAMESPACE)

  def Set(self,key,data):
    memcache.set(key=key,value=data,namespace=self.PYTHON_TWITTER_NAMESPACE)

  def Remove(self,key):
    memcache.delete(key=key,namespace=self.PYTHON_TWITTER_NAMESPACE)

  def GetCachedTime(self,key):
    return None

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session(factory=sessions_ndb.DatastoreSessionFactory)

class MainHandler(BaseHandler):
    def get(self):
        template_values = {}
        if "user" in self.session: template_values["user"] = self.session["user"]
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

from requests_oauthlib import OAuth1Session

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'
consumer_key = open("consumer_key").read().strip()
consumer_secret = open("consumer_secret").read().strip()

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
        api = twitter.Api(cache=_GaeCache(), consumer_key=consumer_key,
                      consumer_secret=consumer_secret,
                      access_token_key=self.session["oauth_token"],
                      access_token_secret=self.session["oauth_token_secret"])
        try:
            self.session["user"] = api.VerifyCredentials()
        except ValueError, e:
            self.do_error("Error verifying Twitter login: %s"%e)
            return
        self.response.status = 302
        self.response.location = "/"
    
    def do_error(self, message):
        self.response.status = 500
        template_values = {"message": message}
        if "user" in self.session: template_values["user"] = self.session["user"]
        template = JINJA_ENVIRONMENT.get_template('error.html')
        self.response.write(template.render(template_values))

class LogoutHandler(BaseHandler):
    def get(self):
        if "oauth_token" in self.session: del self.session["oauth_token"]
        if "oauth_token_secret" in self.session: del self.session["oauth_token_secret"]
        if "user" in self.session: del self.session["user"]
        self.response.status = 302
        self.response.location = "/"

config = {
    'webapp2_extras.sessions': {
        'secret_key': open("secret_key").read()
    }
}

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/login', LoginHandler),
    ('/logout', LogoutHandler)
], config=config, debug=True)
