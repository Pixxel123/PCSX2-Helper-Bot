# PCSX2-CPU-Bot
A reddit bot that grabs CPU information for users to compare with PCSX2 emulator's system requirements.

The PCSX2 subreddit has many new faces each day asking if their PC is capable of running the software, which is heavily CPU-bound. As per the [official PCSX2 requirements page](https://pcsx2.net/getting-started.html), Single Thread Performance rating is a good starting point with the minium being a rating near or greater than 1600, and a recommended rating near or greater than 2100.

This bot was created to quickly scrape the PassMark CPU Benchmarks page for a provided CPU model and return the Single Thread Rating, and how it compares to the PCSX2 requirements.

As a bonus, the bot also links to the newest development builds page, as of the time of this writing, the "latest stable release" of 1.4.0 on the site is several years old, and has been superseded by the 1.7.0 development build that is currently being worked on.

## How it works
The bot is summoned with `CPUBot! <cpu_model>`, and using the CPU model as an input, it searches through the PassMark CPU list with BeautifulSoup, iterating through the main table. The input is cleaned up as follows:

 * Any frequency information is unnecessary when it concerns CPU model, so regex is used to parse the common pattern of @ x.xx GHz with `(\s?@?\s?)(\d\.\d{1,2})(ghz)?.*$` allowing optional provisioning for spaces, 1 or two digits for the frequency value and GHz itself (this is call case-insensitive) and removes it if found.

 * The string is converted to lower-case.

 * Spaces and hyphens are stripped out.

 This is repeated for the CPU model from PassMark as well, to allow the strings to be matched more closely on a fairly unpredictable input.

Matching is done with the [fuzzywuzzy module](https://github.com/seatgeek/fuzzywuzzy) to find some close matching candidates (defined as a lower score to account for variance in user input), of which these are then processed further to find a single match with a score at or over 95. User-provided CPU input is compared against the PassMark entry.

If a match is found, the bot goes to the CPU's detail page and uses BeautifulSoup to scrape out the Single Thread Rating, as well as the url of the detailed benchmark page for the user to access if they wish.

A link to the official PCSX2 requirements page is included for the user's information, as well as the latest development build list and a bot disclaimer.

This is then passed into a Reddit comment.

![Image of PCSX2-CPU-Bot response](https://i.imgur.com/ieB5eir.png)
Version 2 of the bot removes the margin of error output as it is not relevant to most users.

The bot responds with a message if it could not find a match, asking the user to try again with some more information or corrected spelling.

![Image of PCSX2-CPU-Bot no result response](https://i.imgur.com/Q3jkUf2.png)

## Why didn't the bot respond to me?

* Make sure that you are calling the bot correctly with `CPUBot! <cpu model>`

  The first part, `CPUBot!` **is NOT case-sensitive** and requires a space after the `!`.

* The bot currently does not support more than one CPU model lookup at a time.

* The bot will only reply to a comment once. Edited comments after a reply is made will not be seen.

* The bot may be down for maintenance.

* I may have run out of free dynos for the month!

## Notes

### Saving comments
Many people use a database to store ID's of replied comments so that the bot only replies once. Instead, one can save reddit comments and use whether that is saved to check against. The Reddit API has a return limit of 1000 items for any operation involving fetching lists/data, however if you are not fetching this data and just checking whether it is saved, there is no limit. The downside is that it takes an extra API call to save an item, which means an extra second per item. Since this is not a high traffic bot, this is not a problem.

### Heroku deployment

Heroku deployment requires a Procfile, I have included mine as an example.

# Acknowledgements

1. https://github.com/kylelobo/Reddit-Bot - kylelobo
2. https://github.com/harshibar/friendly-redditbot - harshibar
3. The Reddit community, particularly [r/redditdev](https://old.reddit.com/r/redditdev/), [r/Python](https://old.reddit.com/r/python/), and of course, [r/PCSX2](https://old.reddit.com/r/pcsx2/)
