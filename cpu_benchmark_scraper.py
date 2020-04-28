import requests
from bs4 import BeautifulSoup as bs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import praw
import config
import re
import time
import sys

reddit = praw.Reddit(
    client_id=config.client_id,
    client_secret=config.client_secret,
    password=config.password,
    user_agent=config.user_agent,
    username=config.username)


str_minimum = 1600

str_recommended = 2000

summon_phrase = 'CPUBot! '

subreddit = reddit.subreddit('cpubottest')


def get_cpu_info(cpu_search):
    choices = []
    url = "https://www.cpubenchmark.net/cpu_list.php"
    lookup_page = requests.get(url)
    html = bs(lookup_page.content, 'lxml')
    cpu_table = html.find('table', id='cputable').find('tbody')
    for row in cpu_table.find_all("tr")[1:]:  # skip header row
        cells = row.find_all("td")
        # ignores @ clock speeds (with space)
        cpu_name = cells[0].text.split(" @", 1)[0]
        cpu_details_link = cells[0].contents[0].attrs['href']
        if fuzz.partial_ratio(cpu_name.lower(), cpu_search.lower()) >= 50:
            choices.append({'cpu': cpu_name, 'link': cpu_details_link})
    cpu_closest_match = process.extractOne(cpu_search, choices)
    cpu_details_link = cpu_closest_match[0]['link']
    cpu_closest_name = cpu_closest_match[0]['cpu']
    cpu_details_page = requests.get(
        f"https://www.cpubenchmark.net/{cpu_details_link.replace('cpu_lookup', 'cpu')}")
    cpu_page = bs(cpu_details_page.content, 'lxml')
    detail_pane = cpu_page.find('div', class_="right-desc")
    single_thread_rating = detail_pane.find('strong').nextSibling
    cpu_sample_size = detail_pane.find_all(
        "strong")[1].nextSibling.replace('*', "")
    cpu_error_margin = detail_pane.find_all("span")[2].text
    return (cpu_closest_name, single_thread_rating, cpu_sample_size, cpu_error_margin, cpu_details_page.url)


def bot_message(cpu_lookup):
    try:
        cpu_info = get_cpu_info(cpu_lookup)
        cpu_model = cpu_info[0]
        cpu_str_rating = cpu_info[1]
        sample_size = cpu_info[2]
        error_margin = cpu_info[3]
        details_page = cpu_info[4]
        messages = {'minimum': f"Below minimum specs for PCSX2.",
                    'above_minimum': f"Above minimum specs, but still under the recommended specs for PCSX2.",
                    'recommended': f"Above recommended specs for PCSX2."}
        if int(cpu_str_rating) < str_minimum:
            user_specs = messages['minimum']
        if str_minimum < int(cpu_str_rating) < str_recommended:
            user_specs = messages['above_minimum']
        if int(cpu_str_rating) >= str_recommended:
            user_specs = messages['recommended']
        bot_reply = f"**CPU model:** {cpu_model}\n\n **CPU STR:** {cpu_str_rating}\n\n **PCSX2 specs:** {user_specs}\n\n [Single Thread Rating **Minimum:** {str_minimum} | **Recommended:** {str_recommended} (PCSX2 Requirements Page)](https://pcsx2.net/getting-started.html)\n\n[**Sample size:** {sample_size} | **Margin for error:** {error_margin} (CPU Benchmark Page)]({details_page})"
        bot_reply += f"\n\n---\n\n^(I'm a bot, and should only be used for reference (might also make mistakes sometimes, in which case adding a brand name like Intel or AMD could really help!)^) ^(if there are any issues, please contact my) ^[Creator](https://www.reddit.com/message/compose/?to=theoriginal123123&subject=/u/PCSX2-CPU-Bot) \n\n[^GitHub](https://github.com/)"
        return bot_reply
    except TypeError:
        print("Could not find CPU information.")


def run_bot():
    try:
        print("Bot started!")
        replied_to = []
        # look for summon_phrase and reply
        for comment in subreddit.stream.comments():
            if summon_phrase in comment.body:
                if not comment.saved:
                    cpu_lookup = re.search(
                        f"({summon_phrase})(.*)", comment.body, re.IGNORECASE)
                    if cpu_lookup:
                        cpu_lookup = cpu_lookup.group(2)
                    comment.reply(bot_message(cpu_lookup))
                    comment = reddit.comment(id=f"{comment.id}")
                    comment.save()
                    print("Comment posted!")
    except Exception as error:
        # dealing with low karma posting restriction
        # bot will use rate limit error to decide how long to sleep for
        time_remaining = 15
        if (str(error).split()[0] == "RATELIMIT:"):
            units = ['minute', 'minutes']
            # split rate limit warning to grab amount of time
            for i in str(error).split():
                if (i.isdigit()):
                    #  check if time units are present in string
                    for unit in units:
                        if unit in str(error.split()):
                            #  if minutes, convert to seconds for sleep
                            time_remaining = int(i) * 60
                        else:
                            #  if seconds, use seconds for sleep
                            time_remaining = int(i)
                            break
                        break
        #  display error type and string
        print(f"{str(error.__class__.__name__)}: {str(error)}")
        #  loops backwards through seconds remaining before retry
        for i in range(time_remaining, 0, -5):
            print(f"Retrying in {i} seconds...")
            time.sleep(5)


if __name__ == "__main__":
    while True:
        try:
            run_bot()
        except Exception as error:
            print(f"{str(error.__class__.__name__)}: {str(error)}")
            time.sleep(20)
