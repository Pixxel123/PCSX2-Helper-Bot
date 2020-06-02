import requests
from bs4 import BeautifulSoup as bs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import praw
import re
import time
import os
import logging
import logging.config

# Logging allows replacing print statements to show more information
# This config outputs human-readable time, the log level, the log message and the line number this originated from
logging.basicConfig(
    format='%(asctime)s (%(levelname)s) %(message)s (Line %(lineno)d)', level=logging.DEBUG)

# PRAW seems to have its own logging which clutters up console output, so this disables everything but Python's logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True
})


passmark_page = 'https://www.cpubenchmark.net/cpu_list.php'
github_link = 'https://github.com/Pixxel123/PCSX2-CPU-Bot'
latest_build = 'https://buildbot.orphis.net/pcsx2/'
pcsx2_page = 'https://pcsx2.net/getting-started.html'

str_minimum = 1600
str_recommended = 2100

summon_phrase = 'CPUBot! '


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


def get_cpu_info(cpu_search):
    choices = []
    lookup_page = requests.get(passmark_page)
    html = bs(lookup_page.content, 'lxml')
    cpu_table = html.find('table', id='cputable').find('tbody')
    for row in cpu_table.find_all("tr")[1:]:  # skip header row
        cells = row.find_all('td')
        cpu_name = cells[0].text
        cpu_details_link = cells[0].contents[0].attrs['href']
        # ! token_set_ratio ignores word order and duplicated words
        # cpu_name and cpu_search are set to lowercase and whitespace is stripped
        match_criteria = fuzz.token_set_ratio(
            clean_input(cpu_name), clean_input(cpu_search))
        # * show all matching criteria for debugging purposes
        # logging.debug(f"{cpu_name}: {match_criteria}")
        if match_criteria >= 50:
            choices.append({'cpu': cpu_name, 'link': cpu_details_link})
            # * show match values for debugging purposes
            # logging.debug(f"{cpu_name}: {match_criteria}")
    # score_cutoff value set to lessen false positives
    cpu_closest_match = process.extractOne(
        cpu_search, choices, scorer=fuzz.token_set_ratio, score_cutoff=95)
    cpu_details_link = cpu_closest_match[0]['link']
    cpu_closest_name = cpu_closest_match[0]['cpu']
    # show output in console
    logging.info(f"Searching for {cpu_search}: Found: {cpu_closest_match}")
    cpu_details_page = requests.get(
        f"https://www.cpubenchmark.net/{cpu_details_link.replace('cpu_lookup', 'cpu')}")
    cpu_page = bs(cpu_details_page.content, 'lxml')
    detail_pane = cpu_page.find('div', class_='right-desc')
    single_thread_rating = detail_pane.find('strong').nextSibling
    # ! cpu_sample_size is not used as it adds no real information to the user, but the scraping for it took some work
    # ! so this is left here for reference.
    # cpu_sample_size = detail_pane.find_all(
    #     'strong')[1].nextSibling.replace('*', '')
    # cpu_error_margin = detail_pane.find_all('span')[2].text
    return (cpu_closest_name, single_thread_rating, cpu_details_page.url)


def clean_input(input_string):
    try:
        # remove CPU frequency value
        frequency_strip = re.search(
            r"(\s?@?\s?)(\d\.\d{1,2})(ghz)?.*$", input_string, re.IGNORECASE).group(0)
    except AttributeError:
        # if no frequency values to remove, set input to clean_string
        clean_string = input_string
    else:
        clean_string = input_string.split(frequency_strip, 1)[0]
    clean_string = clean_string.lower()
    clean_string = clean_string.replace(' ', '')
    clean_string = clean_string.replace('-', '')
    # * debugging message
    # logging.debug(f"{input_string} becomes {clean_string}")
    return clean_string


def bot_message(cpu_lookup):
    try:
        cpu_info = get_cpu_info(cpu_lookup)
        cpu_model = cpu_info[0]
        cpu_str_rating = cpu_info[1]
        # ! cpu_sample_size removed due to not being needed by end user
        # sample_size = cpu_info[2]
        # ! Error margin output removed due to information not being necessary
        # ! CPU page link appended to STR rating
        # error_margin = cpu_info[3]
        details_page = cpu_info[2]
        messages = {'minimum': 'Below minimum specs for PCSX2.',
                    'above_minimum': 'Above minimum specs, but still under the recommended specs for PCSX2.',
                    'recommended': 'At recommended specs for PCSX2.',
                    'above_recommended': 'Above recommended specs for PCSX2.'}
        if int(cpu_str_rating) < str_minimum:
            user_specs = messages['minimum']
        elif str_minimum < int(cpu_str_rating) < str_recommended:
            user_specs = messages['above_minimum']
        elif int(cpu_str_rating) == str_recommended:
            user_specs = messages['recommended']
        elif int(cpu_str_rating) > str_recommended:
            user_specs = messages['above_recommended']
        bot_reply = f"**CPU model:** {cpu_model}\n\n **CPU STR:** [{cpu_str_rating} (CPU Benchmark Page)]({details_page})\n\n **PCSX2 specs:** {user_specs}\n\n [Single Thread Rating **Minimum:** {str_minimum} | **Recommended:** {str_recommended} (PCSX2 Requirements Page)]({pcsx2_page})"
        bot_reply += f"\n\n The latest version of PCSX2 can be found [HERE]({latest_build})"
    except TypeError:
        # reply if CPU information is not found
        bot_reply = f"Sorry, I couldn't find any information on {cpu_lookup}.\n\n If it's not on [PassMark's CPU Benchmarks list]({passmark_page}), I won't be able to return a result; or perhaps you have a misspelling, in which case, feel free to reply to this with `CPUBot! <model name>` and I'll try again!"
        pass
    bot_reply += f"\n\n---\n\n^(I'm a bot, and should only be used for reference (might also make mistakes sometimes, in which case adding a brand name like Intel or AMD could  help! I also don't need to know the GHz of your CPU, just the model is enough!)^) ^(if there are any issues, please contact my) ^[Creator](https://www.reddit.com/message/compose/?to=theoriginal123123&subject=/u/PCSX2-CPU-Bot) \n\n[^GitHub]({github_link})"
    return bot_reply


def run_bot():
    try:
        logging.info('Bot started!')
        # look for summon_phrase and reply
        for comment in subreddit.stream.comments():
            # allows bot command to NOT be case-sensitive and ignores comments made by the bot
            if summon_phrase.lower() in comment.body.lower() and comment.author.name != reddit.user.me():
                if not comment.saved:
                    # regex allows cpubot to be called in the middle of most sentences
                    cpu_lookup = re.search(
                        f"({summon_phrase})([^!,?\n\r]*)", comment.body, re.IGNORECASE)
                    if cpu_lookup:
                        cpu_lookup = cpu_lookup.group(2)
                    comment.reply(bot_message(cpu_lookup))
                    comment = reddit.comment(id=f"{comment.id}")
                    # Note: the Reddit API has a 1000 item limit on viewing things, so after 1000 saves, the ones prior (999 and back) will not be visible,
                    # but reddit will still keep them saved.
                    # If you are just checking that an item is saved, there is no limit.
                    # However, saving an item takes an extra API call which can slow down a high-traffic bot.
                    comment.save()
                    logging.info('Comment posted!')
    except Exception as error:
        # saves comment where CPU info cannot be found so bot is not triggered again
        comment.save()
        # dealing with low karma posting restriction
        # bot will use rate limit error to decide how long to sleep for
        time_remaining = 15
        error_message = str(error).split()
        if (error_message[0] == 'RATELIMIT:'):
            units = ['minute', 'minutes']
            # split rate limit warning to grab amount of time
            for i in error_message:
                if (i.isdigit()):
                    #  check if time units are present in string
                    for unit in units:
                        if unit in error_message:
                            #  if minutes, convert to seconds for sleep
                            time_remaining = int(i) * 60
                        else:
                            #  if seconds, use directly for sleep
                            time_remaining = int(i)
                            break
                        break
        #  display error type and string
        logging.exception(repr(error))
        #  loops backwards through seconds remaining before retry
        for i in range(time_remaining, 0, -5):
            logging.info(f"Retrying in {i} seconds...")
            time.sleep(5)


if __name__ == '__main__':
    while True:
        logging.info('Bot starting...')
        try:
            reddit = bot_login()
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
