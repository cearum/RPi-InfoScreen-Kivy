import imp
import time
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import BooleanProperty, ObjectProperty, ListProperty, StringProperty
from kivy.lang import Builder
from kivy.logger import Logger
from kivy.factory import Factory
from kivy.metrics import dp
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.clock import Clock

from kivymd.toast.kivytoast.kivytoast import toast
from kivymd.uix.bottomsheet import MDGridBottomSheet, MDCustomBottomSheet, MDBottomSheet
from kivymd.uix.snackbar import Snackbar

from core.failedscreen import FailedScreen
from core.getplugins import getPlugins
from core.getoverlays import get_overlays


class BlackHole(object):
    def __init__(self, **kw):
        super(BlackHole, self).__init__()


# This way we put the debug info to console instead of catching errors
# it allows developers to view more debug info in the console.
DEBUG = True


class InfoScreen(FloatLayout, BlackHole):
    # Flag for determining whether screen is locked or not
    locked = BooleanProperty(False)
    plugins = ListProperty()
    scrmgr = ObjectProperty(None)
    overlay_mgr = ObjectProperty(None)

    # List of plugins

    def __init__(self, plugins=None, overlays=None, config=None, **kwargs):
        self._plugins = plugins
        overlays = overlays
        self._config = config
        super(InfoScreen, self).__init__(**kwargs)

        # We need a list to hold the names of the enabled screens and overlays
        self.available_screens = []
        self.available_overlays = []

        # and an index so we can loop through them:
        self.index = 0

        # We want to handle failures gracefully so set up some variables
        # variable to hold the FailScreen object (if needed)
        self.failscreen = None

        # Empty lists to track various failures
        dep_fail = []
        failed_screens = []

        # TODO - Implement enable/disable settings from settings_enabled boolean
        settings_config = self._config.get("settings", dict())
        settings_enabled = settings_config.get("enabled", False)

        # Loop over overlays
        for w in overlays:
            Logger.info("Loading Overlay: {}".format(w["name"]))
            # Set up a tuple to store list of unmet dependencies
            w_dep = (w["name"], [])

            # Until we hit a failure, there are no unmet dependencies
            unmet = False

            # Loop over dependencies and test if they exist
            for d in w["dependencies"]:
                try:
                    imp.find_module(d)
                except ImportError:
                    # We've got at least one unmet dependency for this screen
                    unmet = True
                    w_dep[1].append(d)
                    Logger.error("Unmet dependencies "
                                 "for {} Overlay. Skipping...".format(w["name"]))

            # Can we use the screen?
            if unmet:
                # Add the tupe to our list of unmet dependencies
                dep_fail.append(w_dep)

            # No unmet dependencies so let's try to load the screen.
            else:
                try:
                    plugin = imp.load_module("overlay", *w["info"])
                    overlay = getattr(plugin, w["overlay"])
                    self.overlay_mgr.add_widget(overlay(name=w["name"],
                                                        master=self,
                                                        params=w["params"]))
                    Logger.info("Overlay: {} loaded.".format(w["name"]))

                # Uh oh, something went wrong...
                except Exception as e:
                    # Add the screen name and error message to our list
                    Logger.error("Could not import "
                                 "{} Overlay. Skipping...".format(w["name"]))
                    failed_screens.append((w["name"], repr(e)))

                else:
                    # We can add the screen to our list of available screens.
                    self.available_overlays.append(w["name"])
        print("Overlay children", self.overlay_mgr.children)
        # Loop over plugins
        for p in self._plugins:

            # Set up a tuple to store list of unmet dependencies
            p_dep = (p["name"], [])

            # Until we hit a failure, there are no unmet dependencies
            unmet = False

            # Loop over dependencies and test if they exist
            for d in p["dependencies"]:
                try:
                    imp.find_module(d)
                except ImportError:
                    # We've got at least one unmet dependency for this screen
                    unmet = True
                    p_dep[1].append(d)
                    Logger.error("Unmet dependencies "
                                 "for {} screen. Skipping...".format(p["name"]))

            # Can we use the screen?
            if unmet:
                # Add the tupe to our list of unmet dependencies
                dep_fail.append(p_dep)

            # No unmet dependencies so let's try to load the screen.
            else:
                # This way we put the debug info to console instead of catching errors
                if DEBUG:
                    plugin = imp.load_module("screen", *p["info"])
                    screen = getattr(plugin, p["screen"])
                    self.scrmgr.add_widget(screen(name=p["name"],
                                                  master=self,
                                                  params=p["params"]))
                    Logger.info("Screen: {} loaded.".format(p["name"]))
                    # We can add the screen to our list of available screens.
                    self.available_screens.append(p["name"])
                else:
                    try:
                        plugin = imp.load_module("screen", *p["info"])
                        screen = getattr(plugin, p["screen"])
                        self.scrmgr.add_widget(screen(name=p["name"],
                                               master=self,
                                               params=p["params"]))
                        Logger.info("Screen: {} loaded.".format(p["name"]))

                    # Uh oh, something went wrong...
                    except Exception as e:
                        # Add the screen name and error message to our list
                        Logger.error("Could not import "
                                     "{} screen. Skipping...".format(p["name"]))
                        failed_screens.append((p["name"], repr(e)))

                    else:
                        # We can add the screen to our list of available screens.
                        self.available_screens.append(p["name"])

        # If we've got any failures then let's notify the user.
        if dep_fail or failed_screens:

            # Create the FailedScreen instance
            self.failscreen = FailedScreen(dep=dep_fail,
                                           failed=failed_screens,
                                           name="FAILEDSCREENS")

            # Add it to our screen manager and make sure it's the first screen
            # the user sees.
            self.scrmgr.add_widget(self.failscreen)
            self.scrmgr.current = "FAILEDSCREENS"

        # Update the overlay opacity to hide/show overlay depending on screen config
        self.overlay_opacity(self.scrmgr.current)

    def toggle_lock(self, locked=None):
        if locked is None:
            self.locked = not self.locked
        else:
            self.locked = bool(locked)

    def reload_screen(self, screen):
        # Remove the old screen...
        self.remove_screen(screen)

        # ...and add it again.
        self.add_screen(screen)

    def reload_overlay(self, overlay):
        # Remove the old overlay
        self.remove_overlay(overlay)

        # and add it again.
        self.add_overlay(overlay)

    def add_screen(self, screen_name):

        # Get the info we need to import this screen
        foundscreen = [p for p in getPlugins() if p["name"] == screen_name]

        # Check we've found a screen and it's not already running
        if foundscreen and screen_name not in self.available_screens:

            # Get the details for the screen
            p = foundscreen[0]

            # Import it
            plugin = imp.load_module("screen", *p["info"])

            # Get the reference to the screen class
            screen = getattr(plugin, p["screen"])

            # Add the KV file to the builder
            Builder.load_file(p["kvpath"])

            # Add the screen
            self.scrmgr.add_widget(screen(name=p["name"],
                                   master=self,
                                   params=p["params"]))

            # Add to our list of available screens
            self.available_screens.append(screen_name)

            # Activate screen
            self.switch_to(screen_name)

        elif screen_name in self.available_screens:

            # This shouldn't happen but we need this to prevent duplicates
            self.reload_screen(screen_name)

    def remove_screen(self, screen_name):

        # Get the list of screens
        foundscreen = [p for p in getPlugins(inactive=True) if p["name"] == screen_name]

        # Loop over list of available screens
        while screen_name in self.available_screens:

            # Remove screen from list of available screens
            self.available_screens.remove(screen_name)

            # Change the display to the next screen
            self.next_screen()

            # Find the screen in the screen manager
            c = self.scrmgr.get_screen(screen_name)

            # Call its "unload" method:
            if hasattr(c, "unload"):
                c.unload()

            # Delete the screen
            self.scrmgr.remove_widget(c)
            del c

        try:
            # Remove the KV file from our builder
            Builder.unload_file(foundscreen[0]["kvpath"])
        except IndexError:
            pass

    def remove_overlay(self, overlay):
        # Get the list of screens
        found_overlay = [p for p in get_overlays(inactive=True) if p["name"] == overlay]
        # TODO - Complete


        # Loop over list of available overlays
        # while overlay in self.available_overlays:

            # Remove overlay from list of available overlays
            # self.available_overlays.remove(overlay)

            # # Find the overlay in the overlay manager
            # c = self.overlay_mgr.get_screen(overlay)
            #
            # # Call its "unload" method:
            # if hasattr(c, "unload"):
            #     c.unload()
            #
            # # Delete the screen
            # self.overlay_mgr.remove_widget(c)
            # del c

        try:
            # Remove the KV file from our builder
            Builder.unload_file(found_overlay[0]["kvpath"])
        except IndexError:
            pass

    def add_overlay(self, overlay):
        # TODO - Complete
        pass

    def next_screen(self, rev=False):
        if not self.locked:
            if rev:
                self.scrmgr.transition.direction = "right"
                inc = -1
            else:
                self.scrmgr.transition.direction = "left"
                inc = 1

            self.index = (self.index + inc) % len(self.available_screens)
            self.scrmgr.current = self.available_screens[self.index]

            # Update the overlay opacity to hide/show overlay depending on screen config
            self.overlay_opacity(self.scrmgr.current)

    def switch_to(self, screen):

        if screen in self.available_screens:

            # Activate the screen
            self.scrmgr.current = screen

            # Update the screen index
            self.index = self.available_screens.index(screen)

            # Update the overlay opacity to hide/show overlay depending on screen config
            self.overlay_opacity(self.scrmgr.current)

    def overlay_opacity(self, screen_name):
        # Find Screen in screen manager
        c = self.scrmgr.get_screen(screen_name)
        for plugin in self._plugins:
            if plugin['name'] == screen_name:
                if plugin['show_overlay']:
                    self.overlay_mgr.opacity = 1
                else:
                    self.overlay_mgr.opacity = 0

    def toggle_overlay(self):
        if self.overlay_mgr.opacity == 1:
            self.overlay_mgr.opacity = 0
        elif self.overlay_mgr.opacity == 0:
            self.overlay_mgr.opacity = 1
        else:
            pass

# TODO Move Settings Screen Popup to it's own file

    def callback_for_setting_items(self, *args):
        toast(args[0])

    def toggle_settings(self):

        bs_menu = MyMDGridBottomSheet()
        bs_menu.add_item(
            "Blank",
            lambda x: self.callback_for_setting_items("Blank"),
            icon_src="images/10x10_transparent.png",
        )
        bs_menu.add_item(
            "Blank",
            lambda x: self.callback_for_setting_items("Blank"),
            icon_src="images/10x10_transparent.png",
        )
        bs_menu.add_item(
            "Facebook",
            lambda x: self.callback_for_setting_items("Brightness"),
            icon_src="images/brightness-5-black.png",
        )
        bs_menu.add_item(
            "Blank",
            lambda x: self.callback_for_setting_items("Blank"),
            icon_src="images/10x10_transparent.png",
        )
        bs_menu.add_item(
            "Blank",
            lambda x: self.callback_for_setting_items("Blank"),
            icon_src="images/10x10_transparent.png",
        )

        bs_menu.open()



Builder.load_string(
    """
<MyBottomIcon>
    
    
<MyGridBottomSheetItem>
    orientation: "vertical"
    padding: 0, 0, 0, 0
    size_hint_y: 50
    size_hint_x: 50
    width: 50
    height: 50
    #size: dp(64), dp(96)
    
    MyBottomIcon:
        id: icon
        size_hint_y: 48
        on_release: root.release_btn()
        source: root.source

    
"""
)


class MyBottomIcon(ButtonBehavior, Image):
    pass


class MyGridBottomSheetItem(BoxLayout):
    source = StringProperty()

    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        super().__init__(**kwargs)

        #Clock.schedule_once(self.bind_on_release)

    def release_btn(self):
        self.dispatch('on_release')

    def on_release(self):
        pass

    def bind_on_release(self, dt):
        pass
        #print(self.ids.icon)
        #self.ids.icon.bind(on_release=lambda x: self.on_release)

class MyMDGridBottomSheet(MDBottomSheet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._gl_content.padding = (dp(30), 0, dp(30), 0)  # (dp(0), 0, dp(0), dp(0))
        self._gl_content.height = 50  # dp(50)
        self._gl_content.cols = 6

    def add_item(self, text, callback, icon_src):
        MyGridBottomSheetItem()

        item = MyGridBottomSheetItem(on_release=callback, source=icon_src)
        self._gl_content.add_widget(item)
