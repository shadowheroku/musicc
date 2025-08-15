from Yumeko_Music.core.bot import Aviax
from Yumeko_Music.core.dir import dirr
from Yumeko_Music.core.git import git
from Yumeko_Music.core.userbot import Userbot
from Yumeko_Music.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Aviax()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
