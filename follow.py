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
        
        suggestions = {}
        cachedUserInfo = {}
        logging.debug("Looking up my friends")
        friends = self.cachedGetFriends()
        friends.sort(key=lambda a: a.friends_count)
        friendIds = [friend.id for friend in friends]
        logging.debug("Found %d friends"%len(friends))
        for friend in friends:
            if friend.friends_count >= 1000:
                logging.debug("%s has too many friends"%friend.screen_name)
                continue
            friendId = friend.id
            logging.debug("%s has %d friends"%(friend.screen_name, friend.friends_count))
            users = self.cachedGetFriends(user_id=friendId, count=friend.friends_count)
            logging.debug("Found %s has %d friends"%(friend.screen_name, len(users)))
            if len(users) == 0: continue
            for user in users:
                userId = user.id
                if userId in friendIds: continue
                if userId not in cachedUserInfo:
                    cachedUserInfo[userId] = user
                if userId in suggestions:
                    suggestions[userId] += 1
                else:
                    suggestions[userId] = 1
            logging.debug("Now there are %d suggestions"%len(suggestions))
        logging.debug("All done finding suggestions, now sorting")
        suggestionPairs = [(cachedUserInfo[userId], score) for userId, score in suggestions.iteritems()]
        suggestionPairs.sort(key=lambda a: a[1], reverse=True)
        suggestionPairs = suggestionPairs[:100]
        logging.debug("Done sorting, now sending response")
        self.write_response("follow.html", {"suggestions": suggestionPairs})

class GetFriendsAjaxHandler(BaseHandler):
    def get(self):
        if "user" not in self.session:
            self.response.status = 403
            self.response.write("Login required")
            return
        
        self.response.content_type = "application/json"
        
        if "id" in self.request.params:
            id = int(self.request.params["id"])
        else:
            id = None
        if "cursor" in self.request.params:
            cursor = int(self.request.params["cursor"])
        else:
            cursor = -1
        self.response.write(json.dumps(self.api.GetFriendIDs(user_id=id, cursor=cursor, count=5000)))

class GetUserAjaxHandler(BaseHandler):
    def get(self):
        if "user" not in self.session:
            self.response.status = 403
            self.response.write("Login required")
            return

        self.response.content_type = "application/json"
        
        self.response.write(json.dumps(self.api.GetUser(user_id=int(self.request.params["id"]))))

class GetTimeoutAjaxHandler(BaseHandler):
    def get(self):
        if "user" not in self.session:
            self.response.status = 403
            self.response.write("Login required")
            return

        self.response.content_type = "application/json"
        
        self.response.write(json.dumps(self.api.GetSleepTime('/friends/ids')))

app = webapp2.WSGIApplication([
    ('/follow', MainHandler),
    ('/ajax/getFriends', GetFriendsAjaxHandler),
    ('/ajax/getUser', GetUserAjaxHandler),
    ('/ajax/getTimeout', GetTimeoutAjaxHandler)
], config=config, debug=True)
