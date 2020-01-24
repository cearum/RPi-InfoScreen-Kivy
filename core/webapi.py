'''Web interface for the Raspberry Pi Information Screen.

   original by elParaguayo and modified by cearum

   This module defines the underlying API.

   Screens can define their own web pages for custom configuration by using
   methods available in this API.

   API format:
    [HOST]/api/screens
        GET: returns JSON format of all available screens

    [HOST]/api/screens/current
        GET: currently displayed screen

    [HOST]/api/screens/<screen_name>/configurations
        GET: returns JSON format of user-configurable settings for screen
        POST: takes JSON format of updated configuration.

    [HOST]/api/screens/<screen_name>/enable
        GET: enable the selected screen

    [HOST]/api/screens/<screen_name>/disable
        GET: disable the selected screen

    [HOST]/api/screens/<screen_name>/restart
        GET: restart the selected screen

    [HOST]/api/screens/<screen_name>/view
        GET: change to screen


    API Response format:
     successful:
       {"status": "success",
        "data": [body of response]}

     unsuccessful:
       {"status": "error",
        "message": [Error message]}

    /api/display/notification
    /api/display/video
    /api/display/image

    /api/overlays
    /api/overlays/view

    /api/overlays/<overlay_name>/enable
    /api/overlays/<overlay_name>/disable
    /api/overlays/<overlay_name>/restart
    /api/overlays/<overlay_name>/configurations
    configurations

    /api/configurations
    /api/configurations/units/{si, uk, us}
    /api/configurations/display/brightness{/int 0:100}
    /api/configurations/notifications
    /api/configurations/notifications/state{/on or /off}
    /api/configurations/notifications/duration{/(int 0 to 600)}
'''

from threading import Thread
from time import sleep
import os
import json
import imp

from kivy.app import App

from bottle import Bottle, template, request, response

from core.getplugins import getPlugins


class InfoScreenAPI(Bottle):
    def __init__(self, infoscreen, folder):
        super(InfoScreenAPI, self).__init__()

        # Get reference to base screen object so API server can
        # access methods
        self.infoscreen = infoscreen.base

        # Get the folder path so we can access config files
        self.folder = folder

        # Get the list of screens
        #self.process_plugins()

        # Define our routes
        self.route("/", callback=self.default)
        self.error_handler[404] = self.unknown

        # API METHODS
        self.route("/api/screens",
                   callback=self.get_screens,
                   method="GET")
        self.route("/api/screens/<screen>/configurations",
                   callback=self.get_config,
                   method="GET")
        self.route("/api/screens/<screen>/configurations",
                   callback=self.set_config,
                   method="POST")
        self.route("/api/screens/<screen>/enable",
                   callback=self.enable_screen)
        self.route("/api/screens/<screen>/disable",
                   callback=self.disable_screen)
        self.route("/api/screens/<screen>/view",
                   callback=self.view)

        self.route("/api/overlays/<overlay_name>/configurations",
                   callback=self.set_overlay_config,
                   method="POST")
        self.route("/api/overlays/<overlay_name>/enable",
                   callback=self.enable_overlay)
        self.route("/api/overlays/<overlay_name>/disable",
                   callback=self.disable_overlay)

    def api_success(self, data):
        """Base method for response to successful API calls."""

        return {"status": "success",
                  "data": data}

    def api_error(self, message):
        """Base method for response to unsuccessful API calls."""

        return {"status": "error",
                  "message": message}

    def get_screens(self):
        result = self.api_success(self.infoscreen.available_screens)
        return result

    def get_config(self, screen):
        """Method to retrieve config file for screen."""

        # Define the path to the config file
        conffile = os.path.join(self.folder, "screens", screen, "conf.json")

        if os.path.isfile(conffile):

            # Get the config file
            with open(conffile, "r") as cfg_file:

                # Load the JSON object
                conf = json.load(cfg_file)

            # Return the "params" section
            result = self.api_success(conf.get("params", dict()))

        else:

            # Something's gone wrong
            result = self.api_error("No screen called: {}".format(screen))

        # Provide the response
        return json.dumps(result)

    def set_config(self, screen):

        try:
            # Get JSON data
            js = request.json

            if js is None:
                # No data, so provide error
                return self.api_error("No JSON data received. "
                                      "Check headers are set correctly.")

            else:
                # Try to save the new config
                success = self.save_config(screen, js)

                # If successfully saved...
                if success:

                    # Reload the screen with the new config
                    self.infoscreen.reload_screen(screen)

                    # Provide success notification
                    return self.api_success(json.dumps(js))

                else:
                    # We couldn't save new config
                    return self.api_error("Unable to save configuration.")

        except:
            # Something's gone wrong
            return self.api_error("Invalid data received.")

    def set_overlay_config(self, overlay_name):

        try:
            # Get JSON data
            js = request.json

            if js is None:
                # No data, so provide error
                return self.api_error("No JSON data received. "
                                      "Check headers are set correctly.")

            else:
                # Try to save the new config
                success = self.save_config(overlay_name, js, "overlays")

                # If successfully saved...
                if success:

                    # Reload the screen with the new config
                    self.infoscreen.reload_screen(overlay_name)

                    # Provide success notification
                    return self.api_success(json.dumps(js))

                else:
                    # We couldn't save new config
                    return self.api_error("Unable to save configuration.")

        except:
            # Something's gone wrong
            return self.api_error("Invalid data received.")

    def enable_overlay(self, overlay_name):
        try:
            # Update status in config
            self.change_overlay_state(overlay_name, True)

            # Reload all Overlays (so far the best way I've found as it's not possible to find specific
            # overlay like you can with the screens)
            self.infoscreen.load_all_overlays(reload=True)

            # Success!
            return self.api_success("{} overlay enabled.".format(overlay_name))

        except:

            # Something went wrong
            return self.api_error("Could not enable {} overlay.".format(overlay_name))

    def disable_overlay(self, overlay_name):

        try:

            # Update status in config
            self.change_overlay_state(overlay_name, False)

            # Reload all Overlays (so far the best way I've found as it's not possible to find specific
            # overlay like you can with the screens)
            self.infoscreen.load_all_overlays(reload=True)

            # Success!
            return self.api_success("{} overlay disabled.".format(overlay_name))

        except:

            # Something went wrong
            return self.api_error("Could not disable {} overlay.".format(overlay_name))

    def default(self):
        # Generic response for unknown requests
        result = self.api_error("Invalid method.")
        return json.dumps(result)

    def unknown(self, addr):
        return self.default()

    def view(self, screen):
        try:
            self.infoscreen.switch_to(screen)
            return self.api_success("Changed screen to: {}".format(screen))
        except:
            return self.api_error("Could not change screen.")

    # Helper Methods ###########################################################

    def save_config(self, widget, params, folder=None):
        if folder is None:
            try:
                conf_file = os.path.join(self.folder, "screens", widget, "conf.json")
                conf = json.load(open(conf_file, "r"))
                conf["params"] = params
                with open(conf_file, "w") as config:
                    json.dump(conf, config, indent=4)
                return True
            except:
                return False
        elif folder is "overlays":
            try:
                conf_file = os.path.join(self.folder, "overlays", widget, "conf.json")
                conf = json.load(open(conf_file, "r"))
                conf["params"] = params
                with open(conf_file, "w") as config:
                    json.dump(conf, config, indent=4)
                self.infoscreen.reload_overlay(widget)
                return True
            except:
                return False

    def enable_screen(self, screen):
        try:
            # Update status in config
            self.change_screen_state(screen, True)

            # Make sure the screen is added
            self.infoscreen.add_screen(screen)

            # Success!
            return self.api_success("{} screen enabled.".format(screen))

        except:

            # Something went wrong
            return self.api_error("Could not enable {} screen.".format(screen))

    def disable_screen(self, screen):
        try:
            # Update status in config
            self.change_screen_state(screen, False)

            # Make sure the screen is added
            self.infoscreen.remove_screen(screen)

            # Success!
            return self.api_success("{} screen disabled.".format(screen))
        except:

            # Something went wrong!
            return self.api_error("Could not disable {} screen.".format(screen))

    def change_screen_state(self, screen, enabled):

        # Build path to config
        conffile = os.path.join(self.folder, "screens", screen, "conf.json")

        # Load existing config
        with open(conffile, "r") as f_config:
            conf = json.load(f_config)

        # Change status to desired state
        conf["enabled"] = enabled

        # Save the updated config
        with open(conffile, "w") as f_config:
            json.dump(conf, f_config, indent=4)

    def change_overlay_state(self, overlay, enabled):

        # Build path to config
        conf_file = os.path.join(self.folder, "overlays", overlay, "conf.json")

        # Load existing config
        with open(conf_file, "r") as f_config:
            conf = json.load(f_config)

        # Change status to desired state
        conf["enabled"] = enabled

        # Save the updated config
        with open(conf_file, "w") as f_config:
            json.dump(conf, f_config, indent=4)