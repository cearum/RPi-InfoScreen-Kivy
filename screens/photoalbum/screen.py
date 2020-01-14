from glob import glob
import os

from kivy.clock import Clock
from kivy.properties import (ObjectProperty,
                             StringProperty,
                             BoundedNumericProperty)
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from random import shuffle
from imghdr import what


class BlackHole(object):
    def __init__(self, **kw):
        super(BlackHole, self).__init__()

class Photo(Screen):
    """Screen object to display a photo."""
    photo_path = StringProperty("")

    def __init__(self, **kwargs):
        super(Photo, self).__init__(**kwargs)
        self.photo_path = self.name


class PhotoLoading(Screen):
    """Holding screen to display while the screen retrieves the list of
       photos.
    """
    pass


class PhotoAlbumScreen(Screen, BlackHole):
    """Base screen to run the photo album."""

    # Reference to the screen manager
    photoscreen = ObjectProperty(None)

    # Value for the screen display time
    photoduration = BoundedNumericProperty(5, min=2, max=60, errorvalue=5)

    def __init__(self, params, **kwargs):
        super(PhotoAlbumScreen, self).__init__(**kwargs)

        # Get the user's preferences
        self.folders = params["folders"]
        # self.exts = params["extensions"]
        self.photoduration = params["duration"]
        self.allow_shuffle = params.get("random", True)

        # Initialise some useful variables
        self.running = False
        self.photos = []
        self.timer = None
        self.oldPhoto = None
        self.photoindex = 0

    def on_enter(self):

        if not self.running:

            # The screen hasn't been run before so let's tell the user
            # that we need to get the photos
            self.loading = PhotoLoading(name="loading")
            self.photoscreen.add_widget(self.loading)
            self.photoscreen.current = "loading"

            # Retrieve photos
            Clock.schedule_once(self.getPhotos, 0.5)

        else:
            # We've been here before so just show the photos
            self.timer = Clock.schedule_interval(self.showPhoto,
                                                 self.photoduration)

    def on_leave(self):

        # We can stop looping over photos
        Clock.unschedule(self.timer)

    def getPhotos(self, *args):
        """Method to retrieve list of photos based on user's preferences."""

        # Get a list of extensions. Assumes all caps or all lower case.
        # exts = []
        # for ext in ([x.upper(), x.lower()] for x in self.exts):
        #     exts.extend(ext)

        # Loop over the folders
        for folder in self.folders:
            for (path, dirs, files) in os.walk(folder):
                for the_file in files:
                    path_file = os.path.join(path, the_file)

                    # uses what from IMGHDR to check for image file types
                    file_type = what(path_file)

                    # If the image type matches an image we go one further
                    if file_type is not None:

                        # We don't want Gif's though as they don't work well
                        if file_type is not 'gif':

                            self.photos.append(path_file)

        # shuffle if requested
        if self.allow_shuffle:
            shuffle(self.photos)
        else:  # Put the photos in order
            self.photos.sort()

        # We've got the photos so we can set the running flag
        self.running = True

        # and start the timer
        self.timer = Clock.schedule_interval(self.showPhoto,
                                             self.photoduration)

        # Show the first photo
        self.showPhoto()

    def showPhoto(self, *args):
        """Method to update the currently displayed photo."""

        # Get the current photo
        photo = self.photos[self.photoindex]

        # Create a screen object to show that photo
        scr = Photo(name=photo)

        # Add it to our screen manager and display it
        self.photoscreen.add_widget(scr)
        self.photoscreen.current = photo

        # If we've got an old photo
        if self.oldPhoto:

            # We can unload it
            self.photoscreen.remove_widget(self.oldPhoto)

        # Create reference to the new photo
        self.oldPhoto = scr

        # Increase our index for the next photo
        self.photoindex = (self.photoindex + 1) % len(self.photos)

        # If we hit the end of the photos reshuffle
        if self.photoindex == len(self.photos):
            if self.allow_shuffle:
                shuffle(self.photos)
