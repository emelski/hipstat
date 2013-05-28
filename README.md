hipstat
=======

hipstat, analytics for HipChat group chat logs

Usage: hipstat.py [options] < messages.json

Options:
  -h, --help            show this help message and exit
  -o FILE, --output=FILE
                        save plot to a file
  -r NAME, --report=NAME
                        report to generate (wordfreq, heatmap, speakers,
                        engagement)
  -w, --wordle          output word freq data in wordle.com format
  -u USER, --user=USER  limit analysis to a specific user


Reports:

  heatmap               Generate a heatmap showing activity over the course
                        of the day and week.
  wordfreq              Count the most commonly used words.
  speakers              Generate a time-series graph showing the percentage of
                        messages from each user.
  engagement            Plot the number of active users per day.
