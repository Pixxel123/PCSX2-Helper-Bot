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


class GPUbot():

    def __init__(self):
        self.passmark_gpu_page = 'https://www.videocardbenchmark.net/gpu_list.php'
        self.latest_build = 'https://buildbot.orphis.net/pcsx2/'
        self.gpu_list = self.get_gpu_list()
        self.g3d_minimum = 3000
        self.g3d_recommended = 6000
        self.pcsx2_page = 'https://pcsx2.net/getting-started.html'

    def get_gpu_list(self):
        logging.info('Getting GPU list from PassMark...')
        res = requests.get(self.passmark_gpu_page)
        html = bs(res.content, 'lxml')
        gpu_table = html.find('table', id='cputable').find('tbody')
        gpu_list = {}
        for row in gpu_table.find_all("tr")[1:]:  # skip header row
            cells = row.find_all("td")
            gpu_name = cells[0].contents[0].text
            gpu_link = cells[0].contents[0].attrs['href'].replace(
                'video_lookup', 'gpu')
            gpu_list[gpu_name] = f"https://www.videocardbenchmark.net/{gpu_link}"
        logging.info(f"Grabbed {len(gpu_list)} GPU's from list")
        return gpu_list

    def get_gpu_info(self, gpu_lookup):
        self.gpu_lookup = gpu_lookup
        details_page = requests.get(self.gpu_list[gpu_lookup])
        gpu_page = bs(details_page.content, 'lxml')
        detail_pane = gpu_page.find('div', class_='right-desc')
        g3d_mark_score = detail_pane.find_all('span')[1].text
        GPU_Details = namedtuple('GPU', [
            'model',
            'g3d_mark',
            'details_page'
        ])
        gpu_info = GPU_Details(
            gpu_lookup, g3d_mark_score, details_page.url)
        return gpu_info

    def display_gpu_info(self, gpu_lookup):
        try:
            gpu = self.get_gpu_info(gpu_lookup)
            messages = {'minimum': 'Below minimum specs for PCSX2.',
                        'above_minimum': 'Above minimum specs, but still under the recommended specs for PCSX2.',
                        'recommended': 'At recommended specs for PCSX2.',
                        'above_recommended': 'Above recommended specs for PCSX2.'}
            if int(gpu.g3d_mark) < self.g3d_minimum:
                user_specs = messages['minimum']
            elif self.g3d_minimum < int(gpu.g3d_mark) < self.g3d_recommended:
                user_specs = messages['above_minimum']
            elif int(gpu.g3d_mark) == self.g3d_recommended:
                user_specs = messages['recommended']
            elif int(gpu.g3d_mark) > self.g3d_recommended:
                user_specs = messages['above_recommended']
            bot_reply = f"\n\n### **{gpu.model}**\n\n **GPU G3D Mark:** [{gpu.g3d_mark} (GPU Benchmark Page)]({gpu.details_page})\n\n **PCSX2 specs:** {user_specs}\n\n [PassMark G3D Mark **Minimum:** {self.g3d_minimum} | **Recommended:** {self.g3d_recommended} (PCSX2 Requirements Page)]({self.pcsx2_page})"
            bot_reply += f"\n\n The latest version of PCSX2 can be found [HERE]({self.latest_build})"
        except TypeError:
            # reply if CPU information is not found
            bot_reply = f"Sorry, I couldn't find any information on {gpu_lookup}.\n\n If it's not on [PassMark's GPU Benchmarks list]({self.passmark_gpu_page}), I won't be able to return a result; or perhaps you have a misspelling, in which case, feel free to reply to this with `GPUBot! model name` and I'll try again!"
            pass
        return bot_reply

    def bot_message(self, gpu_lookup):
        self.gpu_lookup = gpu_lookup
        try:
            try:
                choices = []
                for gpu in self.gpu_list:
                    match_criteria = fuzz.token_set_ratio(gpu, gpu_lookup)
                    if match_criteria >= 50:
                        choices.append(gpu)
                closest_match = process.extractOne(
                    gpu_lookup, choices, scorer=fuzz.token_set_ratio, score_cutoff=85)
                closest_match_name = closest_match[0]
                bot_reply = self.display_gpu_info(closest_match_name)
            except TypeError:
                limit_choices = process.extractBests(gpu_lookup, choices)
                if limit_choices:
                    bot_reply = f"No direct match found for **{gpu_lookup}**, displaying {len(limit_choices)} potential matches:\n\n"
                    search_results = ''
                    for result in limit_choices[:6]:
                        gpu_name = result[0]
                        search_results += f"[{gpu_name}]({self.gpu_list[gpu_name]})\n\n"
                    bot_reply += search_results
                    bot_reply += "\n\nFeel free to ask me again (`GPUBot! gpu model`) with these models or visit PassMark directly!\n"
        # Handles no results being found in search
        except AttributeError:
            bot_reply = f"I'm sorry, I couldn't find any information on **{gpu_lookup}**.\n\nPlease feel free to try again; perhaps you had a spelling mistake, or your GPU does not exist in the [Passmark list]({self.passmark_gpu_page})."
        return bot_reply
