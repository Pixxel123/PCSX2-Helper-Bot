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
            gpu_rating = [(0, 'Slow'),
                          (360, 'Native'),
                          (1720, '2x Native (~720p)'),
                          (3230, '3x Native (~1080p)'),
                          (4890, '4x Native (~2K)'),
                          (6700, '5x Native (~3K)'),
                          (8660, '6x Native (~4K)'),
                          (13030, '8x Native (~5K)')]
            for threshold, gpu_message in gpu_rating:
                if int(gpu.g3d_mark) >= threshold:
                    gpu_performance = gpu_message
                else:
                    break
            bot_reply = f"\n\n### **{gpu.model}**\n\n **GPU G3D Mark:** [{gpu.g3d_mark} (GPU Benchmark Page)]({gpu.details_page})"
            bot_reply += f"\n\n **Performance:** {gpu_performance}\n\n [PassMark G3D Mark **Minimum:** {self.g3d_minimum} | **Recommended:** {self.g3d_recommended} (PCSX2 Requirements Page)]({self.pcsx2_page})"
        except TypeError:
            # reply if CPU information is not found
            bot_reply = f"\n\nSorry, I couldn't find any information on {gpu_lookup}.\n\n If it's not on [PassMark's GPU Benchmarks list]({self.passmark_gpu_page}), I won't be able to return a result; or perhaps you have a misspelling, in which case, feel free to reply to this with `GPUBot! model name` and I'll try again!"
            pass
        return bot_reply

    def bot_message(self, gpu_lookup):
        self.gpu_lookup = gpu_lookup
        logging.info('Looking for GPU...')
        # Ti GPU variants often get entered without a space, which messes up matching
        # so regex is used to try and correct this
        gpu_lookup = re.sub(r"(\d{3,4})(Ti)", r"\1 \2",
                        gpu_lookup, flags=re.IGNORECASE)
        try:
            choices = []
            for gpu in self.gpu_list:
                match_criteria = fuzz.token_set_ratio(gpu, gpu_lookup)
                if match_criteria >= 60:
                    choices.append(gpu)
            # Not specifying scorer allows default use of WRatio()
            # which is a weighted combination of the four fuzz ratios
            closest_match = process.extractOne(
                gpu_lookup, choices, score_cutoff=65)
            logging.info(f"Searching: {gpu_lookup}, Closest: {closest_match}")
            closest_match_name = closest_match[0]
            bot_reply = self.display_gpu_info(closest_match_name)
        except TypeError:
            limit_choices = process.extractBests(gpu_lookup, choices)
            if limit_choices:
                bot_reply = f"\n\nNo direct GPU match found for **{gpu_lookup}**, displaying {len(limit_choices)} potential matches:\n\n"
                search_results = ''
                for result in limit_choices[:6]:
                    gpu_name = result[0]
                    search_results += f"[{gpu_name}]({self.gpu_list[gpu_name]})\n\n"
                bot_reply += search_results
                bot_reply += f"\n\nFeel free to ask me again (`GPUBot! gpu model`) with these models or visit [PassMark]({self.passmark_gpu_page}) directly!\n"
            # Handles no results being found in search
            if not limit_choices:
                bot_reply = f"\n\nI'm sorry, I couldn't find any information on **{gpu_lookup}**.\n\nPlease feel free to try again; perhaps you had a spelling mistake, or your GPU is not listed in the [Passmark GPU list]({self.passmark_gpu_page})."
        return bot_reply
