import logging
import logging.config
import os
import re
import time

import praw

from modules.cpubot import CPUbot
from modules.gpubot import GPUbot
from modules.helperbot import Helperbot
from modules.wikibot import Wikibot

# Logging allows replacing print statements to show more information
# This config outputs human-readable time, the log level, the log message and the line number this originated from
logging.basicConfig(
    format='%(asctime)s (%(levelname)s) %(message)s (Line %(lineno)d)', level=logging.INFO)

# PRAW seems to have its own logging which clutters up console output, so this disables everything but Python's logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True
})


github_link = 'https://github.com/Pixxel123/PCSX2-Helper-Bot'
latest_build = 'https://buildbot.orphis.net/pcsx2/'
summon_phrase = {'wiki': 'WikiBot!', 'cpu': 'CPUBot!',
                 'gpu': 'GPUBot!', 'help': 'HelperBot!'}


def bot_login():
    logging.info('Authenticating...')
    reddit = praw.Reddit(
        client_id=os.getenv('reddit_client_id'),
        client_secret=os.getenv('reddit_client_secret'),
        password=os.getenv('reddit_password'),
        user_agent=os.getenv('reddit_user_agent'),
        username=os.getenv('reddit_username'))
    logging.info(f"Authenticated as {reddit.user.me()}")
    return reddit


def generate_bot_message(comment, bot_reply, phrase, bot_choice):
    # negative lookahead prevents other bot commands from being caught in the search term
    # use list comprehension in case commands get expanded in future
    search_term = re.search(
        fr"({phrase})\s([^!?\n\r]((?!{'|'.join(command for command in summon_phrase.values())}).)*)", comment.body, re.IGNORECASE)
    search_term = search_term.group(2)
    search_options = []
    # allows looking up of multiple items by the user
    for search in search_term.split(', '):
        bot_reply = bot_choice.bot_message(search.strip())
        search_options.append(bot_reply)
    # line break and separator added for visual clarity
    bot_reply = '\n\n---\n\n'.join(search_options)
    return bot_reply


def run_bot():
    try:
        logging.info(
            f"Bot started! Watching comment stream in r/{subreddit}...")
        # look for summon_phrase and reply
        for comment in subreddit.stream.comments(skip_existing=True):
            # allows bot command to NOT be case-sensitive and ignores comments made by the bot
            if comment.author.name != reddit.user.me() and not comment.saved:
                try:
                    bot_reply = ''
                    if summon_phrase['cpu'].lower() in comment.body.lower():
                        bot_reply += generate_bot_message(
                            comment, bot_reply, summon_phrase['cpu'], cpubot)
                    if summon_phrase['gpu'].lower() in comment.body.lower():
                        bot_reply += generate_bot_message(
                            comment, bot_reply, summon_phrase['gpu'], gpubot)
                    if summon_phrase['wiki'].lower() in comment.body.lower():
                        bot_reply += generate_bot_message(
                            comment, bot_reply, summon_phrase['wiki'], wikibot)
                    if summon_phrase['help'].lower() in comment.body.lower():
                        bot_reply += generate_bot_message(
                            comment, bot_reply, summon_phrase['help'], helperbot)
                    # only appends footer if bot_reply has a value to prevent triggering on comments where bot isn't called.
                    if bot_reply:
                        # Appends user approximation warning and buildbot link to avoid repetition on multiple queries
                        cpu_comment_indicator = 'CPU STR'
                        gpu_comment_indicator = 'GPU G3D Mark'
                        if cpu_comment_indicator in bot_reply or gpu_comment_indicator in bot_reply:
                            bot_reply += '\n\n**These ratings should only be used as a rough guide as some games are unusually demanding.**'
                            bot_reply += f"\n\nThe latest dev version of PCSX2 can be found [HERE]({latest_build})"
                        footer = f"\n\n---\n\n^(Check my commands by commenting `HelperBot! commands`. I'm a bot, and should only be used for reference. If there are any issues, please contact my) ^[Creator](https://www.reddit.com/message/compose/?to=theoriginal123123&subject=/u/PCSX2-Wiki-Bot)\n\n[^GitHub]({github_link})\n"
                        bot_reply += footer
                        comment.reply(bot_reply)
                        comment = reddit.comment(id=f"{comment.id}")
                        comment.save()
                        logging.info(f"Comment posted! Saved comment_id: {comment.id}")
                except Exception:
                    pass
    except Exception as error:
        # dealing with low karma posting restriction
        # bot will use rate limit error to decide how long to sleep for
        time_remaining = 15
        # timeout message has a period and single quote after 'minute'
        error_message = str(error).strip(".'").split()
        if (error_message[0] == 'RATELIMIT:'):
            units = ['minute', 'minutes']
            # split rate limit warning to grab amount of time
            for i in error_message:
                if (i.isdigit()):
                    #  check if time units are present in string
                    if any(unit in error_message for unit in units):
                        #  if minutes, convert to seconds for sleep
                        #  add one more minute to be safe
                        time_remaining = int(i + 1) * 60
                    else:
                        #  if seconds, use directly for sleep
                        #  add one more minute to wait
                        time_remaining = int(i + 60)
                        break
        else:
            # If not rate limited, save comment where info cannot be found
            # so bot is not triggered again
            comment.save()
            logging.info("Comment saved after exception.")
        #  display error type and string
        logging.exception(repr(error))
        #  loops backwards through seconds remaining before retry
        for i in range(time_remaining, 0, -5):
            logging.info(f"Retrying in {i} seconds...")
            time.sleep(5)


if __name__ == '__main__':
    logging.info('Bot starting...')
    cpubot = CPUbot()
    gpubot = GPUbot()
    wikibot = Wikibot()
    helperbot = Helperbot()
    reddit = bot_login()
    while True:
        try:
            # uses environment variable to detect whether in Heroku
            if 'DYNO' in os.environ:
                subreddit = reddit.subreddit('pcsx2')
            else:
                # if working locally, use .env files
                import dotenv
                dotenv.load_dotenv()
                subreddit = reddit.subreddit('cpubottest')
            run_bot()
        except Exception as error:
            logging.exception(repr(error))
            time.sleep(20)
