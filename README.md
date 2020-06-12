# PCSX2-Helper-Bot
A reddit bot that rolls in several functions from my previous bots, [PCSX2-CPU-Bot](https://github.com/Pixxel123/PCSX2-CPU-Bot) and [PCSX2-Wiki-Bot](https://github.com/Pixxel123/PCSX2-Wiki-Bot) and provides even more functionality for the r/PCSX2 subreddit.

## How it works

The bot takes the provided CPU, GPU and game name parameters and compares them to specific hashmaps generated at start-up for each command. These comparison points are pulled from PassMark's CPU list, PassMark GPU Benchmarks list and the PCSX2 Wiki game list.

String pre-processing is run, and matching is done with the [fuzzywuzzy module](https://github.com/seatgeek/fuzzywuzzy) to find some close matching candidates. See [PCSX2-CPU-Bot](https://github.com/Pixxel123/PCSX2-CPU-Bot) and [PCSX2-Wiki-Bot](https://github.com/Pixxel123/PCSX2-Wiki-Bot) for more specific information on these particular bots.

## Supported commands

This bot allows users to find the following:

* Single thread rating for a given CPU model as it relates to PCSX2 requirements and performance. (`CPUBot! cpu model` command)

* G3D Mark score for a given GPU model as it relates to PCSX2 requirements and performance. (`GPUBot!gpu model` command)

* Game information from the PCSX2 wiki showing compatibility across regions and any active or fixed issues present on the page, as well as a link to the relevant wiki page. (`WikiBot! game name` command)

The bot also has several helper commands for common questions and issues under the `HelperBot!` command. These are as follows:

* Shows the aforementioned CPU, GPU and Wiki commands

* `HelperBot! support` - A guideline for asking good questions and getting better support with issues

* `HelperBot! specs` - Shows how to find CPU and GPU models in Windows 10

* `HelperBot! steam` - How to set up DualShock4 or other controllers on PCSX2 via Steam

* `HelperBot! commands` - Shows a list of commands and their parameters

* Commands bot calls can be chained together, such as:
   ```
   Are you having issues with Jak II?

   Helperbot! specs

   CPUbot! i5-4690k

   Wikibot! Jak II
   ```
   The bot supports multiple lookups/help commands as long as they're separated by a comma. So the following input will reply in one comment:

   ```
   These games can be fairly demanding for your CPU!

   Wikibot! Jak II, Burnout 3

   CPUBot! i5-4690k
   ```
   ![Multiple query response example](https://i.imgur.com/1J3Ba30.png)
   Here we see how multiple queries are responded to in one reply.

## Why didn't the bot respond to me?

* Make sure that you are calling the bot correctly with [one of the supported commands](https://github.com/Pixxel123/PCSX2-Helper-Bot/blob/master/README.md#supported-commands).

  The first part of the bot call, `CPUBot!`, `GPUBot!`, etc **is NOT case-sensitive** and requires a space after the `!`.

* The bot will only reply to a comment once. Edited comments after a reply is made will not be seen.

* The bot will not see comments between it going down and starting back up, as it will pull from new submissions upon starting. In which case, try again in a few minutes.

* The bot may be down for maintenance.

* I may have run out of free Heroku dynos for the month!

# Acknowledgements

1. https://github.com/kylelobo/Reddit-Bot - kylelobo
2. https://github.com/harshibar/friendly-redditbot - harshibar
3. The Reddit community, particularly [r/redditdev](https://old.reddit.com/r/redditdev/), [r/Python](https://old.reddit.com/r/python/), and of course, [r/PCSX2](https://old.reddit.com/r/pcsx2/)

