#!/usr/bin/env python

import jinja2
import webapp2
import os
import twitter

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class MainHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {}
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class LoginHandler(webapp2.RequestHandler):
    def get(self):
        pass
    
    def post(self):
        pass

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/login', LoginHandler)
], debug=True)
