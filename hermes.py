# This script will generate a CSV showing the timestamps for when a pull
# request was opened, when it was first commented on, and when it was closed.
#
# A future TODO: comments may not be the best end game here.  Giving something
# a label or assigning it could happen without any comment and wouldn't show up
# here.
#
# If you want to re-get all the results, just delete the .cache file in this
# directory
#
# To Use:
#  pip install pygithub3
#  ./hermes.py
#
# This script expects the following environment variables to be set:
#  GH_USERNAME:     The username that is doing the queries and is associated with
#                   the API token.
#  GH_TOKEN:        The API token.
#  GH_REPO:         The name of the repository for the code.
#  GH_ORGANIZATION: The name of the organization which owns the code.
#
# For https://github.com/mozilla/testpilot my GH_REPO is "testpilot" and my
# GH_ORGANIZATION is "mozilla"
#
# Questions? find clouserw on irc.mozilla.org

import os
import shelve

from pygithub3 import Github

gh = Github(login=os.environ['GH_USERNAME'], token=os.environ['GH_TOKEN'])

# As far as I know, you have to set these for each service.  See
# http://pygithub3.readthedocs.io/en/latest/repos.html#config-precedence for
# what seems like an incomplete explanation.
gh.issues.comments.set_repo(os.environ['GH_REPO'])
gh.issues.comments.set_user(os.environ['GH_ORGANIZATION'])
gh.pull_requests.set_repo(os.environ['GH_REPO'])
gh.pull_requests.set_user(os.environ['GH_ORGANIZATION'])
gh.pull_requests.comments.set_repo(os.environ['GH_REPO'])
gh.pull_requests.comments.set_user(os.environ['GH_ORGANIZATION'])

prs = gh.pull_requests.list(state='closed').all()

# This doesn't populate until after you do a query
#print "Remaining API Requests: %s" % gh.remaining_requests

cache = shelve.open('hermes.cache')

bucket = {}

for i in prs:

    _cache_key = "pr_%s" % i.number
    bucket[i.number] = {}

    try:
        bucket[i.number] = cache[_cache_key]
    except KeyError:

        bucket[i.number]['created_at'] = i.created_at
        bucket[i.number]['merged_at']  = i.closed_at or '' # otherwise it's None

        # It turns out comments on a pull request are different than comments
        # on an issue, but loading a pull request in the GitHub website UI
        # allows you to comment on the pull-request-as-an-issue in addition to
        # pull-request-as-a-pull-request.  So, we actually need to check the
        # Issues service for comments as well, and merge the two lists
        # together.
        comments = (gh.pull_requests.comments.list(number=i.number).all() +
                    gh.issues.comments.list(number=i.number).all())

        bucket[i.number]['total_comments'] = len(comments)

        if len(comments) > 0:
            comments.sort(key=lambda r: r.created_at)
            bucket[i.number]['first_comment_created_at'] = comments[0].created_at
        else:
            bucket[i.number]['first_comment_created_at'] = ''

        cache[_cache_key] = bucket[i.number]

cache.sync()
cache.close()

print "number, created_at, first_comment_created_at, merged_at"
for number, data in bucket.items():
    print "%s, %s, %s, %s" % (number,
                              data['created_at'],
                              data['first_comment_created_at'],
                              data['merged_at'])

