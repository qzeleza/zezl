import json

from libraries.main import tools as tools
from setup.data import etag


def get_list_devices() -> dict:
    cmd_request = 'curl -s localhost:79/rci/show/ip/hotspot'
    is_ok, output = tools.run(cmd_request)
    if is_ok:
        all_in_dict = json.loads(output)
        all_devices = all_in_dict[etag.host]
    else:
        all_devices = {}

    return all_devices


def list_devices_online() -> list:
    all_devices = get_list_devices()
    # dev_dict = {}
    result = list
    if all_devices:
        # _ = [dev_dict.update({dev[tag.name]: {tag.ip: dev[tag.ip], tag.mac:dev[tag.mac]}})
        #      for dev in all_devices if dev[tag.active]]
        # result = [rf'{dev[tag.name]}: "{dev[tag.ip]} {dev[tag.mac]}"'
        #      for dev in all_devices if dev[tag.active]]
        result = [rf'{dev[etag.name]} {dev[etag.ip]}' for dev in all_devices if dev[etag.active]]
        del all_devices

    # result = {
    #     "Телефон сына": "10.0.22.11",
    #     "Телефон жены": "10.0.22.8",
    #     "Сервер": "10.0.22.2",
    #     "Ноутбук": "10.0.22.12",
    # }
    return result


def about_model() -> str:
    result = """Keenetic KN 1810
    Версия прошивки 11.1111.432
    """
    return result
