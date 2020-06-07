import requests
from bs4 import BeautifulSoup as bs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from collections import namedtuple
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


class GPUBot():

    def __init__(self):
        self.passmark_gpu_page = 'https://www.videocardbenchmark.net/gpu_list.php'
        self.latest_build = 'https://buildbot.orphis.net/pcsx2/'
        self.gpu_list = self.get_gpu_list()

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


# GPUBot().get_gpu_list()
print(GPUBot().get_gpu_info('Radeon R5 M240'))
