#!/usr/bin/env python
import os
import sys
import json

from kivy.app import App
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.graphics import Rectangle, Color
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ListProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

from core.bglabel import BGLabel, BGLabelButton
from core.getplugins import getPlugins
from core.getoverlays import get_overlays
from core.hiddenbutton import HiddenButton
from core.infoscreen import InfoScreen

# Set the current working directory
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

VERSION = "0.4.1"


class InfoScreenApp(MDApp):
    base = None

    def __init__(self, **kwargs):
        self.title = "My Material Application"
        super().__init__(**kwargs)
        self._config = config

    def build(self):
        # Window size is hardcoded for resolution of official Raspberry Pi
        # display. Can be altered but plugins may not display correctly.
        Window.size = (800, 480)
        self.base = InfoScreen(plugins=plugins, overlays=overlays, config=config)
        return self.base


if __name__ == "__main__":
    # Load our config
    with open("config.json", "r") as cfg_file:
        config = json.load(cfg_file)

    # Get a list of installed plugins and overlays
    plugins = getPlugins()
    overlays = get_overlays()

    # Load the master KV file
    Builder.load_file("base.kv")

    # Loop over the plugins and add to Builder
    for p in plugins:
        Builder.load_file(p["kvpath"])

    # Loop over the overlays and add to Builder
    for w in overlays:
        Builder.load_file(w['kvpath'])

    # Do we want a webserver?
    web = config.get("webserver", dict())

    # Is bottle installed?
    try:

        # I don't like doing it this way (all imports should be at the top)
        # but I'm feeling lazy
        from core.webinterface import start_web_server
        web_enabled = True

    except ImportError:
        Logger.warning("Bottle module not found. Cannot start webserver.")
        web_enabled = False

    if web.get("enabled") and web_enabled:

        # Start our webserver
        webport = web.get("webport", web.get("webport"))
        apiport = web.get("apiport", web.get("apiport"))
        debug = web.get("debug", False)
        start_web_server(os.path.dirname(os.path.abspath(__file__)),
                         webport,
                         apiport,
                         debug)

    # Good to go. Let's start the app.
    InfoScreenApp().run()
