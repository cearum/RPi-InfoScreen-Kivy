'''Web interface for the Raspberry Pi Information Screen.

   by elParaguayo

   There are two parts to the web interface:

   - Web frontend (user-friendly means for customising screens etc)
   - API (for making changes to screens)

   Screens are able to provide their own web pages via the frontend.

   Once the screen is running, use a web browser to open the following URL:
     http://(IP address of Pi):(web port)
'''

from threading import Thread
from time import sleep
import os
import json
import imp

from kivy.app import App

from bottle import Bottle, template, request, TEMPLATE_PATH, redirect
import requests

from core.getplugins import getPlugins
from core.getoverlays import get_overlays
from core.webapi import InfoScreenAPI

HEADER = '''Raspberry Pi Information Screen<br />'''

SCREEN_CONFIG = '''% rebase("base.tpl", title="Configuration Screen: {}".format(screen.capitalize()))
    <form action="/configure/screen/{{screen}}" method="POST">
    <br />
    <textarea cols="60" rows="10" name="params" maxlength="2500">{{conf}}</textarea><br />
    <br />
    <button type="submit">Save Config</button></form>'''

OVERLAY_CONFIG = '''% rebase("base.tpl", title="Configuration Screen: {}".format(overlay.capitalize()))
    <form action="/configure/overlay/{{overlay}}" method="POST">
    <br />
    <textarea cols="60" rows="10" name="params" maxlength="2500">{{conf}}</textarea><br />
    <br />
    <button type="submit">Save Config</button></form>'''

class InfoScreenWebServer(Bottle):
    """This is the web frontend for the Raspberry Pi Information Screen.

       The default screen lists all screens installed on the system. From there
       the user is able to customise screens directly.
    """
    def __init__(self, infoscreen, folder, apiport):
        super(InfoScreenWebServer, self).__init__()

        # We need access to the infoscreen base object in order to manipulate it
        self.infoscreen = infoscreen.base

        # Get the folder path so we can build paths to templates etc.
        self.folder = folder

        # Set up the api
        self.api = "http://localhost:{}/api/".format(apiport)

        # Set up templates
        tpls = os.path.join(self.folder, "web", "templates")
        TEMPLATE_PATH.insert(0, tpls)

        # Initialise dictionary for custom web pages provided by screens
        self.custom_screens = {}

        # Build the dictionary of available screens
        self.screens = None
        self.process_plugins()
        self.overlays = None
        self.process_overlays()

        # Define our routes
        self.route("/configure/screen/<screen>", callback=self.update_screen_config, method="GET")
        self.route("/configure/screen/<screen>", callback=self.save_screen_config, method="POST")
        self.route("/configure/overlay/<overlay>", callback=self.update_overlay_config, method="GET")
        self.route("/configure/overlay/<overlay>", callback=self.save_overlay_config, method="POST")
        self.route("/view/<screen>", callback=self.view)
        self.route("/", callback=self.list_screens, method=["GET", "POST"])

        # See if there are any custom screens
        self.add_custom_routes()

    def process_plugins(self):
        # Build a dictionary of screens, their current state and whether or not
        # they provide a custom screen
        self.screens = {s["name"]: {"web": s["web"], "enabled": s["enabled"]}
                         for s in getPlugins(True)}

    def process_overlays(self):
        self.overlays = {s["name"]: {"web": s["web"], "enabled": s["enabled"]}
                         for s in get_overlays(True)}

    def add_custom_routes(self):

        # Get the custom screen dictionary
        sc = self.screens

        # Get a list of just those screens who have custom web pages
        addons = [(x, sc[x]["web"]) for x in sc if sc[x]["web"]]

        # Get the custom overlay dictionary
        ol = self.overlays
        overlays = [(x, ol[x]["web"]) for x in ol if ol[x]["web"]]

        # Loop over the list
        for screen, addon in addons:

            # Load the module
            plugin = imp.load_module("web", *addon)

            # Loop over the list of web pages...
            for route in plugin.bindings:

                # ...and add to the available routes
                self.route(route[0],
                           callback=getattr(plugin, route[1]),
                           method=route[2])

            # We also need to store the default page to make it accessible via
            # the list of installed screens
            self.custom_screens[screen] = plugin.bindings[0][0]

        for overlay, addon in overlays:

            # Load the module
            plugin = imp.load_module("web", *addon)

            # Loop over the list of web pages...
            for route in plugin.bindings:

                # ...and add to the available routes
                self.route(route[0],
                           callback=getattr(plugin, route[1]),
                           method=route[2])

            # We also need to store the default page to make it accessible via
            # the list of installed screens
            self.custom_screens[overlay] = plugin.bindings[0][0]

    def valid_screen(self, screen):
        """Returns True if screen is installed and enabled."""
        return (screen is not None and
                screen in self.infoscreen.availablescreens)

    def list_screens(self):
        """Provides a list of all installed screens with various options."""

        # Check if the form ws submitted
        form = request.forms.get("submit", False)

        # If so...
        if form:

            # ...find out what the user wanted to do and to which screen
            try:
                action, screen, overlay = form.split("+")
            except ValueError:
                overlay = None
                action, screen = form.split("+")

            if overlay is None:
                # Call the relevant action
                if action == "view":
                    r = requests.get("{}screens/view/{}".format(self.api, screen))

                elif action == "enable":
                    r = requests.get("{}screens/enable/{}".format(self.api, screen))

                elif action == "disable":
                    r = requests.get("{}screens/disable/{}".format(self.api, screen))

                elif action == "configure":
                    redirect("/configure/screen/{}".format(screen))

                elif action == "custom":
                    url = self.custom_screens.get(screen, "/")
                    redirect(url)
            else:
                # Call the relevant action
                if action == "view":
                    r = requests.get("{}overlays/view/{}".format(self.api, screen))

                elif action == "enable":
                    r = requests.get("{}overlays/enable/{}".format(self.api, screen))

                elif action == "disable":
                    r = requests.get("{}overlays/disable/{}".format(self.api, screen))

                elif action == "configure":
                    redirect("/configure/overlay/{}".format(screen))

                elif action == "custom":
                    url = self.custom_screens.get(screen, "/")
                    redirect(url)

        # Rebuild list of screens
        self.process_plugins()
        self.process_overlays()
        sc = self.screens
        ol = self.overlays

        # Return the web page
        return template("all_screens_overlays.tpl", screens=sc, overlays=ol)

    def view(self, screen=None):
        """Method to switch screen."""
        r = requests.get("{}/screens/view/{}".format(self.api, screen))

        return template("all_screens.tpl", screens=self.screens)

    def update_screen_config(self, screen=None):

        if screen in self.screens:

            # Build the path to our config file
            conffile = os.path.join(self.folder, "screens", screen, "conf.json")

            # Open the file and load the config
            with open(conffile, "r") as cfg_file:
                params = json.load(cfg_file)

            # We only want the user to edit the "params" section so just
            # retrieve that part
            conf = json.dumps(params.get("params", dict()), indent=4)

            # Build the web page
            return template(SCREEN_CONFIG, screen=screen, conf=conf)

    def save_screen_config(self, screen):

        # Flag to indicate whether params have changed
        change_params = False

        # Get the new params from the web form
        try:
            params = json.loads(request.forms.get("params"))
        except ValueError:
            return "INVALID JSON"
        else:
            # Let's check if the params have changed

            # Build the path to our config file
            conffile = os.path.join(self.folder, "screens", screen, "conf.json")

            # Open the file and load the config
            with open(conffile, "r") as cfg_file:
                conf = json.load(cfg_file)

            # Check if the form is the same as the old one
            if conf.get("params", dict()) != params:

                # If not, we need to update
                change_params = True

            if change_params:
                # Submit the new params to the API
                r = requests.post("{}screens/configure/{}".format(self.api, screen), json=params)

            redirect("/")

    def update_overlay_config(self, overlay=None):

        if overlay in self.screens:

            # Build the path to our config file
            conffile = os.path.join(self.folder, "overlays", overlay, "conf.json")

            # Open the file and load the config
            with open(conffile, "r") as cfg_file:
                params = json.load(cfg_file)

            # We only want the user to edit the "params" section so just
            # retrieve that part
            conf = json.dumps(params.get("params", dict()), indent=4)

            # Build the web page
            return template(OVERLAY_CONFIG, overlay=overlay, conf=conf)

    def save_overlay_config(self, overlay):

        # Flag to indicate whether params have changed
        change_params = False

        # Get the new params from the web form
        try:
            params = json.loads(request.forms.get("params"))
        except ValueError:
            return "INVALID JSON"
        else:
            # Let's check if the params have changed

            # Build the path to our config file
            conffile = os.path.join(self.folder, "overlays", overlay, "conf.json")

            # Open the file and load the config
            with open(conffile, "r") as cfg_file:
                conf = json.load(cfg_file)

            # Check if the form is the same as the old one
            if conf.get("params", dict()) != params:

                # If not, we need to update
                change_params = True

            if change_params:
                # Submit the new params to the API
                r = requests.post("{}overlays/configure/{}".format(self.api, overlay), json=params)

            redirect("/")

def start_web(appdir, webport, apiport, debug=False):
    """Starts the webserver on "webport"."""
    infoapp = None

    while infoapp is None:
        infoapp = App.get_running_app()
        if getattr(infoapp, "base", None) is None:
            infoapp = None
        sleep(1)

    ws = InfoScreenWebServer(infoapp, appdir, apiport)

    ws.run(host="0.0.0.0", port=webport, debug=debug)

def start_api(appdir, apiport, debug=False):
    """Starts the API server on "apiport"."""
    infoapp = None

    while infoapp is None:
        infoapp = App.get_running_app()
        if getattr(infoapp, "base", None) is None:
            infoapp = None
        sleep(1)

    ws = InfoScreenAPI(infoapp, appdir)

    ws.run(host="0.0.0.0", port=apiport, debug=debug)

def start_web_server(appdir, webport=8088, apiport=8089, debug=False):
    # Create the webserver in a new thread
    t = Thread(target=start_web, args=(appdir, webport, apiport, debug))

    # Daemonise it
    t.daemon = True

    # Go!
    t.start()

    # Create the API server in a new thread
    api = Thread(target=start_api, args=(appdir, apiport))

    # Daemonise it
    api.daemon = True

    # Go!
    api.start()
