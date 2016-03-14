import webapp2
import jinja2
from webapp2_extras import sessions
from webapp2_extras import sessions_ndb
import os
import twitter

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

consumer_key = open("consumer_key").read().strip()
consumer_secret = open("consumer_secret").read().strip()

class _GaeCache(object):  
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

    def do_error(self, message, status=500):
        self.response.status = status
        self.write_response("error.html", {"message": message})
    
    def write_response(self, template, template_values={}):
        if "user" in self.session: template_values["user"] = self.session["user"]
        template = JINJA_ENVIRONMENT.get_template(template)
        self.response.write(template.render(template_values))
    
    @webapp2.cached_property
    def api(self):
        return twitter.Api(cache=_GaeCache(), consumer_key=consumer_key,
                      consumer_secret=consumer_secret,
                      access_token_key=self.session["oauth_token"],
                      access_token_secret=self.session["oauth_token_secret"])

config = {
    'webapp2_extras.sessions': {
        'secret_key': open("secret_key").read()
    }
}
