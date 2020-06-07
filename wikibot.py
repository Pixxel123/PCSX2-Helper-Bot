import requests
from bs4 import BeautifulSoup as bs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from collections import namedtuple
from pytablewriter import MarkdownTableWriter
import io
import praw
import re
import time
import os
import logging
import logging.config

# Logging allows replacing print statements to show more information
# This config outputs human-readable time, the log level, the log message and the line number this originated from
logging.basicConfig(
    format='%(asctime)s (%(levelname)s) %(message)s (Line %(lineno)d)', level=logging.INFO)

# PRAW seems to have its own logging which clutters up console output, so this disables everything but Python's logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': True
})


class Wikibot:

    def __init__(self):
        self.wiki_complete_url = 'https://wiki.pcsx2.net/Complete_List_of_Games'
        self.wiki_base_url = 'https://wiki.pcsx2.net'
        self.games_list = self.get_games_list()
        self.github_link = 'https://github.com/Pixxel123/PCSX2-Wiki-Bot'

    def get_games_list(self):
        logging.info("Getting games list from PCSX2 wiki...")
        session = requests.Session()
        res = session.get(self.wiki_complete_url)
        html = bs(res.content, 'lxml')
        game_table = html.find('table', class_='wikitable').find('tbody')
        games_list = {}
        # Ignores header row
        for row in game_table.find_all('tr')[1:]:
            # There are some hidden rows containing region info only,
            # skip as there is no game name or link
            try:
                cell = row.find_all('td')[0]
                game_name = cell.contents[0].attrs['title']
                game_link = cell.contents[0].attrs['href']
                games_list[game_name] = self.wiki_base_url + game_link
            except AttributeError:
                continue
        logging.info(f"Grabbed {len(games_list)} games from wiki")
        return games_list

    def get_game_html(self, game_search):
        self.game_search = game_search
        game_search_url = self.games_list[game_search]
        session = requests.Session()
        res = session.get(game_search_url)
        # Gets HTML output of page for parsing
        html = bs(res.content, 'lxml')
        return html

    def find_compatibility(self, game_page):
        self.game_page = game_page
        compatibility_table = []
        regions = game_page.find_all('th', string=re.compile(r'^(Region).*:$'))
        for region in regions:
            # Finds region and strips out 'Region' and ':', returning region code via regex group 2
            game_region = re.sub(r'(Region\s)(.*)(:)', r'\2', region.text)
            compatibility = {'region': game_region}
            compatibility_info = []
            table = region.findParent('tbody')
            os_string = table.find_all(
                'td', string=re.compile(r'^.*(Status):'))
            for system in os_string:
                os_string = system.text.replace(' Status:', '')
                try:
                    game_state = system.find_next('td').find('b').text
                except AttributeError:
                    # If no text, shows '?' from page
                    # game_state = system.find_next('td').string
                    # N/A is clearer than a question mark
                    game_state = 'N/A'
                compatibility_info.append(
                    {'os': os_string, 'state': game_state})
            compatibility['stats'] = compatibility_info
            compatibility_table.append(compatibility)
        return compatibility_table

    def find_issues(self, game_page):
        self.game_page = game_page
        active_issues = []
        fixed_issues = []
        try:
            issues = game_page.find('span', {'id': 'Known_Issues'}).parent
            for element in issues.next_siblings:
                # Deals with BS4 finding newline as next_sibling
                if element.name == 'ul':
                    try:
                        if element.contents[0].text == 'Status: Fixed':
                            # If issue is fixed, find issue text
                            fixed_issue = element.previous_sibling.previous_sibling.text
                            fixed_issues.append(fixed_issue)
                        elif element.contents[0].text == 'Status: Active':
                            active_issue = element.previous_sibling.previous_sibling.text
                            active_issues.append(active_issue)
                    except AttributeError:
                        pass
        # Some pages may not have a Known Issues section
        except AttributeError:
            pass
        Game_Issues = namedtuple('Issues', [
            'active',
            'fixed',
        ])
        game_issues = Game_Issues(active_issues, fixed_issues)
        return game_issues

    def generate_table(self, game_page):
        self.game_page = game_page
        compatibility = self.find_compatibility(game_page)
        writer = MarkdownTableWriter()
        table_data = []
        for i in compatibility:
            table_row = []
            # bold region index with markdown
            table_row.append(f"**{i['region']}**")
            # Gets each playable state per OS
            for j in i['stats']:
                table_row.append(j['state'])
            table_data.append(table_row)
        # Uses first table value to make OS headers
        table_header = [i['os'] for i in compatibility[0]['stats']]
        # Blank space added to header to allow "index" column
        table_header.insert(0, '')
        writer.headers = table_header
        writer.value_matrix = table_data
        # Output stream changed to variable instead of default stdout
        writer.stream = io.StringIO()
        writer.write_table()
        return writer.stream.getvalue()

    # Game name gets passed in for the lookup
    def display_game_info(self, game_lookup):
        self.game_lookup = game_lookup
        html = self.get_game_html(game_lookup)
        try:
            reply_table = '#### **Compatibility table**\n\n'
            reply_table += str(self.generate_table(html))
        except AttributeError:
            reply_table = 'No compatibility information found'
        issues = self.find_issues(html)
        issue_message = ''
        # If active issues is not empty
        if issues.active:
            issue_message += '\n\n**Active issues:**\n\n'
            for issue in issues.active:
                issue_message += f"* {issue}\n"
        # If fixed issues is not empty
        if issues.fixed:
            issue_message += '\n\n**Fixed issues:**\n\n'
            for issue in issues.fixed:
                issue_message += f"* {issue}\n"
        if not issues.active and not issues.fixed:
            issue_message = '\n\nNo active or fixed issues found.'
        bot_reply_info = f"\n\n## [{game_lookup}]({self.games_list[game_lookup]})\n\n{reply_table}{issue_message}"
        return bot_reply_info

    def bot_message(self, game_lookup):
        self.game_lookup = game_lookup
        try:
            if game_lookup == '':
                bot_reply = "\n\nI need a search term to work with! Please try `WikiBot! <game name>`"
            else:
                # run bot if not blank
                try:
                    choices = []
                    for game in self.games_list:
                        # strip out spaces/non-word characters and lower for case-insensitive match
                        cleaned_lookup = re.sub(r'\W', '', game_lookup).lower()
                        cleaned_game = re.sub(r'\W', '', game).lower()
                        match_criteria = fuzz.ratio(
                            cleaned_lookup, cleaned_game)
                        # looser criteria attempts to allow abbreviations to be caught
                        if match_criteria >= 48:
                            choices.append(game)
                    closest_match = process.extractOne(
                        game_lookup, choices, score_cutoff=85)
                    closest_match_name = closest_match[0]
                    bot_reply = self.display_game_info(closest_match_name)
                except TypeError:
                    # Limits results so that users are not overwhelmed with links
                    limit_choices = process.extractBests(game_lookup, choices)
                    if limit_choices:
                        bot_reply = f"\n\nNo direct match found for **{game_lookup}**, displaying {len(limit_choices)} wiki results:\n\n"
                        search_results = ''
                        for result in limit_choices[:6]:
                            game_name = result[0]
                            search_results += f"[{game_name}]({self.games_list[game_name]})\n\n"
                        bot_reply += search_results
                        bot_reply += "\n\nFeel free to ask me again (`WikiBot! game name`) with these game names or visit the wiki directly!\n"
        # Handles no results being found in search
        except AttributeError:
            bot_reply = f"\n\nI'm sorry, I couldn't find any information on **{game_lookup}**.\n\nPlease feel free to try again; perhaps you had a spelling mistake, or your game does not exist in the [PCSX2 Wiki]({self.wiki_base_url})."
        return bot_reply
