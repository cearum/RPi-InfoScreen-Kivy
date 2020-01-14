import imp
import os
import json

# Constants that are used to find overlays
OverlayFolder = "./overlays"
OverlayScript = "overlay.py"
OverlayConf = "conf.json"


def get_overlays(inactive=False):
    overlays = []
    a = 1

    # Get the contents of the widget folder
    possible_widgets = os.listdir(OverlayFolder)

    # Loop over it
    for i in possible_widgets:
        location = os.path.join(OverlayFolder, i)

        # Ignore anything that doesn't meet our criteria
        if not os.path.isdir(location) or OverlayScript not in os.listdir(location):
            continue

        # Load the module info into a variables
        inf = imp.find_module("overlay", [location])

        # Widget needs a conf file.
        if OverlayConf in os.listdir(location):
            conf = json.load(open(os.path.join(location, OverlayConf)))

            # See if the user has disabled the widget.
            if conf.get("enabled", False) or inactive:

                # Get the KV file text
                kvpath = os.path.join(location, conf["kv"])
                kv = open(kvpath).readlines()

                # See if there's a web config file
                webfile = os.path.join(location, "web.py")
                if os.path.isfile(webfile):
                    web = imp.find_module("web", [location])
                else:
                    web = None

                # Custom dict for the widget
                overlay = {"name": i,
                          "info": inf,
                          "id": a,
                          "overlay": conf["overlay"],
                          "dependencies": conf.get("dependencies", list()),
                          "kv": kv,
                          "kvpath": kvpath,
                          "params": conf.get("params", None),
                          "enabled": conf.get("enabled", False),
                          "web": web}

                overlays.append(overlay)
                a = a + 1

    # We're done so return the list of available/enabled overlays
    return overlays
