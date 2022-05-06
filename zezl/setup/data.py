#!/opt/bin/python3
from setup.description import etag


APP_NAME = "zezl"
DEMON_NAME = 'zpu'
BACKUP_DIR_NAME = 'backups'
VERSION = "1.1 beta 1"
APP_INITD_NAME = f"S61{APP_NAME}"

CRON_FILE = "/opt/etc/crontab"
CONFIG_FILE_NAME = f"{APP_NAME}.conf"
CRON_PERIODS = {"m": 0, "h": 1, "d": 2, "w": 3, "n": 4}

TIMER_FORMAT = "%d-%m-%y %H:%M"
BACKUP_FORMAT_FILENAME = "%d_%m_%y-%H_%M"
WDOG_SAVE_FORMAT = '%d%m%Y%H%M%S'
ROUTER_LOG_DATE_FORMAT = "%a, %d %b %Y %X %Z"

ETC_PATH = '/opt/etc'
DEMON_PATH = '/opt/bin'
APP_PATH = f'/opt/apps/{APP_NAME}'
CONFIG_PATH = f'{ETC_PATH}/{APP_NAME}'
CONFIG_FILE = f"{CONFIG_PATH}/{CONFIG_FILE_NAME}"
BACKUP_PATH = f"{ETC_PATH}/{APP_NAME}/{BACKUP_DIR_NAME}"
LOG_FILE = f"{CONFIG_PATH}/{APP_NAME}.log"

LINK_LIST_FILE = f"{CONFIG_PATH}/links.watch"


CMD_GET_ROUTE = "localhost:79/rci/ip/route"
CMD_GET_INTERFACE = "localhost:79/rci/show/interface"
CMD_GET_DNS = "localhost:79/rci/show/ip/name-server"
CMD_GET_SYSLOG = "localhost:79/rci/show/log"
# CMD_GET_IKEV2 = "localhost:79/rci/crypto/map"

LINE = '---------------------------------------------------\n'
HOST_PATTERN = r"[a-zA-Zа-яА-Я0-9]{2,63}[\.][a-z]{2,5}"

DELAY_BEFORE_DELETE = 4
LIMIT_RECORDS_FOR_BACKGROUND = 10
WDOGS_DELAY_BEFORE_DELETE = 3600

DNS_SELECTED: str = ''
NEED_TO_CHECK_CONFIG_FILE: bool = True


class InRow:
    MENU_BUTTONS_INROW = 3
    INLINE_LISTITEMS_INROW = 1
    CMD_BUTT_INROW = 2


# Список доступных интерфейсов в роутере
INTERFACE_TYPES = [
    etag.openvpn,
    etag.wireguard,
    etag.ike,
    etag.sstp,
    etag.pppoe,
    etag.l2tp,
    etag.dongle,  # usb dongle - сотовый оператор через usb "свисток"
]

# Список полей, которые могут быть получены об интерфейсе
INTERFACE_FIELDS = [
    etag.description,
    etag.connected,
    etag.link,
    etag.state,
    etag.mac
]

