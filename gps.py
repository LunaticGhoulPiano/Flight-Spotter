import asyncio
import platform
import winsdk.windows.devices.geolocation as wdg

class NotSupportedError(Exception):
    def __init__(self, platform_name):
        super().__init__(f"ERROR: Platform '{platform_name}' not supported.")
        self.platform_name = platform_name

class PermissionError(Exception):
    def __init__(self):
        super().__init__("ERROR: You need to allow applications to access your location.")

async def getCoords():
    system_name = platform.system()
    match system_name:
        case 'Windows':
            locator = wdg.Geolocator()
            pos = await locator.get_geoposition_async()
            return [pos.coordinate.point.position.latitude, pos.coordinate.point.position.longitude]
        case _:
            raise NotSupportedError(system_name)

def getLoc():
    try:
        return asyncio.run(getCoords())
    except PermissionError as e:
        return e
    except NotSupportedError as e:
        return e