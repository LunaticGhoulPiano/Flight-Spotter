from adsb_lol_api import ADSB_LOL_API
import gps

api = ADSB_LOL_API()
loc = gps.getLoc()
if type(loc) == gps.PermissionError:
    print(loc)
elif type(loc) == gps.NotSupportedError:
    print(loc)
else:
    lat = loc[0]
    lon = loc[1]
    radius = 250
    print(api.get_closest(loc[0], loc[1], 250))