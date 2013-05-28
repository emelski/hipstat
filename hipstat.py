#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2013, Eric Melski
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
# 
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import json
import sys
import dateutil.parser
import matplotlib.pyplot as plt
import matplotlib.dates  as mdates
import numpy as np
import re
import collections as co
import datetime as dt
from optparse import OptionParser

# heatmap
#
#     Summarize chatroom activity according to day-of-week and hour-of-day,
#     visualized as a heatmap where higher intensity colors indicate more
#     messages during that interval.  Returns true to indicate there is a
#     graph to show.

def heatmap():
    buckets = np.zeros((7,24))
    for msg in data["messages"]:
        localtime = ToLocaltime(msg["date"])
        buckets[localtime.weekday()][localtime.hour] += 1

    row_labels = [ "Monday", 
                   "Tuesday", 
                   "Wednesday", 
                   "Thursday", 
                   "Friday", 
                   "Saturday", 
                   "Sunday" ]
    fig = plt.figure()
    ax  = fig.add_subplot(111)
    ax.set_title('Accelerator HipChat room activity')
    cax = ax.imshow(buckets, interpolation='nearest', cmap=plt.cm.Blues)
    ax.set_yticks(np.arange(buckets.shape[0]), minor=False)
    ax.set_yticklabels(row_labels, minor=False)
    ax.set_xticks(np.arange(buckets.shape[1]), minor=False)
    cbar= fig.colorbar(cax, orientation='horizontal')
    cbar.set_label('Messages')
    plt.xlabel("Hour of day")
    return True

# engagement
#
#     Graph team "engagement" as defined by number of users with >= threshold
#     messages on a given day.  Returns true to indicate there is a graph to
#     show.

def engagement():
    buckets = {}
    for msg in data["messages"]:
        localtime = ToLocaltime(msg["date"])
        strtime   = localtime.strftime("%Y%m%d")
        user = msg["from"]["name"]
        if strtime not in buckets:
            buckets[strtime] = {}
        buckets[strtime][user] = 1

    days  = []
    count = []

    # Convert to a format that matplotlib understands -- numpy arrays, with
    # the dates as floating-point values.

    count = [len(buckets[key]) 
             for key in sorted(buckets.iterkeys())]
    days  = [mdates.strpdate2num('%Y%m%d')(key) 
             for key in sorted(buckets.iterkeys())]

    # x-axis is the months.

    x = [dt.datetime.strptime(d, '%Y%m%d').date() 
         for d in sorted(buckets.iterkeys())]
    ncount = np.array(count)
    
    plt.plot(x, ncount, color='r')

    ndays = np.array(days)
    coeffs = np.polyfit(ndays, ncount, 5)
    x2 = np.arange(min(ndays)-1, max(ndays)+1, .01)
    y2 = np.polyval(coeffs, x2)
    plt.plot(x2, y2, color='b')

    # Set labels

    plt.title("Accelerator team HipChat engagement")
    plt.ylabel("Active users")
    plt.xlabel("Month")

    # Make the x-axis display dates.

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()

    return True

# speakers
#
#     Plot the percentage of messages per speaker by month, as a stacked
#     time series.
#
#     Returns true to indicate there is a graph to show.

def speakers():
    buckets = {}
    total = co.defaultdict(int)
    users = co.defaultdict(int)
    for msg in data["messages"]:
        localtime = ToLocaltime(msg["date"])
        strtime   = localtime.strftime("%Y%m")
        user = msg["from"]["name"]
        if strtime not in buckets:
            buckets[strtime] = co.defaultdict(int)
        buckets[strtime][user] += 1
        total[strtime] += 1
        users[user] += 1

    # Sort users by *total* messages sent, which will define the plotting order
    # for the graph.  Also filter out uncommon users.

    sortedUsers = [user 
                   for user in sorted(users, key=users.get, reverse=True) 
                   if users[user] > 50]

    # Put the data in a form usable by matplotlib: an MxN array.

    points = np.zeros((len(sortedUsers), len(buckets)))
    col  = 0
    for month in sorted(buckets.iterkeys()):
        row = 0
        for user in sortedUsers:
            if user in buckets[month]:
                points[row][col] = round(100 
                                         * buckets[month][user] 
                                         / total[month])
            row += 1
        col += 1
    p2 = np.cumsum(points, axis=0)

    fig = plt.figure()
    ax = fig.add_subplot(111)

    # Setup a color palette; these come from http://colorbrewer2.org

    colors = ['#003C30', '#543005', '#01665E', '#8C510A', '#35978F',
              '#BF812D', '#80CDC1', '#DFC27D', '#C7EAE5', '#DFC27D',
              '#C7EAE5', '#F6E8C3', '#F5F5F5']
    ax.set_color_cycle(colors)

    # Constrain the y-axis; otherwise matplotlib will autoscale too big.

    plt.ylim([0,100])

    # x-axis is the months.

    x = [dt.datetime.strptime(d, '%Y%m').date() 
         for d in sorted(buckets.iterkeys())]

    # Draw the curves.  The bottom and top curves are handled specially, since
    # they have different start/end boundaries, respectively.  As we're going,
    # create some boxes to use in the legend as well -- matplotlib doesn't
    # automatically make a legend for stacked plots like this.

    # Bottom curve:

    handles = []
    color = ax._get_lines.color_cycle.next()
    ax.fill_between(x, 0, p2[0,:], facecolor=color, alpha=.8)
    handles.append(plt.Rectangle((0, 0), 1, 1, facecolor=color, alpha=.8))

    # Middle curves:

    for i in xrange(len(p2) - 1):
        color = ax._get_lines.color_cycle.next()
        ax.fill_between(x, p2[i, :], p2[i + 1, :], facecolor=color, alpha=.8)
        handles.append(plt.Rectangle((0, 0), 1, 1, facecolor=color, alpha=.8))

    # Top curve:

    color = ax._get_lines.color_cycle.next()
    ax.fill_between(x, p2[len(p2) - 1], 100, facecolor=color, alpha=.8)
    handles.append(plt.Rectangle((0, 0), 1, 1, facecolor=color, alpha=.8))

    # Set labels

    plt.title("Accelerator team HipChat contribution")
    plt.ylabel("Percentage of total messages")
    plt.xlabel("Month")

    # Make the x-axis display dates.

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.gcf().autofmt_xdate()

    # Draw the legend.  Make sure it's _outside_ the plot area.  Do this last,
    # so that the full size of the plot is known before we try to scale it.

    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(handles[::-1], 
        [user.split()[0] for user in sortedUsers+['Other']][::-1],
        loc='center left',
        bbox_to_anchor=(1, 0.5))

    plt.grid()

    return True

# wordfreq
#
#     Count the number of occurrences of each word in the message corpus,
#     then print either a summary table, or a simplified form suitable for
#     pasting in to wordle.com.  Minimal effort is made to account for
#     punctuation, so that, eg, 'hello' and 'hello,' are the same.
#
#     Returns false to indicate there is no graph to show.

def wordfreq():
    words = {}
    ignore = {}
    for msg in data["messages"]:
        for word in msg["message"].split():
            word = re.sub("&quot;", "\"", word)
            word = word.strip("?!:,.\"()*'-").lower()
            if word not in words:
                words[word] = 0
            words[word] += 1

    # Get a list of words to ignore, like "the", "and", etc.

    ignore = {}
    try:
        f = open('ignore.txt', 'r')
        for word in f:
            ignore[word.strip().lower()] = 1
        f.close()
    except:
        pass

    for key in sorted(words.iterkeys()):
        if words[key] < 100 or key in ignore:
            continue
        if options.wordle:
            print "%s " % (key) * words[key]
        else:
            print "%s %d" % (key, words[key])
    return False

def ToLocaltime(raw):
    timestamp = dateutil.parser.parse(raw)
    timestamp = timestamp.replace(tzinfo=dateutil.tz.tzutc())
    localtime = timestamp.astimezone(dateutil.tz.tzlocal())
    return localtime

def Include(msg, user, after, before):
    if user != "" and msg["from"]["name"] != user:
        return False
    
    return True
        

parser = OptionParser()
parser.add_option("-o", "--output", 
                  dest="filename", 
                  help="save plot to a file", 
                  metavar="FILE",
                  default="")
parser.add_option("-r", "--report", 
                  dest="report",
                  help="report to generate (wordfreq, heatmap, speakers, engagement)",
                  metavar="NAME", 
                  default="heatmap")
parser.add_option("-w", "--wordle", 
                  dest="wordle",
                  help="output word freq data in wordle.com format",
                  default=False, 
                  action="store_true")
parser.add_option("-u", "--user",
                  dest="user",
                  help="limit analysis to a specific user",
                  default="",
                  metavar="USER")
(options, args) = parser.parse_args()

data = json.load(sys.stdin)
if options.user != "":
    data["messages"] = [msg for msg in data["messages"] 
                        if msg["from"]["name"] == options.user]

if globals()[options.report]():
    if options.filename != "":
        plt.savefig(options.filename, bbox_inches='tight')
    else:
        plt.show()
