# PCSX2-CPU-Bot
A reddit bot that grabs CPU information for users to compare with PCSX2 emulator's system requirements.

The PCSX2 subreddit has many new faces each day asking if their PC is capable of running the software, which is heavily CPU-bound. As per the [official PCSX2 requirements page](https://pcsx2.net/getting-started.html), Single Thread Performance rating is a good starting point with the minium being a rating near or greater than 1600, and a recommended rating near or greater than 2100.

This bot was created to quickly scrape the PassMark CPU Benchmarks page for a provided CPU model and return the Single Thread Rating, and how it compares to the PCSX2 requirements.

As a bonus, the bot also links to the newest development builds page, as of the time of this writing, the "latest stable release" of 1.4.0 on the site is several years old, and has been superseded by the 1.5.0 development build that is currently being worked on.

## How it works
The bot is summoned with `CPUBot! <cpu_model>`, and using the CPU model as an input, it searches through the PassMark CPU list, iterating through the main table. The input is cleaned up, and matching is done with the [fuzzywuzzy module](https://github.com/seatgeek/fuzzywuzzy) to find the closest CPU match it can.

This is then passed into a Reddit comment.

![Image of PCSX2-CPU-Bot response](https://i.imgur.com/ieB5eir.png)
Version 2 of the bot removes the margin of error output as it is not relevant to most users.

## Why didn't the bot respond to me?

* Make sure that you are calling the bot correctly with `CPUBot! <cpu model>`

  The first part, `CPUBot!` **is NOT case-sensitive**.

* The bot currently does not support more than one CPU model lookup at a time.

* The bot relies on fuzzy matching to find the correct model. If it less than a 95% score on the single match it finds, it will not treat it as finding a result. This is so that similar model inputs like just `AMD Ryzen 3` or `Ryzen 4` do not produce a wrong result.

* The bot may be down for maintenance.

* I may have run out of free dynos for the month!
