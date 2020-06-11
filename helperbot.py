import logging
import logging.config
import os
import re

import requests


class Helperbot():

    def __init__(self):
        self.steam_controller_tutorial = "https://forums.pcsx2.net/Thread-A-steam-guide-to-using-your-DS4-and-other-controllers"
        self.windows_specs_image = 'https://media.discordapp.net/attachments/453394610514034689/697528371562676244/unknown.png?width=1442&height=654'

    def bot_message(self, command):
        bot_reply = ''
        command = command.lower()
        if command == 'support':
            bot_reply = "### **Getting Help on r/PCSX2**\n\n1) Please have the following information ready:\n\n- What PCSX2 version you are using. 'Latest' is not helpful, please look at the actual version number (Found at the top of your PCSX2 window if you're not in fullscreen).\n- What CPU and GPU your PC has. The `HelperBot! specs` command will show you where you can find these on Windows 10.\n- What specific game(s) you are having problems with.\n\n2) Ask your question! Don't worry about asking  (as long as your question falls within the rules)."
        if command == 'specs':
            bot_reply = f"### **Finding PC specs on Windows 10:**\n\nOpen Task Manager by pressing 'Ctrl + Shift + Esc', then follow these screenshots to locate your CPU and GPU: [SPECS SCREENSHOT]({self.windows_specs_image})"
        if command == 'steam':
            bot_reply = f"### **A guide to using your DS4 and other controllers via Steam:**\n\nA basic guide to setting up your controller:\n\n{self.steam_controller_tutorial}"
        if command == 'commands':
            bot_reply = "I respond to the following commands (**NOTE:** The bot call is not case-sensitive):\n\n`GPUBot! gpu model` - Find graphics card G3D mark and how it performs with PCSX2\n\n`CPUBot! cpu model` - Find processor Single Thread Rating and how it performs with PCSX2\n\n`WikiBot! game name` - Find game from PCSX2 wiki and lists active and fixed issues if available\n\n`HelperBot! support` - A guideline for asking good questions and getting better support with issues\n\n`HelperBot! specs` - Shows how to find CPU and GPU models in Windows 10\n\n`HelperBot! steam` - How to set up DualShock4 or other controllers on PCSX2 via Steam\n\n`HelperBot! commands` - Shows this message."
        return bot_reply
