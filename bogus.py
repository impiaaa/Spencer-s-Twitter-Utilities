#!/usr/bin/env python

import webapp2
import logging
from base import BaseHandler, config
import json
from twitter import TwitterError

class MainHandler(BaseHandler):
    def get(self):
        if "user" not in self.session:
            self.do_error("Login required", 403)
            return

        logging.debug("Looking up my friends")
        friendIds = set(self.cachedGetFriendIds())
        logging.debug("Found %d friends"%len(friendIds))
        
        logging.debug("Looking up my followers")
        followers = self.api.GetFollowers()
        followerIds = [follower.id for follower in followers]
        logging.debug("Found %d followers"%len(followers))
        
        bogusFollowers = []
        
        for follower in followers:
            if follower.friends_count >= 5000:
                logging.debug("%s has too many friends"%follower.screen_name)
                continue
            logging.debug("%s has %d friends"%(follower.screen_name, follower.friends_count))
            followerFriendIds = set(self.cachedGetFriendIds(user_id=follower.id, count=follower.friends_count))
            logging.debug("Found %s has %d friends"%(follower.screen_name, len(followerFriendIds)))
            bogusFollowers.append((follower, len(friendIds.intersection(followerFriendIds))))
        
        bogusFollowers.sort(key=lambda a: a[1])
        
        self.write_response("bogus.html", {"bogusFollowers": bogusFollowers})

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
