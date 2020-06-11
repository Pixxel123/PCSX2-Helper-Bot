import logging
import logging.config
import os
import re
from collections import namedtuple

import requests
from bs4 import BeautifulSoup as bs
from fuzzywuzzy import fuzz, process

# Logging allows replacing print statements to show more information
# This config outputs human-readable time, the log level, the log message and the line number this originated from
logging.basicConfig(
    format='%(asctime)s (%(levelname)s) %(message)s (Line %(lineno)d)', level=logging.DEBUG)

# PRAW seems to have its own logging which clutters up console output, so this disables everything but Python's logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True
})


class CPUbot():

    def __init__(self):
        self.passmark_page = 'https://www.cpubenchmark.net/cpu_list.php'
        self.github_link = 'https://github.com/Pixxel123/PCSX2-CPU-Bot'
        self.latest_build = 'https://buildbot.orphis.net/pcsx2/'
        self.pcsx2_page = 'https://pcsx2.net/getting-started.html'
        self.cpu_list = self.get_cpu_list()

    def get_cpu_list(self):
        logging.info('Getting CPU list from PassMark...')
        res = requests.get(self.passmark_page)
        html = bs(res.content, 'lxml')
        cpu_table = html.find('table', id='cputable').find('tbody')
        cpu_list = {}
        for row in cpu_table.find_all("tr")[1:]:  # skip header row
            cells = row.find_all("td")
            cpu_name = cells[0].text.split(" @", 1)[0]
            cpu_details_link = cells[0].contents[0].attrs['href']
            cpu_list[cpu_name] = f"https://www.cpubenchmark.net/{cpu_details_link.replace('cpu_lookup', 'cpu')}"
        logging.info(f"Grabbed {len(cpu_list)} CPU's from list")
        return cpu_list

    def clean_input(self, input_string):
        self.input_string = input_string
        try:
            # remove CPU frequency value
            frequency_strip = re.search(
                r"(\s?@?\s?)(\d\.\d{1,2})(ghz)?.*$", input_string, re.IGNORECASE).group(0)
        except AttributeError:
            # if no frequency values to remove, set input to clean_string
            clean_string = input_string
        else:
            clean_string = input_string.split(frequency_strip, 1)[0]
        # fuzz.token_set_ratio converts strings to lower case before sequence matching
        clean_string = clean_string.replace(' ', '')
        clean_string = clean_string.replace('-', '')
        # * debugging message
        # logging.debug(f"{input_string} becomes {clean_string}")
        return clean_string

    def get_cpu_info(self, cpu_lookup):
        self.cpu_lookup = cpu_lookup
        details_page = requests.get(self.cpu_list[cpu_lookup])
        cpu_page = bs(details_page.content, 'lxml')
        detail_pane = cpu_page.find('div', class_='right-desc')
        single_thread_rating = detail_pane.find('strong').nextSibling
        CPU_Details = namedtuple('CPU', [
            'model',
            'single_thread_rating',
            'details_page'
        ])
        cpu_info = CPU_Details(cpu_lookup, single_thread_rating, details_page.url)
        return cpu_info

    def display_cpu_info(self, cpu_lookup):
        self.str_minimum = 1600
        self.str_recommended = 2100
        try:
            cpu = self.get_cpu_info(cpu_lookup)
            cpu_rating = [(0, 'Awful'),
                          (800, 'Very slow'),
                          (1200, 'OK for 2D games'),
                          (1600, 'OK for 3D games'),
                          (2000, 'Good for most games'),
                          (2400, 'Great for most games'),
                          (2800, 'Overkill')]
            for threshold, cpu_message in cpu_rating:
                if int(cpu.single_thread_rating) >= threshold:
                    cpu_performance = cpu_message
                else:
                    break
            bot_reply = f"\n\n### **{cpu.model}**\n\n **CPU STR:** [{cpu.single_thread_rating} (CPU Benchmark Page)]({cpu.details_page})"
            bot_reply += f"\n\n **Performance:** {cpu_performance}"
            bot_reply += '\n\n**These ratings should only be used as a rough guide** as some games are unusually demanding.'
            bot_reply += f"\n\n [Single Thread Rating **Minimum:** {self.str_minimum} | **Recommended:** {self.str_recommended} (PCSX2 Requirements Page)]({self.pcsx2_page})"
            bot_reply += f"\n\n The latest version of PCSX2 can be found [HERE]({self.latest_build})"
        except TypeError:
            # reply if CPU information is not found
            bot_reply = f"Sorry, I couldn't find any information on {cpu_lookup}.\n\n If it's not on [PassMark's CPU Benchmarks list]({self.passmark_page}), I won't be able to return a result; or perhaps you have a misspelling, in which case, feel free to reply to this with `CPUBot! <model name>` and I'll try again!"
            pass
        return bot_reply

    def bot_message(self, cpu_lookup):
        self.cpu_lookup = cpu_lookup
        try:
            try:
                choices = []
                for cpu in self.cpu_list:
                    match_criteria = fuzz.token_set_ratio(
                        self.clean_input(cpu), self.clean_input(cpu_lookup))
                    if match_criteria >= 50:
                        choices.append(cpu)
                closest_match = process.extractOne(
                    cpu_lookup, choices, scorer=fuzz.token_set_ratio, score_cutoff=85)
                closest_match_name = closest_match[0]
                bot_reply = self.display_cpu_info(closest_match_name)
            except TypeError:
                limit_choices = process.extractBests(cpu_lookup, choices)
                if limit_choices:
                    bot_reply = f"No direct match found for **{cpu_lookup}**, displaying {len(limit_choices)} potential matches:\n\n"
                    search_results = ''
                    for result in limit_choices[:6]:
                        cpu_name = result[0]
                        search_results += f"[{cpu_name}]({self.cpu_list[cpu_name]})\n\n"
                    bot_reply += search_results
                    bot_reply += "\n\nFeel free to ask me again (`CPUBot! cpu model`) with these models or visit PassMark directly!\n"
        # Handles no results being found in search
        except AttributeError:
            bot_reply = f"I'm sorry, I couldn't find any information on **{cpu_lookup}**.\n\nPlease feel free to try again; perhaps you had a spelling mistake, or your CPU does not exist in the [Passmark list]({self.passmark_page})."
        return bot_reply
