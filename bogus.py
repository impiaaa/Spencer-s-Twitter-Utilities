#!/usr/bin/env python

import webapp2
import logging
from base import BaseHandler, config
import json
import time
from twitter import TwitterError

class MainHandler(BaseHandler):
    def get(self):
        if "user" not in self.session:
            self.do_error("Login required", 403)
            return

        self.write_response("follow.html", {"suggestions": suggestionPairs})

class BlockAjaxHandler(BaseHandler):
    def post(self):
        if "user" not in self.session:
            self.response.status = 403
            self.response.write("Login required")
            return
        
        if "id" not in self.request.post:
            self.response.status = 400
            self.response.write("ID required")
            return
        
        self.response.write(json.dumps(api.CreateBlock(int(self.request.post["id"]))))

app = webapp2.WSGIApplication([
    ('/bogus', MainHandler),
    ('/ajax/block', BlockAjaxHandler)
], config=config, debug=True)
