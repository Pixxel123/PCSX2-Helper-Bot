# PCSX2-CPU-Bot
A reddit bot that grabs CPU information for users to compare with PCSX2 emulator's system requirements.

The PCSX2 subreddit has many new faces each day asking if their PC is capable of running the software, which is heavily CPU-bound. As per the [official PCSX2 requirements page](https://pcsx2.net/getting-started.html), Single Thread Performance rating is a good starting point with the minium being a rating near or greater than 1600, and a recommended rating near or greater than 2100.

This bot was created to quickly scrape the PassMark CPU Benchmarks page for a provided CPU model and return the Single Thread Rating, and how it compares to the PCSX2 requirements.

As a bonus, the bot also links to the newest development builds page, as of the time of this writing, the "latest stable release" of 1.4.0 on the site is several years old, and has been superseded by the 1.5.0 development build that is currently being worked on.

## How it works
The bot is summoned with `CPUBot! <cpu_model>`, and using the CPU model as an input, it searches through the PassMark CPU list, iterating through the main table. The input is cleaned up, and matching is done with the [fuzzywuzzy module](https://github.com/seatgeek/fuzzywuzzy) to find the closest CPU match it can.

This is then passed into a Reddit comment.

![Image of PCSX2-CPU-Bot response](https://i.imgur.com/N7PqTeG.png)
