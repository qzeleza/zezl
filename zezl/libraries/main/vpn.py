#!/opt/bin/python3
# -*- coding: UTF-8 -*-

#
#  Copyright (c) 2022.
#
#  Автор: mail@zeleza 04.2022
#  Вся сила в правде!
#

#
#

# Автор: zeleza
# Вся сила в правде!
# Email: info@zeleza.ru
# Дата создания: 24.04.2022 18:03
# Пакет: PyCharm

"""

 Файл содержит библиотеку работы с туннелями VPN

"""

import json
from subprocess import DEVNULL
from time import sleep

from libraries.main import tools as tools
from libraries.main.config import get_config_value, set_config_value
# from dialog import list_chunk
from logs.logger import zlog
from setup.autosets import (
    CREATE_NEW, ADD_TO_END, ROUTER, NET,
)
from setup.data import (
    CRON_FILE,
    CONFIG_FILE,
    BACKUP_PATH,
    CONFIG_PATH,
    DEMON_NAME,
    etag, LINE,
    DEMON_PATH,
    INTERFACE_FIELDS, INTERFACE_TYPES,
    BACKUP_FORMAT_FILENAME,
    CMD_GET_INTERFACE, CMD_GET_DNS, CMD_GET_ROUTE,
)
from setup.description import (
    ErrorTextMessage as Error,
    be, bs, icon,
)

INTERFACE, HOST = range(2)


def get_dns_config() -> list:
    """
    Функция получает список dns адресов из файла конфигурации

    :return: список dns адресов
    """
    # получаем данные DNS из файла конфигурации
    result = get_config_value(name=etag.dns)

    if result:
        # если результат не пустой,
        # то формируем список dns отделяя значения точкой с запятой;
        result = result.split(etag.pdot)
    else:
        # если данных из файла конфигурации не получено,
        # то получаем данные о dns из системы
        dns_list = get_system_dns_list()
        # проверяем
        _, result = check_dns_tls(dns_list)
        # Формируем строку с разделителем - точка с запятой;
        value = etag.pdot.join(result)
        # сохраняем значение в файле конфигурации
        set_config_value(name=etag.dns, value=value)

    return result


def set_dns_config(dns_list: list) -> str:
    """
    Функция записывает значения DNS в файл конфигурации

    :param dns_list: список значений DNS
    :return: сообщение об успешности завершения команды
    """

    # Название переменной только в верхнем регистре
    dns_tag = etag.dns.upper()
    # команда bash сначала удаляет предыдущее значение, затем добавляет в файл новое
    cmd = f"sed -i '/{dns_tag}=/d' {CONFIG_FILE} && echo '{dns_tag}={etag.pdot.join(dns_list)}' >> {CONFIG_FILE}"
    is_ok, _ = tools.run(command=cmd)
    # в зависимости от результата формируем сообщение о завершении функции
    if is_ok:
        _result = f"DNS сервер/а успешно изменен/ы на {', '.join(dns_list)}."
    else:
        _result = f"{Error.INDICATOR} DNS сервер/а записать НЕ удалось."
    return _result


def remove_timer() -> str:
    """
    Функция удаляет строку обновления данных tunnels из крона

    :return: сообщение о результате операции удаления

    """
    is_ok, out = tools.run(f'sed -i /{DEMON_NAME}/d {CRON_FILE}')
    result = f"Таймер успешно удален." if is_ok else f"{Error.INDICATOR} Таймер удалить не удалось!"
    return result


def set_timer_period(data: str = None) -> str:
    """
    Функция устанавливает таймер обновления ip адресов доменов
    в зависимости от заданного параметра period

    :param data: строка состоящая из 2 частей: числа (интервал) и символа периода
                   например - 22m, обновление каждые 22 минуты, возможные значения:
                   m - минуты,
                   h - часы,
                   d - дни,
                   w - недели,
                   M - месяца
    :return: сообщение об успешности установки таймера

    """
    if not data:
        # в случае, если параметр отсутствует, тогда выводим текущее значение таймера обновления
        return get_timer_period()

    # задаем шаблон это от 1 до 2 цифр и далее одна из букв 'mhwdM', без пробела
    # пример 22w или 60d или 24m, проверку на
    regex = r"(\d{1,2}[mhwdM]{1})"
    # провидим проверку на верность введенного периода
    from re import findall
    period = "".join(findall(regex, data))
    # проверяем на корректность ввода данных
    if period:
        # В случае если данные введены корректно...
        # error_message = None
        # задаем словарь периодов для автоматизации процесса установки периода в крон
        periods = {"m": 0, "h": 1, "d": 2, "w": 3, "M": 4}
        # строка крона превращенная в список
        cron_file = f"{DEMON_PATH}/{DEMON_NAME}"
        # разбиваем строку крона на части для последующей обработки
        crontab = ["0", "*", "*", "*", "*", "root", f"{cron_file}", f"{etag.update}\n"]
        #  если параметр задан, то получаем значение интервала
        interval = int("".join([k for k in period if k.isdigit()]))
        # получаем значение периода
        period = period[-1]

        # проводим проверку верности ввода значений интервала
        # и в случае возможности автоматически их корректируем
        # match period:
        #     case 'm':
        #         if interval <= 0:
        #             error_message = 'Значение интервала не может быть меньше или рано нулю.'
        #         elif interval > 60:
        #             hours = int(interval/60)
        #             mins = interval%60
        #             if hours > 23:
        #                 error_message = 'Значение интервала в минутах превышает количество минут в сутках.'
        #
        #     case _:

        # удаляем предыдущий таймер
        remove_timer()
        # формируем крона в соответствии с заданными параметрами
        crontab[periods[period]] = f"0/{interval}" if period == 'm' else f"*/{interval}"
        timer = " ".join(crontab)
        # записываем строку в файл крона
        if tools.write_to_file(file=CRON_FILE, lines=[timer], mode=ADD_TO_END):
            result = f"Период обновления {bs}{interval}{period}{be} успешно установлен."
        else:
            result = f"{Error.INDICATOR} Период обновления " \
                     f"{bs}{interval}{period}{be} установить не удалось!"
    else:
        # в случае, если параметр отсутствует, значит он был введен не верно
        # тогда выводим сообщение об ошибке и текущее значение таймера обновления
        result = f"{bs}{Error.INDICATOR}{be} Введенный период содержит ошибки.\n" \
                 "Попробуйте их исправить и ввести заново.\n" \
                 f"Примеры корректного ввода: {bs}33m 44d 33w 6M{be}."

    return result


def get_timer_period() -> str:
    """
    Функция получает из крона и преобразует
    из кода в текстовое значение период обновления

    :return: текстовое значение периода обновления
             пример: 22 мин, 2 час, 3 дн

    """
    # задаем список текстовых преобразователей кода
    periods_text = ["мин", "час", "дн", "нед", "мес", ]
    # ищем в кроне соответствие в получаем строку с данными
    crontab = tools.find_in_file(CRON_FILE, DEMON_NAME)
    result = f"{Error.INDICATOR} Период обновления получить не удалось!"
    # проверяем наличие строки из крона
    if crontab:
        # в случае наличия строки получаем список из значений крона
        crontab = crontab.split(" ")
        # обрабатываем только первых 4 значения из списка, так как именно в них
        # зашита информация о периодах обновления данных
        index = [k for k in range(len(crontab)) if ("*/" in crontab[k] or "0/" in crontab[k]) and k < 5][0]
        # формируем строку с данными из крона и преобразуем ее в текстовое сообщение
        result = f"{tools.get_digits(crontab[index])} {periods_text[index]}."

    return result


def get_interface_name(interface: str) -> str:
    """
    Функция возвращает имя (description) заданного интерфейса.
    :param interface: номер интерфейса.
    :return: случае успеха возвращаем имя интерфейса,
              в случае провала - пустое значение.
    """

    # Запрашиваем из роутера название интерфейса при помощи bash команды
    grep = f"grep description  -A1 | grep {interface} -B1 | grep description | sed 's/[ \",]//g' | cut -d: -f2"
    is_ok, output = tools.run(f"curl -s {CMD_GET_INTERFACE} | {grep}")

    # в случае успеха возвращаем имя интерфейса,
    # в случае провала - пустое значение
    return "".join(output.split('\n')) if is_ok else ''


def get_router_interfaces_details(types: list = None) -> (list, dict):
    """
    Функция формирует список доступных на роутере интерфейсов и
    возвращает полную информацию о них в виде
    списка их названий и словаря с детальной информацией

    :param types: типы интерфейсов из INTERFACE_TYPES, например openvpn или wireguard и пр.
    :return: vpn_names - список названий интерфейсов;
             vpn_dict - словарь с детальной информацией.
    """

    # формируем список типов доступных интерфейсов
    types = INTERFACE_TYPES if types is None else types

    vpn_names, vpn_dict = [], {}

    # Запрашиваем список из роутера при помощи bash команды
    is_ok, output = tools.run(f"curl -s {CMD_GET_INTERFACE}")
    #  Если все хорошо, то формируем список и словарь с данными
    if is_ok and output:
        # конвертируем полученные данные в json словарь
        all_in_dict = json.loads(output)
        del output
        # получаем список всех доступных интерфейсов в роутере
        all_names = list(all_in_dict.keys())
        # фильтруем только те, что указаны в нашем списке types
        vpn_names = list(filter(lambda x: [el for el in types if el in x], all_names))
        # заполняем данными найденных интерфейсов словарь
        _ = [vpn_dict.update({n: all_in_dict[n]}) for n in vpn_names]
        # освобождаем память
        del all_in_dict, all_names
    else:
        raise Exception('В роутере нет доступных VPN интерфейсов!\n'
                        'Для работы пакета необходимо подключить хотя бы один!')

    return vpn_names, vpn_dict


def get_available_interface_list(connected_only: bool = True) -> (list, list, list):
    """
    Функция возвращает список всех подключенных на текущий момент
    VPN интерфейсов в роутере (по умолчанию) или всех доступных
    VPN интерфейсов в роутере, если установлен флаг connected_only в False

    :param connected_only: флаг подключенных интерфейсов.
    :return: Список подключенных или существующих интерфейсов VPN доступных в роутере
             например: ['OpenVPN0', 'Wireguard0']
    """
    inface_types, inface_names, inface_connected = [], [], []
    # Получаем список tunnels интерфейсов с детальной информацией о них
    vpn_list, vpn_dict = get_router_interfaces_details()
    # если в списке есть элементы
    if vpn_list:
        # получаем только те интерфейсы из доступных,
        # которые подключены, если стоит флаг connected_only
        type_list = [i for i in vpn_list if vpn_dict[i][etag.connected] == etag.yes]
        # генерируем имена интерфейсов
        if connected_only:
            # только подключенные типы и имена интерфейсов
            inface_types = type_list
            inface_names = [vpn_dict[i][etag.description] for i in vpn_list if vpn_dict[i][etag.connected] == etag.yes]
        else:
            inface_types = vpn_list
            inface_names = [vpn_dict[i][etag.description] for i in vpn_list]
        # извлекаем флаг подключения интерфейса к сети
        inface_connected = [True if vpn_dict[i][etag.connected] == etag.yes else False for i in vpn_list]
        #  освобождаем память
        del vpn_dict

    return inface_types, inface_names, inface_connected


def get_filtered_interfaces_details(details: list = None, types: list = None) -> dict:
    """
    Функция получает детальную информацию о конкретных типах интерфейсах
    в случае отсутствия аргументов возвращается информация о всех доступных
    типах интерфейсах в системе со следующими полями:
    description, connected, link, state

    :param details: список полей с информацией об интерфейсах.
    :param types: доступные типы интерфейсов в системе роутера.

    :return: словарь с элементами словаря следующего содержания, как пример
             { 'OpenVPN0': { 'description': 'My Rome',
                              'connected': 'yes',
                              'link': 'up',
                              'state': 'up',
                              },
                'Wireguard0': { 'description': 'My Rome',
                              'connected': 'yes',
                              'link': 'up',
                              'state': 'up',
                              },
                }
    """
    # поля для выборки по умолчанию
    details = INTERFACE_FIELDS if details is None else details
    result = []
    # получаем весь пакет данных
    vpn_list, vpn_dict = get_router_interfaces_details(types=types)
    if vpn_list:
        # производим выборку данных
        result = {}
        for v in vpn_list:
            result[v] = {}
            #  формируем словарь с отфильтрованными полями
            _ = [result[v].update({d: vpn_dict[v][d]}) for d in details if d in vpn_dict[v]]
            # result.append({v: buff[v]})
        #  на всякий случай заботимся о размере памяти
        del vpn_dict, vpn_list

    return result


# def get_interface_info(interface: str, details=None) -> dict:
#     """
#     Функция запрашивает детальную информацию о КОНКРЕТНО-ЗАДАННОМ интерфейсе
#
#     :param interface: название интерфейса по которому запрашиваются данные.
#     :param details: список тегов с информацией (по умолчанию ['description', 'connected', 'mac'])
#             может содержать type, interface-name, link, state, mtu, priority, security-level и пр.
#     :return: возвращает словарь в виде: {'description': 'описание', 'connected': 'yes', 'mac': 'ХХ.XX.XX.XX.XX'}
#              или словарь {'error': 'описание ошибки'}
#     """
#
#     # список деталей, которые хотим получить
#     details = INTERFACE_FIELDS if details is None else details
#     # отправляем запрос
#     is_ok, all_in_dict = libraries.run(f"curl -s {CMD_GET_INTERFACE}")
#     # если все хорошо и результат имеется
#     if is_ok and all_in_dict:
#         _result = {}
#         # загружаем данные в json словарь
#         all_in_dict = json.loads(all_in_dict)
#         # получаем список всех доступных имен интерфейсов
#         interface_names = list(all_in_dict.keys())
#         # фильтруем данные только по заданному интерфейсу
#         # для этого получаем точное имя нашего интерфейса
#         selected = "".join([i for i in interface_names if interface in i])
#         # осуществляем выборку по имени
#         out = all_in_dict[selected]
#         # формируем словарь данных для заданного интерфейса
#         _ = [_result.update({d: out[d]}) for d in details if d in out]
#     else:
#         #  если были ошибки, то возвращаем соответствующий словарь
#         _result = {etag.error: all_in_dict}
#     return _result


# def is_interface_connected(interface: str) -> bool:
#     out = get_interface_info(interface=interface)
#     return True if out[etag.connected] == etag.yes else False


# def set_interface_for_hosts(interface: str, hosts_list=None) -> str:
#     """
#     Функция устанавливает заданный интерфейс для списка хостов
#
#     :param interface: заданный интерфейс.
#     :param hosts_list: список хостов, для которых необходимо задать интерфейс.
#     :return: сообщение о результате исполнения
#     """
#     #  флаг наличия ошибок
#     errors = []
#     # поучаем список хостов для работы
#     hosts = get_hosts() if hosts_list is None else hosts_list
#     # цикл по всем элементам в списке
#     for host in hosts:
#         # устанавливаем атрибуты по каждому хосту с заданным интерфейсом
#         _result = add_one_host(host=host, interfaces=[interface])
#         # отлавливаем ошибки при работе
#         if Error.INDICATOR in _result:
#             errors.append(host)
#
#     if errors:
#         # при наличии ошибок формируем соответствующее сообщение
#         ls = ",".join(errors)
#         _result = f"{Error.INDICATOR} Интерфейс {bs}{interface}{be} установить не удалось " \
#                   f"для следующих доменов {ls}!"
#     else:
#         _result = f"Интерфейс {bs}{interface}{be} успешно установлен для всех доменов."
#
#     return _result


# def get_interface_default() -> str:
#     """
#     Функция возвращает интерфейс выбранный по умолчанию для роутера.
#
#     :return: Название интерфейса по умолчанию.
#     """
#     return get_config_value(name=etag.interface)
#
#
# def set_interface_default(interface_to_set: str) -> bool:
#     """
#     Функция записывает в файл конфигурации интерфейс по умолчанию
#
#     :param interface_to_set:
#     :return:
#     """
#     return set_config_value(name=etag.interface, value=interface_to_set)


# def mark_dns_default() -> list:
#     """
#     УСТАРЕВШЕЕ
#     Функция отмечает иконкой dns адрес, который был выбран по умолчанию
#
#     :return:
#     """
#     dns_default = get_dns_config()
#     result = []
#     if dns_default:
#         from setup import DNS_LIST_FILE
#         dns_list = libraries.get_file_content(file=DNS_LIST_FILE)
#         for dns in dns_list:
#             if dns_default in dns:
#                 dns = f"{ICON_DEFAULT} {dns}"
#             result.append(dns)
#     return result


def mark_interface_online() -> (dict, list):
    """
    Функция отмечает светлой иконкой интерфейс,
    который находится в он-лайн и отмечает темной иконкой
    интерфейс - в офф-лайн или возвращает пустой список,
    если интерфейсы отсутствуют

    :return: buttons_text - список с отмеченным иконкой интерфейсом
             interfaces - словарь в виде {'OpenVPN0':'My-tunnels-main', 'OpenVPN1':'My-tunnels'}
    """

    # получаем список всех доступных интерфейсов в системе
    buttons_text, interfaces = [], {}
    # _, detail_list = get_interfaces_list_in_details()
    detail_list = get_filtered_interfaces_details(details=[etag.description, etag.connected])
    # проходим по всем интерфейсам
    for inface in detail_list:
        # если находим интерфейс по умолчанию, то отмечаем его иконкой
        # при этом название кнопки будет выглядеть, как "My-OpenVPN-India [OpenVPN1]"
        # ВАЖНО: для корректной работы menu_vpn->vpn_interface_list_show
        # необходимо, чтобы между названием интерфейсом и его id был ОБЯЗАТЕЛЬНО пробел
        # например так My-VPN []
        inface_name = detail_list[inface][etag.description]
        inface_button_text = f"{inface_name}"
        # inface_button_text = f"{inface_name} -> {inface}"
        # формируем иконку текста кнопки в зависимости от состояния подключения интерфейса
        res = f"{icon.ok} {inface_button_text}" if detail_list[inface][etag.connected] == etag.yes \
            else f"{icon.stop} {inface_button_text}"
        # добавляем элемент в список
        buttons_text.append(res)
        interfaces[inface] = inface_name

    return interfaces, buttons_text


# def mark_interface_default(interface=None) -> list:
#     """
#     Функция отмечает иконкой интерфейс адрес
#     который был задан или выбран по умолчанию
#
#     :param interface: заданный интерфейс.
#     :return: список с отмеченным иконкой интерфейсом
#     """
#
#     # если интерфейс не задан, то получаем его из файла конфигурации
#     inf_default = get_interface_default() if interface is None else interface
#     _result = []
#     # проверяем задан ли интерфейс в принципе
#     if inf_default:
#         # если интерфейс задан, то получаем список
#         # всех доступных интерфейсов в системе
#         inf_list = get_available_interface_list()
#         # проходим по всем интерфейсам
#         for inf in inf_list:
#             if inf_default in inf:
#                 # если находим интерфейс по умолчанию,
#                 # то отмечаем его иконкой
#                 inf = f"{icon.ok} {inf_default}"
#             # добавляем элемент в список
#             _result.append(inf)
#
#     return _result


def get_system_dns_report() -> str:
    """
    Функция получает DNS адреса из роутера и затем формирует строку
    данных в виде "DNS [interface]: IP".

    :return: строки данных в виде "DNS [interface]: IP".
    """

    # Формируем команду bash для получения DNS из роутера
    # оставляем из вывода только строки со словами address|service
    # затем, извлекаем значение и убираем из него все кавычки,
    # запятые и пробелы и меняем символ новой строки на точку с запятой.
    cmd = f"curl -s {CMD_GET_DNS} | grep -E 'address|interface' " \
          f"| cut -d: -f2 |  sed 's/[ \",]//g' | tr '\n' '{etag.pdot}'"
    # исполняем команду
    is_ok, out = tools.run(command=cmd)
    if is_ok and out:
        # если результат положительный,
        # то формируем список из полученных DNS
        # В нашем случае, первым идет адрес и
        # затем название сервиса и они чередуются через два
        # out = out.replace("Dns", "Ethernet")
        dns_list = out.split(etag.pdot)
        len_ls = len(dns_list)
        # обходим по циклу каждые два элемента
        # dns_list[i] - название сервиса
        # dns_list[i-1] - адрес DNS
        dns_list = [[dns_list[i - 1], dns_list[i]] for i in range(1, len_ls, 2)]
        dns_str = "\n".join([f"DNS [{v[1]}]: {v[0]} " for v in dns_list])
    else:
        # если возникли ошибки при получении DNS,
        # то дальше работать не имеет смысла
        raise Exception('Ошибка при запросе DNS из роутера!')

    return dns_str


def get_system_dns_list() -> list:
    """
    Функция получения DNS адресов из роутера.

    :return: список DNS адресов в системе роутера
    """

    # Формируем команду bash для получения DNS из роутера.
    cmd = f"curl -s {CMD_GET_DNS} | grep address | cut -d: -f2 |  sed 's/[ \",]//g'"
    # исполняем команду
    is_ok, out = tools.run(command=cmd)
    if is_ok:
        # если результат положительный,
        # то формируем список из полученных DNS построчно
        dns_list = out.split('\n')
        # Оставляем только уникальные и не пустые значения
        dns_list = [el for el in tools.unique_list(dns_list) if el]
    else:
        # если возникли ошибки при получении DNS,
        # то дальше работать не имеет смысла
        raise Exception('Ошибка при запросе адресов DNS из роутера!')

    return dns_list


def delete_ip(ip: str, interface: str = None) -> bool:
    """
    Функция удаляет конкретный ip с конкретным интерфейсом (если задан)
    или удаляет этот ip на всех доступных интерфейсах

    :param ip: заданный ip
    :param interface: название интерфейса на котором удаляется ip

    :return: True - удален, False - не удалось удалить
    """

    if interface is None:
        # если не задан интерфейс, то формируем строку данных
        #  для удаления на всех интерфейсах данный ip
        data = f'{{"{etag.host}":"{ip}","{etag.no}":true}}'
    else:
        # если интерфейс задан, то учитываем это при формировании команды
        data = f'{{"{etag.host}":"{ip}","{etag.interface}":"{interface}","{etag.no}":true}}'
    # формируем команду
    cmd = f"curl -s -d '{data}' {CMD_GET_ROUTE}"

    # производим попытку удаления
    is_ok, out = tools.run(command=cmd)
    # возвращаем результат
    return True if is_ok else False


# def delete_host(host: str, inface_list: list = None) -> str:
#     """
#     Функция удаляет заданный хост на всех доступных интерфейсах
#
#     :param host: название хоста для удаления
#     :param inface_list: список интерфейсов на которых будет удален хост
#     :return: сообщение о результате удаления
#     """
#     # получаем данные о домене (на каких интерфейсах имеется и список ip)
#     inf_cur_list, _, iplist = get_host_info(host)
#     # если задан список интерфейсов, то оставляем его иначе берем из полученных данных
#     inface_list = inface_list if inface_list else inf_cur_list
#
#     result_ok, result_err = [], []
#     # проходимся по каждому интерфейсу
#     for inface in inface_list:
#         # получаем список результатов True или False
#         res_list = [delete_ip(ip=ip, interface=inface) for ip in iplist] if iplist else []
#         # интерпретируем результаты
#         host_text = f"{bs}{host}{be} на {bs}{inface}{be}"
#         if res_list:
#             # если список содержит элементы, то перемножаем их для проверки на наличие ошибок
#             if libraries.mult(source=res_list, and_mode=True):
#                 # если вернулся True - то все хорошо
#                 result_ok = f"Домен {host_text} успешно удален."
#             else:
#                 # если вернулся False - то ошибка
#                 result_err.append(f"{Error.INDICATOR} Домен {host_text} не может быть удален!")
#         else:
#             # если список пустой, то удалять было нечего
#             result_err.append(f"{Error.INDICATOR} Домена {host_text} не существует и он не может быть удален!")
#
#     # формируем результат выполнения команды из строк о результатах удаления
#     er_result = "\n".join(result_err)
#     # o_result = "\n".join(result_ok)
#
#     # return f"{r_result}\n{o_result}"
#     # возвращаем только сообщения об ошибках
#     return er_result


def remove_hosts_list(hosts: list = None, interfaces: list = None, result_ok: bool = False) -> str:
    """
    Функция удаляет хосты из БС.

    :param hosts: список хостов на удаление.
    :param interfaces: список интерфейсов на которых необходимо удалить хосты.
    :param result_ok: флаг необходимости возврата сообщений об успешном удалении.
                      По умолчанию возвращаются сообщения только об ошибках.
    :return: сообщение о результате в зависимости от флага result_ok
    """

    # был ли передан список хостов
    # if not hosts:
    #     # список хостов был пустым
    #     error_text = "Переданный список хостов пуст! Проверьте код!"
    #     zlog.error(error_text)
    #     raise Exception(error_text)

    host_err, hosts_not_exist, hosts_ok, result = [], [], [], ''
    # получаем детальную информацию по хостам из БС, которые
    # совпадают по заданным фильтрам: списку хостов и интерфейсам.
    hosts_details = get_hosts_details(selected_hosts=hosts, interfaces=interfaces)
    # проверяем передали ли список интерфейсов
    if not interfaces:
        # если список не передали
        interfaces, _, _ = get_available_interface_list()
    # список хостов генерируется в случае их отсутствия
    target_hosts = hosts if hosts else list(hosts_details.keys())
    # выделяем только имена хостов
    hosts_list = hosts_details.keys()
    # Получаем разницу между входящими хостами и теми,
    # которые есть в системе, т.е. получаем список несуществующих в БС хостов
    diff_host_list = list(set([h for h in target_hosts if etag.dot in h]) - set(hosts_list))
    #  если разница есть, значит хостов в БС не существует
    if diff_host_list:
        # формируем массив для генерации сообщений об ошибках
        hosts_not_exist = [(h, 'ALL') for h in diff_host_list]

    def delete_ips(ip_list: list, in_face: str):
        """

        :param ip_list:
        :param in_face:
        """
        # получаем список результатов True или False при удалении каждого ip в списке
        res_list = [delete_ip(ip=ip, interface=in_face) for ip in ip_list] if ip_list else []
        # интерпретируем результаты
        if res_list:
            # если список содержит элементы, то перемножаем их для проверки на наличие ошибок
            if not tools.mult(source=res_list):
                # если есть ошибки
                host_err.append((host, inface))
            else:
                hosts_ok.append((host, inface))
        else:
            # если список пустой, то удалять было нечего - хост
            # не существует на обозначенном интерфейсе
            hosts_not_exist.append((host, inface))

    # проходимся по каждому элементу в списке хостов и удаляем их
    for host in hosts_list:

        # if hosts:
        #     for inface in interfaces:
        #         iplist = hosts_details[host][0][etag.ip] if hosts_details[host][0][etag.interface] == inface else []
        #         delete_ips(iplist, inface)
        # else:
        for el in hosts_details[host]:
            iplist = el[etag.ip]
            inface = el[etag.interface]
            if not hosts or inface in interfaces:
                delete_ips(iplist, inface)

    def join_hosts_by_infaces(list_to_analise: list[(str, str)]) -> dict:
        """

        :param list_to_analise:
        :return:
        """
        inface_dict = dict([])
        for h, i in list_to_analise:
            if i not in inface_dict:
                inface_dict.update({i: []})
            if h not in inface_dict[i]:
                inface_dict[i].append(h)
        return inface_dict

    OK, ERROR, NOT_EXIST = range(3)

    def get_result(list_to_analise: list[(str, str)], stage: int) -> str:
        """

        :param list_to_analise:
        :param stage:
        :return:
        """
        res = []
        _inface_dict = join_hosts_by_infaces(list_to_analise=list_to_analise)
        for k, v in _inface_dict.items():
            _hosts = '\n'.join(v)
            _hosts = f"{bs}{_hosts}{be}"
            is_mult = len(v) > 1
            inf = get_interface_name(interface=k)
            mult_1 = 'ы' if is_mult else ''
            mult_2 = ', \nперечисленные выше ' if is_mult else f" {bs}{v}{be} "
            mult_3 = f"{_hosts}\n{LINE}" if is_mult else ''
            if stage == OK:
                mult_1 = 'ы' if is_mult else ''
                res.append(f"{mult_3}Домен{mult_1} на интерфейсе {bs}{inf}{be}{mult_2}успешно удален{mult_1}.")
            elif stage == ERROR:
                mult_4 = 'и' if is_mult else ''
                res.append(f"{mult_3}Домен{mult_1} на интерфейсе {bs}{inf}{be}{mult_2}НЕ был{mult_4} удален{mult_1}.")
            elif stage == NOT_EXIST:
                mult_4 = 'ЮТ' if is_mult else 'ЕТ'
                res.append(f"{mult_3}Домен{mult_1} на интерфейсе {bs}{inf}{be}{mult_2}ОТСУТСТВУ{mult_4} в БС.")
            else:
                raise Exception("ОШИБКА в коде: задан неверный аргумент в функции vpn_lib->print_result! ")

        return "\n".join(res)

    # Если стоит флаг возврата результата об успешном удалении
    if result_ok and hosts_list:
        result = get_result(hosts_ok, OK)

    # формируем сообщение об ошибке для хостов которые не существуют в БС
    if host_err:
        result = get_result(host_err, ERROR)

    # формируем сообщение об ошибке для хостов которые не существуют в БС
    if hosts and hosts_not_exist:
        result = get_result(hosts_not_exist, NOT_EXIST)

    zlog.debug(result)

    return result


def update_host_list(hosts: list = None, interfaces: list = None, insist_to_del: bool = False) -> str:
    """
    Функция обновляет ip адреса из списка переданных доменных имен

    :param interfaces: выбранные интерфейсы для обновления.
    :param hosts: список доменных имен.
    :param insist_to_del: флаг принудительного удаления предыдущих данных (False по умолчанию).
                          Если стоит False, то только обновляем данные, без удаления (как копилка).
                          Если стоит True, все предыдущие ip удаляем и затем добавляем вновь.

    :return: сообщение об операции
    """
    del_ip_results, add_ip_results, diff_ip_result = [], [], []
    err_result, no_update_result = '', ''

    def update_on_interface(interface_selected: str):
        # генерируем сообщение о новых ip у хоста
        diff_ip_result.append(f"{host} [{interface_selected}: {len(diff_ip_list)}] -> [{', '.join(diff_ip_list)}]")
        # удаляем все ip, которых нет в новом списке в случае наличия флага принудительного удаления
        if insist_to_del:
            # удаляем все ip из существующего на роутере БС
            for ip in prev_list_ip:
                del_ip_results.append(delete_ip(ip=ip, interface=interface_selected))
        # добавляем новые ip, если они имеются в новом списке (с накоплением, если флаг insist_to_del = False)
        auto = hosts_details[host][0][etag.auto]
        # если стоит флаг принудительного удаления, то добавляем все ip из нового списка,
        # если флаг ен стоит, то добавляем только те, которые из списка выявленных различий
        list_to_add = new_list_ip if insist_to_del else diff_ip_list
        for ip in list_to_add:
            res, _ = add_one_ip(host_name=host, ip=ip, interface=interface_selected, auto=auto)
            add_ip_results.append(res)

    # получаем информацию о доменах и их ip из роутера.
    hosts_details = get_hosts_details(selected_hosts=hosts, interfaces=interfaces)
    num_hosts = len(hosts_details)
    # формируем сообщение в зависимости от количества доменов в списке
    if num_hosts == 0:
        # если хостов не обнаружено
        return "Список доменов пуст. Обновлять нечего."

    elif num_hosts == 1:
        # если список хостов не пустой и в нем всего один хост
        host = f"{bs}{''.join(hosts_details)}{be}"
        err_result = f"{Error.INDICATOR} Домен {host} НЕ может быть обновлен!\n" \
                     f"Ошибка при обновлении - "
        no_update_result = f"Домен {host} успешно обновлен."

    elif num_hosts > 1:
        # если хостов в списке нет или их число больше одного
        h_list = f"{bs}{', '.join(hosts_details)}{be}"
        err_result = f"{Error.INDICATOR} Эти хосты {h_list} НЕ не могут быть обновлены!\n" \
                     f"Ошибка при обновлении -"
        no_update_result = f"Обновления для {h_list} {bs}отсутствуют{be}."

    # проходимся по каждому отобранному хосту
    for host in hosts_details:
        # обновляем данные по хосту и получаем новый список ip
        new_list_ip = get_host_ip_list(host=host)
        prev_list_ip = hosts_details[host][0][etag.ip]
        # получаем разницу списков - новые ip для хоста
        diff_ip_list = list(set(prev_list_ip) - set(new_list_ip))
        # если есть разные данные в списках, то проводим обновление по ним
        if diff_ip_list:
            # если задан список интерфейсов, то проводим обновление только по ним
            if interfaces:
                for inface in interfaces:
                    update_on_interface(interface_selected=inface)
            else:
                prev_inface = hosts_details[host][0][etag.interface]
                update_on_interface(interface_selected=prev_inface)

    if False in del_ip_results:
        # при наличии ошибок на стадии удаления пишем в лог
        result = f"{err_result} на стадии удаления!"
    elif False in add_ip_results:
        # при наличии ошибок на стадии удаления пишем в лог
        result = f"{err_result} на стадии добавления!"
    else:
        # Все хорошо!
        if diff_ip_result:
            # Если есть различия в списках старых и новых
            text = '\n'.join(diff_ip_result)
            result = f"Были внесены следующие изменения:\n{text}"
        else:
            # Если различий=обновлений нет.
            result = no_update_result

    zlog.debug(result)

    return result


# def get_host_info(host: str) -> (list, bool, list):
#     """
#     Функция возвращает информацию о хостах, переданных в аргументах
#
#     :param host: имя хоста или список имен.
#     :return: interface - интерфейс хоста;
#              auto - флаг подключения;
#              ip_list - список ip принадлежащих домену;
#     """
#
#     # Формируем команду для получения информации
#     # со стороны роутера и исполняем ее.
#     cmd = f'curl -s {CMD_GET_ROUTE} | grep {host} -B4'
#     result, out = libraries.run(command=cmd)
#     interface, auto, ip_list = '', False, []
#     # проверяем результат
#     if result and out:
#         # если результат положительный, то делим полученный результат на строки
#         out = out.split('\n')
#         length = len(out)
#         if length > 1:
#             # Если получили две и более строк...
#             # то извлекаем информацию об интерфейсе, auto и списке ip
#             interface = list(set([libraries.clean_me(k, ' ",').replace(f'{etag.interface}:', '')
#                                   for k in out if f'{etag.interface}' in k]))
#             ip_list = [libraries.clean_me(k, ' ",').replace(f'{etag.host}:', '')
#                        for k in out if f'{etag.host}' in k]
#             auto = [libraries.clean_me(k, ' "') for k in out if f'"{etag.auto}": true' in k]
#             auto = False if etag.openvpn in auto or etag.wireguard in auto or not auto else True
#
#         elif length == 0:
#             # Если нет строк в выводе...
#             # то получаем данные об интерфейсе
#             interface = libraries.clean_me(out[0].split(":")[1], '",')
#             auto = False
#         else:
#             # Во всех иных случаях...
#             # возвращаем пустые значения
#             interface, auto = '', False
#
#     return interface, auto, ip_list


def switch_host_auto_state(hosts_details: dict, interfaces: list = None, auto_mode: bool = None) -> str:
    """
    Функция производит переключение
    переданных доменов в состояние AUTO - вкл/вкл

    :param hosts_details: словарь доменов в детализацией.
    :param interfaces: интерфейс на котором производится переключение.
    :param auto_mode: необходимый режим для переключения флага AUTO

    :return: сообщение о результате переключения
    """

    # узнаем статус AUTO для большинства переданных хостов, если не был задан режим переключения
    auto = not tools.mult([[dd[etag.auto] for dd in details][0] for details in hosts_details.values()], False) \
        if auto_mode is None else auto_mode
    state = "подключен" if auto else "отключен"
    # меняем статус у каждого домена по заданным интерфейсам
    for host in hosts_details:
        for detail in hosts_details[host]:
            add_one_host(host, auto=auto, interfaces=interfaces, ip_list=detail[etag.ip])

    # выводим результат действий
    if len(hosts_details) == 1:
        # выводим результат в единственном числе для одного домена
        result = f"Домен {bs}{''.join(hosts_details)}{be} {state}!"
    else:
        # выводим результат во множественном числе для списка доменов
        result = f"Домены {bs}{', '.join(hosts_details)}{be} {state}ы!"

    return result

    # проверка на возможность работать по закрытому протоколу
    # на выходе получаем команду с несколькими запросами для определения ip


def check_dns_tls(dns_ip_list: list, domain: str = 'ya.ru') -> (str, list):
    """
    Функция проверяет наличие возможности
    поддержки TLS для текущих DNS

    :param dns_ip_list: список DNS
    :param domain: тестовый домен для проверки (по умолчанию 'ya.ru')

    :return: bash_cmd - готовая bash команда для запроса адреса для хоста
             dns_config - список DNS с портом поддержки TLS (порт:853) или без оной (порт:53)
    """
    bash_cmd, dns_config = '', []
    # цикл по всем имеющимся DNS в списке
    for ip in dns_ip_list:
        #  формируем bash команду для проверки поддержки TLS
        cmd = f"{etag.dig} {domain} @{ip} {etag.short}"
        # исполняем bash команду
        is_ok, _ = tools.run(cmd, stderr=DEVNULL)
        # если DNS получает данные, то все нормально.
        if is_ok:
            #  формируем bash команду для проверки поддержки TLS
            cmd = f"{etag.dig} {domain} @{ip} {etag.short} {etag.tls}"
            # cmd = f"{tag.dig} {domain} @{ip} {tag.short} {tag.tls}  2>&1 | grep 'ERROR'"
            # исполняем bash команду
            is_ok, ip_list = tools.run(cmd, stderr=DEVNULL)
            # формируем часть bash команды для исполнения в зависимости от теста
            data = f'{etag.short} {etag.tls}' if is_ok else f'{etag.short}'
            # формируем всю bash команду для запроса ip
            bash_cmd = f'{cmd}{etag.dig} {domain} @{ip} {data}{etag.pdot}'
            # формируем значение списка DNS:PORT в зависимости от поддержки TLS
            ip_port = f'{ip}:853' if is_ok else f'{ip}:53'
            # добавляем значение DNS в список
            dns_config.append(ip_port)
    # Записываем значения DNS в файл конфигурации
    set_dns_config(dns_config)
    return bash_cmd, dns_config


def get_host_ip_list(host: str, dns_ip_list=None) -> list:
    """
    Функция возвращает список ip для заданного хоста

    :param host: имя хоста
    :param dns_ip_list: список dns адресов для получения ip хоста
    :return: список ip хоста
    """

    # Определяем внутреннюю функцию для получения ip,
    # чтобы можно было улучшить читаемость кода
    def get_domain_ip_list(bash_cmd_to_get_ip: str) -> list:
        """
        Функция для получения адресов хоста

        :param bash_cmd_to_get_ip: bash команда для получения ip адресов
        :return: список ip адресов
        """

        # задаем начальные значения
        # для переменных
        # count - счетчик циклов запросов (по умолчанию 1)
        # try_limit - лимит попыток запросов (по умолчанию 3 попытки)
        # sleep_limit - число секунд сна между попытками запросов (по умолчанию 3 сек)
        count, try_limit, sleep_limit = (1, 3, 3)
        # вечный цикл
        while True:
            if count > try_limit:
                ret = [etag.error, 'Превышен лимит по числу запросов!']
                break
            # делаем запрос и анализируем ответ
            is_ok, ip_list = tools.run(bash_cmd_to_get_ip)

            zlog.debug(f"Список полученных ip :\n{ip_list}")

            if is_ok and ip_list:
                # если ответ положительный,
                # и есть адреса в списке, то получаем список
                # путем деления строки по возврату каретки
                ret = ip_list.split("\n")
                # И выходим из цикла
                break
            else:
                # если очередная попытка не удалась,
                # то берем паузу и увеличиваем счетчик попыток
                sleep(sleep_limit)
                count += 1

        return ret

    # получаем список DNS
    # dns_ip_list = dns_ip_list if dns_ip_list else get_dns_config()
    #  формируем bash команду для запроса ip хоста, которая может содержать до трех DNS запросов в одной команде
    # bash_cmd = [f"{etag.dig} {host} @{ip} {etag.short}{f' {etag.tls}' if ':853' in ip else ''}" for ip in dns_ip_list]
    # bash_cmd = f" && ".join(bash_cmd)
    # ips = get_domain_ip_list(bash_cmd_to_get_ip=bash_cmd)

    # ГИПОТЕЗА
    bash_cmd = f"{etag.dig} {host} +tls +short 2&>1 | grep -v ';;'"
    # получаем список ip для домена на основании сформированной команды
    is_ok, ip_list = tools.run(bash_cmd)
    if is_ok and ip_list:
        ips = ip_list.split("\n")
    else:
        bash_cmd = f"{etag.dig} {host} +short 2&>1 | grep -v ';;'"
        is_ok, ip_list = tools.run(bash_cmd)
        if is_ok and ip_list:
            ips = ip_list.split("\n")
        else:
            zlog.debug(f"DNS сервера не работают! Проверьте интернет!")
            ips = []

    # фильтруем список и оставляем только ip адреса и те, которые не равны значению '0.0.0.0'
    list_ips = [] if etag.error == ips[0] \
        else [ip for ip in ips if ip is not None and ip != etag.empty_ip and tools.get_ip_only(ip)]
    # оставляем только уникальные значения и сортируем список
    result = sorted(tools.unique_list(list_elements=list_ips)) if list_ips else []

    zlog.debug(f"Список обработанных ip:\n{result}")

    return result


def add_one_ip(host_name: str,
               ip: str,
               interface: str,
               auto: bool = True) -> (bool, str):
    """
    Функция добавляет один из адресов принадлежащих домену

    :param host_name: имя домена
    :param ip: ip адрес
    :param interface: интерфейс на который добавляем адрес
    :param auto: флаг auto

    :return: tuple(результат булевый, консольный вывод)
            где результат булевый - True: успешно добавлен, False: возникла ошибка
            консольный вывод - результат исполнения команды в bash
    """
    #  формируем флаг для командной строки
    auto = f' "{etag.auto}": true, ' if auto else ' '
    # формируем строку исполнения
    data = fr'{{"{etag.host}":"{ip}","{etag.interface}":"{interface}",' \
           fr'{auto}"{etag.comment}":"{DEMON_NAME}{etag.divhost}{host_name}"}}'
    # выполняем команду и получаем результаты
    is_ok, output = tools.run(f"curl -s -d '{data}' {CMD_GET_ROUTE}")
    # возвращаем результаты
    return is_ok, output


def set_host_attributes(host_name: str,
                        interface: str,
                        auto: bool = True,
                        ip_list: list = None,
                        dns_ip: list = None) -> str:
    """
    Функция устанавливает/меняет аттрибуты домена, а в случае отсутствия домена - добавляет его в БС

    :param host_name: доменное имя
    :param interface: название интерфейса
    :param auto: флаг auto для домена
    :param ip_list: список ip адресов домена
    :param dns_ip: список dns

    :return: сообщение о результате исполнения функции
    """
    # если dns адреса отсутствуют, то получаем их из файла конфигурации
    dns_config = dns_ip if dns_ip else get_dns_config()
    #  получаем список адресов для домена, если он не задан
    ip_list = get_host_ip_list(host_name, dns_config) if ip_list is None else ip_list
    #  получаем название интерфейса, если он не задан
    # interface = get_interface_default() if interface is None else interface
    result, error_result = '', ''
    #  проверяем список адресов на его существование
    if ip_list:
        #  проверяем определился ли интерфейс
        if interface:
            # проверяем, что список адресов не содержит только
            # один элемент в списке со значением нулей в адресе - 0.0.0.0
            # это скорее всего означает, что данный домен блокирован
            # на уровне DNS роутера
            if len(ip_list) == 1 and ip_list[0] == etag.empty_ip:
                result = f"Вероятно домен {host_name} заблокирован на уровне DNS сервера!"
            else:
                for ip in ip_list:
                    # проходимся по каждому адресу в списке и добавляем его в таблицу БС
                    is_ok, output = add_one_ip(host_name=host_name, ip=ip, interface=interface, auto=auto)
                    if not is_ok:
                        # если результат отрицательный, то передаем его
                        error_result = f"{Error.INDICATOR} при добавлении ip адреса {ip} " \
                                       f"домена '{host_name} [{interface}]':\n" \
                                       f"\t{output}"
                        zlog.error(error_result)
                        break
                result = f"Атрибуты домена '{host_name}': {interface}, {auto} успешно установлены!"
        else:
            error_result = f"{Error.INDICATOR} Не удалось определить текущий VPN интерфейс!\n" \
                           f"Проверьте файл конфигурации '{CONFIG_FILE}'!"
            zlog.error(error_result)
    else:
        error_result = f"{Error.INDICATOR} Домен {host_name} не существует!\n" \
                       f"Проверьте его написание."
        zlog.error(error_result)
    return error_result if error_result else result


def load_hosts_to_white_list(host_list: str | list,
                             interfaces: list = None,
                             auto_list: list = None,
                             dns_ip: str = None) -> str:
    """
    Функция добавляет список хостов в БС (белый список) и возвращает строку с результатом
    Это фактически надстройка над функцией add_hosts, которая интерпретирует результаты
    в возвращаемом списке

    :param host_list: список хостов.
    :param interfaces: список интерфейсов для добавляемых хостов.
    :param auto_list: список флагов auto для всех хостов в списке hosts_list
    :param dns_ip: список dns адресов которые используются для получения ip.

    :return: СООБЩЕНИЕ об ошибках или о хорошем результате.
    """

    out = []
    # если dns адреса отсутствуют, то получаем их из файла конфигурации
    dns_config = dns_ip if dns_ip else get_dns_config()
    # Если передали строку, то преобразуем ее в список
    domains = tools.get_domain_list(host_list) if isinstance(host_list, str) else host_list
    # если при удалении ошибок не было, то добавляем хосты из архива в БС
    messages_list = add_some_hosts(hosts=domains, interfaces=interfaces, auto_list=auto_list, dns_ip=dns_config)
    # Проверяем результат на наличие ошибок
    errors_list = [ms for ms in messages_list if Error.INDICATOR in ms]
    if errors_list:
        # если при добавлении были ошибки,
        # то первым добавляем общее сообщение об ошибке при добавлении
        out.append(f'{bs}{Error.INDICATOR}{be} '
                   f'При добавлении хостов возникли следующие ошибки:')
        # в случае наличия ошибок составляем список и
        # нумеруем его, в каждой новой строке
        out += [mes.replace(Error.INDICATOR, f"{bs}{n}.{be} ") for n, mes in enumerate(errors_list, 1)]
        result = "\n".join(out)
        zlog.error(result)
    else:
        mult_hosts = len(domains) > 1
        mult_inface = len(interfaces) > 1
        # выводим домен и его IP
        host_in_str = ", ".join([f'{d} {get_host_ip_list(d, dns_config)}' for d in domains])
        mult_hs = 'ы' if mult_hosts else ''
        mult_if = 'ы' if mult_inface else ''
        # Если ошибок нет, то формируем финальное сообщение об этом.
        inface_names = [get_interface_name(i) for i in interfaces]
        interfaces_str = ", ".join(inface_names)
        result = f"Домен{mult_hs} {bs}{host_in_str}{be} успешно добавлен{mult_hs} " \
                 f"на интерфейс{mult_if} {bs}'{interfaces_str}'{be}."
        zlog.debug(result)

    return result


def get_interface_type_name(source: str) -> list:
    """
    Функция возвращает, список обнаруженных в строке источнике названий интерфейсов с их номерами
    с соблюдением букв нижнего и верхнего регистра в названии из строки источника,
    который может быть в любом регистре.

    :param source: строка-источник в которой ищется совпадение элементов из списка - checking_list.

    :return: список элементов, которые совпали с оригиналами и содержится в списке искомых элементов
    """

    # Проверяем на наличие записей
    if source:
        #  переводим все в нижний регистр
        _source = source.lower().split()
        result = []
        #  Проверяем наличие
        for elem in INTERFACE_TYPES:
            # объедением элементы списков для того, чтобы возвратить
            # именно исходный текст с сохранением регистра
            for sub_fnd in _source:
                # проверяем на совпадение
                if elem.lower() in sub_fnd:
                    inface_num = "".join([num for num in sub_fnd if num.isdigit()])
                    result.append(f"{elem}{inface_num}")
    else:
        #  если нет записей возвращаем пустой список
        result = []

    return result


def change_hosts_interface(hosts: list, new_inface: str, old_inface: str) -> str:
    """
    Функция меняет у всех переданных доменов интерфейс,
    при этом устанавливает лаг auto как и в оригинале

    :param hosts: список хостов.
    :param new_inface: интерфейс на замену.
    :param old_inface: старый тип интерфейса.

    :return: сообщение о результате операции
    """

    del_err, add_err = [], []
    # получаем данные по текущим деталям с текущим интерфейсом
    hosts_dict = get_hosts_details(selected_hosts=hosts, interfaces=[old_inface])
    #  по каждому хосту организуем обработку
    for host in hosts_dict:
        # извлекаем состояние auto и список хостов
        auto = hosts_dict[host][0][etag.auto]
        ip_list = hosts_dict[host][0][etag.ip]
        # проходимся по каждому ip
        for ip in ip_list:
            # удаляем запись об ip со старым интерфейсом
            res = delete_ip(ip=ip, interface=old_inface)
            if not res:
                # если возникла ошибка при удалении - добавляем сообщение о ней
                error_mess = f'Возникла ошибка при удалении хоста {host}::{ip}'
                del_err.append(error_mess)
                zlog.debug(error_mess)

            # добавляем запись об ip с новым интерфейсом
            res, _ = add_one_ip(host_name=host, ip=ip, interface=new_inface, auto=auto)
            if not res:
                # если возникла ошибка при добавлении - добавляем сообщение о ней
                error_mess = f'Возникла ошибка при добавлении хоста {host}::{ip}'
                add_err.append(error_mess)
                zlog.debug(error_mess)

    result = f"Интерфейс для {bs}{', '.join(hosts)}{be} успешно изменен " \
             f"c {bs}{old_inface}{be} на {bs}{new_inface}{be} "

    if add_err or del_err:
        # если возникли ошибки при удалении
        # или добавлении, то формируем сообщение о них
        result_d = "\n".join(del_err)
        result_a = "\n".join(add_err)
        result = f"{result_d}{LINE}{result_a}"

    return result


def add_some_hosts(hosts: list | dict, interfaces: list = None, auto_list: list = None, dns_ip: list = None) -> list:
    """
    Функция добавляет список хостов в БС (белый список) и возвращает список с результатами

    :param hosts: список хостов или строка с хостами с разделителями [ ,;\n\t].
    :param interfaces: список названий интерфейсов для добавляемых хостов.
    :param auto_list: флаг auto для каждого из хостов в списке hosts
    :param dns_ip: список dns адресов которые используются для получения ip.

    :return: СПИСОК сообщений об ошибках или о хорошем результате.
    """

    # инициализация переменных
    current_hosts_list, added, not_added, repeated, messages_list = {}, [], [], [], []
    # если dns адреса отсутствуют, то получаем их из файла конфигурации
    dns_config = dns_ip if dns_ip else get_dns_config()
    _ = [current_hosts_list.update({inface:get_hosts(interfaces=[inface])}) for inface in interfaces]
    # В случае наличия хостов в переданном списке идем дальше
    if hosts:
        is_tuple, _inface = isinstance(hosts[0], tuple), []
        if is_tuple:
            # если передали внутри tuple
            domain_list = [(h, a) for h, _, a in hosts]
            _inface = [i for _, i, _ in hosts]
        else:
            # генерируем список согласно полученным данным из auto_list
            domain_list = zip(hosts, auto_list) if auto_list else zip(hosts, [True for _ in hosts])
        #  проходимся по каждому хосту в списке
        for _ind, (_host, _auto) in enumerate(domain_list):
            inface_list = [_inface[_ind]] if is_tuple else interfaces
            has_in_host_list = _host in current_hosts_list[_inface[_ind]] if is_tuple \
                                else sum(current_hosts_list.values(), [])
            if has_in_host_list:
                # если добавляемый хост уже есть в БС, то добавляем
                # его в соответствующий список для последующего формирования
                # результирующего сообщения
                repeated.append(_host)
                zlog.debug(f'Хост "{_host}" уже имеется в БС.')
            else:
                # если хост не повторяется, то добавляем его в БС
                for inface in inface_list:
                    mess = set_host_attributes(host_name=_host, auto=_auto, interface=inface, dns_ip=dns_config)
                    if Error.INDICATOR in mess:
                        #  проверяем результат на наличие ошибок
                        #  и в случае их наличия формируем соответствующий список
                        not_added.append(_host)
                        zlog.debug(f'Хост "{_host} [{inface}]" НЕ был добавлен в БС.')
                    else:
                        # в случае отсутствия ошибок добавляем хост
                        # в список успешно добавленных хостов
                        added.append(_host)
                        zlog.debug(f'Хост "{_host} [{inface}]" успешно добавлен в БС.')

        #  формируем список сообщений в зависимости от содержимого списков
        if repeated:
            # если есть хосты, которые повторяются в БС
            out_list = f'{bs}{", ".join(repeated)}{be}'
            messages_list.append(f"{Error.INDICATOR}Данные хосты {out_list} уже имеются в списке.")
        if not_added:
            # если есть хосты, при добавлении которых возникли ошибки
            out_list = f'{bs}{", ".join(not_added)}{be}'
            messages_list.append(f"{Error.INDICATOR}Домен {out_list} не был добавлен в БС. Проверьте написание домена.")
        if added:
            # если есть хосты, успешно добавленные в список
            out_list = f'{bs}{", ".join(added)}{be}'
            mult = '' if len(added) == 1 else 'ы'
            messages_list.append(f"Домен{mult} {out_list} успешно добавлен{mult} в белый список!")
    else:
        # формируем сообщение о наличии ошибки при получении данных о содержимом белого списка
        messages_list.append(f"{Error.INDICATOR}Переданный список хостов пуст\n"
                             f"Проверьте данные для отправки в {__name__}!")
        zlog.error(f'Переданный список хостов пуст.')

    return messages_list


def add_one_host(host: str,
                 auto: bool = True,
                 interfaces: list = None,
                 ip_list: list = None) -> str:
    """
    Функция для добавления домена с предварительным его удалением из БС

    :param host: имя домена для удаления
    :param auto: флаг auto
    :param interfaces: список названий tunnels интерфейсов
    :param ip_list: список ip адресов принадлежащих домену

    :return: сообщение о результате действий
    """

    # предварительно удаляем хост (в случае его наличия в БС)
    result = remove_hosts_list(hosts=[host], interfaces=interfaces)
    # если обнаружены ошибки при удалении - выводим их,
    # в противном случае вывод игнорируем
    result = f"{result}\n" if Error.INDICATOR in result else ''

    # устанавливаем аттрибуты домена - по сути мы просто добавляем новый хост
    has_one_inface_only = len(interfaces) == 1
    if has_one_inface_only or interfaces is None:
        # если интерфейс задан один или не задан
        inface = "".join(interfaces) if has_one_inface_only else None
        mess = set_host_attributes(host_name=host, auto=auto, interface=inface, ip_list=ip_list)
        result = f"{result}{mess}\n"
    else:
        # если интерфейсов задано несколько
        for inface in interfaces:
            mess = set_host_attributes(host_name=host, auto=auto, interface=inface, ip_list=ip_list)
            result = f"{result}{mess}\n"

    return result


def count_hosts_ip(hosts_list: list = None, method: int = ROUTER, interfaces=None) -> int:
    """
    Функция возвращает количество всех ip для всех доменных имен в БС

    :param hosts_list: список хостов для анализа,
           по умолчанию получаем все доступные хосты в БС роутера.
    :param method: может принимать несколько значений
           ROUTER (по умолчанию) - получаем данные из роутера
           NET - формируем запросы в сеть через DNS сервера для получения данных.
    :param interfaces: название интерфейса.

    :return: количество всех ip для всех доменных имен в БС
    """
    # ставим заплатку на случай передачи строки вместо списка
    inface_list = [] if interfaces is None else ([interfaces] if isinstance(interfaces, str) else interfaces)
    # Инициализируем список хостов для дальнейшей обработки
    hosts_list = hosts_list if hosts_list else get_hosts()
    # Если необходимо запрашивать данные о хостах из сети, то...
    if method == NET:
        # формируем запросы в сеть через DNS сервера для получения данных
        dns_list = get_dns_config()
        # получаем список ip по каждому хосту и затем суммируем
        result = sum([len(get_host_ip_list(host=h, dns_ip_list=dns_list)) for h in hosts_list])
    elif method == ROUTER:
        # получаем из роутера данные по всем хостам в БС
        all_hosts = get_hosts_details(selected_hosts=hosts_list, interfaces=inface_list)
        # оставляем только те хосты, которые нам необходимы
        # domains_info = [all_hosts[h] for h in all_hosts.keys() if h in hosts_list]
        # результат суммируем
        result = sum([d[0] for d in [[len(d[etag.ip]) for d in h] for k, h in all_hosts.items()]])
    else:
        result = -1
        zlog.error(f'Неверно задан параметр "method":{method}\n'
                   f'Допустимые значения: NET и ROUTER')

    return result


def get_hosts_details(selected_hosts: list = None, interfaces: list = None) -> dict:
    """
    Функция для получения детальной информации о текущих хостах в белом списке

    :param: selected_hosts - список выбранных хостов
    :param: interfaces - список интерфейсов для фильтрации данных
    :return: словарь следующего виде
             'site.name': [
                 {
                   'interface': 'OpenVPN0',
                   'auto': True,
                   'ip': [XXX.XXX.XXX.XXX, XXX.XXX.XXX.XXX, XXX.XXX.XXX.XXX, ]
                },
                {
                   'interface': 'IKE0',
                   'auto': False,
                   'ip': [XXX.XXX.XXX.XXX, XXX.XXX.XXX.XXX, XXX.XXX.XXX.XXX, ]
                },
            ]
            или словарь с ошибкой {'error': 'описание ошибки'} - в случае проблемы
    """
    # формируем команду для получения информации из роутера.
    cmd = f'curl -s {CMD_GET_ROUTE}'
    is_ok, out = tools.run(cmd)
    interfaces = None if interfaces and interfaces[0] is None else interfaces
    # если все хорошо и есть данные...
    if is_ok and out:
        result = {}
        # загружаем данные в json словарь
        hosts = json.loads(out)
        # проходимся по каждому домену в списке
        for domain in hosts:
            #  извлекаем имя хоста, которое храним в комментариях всегда
            host_name = domain.get(etag.comment)
            # если значения в комментариях нет, то пропускаем запись.
            if not host_name:
                continue
            # проверяем принадлежность записи именно нашему пакету (должно присутcтвовать 'zpu->'
            if f'{DEMON_NAME}{etag.divhost}' not in host_name:
                continue
            else:
                # получаем данные после zpu-> хост должен идти вторым
                # элементом, первый элемент пустой
                host_name = host_name.split(f'{DEMON_NAME}{etag.divhost}')[1]

            if selected_hosts and not tools.has_inside(checking_list=selected_hosts, source=host_name):
                # Если задан список выбранных хостов и текущее имя хоста
                # отсутствует в этом списке, то пропускаем дальнейшую обработку данных
                continue
            # извлекаем интерфейс через который работает хост
            inface = domain.get(etag.interface)
            if interfaces and not tools.has_inside(checking_list=interfaces, source=inface):
                # в случае, если задан конкретный интерфейс
                # то производим по нему фильтрацию -
                # пропускаем цикл в случае несоответствия.
                continue

            # извлекаем ip
            ip = domain.get(etag.host)
            #  извлекаем флаг auto
            auto = True if etag.auto in domain else False
            # если имя хоста отсутствует...
            if host_name is not None and ip is not None and ip != etag.empty_ip:
                # формируем наш словарь
                el = {etag.interface: inface, etag.auto: auto, etag.ip: [ip]}
                if host_name not in result:
                    # если имя хоста пока нет в нашем словаре,
                    # то добавляем новый элемент в словарь
                    result[host_name] = [el]

                for ind, elem in enumerate(result[host_name]):
                    if inface not in [ell[etag.interface] for ell in result[host_name]]:
                        # если интерфейса еще нет в словаре у нашего хоста,
                        # то обновляем информацию в нем
                        result[host_name].append(el)
                    else:
                        # если он там есть, то нужно добавить только ip
                        if ip not in result[host_name][ind][etag.ip]:
                            result[host_name][ind][etag.ip].append(ip)
        #  освобождаем память
        del out, hosts
    else:
        # если возвращена ошибка, то формируем с ней словарь
        result = {etag.error: out}
    return result


def get_hosts(interfaces: list = None) -> list:
    """
    Функция возвращает список доступных хостов в БС по выбранному интерфейсу
    В случае, если interface не задан, то возвращаем все хосты для всех интерфейсов.

    :param interfaces: название интерфейса, хосты которого необходимо отфильтровать

    :return: список доступных хостов в БС
    """
    result = []

    # на всякий случай ставим заглушку для случайных вызовов функции
    # с interface типа строки и преобразовываем ее в список
    interfaces = [interfaces] if isinstance(interfaces, str) else interfaces
    domains_list = []
    # формируем команду для получения списка
    cmd = f'curl -s {CMD_GET_ROUTE}'
    # делаем запрос на роутер
    is_ok, out = tools.run(cmd)
    if is_ok and out:
        # в случае успеха загружаем результат в json словарь
        hosts = json.loads(out)
        zpu_inside = f'{DEMON_NAME}{etag.divhost}'
        # выбираем из словаря, только те значения,
        # у которых существуют значения ip адреса (в host) и имя самого хоста, хранимое в comment
        # фильтруем по интерфейсам, если они заданы
        for h in hosts:
            # извлекаем комментарий
            comment = h.get(etag.comment)
            # проверяем на наличие интерфейса в списке доступных
            inface_inside = tools.has_inside(checking_list=interfaces,
                                             source=h.get(etag.interface)) if interfaces else True
            if h.get(etag.host) and comment and zpu_inside in comment and inface_inside:
                # получаем имя хоста ТОЛЬКО если запись была сделана zpu
                host = comment.split(zpu_inside)[1]
                domains_list.append(host)

        zlog.debug(f"Список до сортировки и перед удалением дубликатов:\n'{hosts}'")
        # затем, оставляем только уникальные значения в массиве
        result = tools.unique_list(domains_list)
        zlog.debug(f"Список ПОСЛЕ сортировки и проверки на уникальность:\n'{result}'")

    #  результат сортируем
    return sorted(result) if result else result
    # return result


# ----------------------------------------------------------------------------------------------
#
#   Функции для работы с Архивами
#
# ----------------------------------------------------------------------------------------------


def create_backup(backup_file: str = None, domains: list = None, interfaces: list = None) -> str:
    """
    Функция записывает список доменов в архив с именем текущей даты
    пример названия файла: yota[22]-22_04_22-11_04.zpu или all-[44]-22_04_22-11_04.zpu
    где yota или all - название интерфейса (или все интерфейсы)
    [44] - количество ip в файле и 22_04_22-11_04 - дата и время создания архива
    пример строки для хранения архива: www.astra.ru|OpenVPN0|off

    :param backup_file: полный путь до имени файла.
    :param interfaces: название интерфейса текущего, если не задано, то сохраняем по всем интерфейсам.
    :param domains: список доменов для записи, если на задано, то сохраняем все домены.
    :return: сообщение о результате исполнения задания
    """
    hosts_list = []
    # Фильтруем список доменов на основании входных параметров - получаем их из БС.
    hosts = get_hosts_details(selected_hosts=domains, interfaces=interfaces)
    # логируем
    zlog.debug(hosts)
    # фильтруем список, если задан интерфейс и хосты
    # пример строки для хранения архива: www.astra.ru|OpenVPN0|off
    for host in hosts:
        # формируем строки для записи в файл
        # в виде 'host|interface|auto'
        for detail in hosts[host]:
            auto = 'on' if detail[etag.auto] else 'off'
            hosts_list.append(f"{host}{etag.divo}{detail[etag.interface]}{etag.divo}{auto}")

    # и преобразуем в список из строк
    hosts = "\n".join([h for h in hosts if h])

    if hosts:
        # Если в списке домены имеются, то проверяем
        # на наличие путь для записи архивов
        if not tools.check_path(path=BACKUP_PATH):
            #  если не создан, то создаем его
            tools.mkdir(CONFIG_PATH)
        # формируем имя файла на основании текущей даты
        from datetime import datetime
        # название файла - yota[22]-22_04_22-11_04.zpu или all-[44]-22_04_22-11_04.zpu
        host_count = len(hosts_list)
        inface_text = get_interface_name("".join(interfaces)).lower() \
            if interfaces and len(interfaces) == 1 else etag.all
        backup_name = f"{datetime.now().strftime(BACKUP_FORMAT_FILENAME)}-{inface_text}[{host_count}].{etag.backup_ext}"
        backup_file = backup_file if backup_file else f"{BACKUP_PATH}/{backup_name}"
        # пишем в архив данные
        result = tools.write_to_file(file=backup_file, lines=hosts_list, mode=CREATE_NEW)
        # по результатам отправляем сообщения
        if result:
            result = f"Новый архив был успешно создан!\n" \
                     f"{bs}{backup_file}{be}"
        else:
            result = f"{Error.INDICATOR} Архив создать НЕ удалось!\n" \
                     f"Возникла ошибка при записи в файл!"
    else:
        result = f"{Error.INDICATOR} Архив создать НЕ удалось!\n" \
                 f"Отсутствуют данные для записи!"

    return result


def load_backup(backup_name: str, interfaces: list = None,
                dns_ip: str = None, refresh: bool = True, hosts_list=None) -> str:
    """
    Функция загружает домены из файла в текущий белый список роутера.

    :param backup_name: имя архива без пути к нему.
    :param interfaces: интерфейс, через который будут работать в загруженные хосты.
    :param dns_ip: список dns адресов, которые будут использоваться при получении ip адресов доменных имен.
    :param refresh: флаг обновления или загрузки с нуля
                    если True - то просто подгружаем домены без очистки списка,
                    если False - то сначала удаляем все домены, затем добавляем новые.
    :param hosts_list: содержание архива

    :return: Возвращаем сообщение о результате проведения операции
    """

    def make_update(domains: list[str | tuple], inface_list: list = None, auto_flist: list = None) -> (list, list):
        """
        Функция осуществляет обновление данных по доменам
        в зависимости от существующих ограничений

        :param domains: список доменов для обновления.
        :param inface_list: список интерфейсов для обновления.
        :param auto_flist: список auto для обновления.
        :return: возвращает сет из двух списков:
                 result_out - сообщений о положительном результате обновлений
                 errors_list - сообщений об отрицательном результате обновлений
        """
        # инициализируем данные
        messages_list, errors_list, result_out = [], [], []
        # если ошибок в первом элементе списка при получении содержимого архива нет,
        # то проверяем флаг обновления БС (белого списка)
        if not refresh:
            # если необходимо перегрузить все данные, то предварительно очищаем белый список
            messages_list = remove_hosts_list(hosts=domains,
                                              interfaces=inface_list)
            errors_list = [ms for ms in messages_list if Error.INDICATOR in ms]
            if errors_list:
                # если при удалении были допущены ошибки,
                # то первым добавляем общее сообщение об ошибке при удалении хостов
                result_out.append(f"{bs}{Error.INDICATOR}{be} "
                                  f"Архив {bs}{backup_name}{be} "
                                  f"не может быть загружен по следующим причинам:")
        if not errors_list:
            # Если передан точный список данных из файла, то данные об интерфейсе и auto есть внутри domains
            auto_flist = None if isinstance(domains[0], tuple) else auto_flist
            # если при удалении ошибок не было, то добавляем хосты из архива в БС
            messages_list = add_some_hosts(hosts=domains,
                                           interfaces=inface_list,
                                           auto_list=auto_flist,
                                           dns_ip=dns_ip)
            # Проверяем результат на наличие ошибок
            errors_list = [ms for ms in messages_list if Error.INDICATOR in ms]
            if errors_list:
                # если при добавлении были ошибки,
                # то первым добавляем общее сообщение об ошибке при добавлении
                result_out.append(f'{bs}{Error.INDICATOR}{be} '
                                  f'При загрузке архива {bs}{backup_name}{be} '
                                  f'возникли следующие ошибки:')
        return result_out, errors_list

    # Получаем данные о всех доменных именах в архиве
    _hosts = get_backup_host_list(backup_name)
    if hosts_list:
        # оставляем только те, что есть в списке отобранных
        hosts = [ht for ht in _hosts if ht.split(etag.divo)[0] in hosts_list]
    else:
        hosts = _hosts
    del _hosts
    # Проверяем на наличие ошибок при получении содержимого архива
    if Error.INDICATOR not in hosts[0]:
        # проверяем содержится ли в файле данные об интерфейсе и флаге auto
        # которые разделены знаком '|'
        if etag.divo in hosts[0]:
            # в случае, если имеются данные разделенные знаком '|'
            # если флаг есть, то значит данные записаны в нем верно
            domains_tuple = []
            if interfaces:
                for inface in interfaces:
                    domains_tuple += [(h, inface, a) for h, _, a in [ln.split('|') for ln in hosts]]

            else:
                domains_tuple = [(h, i, a) for h, i, a in [ln.split('|') for ln in hosts]]
            # производим обновление данных
            out, errs = make_update(domains=domains_tuple, inface_list=interfaces)
        else:
            # в случае, если данных разделенных знаком '|' НЕТ
            # производим обновление данных
            out, errs = make_update(domains=hosts, inface_list=interfaces)

        # Проверяем на наличие ошибок при предыдущих операциях
        if errs:
            # в случае наличия ошибок составляем список и
            # нумеруем его, в каждой новой строке
            out += [mes.replace(Error.INDICATOR, f"{bs}{n}.{be} ")
                    for n, mes in enumerate(errs, 1)]
            result = "\n".join(out)
        else:
            # Если ошибок нет, то формируем финальное сообщение об этом.
            hosts_text = "\n".join(hosts).replace(etag.divo, ' --> ')
            mult = len(hosts) > 1
            mult_1 = 'ые имена' if mult else 'ое имя'
            mult_2 = f"{bs}{hosts_text}{be}\n{LINE}" if mult else ''
            mult_3 = ', перечисленные выше' if mult else f" ({hosts_text})"
            mult_4 = 'ы' if mult else 'о'
            result = f"{mult_2}Доменн{mult_1}{mult_3} из архива \n{bs}{backup_name}{be} успешно загружен{mult_4}."

    else:
        # если в первом элементе списка есть флаг ошибки,
        # то возвращаем сообщение об ошибке при получении списка из архива
        result = hosts[0]

    return result


def delete_backup(backup_list: list) -> str:
    """
    
    Функция проводит удаление всех переданных для удаления имен архивов
    
    :param backup_list: 
    :return: 
    """
    # Сообщение о результате
    result = ''
    # списки для имен файлов которые были удалены хорошо и с ошибками
    err_list, ok_list = [], []
    # проверяем наличие папки для архивов
    if tools.check_path(BACKUP_PATH):
        # если папка существует, то идем по циклу
        for file in backup_list:
            # удаляем файл
            res = tools.rm_file(f"{BACKUP_PATH}/{file}")
            # проверяем на ошибки
            if res:
                # если все хорошо добавляем соответствующий список
                ok_list.append(file)
            else:
                # если были ошибки, то добавляем соответствующий список
                err_list.append(file)
    else:
        return f"Целевой папки {bs}{BACKUP_PATH}{be} для хранения архивов не существует!"

    mult = len(ok_list) > 1
    mult_1 = "ы" if mult else ''
    if ok_list:
        result = f"Архив{mult_1} {bs}{' ,'.join(ok_list)}{be} успешно удален{mult_1}!\n"
    if err_list:
        result = f"{result}\n" if result else '' + f"Архив{mult_1} {bs}{' ,'.join(err_list)}{be} удалить не удалось!\n"

    return result


def get_backup_details() -> dict:
    """
    Функция формирует и возвращает словарь с информацией об архивах,
    где ключ это название файла и значение это число доменов в файле
    {
        '12.02.2022': { 'count': 2 },
        '13.03.2022': { 'count': 4 },
    }

    :return:
    """

    result = {}

    # Проверяем наличие папки архива по умолчанию
    if tools.check_path(path=BACKUP_PATH):
        # получаем и сортируем список архива
        backup_list = sorted(tools.listdir(path=BACKUP_PATH))
        # проверяем на наличие файлов
        if backup_list:
            #  если они есть, по обрабатываем каждый из них
            for file in backup_list:
                backup_file = f"{BACKUP_PATH}/{file}"
                # получаем число строк в файле
                lines = tools.lines_in_file(file=backup_file)
                # добавляем в словарь информацию
                result.update({file: {etag.count: lines}})
    else:
        # Если пути к архивам нет - создаем ее и возвращаем пустой результат.
        tools.mkdir(path=BACKUP_PATH)
        result = {}

    return result


def get_backup_host_list(backup_name: str) -> list:
    """
    Функция возвращает список хостов записанных в файле архива

    :param backup_name: имя архива, без пути к нему.
    :return: список архива или список с одним сообщением об ошибке
    """

    #  формируем команду для получения содержимого архива
    cmd = f"cat < '{BACKUP_PATH}/{backup_name}'"
    state, out = tools.run(command=cmd)
    if state and out:
        # если все прошло успешно, то формируем список,
        # оставляя только значения
        result = [h for h in out.split('\n') if h]
    else:
        # если возникли ошибки, то пишем об этом
        result = [f'{Error.INDICATOR} Архив {backup_name} прочитать не удалось!']

    return result


def rename_backup(old_name: str, new_name: str) -> str:
    """
    Функция переименовывает архив

    :param old_name: старое имя архива
    :param new_name: новое имя архива для замены

    :return: сообщение о результате операции
    """

    cmd = f"mv '{BACKUP_PATH}/{old_name}' '{BACKUP_PATH}/{new_name}'"
    state, out = tools.run(command=cmd)
    if state:
        result = f'Архив {bs}{old_name} успешно{be} переименован в ' \
                 f'{bs}{new_name}{be}!'
    else:
        result = f'{Error.INDICATOR} Архив {bs}{old_name}{be}  переименовать {bs}не удалось{be}!'
    return result


def delete_host_from_backup(backup_name: str, host: str) -> str:
    """
    Функция удаляет из архива конкретный хост

    :param backup_name:
    :param host:
    :return:
    """
    # формируем команду н удаление
    cmd = f"sed -i '/{host}/d' '{BACKUP_PATH}/{backup_name}'"
    # производим удаление хоста
    state, out = tools.run(command=cmd)
    # выдаем результат
    host_txt = f"{bs}{host}{be}"
    backup_txt = f"{bs}{backup_name}{be}"
    # возвращаем сообщение о результате
    if state:
        result = f'Домен {host_txt} успешно удален ' \
                 f'из архива {backup_txt}!'
    else:
        result = f'Домен {host_txt} удалить из архива ' \
                 f'{backup_txt} не удалось!'
    return result
