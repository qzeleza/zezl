#!/opt/bin/python3
# -*- coding: UTF-8 -*-
#
#  Copyright (c) 2022.
#
#  Автор: mail@zeleza 03.2022
#  Вся сила в правде!
#
import sys

from libraries.main import tools as tools, vpn as vpn_lib
from libraries.main.config import get_config_value
from logs.logger import zlog
from setup.autosets import (
    ADD_ACTION, DEL_ACTION, EXPORT_ACTION, PURGE_ACTION,
)
from setup.data import (
    DEMON_NAME, VERSION, etag,
    CONFIG_FILE, INTERFACE_TYPES,
    APP_INITD_NAME, LINE, ETC_PATH,
    BACKUP_PATH
)
from setup.description import (bs, be, rtag, ErrorTextMessage as Error)


def cmd_show_help() -> str:
    """
    Функция отображает в режиме командной
    строки справку о возможностях утилиты

    :return: строку со справкой
    """

    h_line = "--------------------------------------------------------------------------------------------------------"
    text = f"""{h_line}
Данная утилита zpu™ является частью пакета Жезл™ (Zezl™). Она позволяет обрабатывать доменные имена, находящиеся 
в \"Белом списке\" (далее БС), и занимается маршрутизацией этих имен через существующее VPN соединение. 
При обращении к любому домену из этого списка, весь трафик будет идти через выбранное Вами VPN соединение.
{h_line}
Ключи запуска: 
{DEMON_NAME} {{update|add|new|del|rm|show|list|purge|clear|interface|infacelist|import|restore|export|period|dns|version|help}} [хост]
{h_line}
add | new          -  добавляем один или несколько хостов в БС, где первым аргументом является сам хост,
                      вторым может быть указан флаг авто-включения маршрута, когда доступен выбранный VPN шлюз.
                      Не включать маршрут: off. По умолчанию всегда on (указывать не обязательно). Как пример:
                      {DEMON_NAME} add ya.ru google.com on Wireguard1
del | rm           -  удаляем указанный хост из БС на заданном интерфейсе.
purge | clear      -  полностью очищаем/удаляем БС.
dns                -  отображает текущие используемые DNS сервера для запросов IP искомого хоста.
show | list        -  выводим список всех хостов в БС.
update             -  обновляем список IP адресов для хостов в БС.
period             -  установка/просмотр периода обновления ip адресов для БС.
                      Период должно указывать в форматах: m,h,d,w,M, например:
                        2m - обновляем каждые две минуты
                        2h - обновляем каждые два часа
                        3d - обновляем каждые три дня
                        4w - обновляем каждые четыре недели
                        2M - обновляем каждых два месяца
                      возможен только один из вариантов, например, 10m или 2h
                      по умолчанию, установлен период обновления каждые 12 часов или 2 раза в сутки.
period del | rm    -  удаление периода обновления ip адресов 
export             -  экспорт БС в указанный (если задан) или в файл по умолчанию.
backups            -  отображает все созданные архивные файлы.
backups del | rm   -  выводит список существующих архивов для последующего удаления.
import | restore   -  добавляем хосты из файлового архива в БС. Правила хранения в файле: 
                      один хост - одна строка, на строке может быть записаны три параметра, разделенных
                      знаком '|', как пример ya.ru|OpenVPN0|on, где ya.ru - хост, OpenVPN0 - номер интерфейса, 
                      и on - флаг auto (может принимать значения on или off).
interface | 
infacelist         -  отображаем доступные VPN интерфейсы в системе (если их несколько).
version            -  отображаем версию утилиты.
help               -  настоящая справка.
{h_line}
Примеры использования:
{h_line}
{DEMON_NAME} add google.com OpneVPN1  	- добавляем google.com в БС.
{DEMON_NAME} add google.com off         - добавляем google.com в БС, при этом маршрут 
                                          не будет применяться, когда будет доступен выбранный VPN шлюз.
{DEMON_NAME} import ./list.txt 	        - добавляем хосты из файла ./list.txt в БС.
{DEMON_NAME} del google        	        - удаляем все хосты из БС, которые содержат слово google.
{DEMON_NAME} show              	        - выводим все хосты из БС.
{DEMON_NAME} purge             	        - очищаем/удаляем все хосты из БС.
{h_line}
    """

    return text


def cmd_show_version() -> str:
    """
    Функция выводит информацию о проекте

    :return:
    """
    mess = f"{LINE}" \
           f"Проект 'Жезл™'/'Zezl™' ({DEMON_NAME}™) Версия {VERSION}\n" \
           f"{LINE}"
    return mess


def cmd_show_backup_list():
    """
    Функция выводит список всех архивов

    :return:
    """
    list_files = "\n".join(tools.listdir(BACKUP_PATH))
    mess = f"{LINE}" \
           f"Список архивных файлов в папке {BACKUP_PATH}\n" \
           f"{LINE}" \
           f"{list_files}\n" \
           f"{LINE}"

    return mess


def cmd_show_hosts() -> str:
    """
    Функция отображает список хостов

    :return:
    """
    # Получаем информацию о доменах в БС
    hosts = vpn_lib.get_hosts_details()
    # Для получения ровных рядов при выводе информации используем
    # функцию подсчета максимальной длины элемента в списке
    # по всем трем основным полям auto, интерфейс и домен
    # ljust_hosts = max([len(k) for k in hosts.keys()])
    # ljust_auto = 3
    # ljust_inter = max([len(v[etag.interface]) for v in hosts.values()])
    mess = [
        f"{h}: ({', '.join([f'{db[etag.interface]}:{etag.on if db[etag.auto] else etag.off}' for db in dt])}) -> "
        f"[{', '.join([' '.join(da[etag.ip]) for da in dt])}]"
        for h, dt in hosts.items()]

    # #  Формируем сообщение для вывода
    # mess = [f"{f'{etag.on}:'.ljust(ljust_auto) if v[etag.auto] else f'{etag.off}:'.ljust(ljust_auto)} "
    #         f"({v[etag.interface].ljust(ljust_inter)}) {k.ljust(ljust_hosts)} [{', '.join(v[etag.ip])}]"
    #         for k, v in hosts.items()]
    mess = "\n".join(mess) if mess else "Доменов в списке нет."
    #  дополняем сообщение линиями разделения
    mess = f"Белый список:\n" \
           f"{LINE}" \
           f"{mess}\n" \
           f"{LINE}"

    return mess


def cmd_update_hosts() -> str:
    """
    Функция возвращает сообщение о результате обновления в белом списке

    :return:
    """
    mess = f"{LINE}" \
           f"ВНИМАНИЕ!\n" \
           f"Процедура обновления может занять значительное время.\n" \
           f"Пожалуйста дождитесь ее окончания!"
    print(mess)

    # Получаем все домены из белого списка
    hosts = vpn_lib.get_hosts()
    #  получаем по каждому домену сообщения о результате обновления
    results_mess = vpn_lib.update_host_list(hosts=hosts)
    # производим выборку только сообщений об ошибках
    errors_mess = [ms for ms in results_mess if Error.INDICATOR in ms]

    if errors_mess:
        # если возникли ошибки печатаем их все
        mess = "\n".join(errors_mess)
        mess = f"При обновлении возникли ошибки:\n" \
               f"{mess}"
    else:
        #  если ошибок нет - тоже печатаем
        mess = f'Обновление прошло успешно!\n' \
               f"{LINE}" \
               f"{cmd_show_hosts()}"
    # добавляем пунктир сверху сообщения
    mess = f"{LINE}" \
           f"{mess}\n" \
           f"{LINE}"

    return mess


def cmd_choose_interface(action: str, raw_interfaces: list = None) -> list | str:
    """
    Функция осуществляет генерацию списка интерфейсов в системе и выбор одного из них.

    :param: action - тип операции для которой производится выбор интерфейсов.
            DEL_ACTION - удаление хоста, ADD_ACTION - добавление хоста
            PURGE_ACTION - удаление всех хостов на выбранном интерфейсе
            EXPORT_ACTION - экспорт хостов на выбранный интерфейс.
    :param: raw_interfaces - список не отформатированных интерфейсов, обнаруженных в строке ввода.

    :return: список номеров интерфейсов, в случае выбора одного или всех интерфейсов и
             сообщение об ошибке, в случае если интерфейс такой не был найден
    """
    av_inface_list, inface_names, connected = vpn_lib.get_available_interface_list(connected_only=False)
    # проверяем были ли заданы интерфейсы в строке ввода
    if raw_interfaces:
        # в случае, если интерфейсы были заданы из командной строки,
        # то проверяем их на правильность введения и получаем результат
        # с учетом регистра и с номером интерфейса на конце
        inface = vpn_lib.get_interface_type_name(source=" ".join(raw_interfaces))
        # проверяем на полученный результат
        for el in inface:
            if el not in av_inface_list:
                # если полученного интерфейса НЕТ в списке доступных
                return f"Указанный интерфейс '{bs}{el}{be}' отсутствует в списке доступных\n" \
                       f"Исправьте и повторите ввод, либо вовсе не вводите название интерфейса,\n" \
                       f"в этом случае, Вы сможете выбрать доступные варианты из списка."
    else:
        # в случае, если интерфейсы НЕ были заданы из командной строки
        # получаем список интерфейсов
        if action == DEL_ACTION:
            action_text = "удаления"
            # при удалении ориентируемся на интерфейсы существующих
            # доменных имен помеченных для удаления
            interfaces = raw_interfaces
        else:
            if action == PURGE_ACTION:
                action_text = "удаления"
            elif action == ADD_ACTION:
                action_text = "добавления"
            elif action == EXPORT_ACTION:
                action_text = "экспорта"
            else:
                raise Exception(f"ОШИБКА в коде: Данный вид действия с кодом '{action}' не предусмотрен!")
            # во всех случаях кроме удаления ориентируемся на доступные в системе интерфейсы
            interfaces = av_inface_list

        # ориентируемся на число интерфейсов
        ask_to_choose = f"Список доступных интерфейсов для {action_text}:"
        # получаем список имен интерфейсов вместо их номерам
        list_to_choose = [f"{n} [{rtag.StatusOn if c else rtag.StatusOff}]" for c, n in zip(connected, inface_names)]
        # через консоль запрашиваем выбор пользователя для продолжения
        chosen = tools.ask_input(ask_to_choose=ask_to_choose,
                                 list_to_choose=list_to_choose,
                                 element_text="интерфейс")
        # так как мы отображали имена интерфейсов,
        # а не их номера, то сейчас нужно их преобразовать в номера
        if len(chosen) > 1:
            # если выбор на все интерфейсы
            inface = interfaces
        else:
            # если выбор пал только на один интерфейс
            index = list_to_choose.index(chosen[0])
            inface = [interfaces[index]]

    return inface


def cmd_add_or_del_hosts_action(action: str, text_data: str = None) -> str:
    """
    Функция добавления/удаления доменов через командную строку
    при этом производится анализ ввода названия определенных интерфейсов в сроке ввода

    :param text_data: строка с данными в которой могут быть хост, интерфейс
           и флаг auto в виде 'on' или 'off'. Пример, 'ya.ru on OpenVPN1'
    :param action: тип производимого действия Удаление или добавление DEL_ACTON | ADD_ACTION
    :return: сообщение о результате исполнения
    """
    # извлекаем из текста список хостов
    domains = tools.get_domain_list(text_data) if action == ADD_ACTION else text_data.split()
    # проверяем данные
    if domains:
        # извлекаем данные по интерфейсам из строки ввода
        interfaces = tools.get_inside(checking_list=INTERFACE_TYPES, source=text_data)
        if interfaces:
            # если были введены интерфейсы в командной строке, то извлекаем их из списка доменных имен
            domains = [el for el in domains if not tools.has_inside(checking_list=interfaces, source=el)]
        # извлекаем данные по флагу auto из строки ввода
        auto_list = tools.get_inside(checking_list=[etag.on, etag.off], source=text_data)
        if auto_list:
            # если были введен флаг auto в командной строке, то извлекаем их из списка доменных имен
            auto_list = [bool(el.replace(etag.on, 'True').replace(etag.off, 'False')) for el in domains if
                         el == etag.on or el == etag.off]
            domains = [el for el in domains if not (el == etag.on or el == etag.off)]
        else:
            auto_list = [True for _ in domains]
    else:
        # введенные доменные имена содержат ошибки
        return "Проверьте введенные доменные имена, скорее всего список содержит ошибки."

    # inface_text = f'"{", ".join(inface)}"' if inface else 'всех интерфейсов'
    if action == ADD_ACTION:
        # если интерфейс не задан в командной строке, то выбираем его из списка
        inface = cmd_choose_interface(raw_interfaces=interfaces, action=ADD_ACTION)
        if isinstance(inface, str):
            # если полученного интерфейса НЕТ в списке доступных,
            # то возвращаем сообщение об этом
            return inface
        # загружаем данные (добавляем)
        mess = f"{LINE}" \
               f"ВНИМАНИЕ!\n" \
               f"Процедура добавления может занять значительное время.\n" \
               f"Пожалуйста дождитесь ее окончания!"
        print(mess)
        mess = tools.clean_html(
            vpn_lib.load_hosts_to_white_list(host_list=domains,
                                             interfaces=inface,
                                             auto_list=auto_list)
        )
        mess = f"{LINE}" \
               f"{mess}\n" \
               f"{LINE}"

    elif action == DEL_ACTION:
        # в случае удаления избранных хостов
        # получаем список доступных интерфейсов для удаляемых хостов
        data = vpn_lib.get_hosts_details(selected_hosts=domains, interfaces=interfaces)
        interfaces = list(set(" ".join([" ".join([k[etag.interface] for k in data[el]]) for el in data]).split()))
        # если интерфейс не задан в командной строке, то выбираем его из списка
        inface = cmd_choose_interface(raw_interfaces=interfaces, action=DEL_ACTION)
        if isinstance(inface, str):
            # если полученного интерфейса НЕТ в списке доступных,
            # то возвращаем сообщение об этом
            return inface

        # удаляем доменные имена
        mess = f"{LINE}" \
               f"ВНИМАНИЕ!\n" \
               f"Процедура удаления может занять значительное время.\n" \
               f"Пожалуйста дождитесь ее окончания!"
        print(mess)
        mess = tools.clean_html(vpn_lib.remove_hosts_list(hosts=domains, interfaces=inface, result_ok=True))
        mess = f"{LINE}" \
               f"{mess}\n" \
               f"{LINE}"
    else:
        raise Exception(f"Данный вид действия с кодом '{action}' не предусмотрен! Ошибка в коде.")

    return mess


def cmd_purge_all_hosts():
    """
    Функция удаляет все имеющиеся в сисиме хосты из БС

    :return: сообщение о результате удаления
    """
    # делаем запрос на выбор интерфейса для удаления данных
    inface = cmd_choose_interface(action=EXPORT_ACTION)
    # inface, _, _ = vpn_lib.get_available_interface_list(connected_only=False)
    if isinstance(inface, str):
        # если полученного интерфейса НЕТ в списке доступных,
        # то возвращаем сообщение об этом
        return inface
    mess = f"{LINE}" \
           f"ВНИМАНИЕ!\n" \
           f"Процедура удаления может занять значительное время.\n" \
           f"Пожалуйста дождитесь ее окончания!"
    print(mess)
    # удаляем доменные имена
    mess = tools.clean_html(vpn_lib.remove_hosts_list(interfaces=inface, result_ok=True))
    mess = mess if mess else "Домены для удаления отсутствуют."
    # выводим результаты удаления данных
    mess = f"{LINE}" \
           f"{mess}\n" \
           f"{LINE}"

    return mess


def cmd_choose_backup(action_desc: str, all_first: bool = False) -> list:
    """
    Функция выводит в консоли список существующих архивов

    :param action_desc: текст описывающий действие, которое будет производиться
                        с архивами в творительном падеже например: удаления, импорта и пр.,
                        Служит для заголовка.
    :param all_first: флаг наличия первого элемента в списке с вариантом "1. Все варианты ниже"

    :return: имя архива
    """
    # получаем список доступных архивов
    backup_list = tools.listdir(BACKUP_PATH)
    # если их более одного производим запрос
    if len(backup_list) > 1:
        # заголовок запроса
        ask_to_choose = f"Список архивов, доступных  для {action_desc}:"
        # выбираем один из них, если их несколько
        chosen = tools.ask_input(ask_to_choose=ask_to_choose,
                                 list_to_choose=backup_list,
                                 element_text="архив",
                                 all_first=all_first)
    else:
        # если доступен только один архив
        chosen = backup_list

    # должен быть выбран только один архив
    return chosen


def cmd_delete_backup() -> str:
    """
        Функция удаляет архив/ы

        :return: результат удаления в виде строки

        """
    # для импорта должен быть выбран только один архив
    chosen = cmd_choose_backup(action_desc="удаления", all_first=True)
    result = tools.clean_html(vpn_lib.delete_backup(backup_list=chosen))
    mess = f"{LINE}" \
           f"{result}" \
           f"{LINE}"
    return mess


def cmd_import_backup() -> str:
    """
    Функция импортирует данные из архива

    :return: результат импорта в виде строки

    """
    # для импорта должен быть выбран только один архив
    chosen = cmd_choose_backup(action_desc="импорта", all_first=False)
    chosen = "".join(chosen)
    zlog.debug(chosen)
    if chosen:
        mess = f"{LINE}" \
               f"ВНИМАНИЕ!\n" \
               f"Процедура импорта может занять значительное время.\n" \
               f"Пожалуйста дождитесь ее окончания!"
        print(mess)
        # производим импорт архива
        result = tools.clean_html(vpn_lib.load_backup(backup_name=chosen))
        mess = f"{LINE}" \
               f"{result}\n" \
               f"{LINE}"
    else:
        mess = "Архив не был выбран!"

    return mess


def cmd_export_backup(backup_name: str = None) -> str:
    """
     Осуществляем экспорт данных в файл

    :param: backup_name: полный путь до имени архива.
    :return: сообщение о результате проведения экспорта
    """
    # Запрашиваем на какой интерфейс производить экспорт данных
    infaces = cmd_choose_interface(action=EXPORT_ACTION)
    # infaces, _ = vpn_lib.get_available_interface_list(connected_only=False)
    # создаем архив
    zlog.debug(infaces)

    mess = tools.clean_html(vpn_lib.create_backup(backup_file=backup_name, interfaces=infaces))
    backup_name = mess.split('\n')[1]
    zlog.debug(backup_name)
    # получаем содержимое архива и выводим его
    # file_content = libraries.get_file_content(file=backup_name)
    # file_content = "\n".join(file_content) if etag.cmd.slash in backup_name else "Архив не может быть прочитан."
    hosts_count = tools.lines_in_file(backup_name)
    mess = f"{LINE}" \
           f"{mess}\n" \
           f"{LINE}" \
           f"Всего доменов: {hosts_count} шт.\n" \
           f"{LINE}"

    return mess


def cmd_set_admin(user_id: str) -> str:
    """
    Функция устанавливает user_id в качестве администратора бота
    После его установки другие пользователи не смогу управлять ботом

    :param user_id: идентификатор пользователя admin
    :return: сообщение о результате установки user_id

    """
    # шаблон для проверки user_id [6-10 цифр]
    regex = r'([0-9]{6,10})'
    from re import findall
    # проверяем на совпадение с шаблоном
    user_id_is_ok = "".join(findall(regex, user_id))
    #  проверка на наличие токена после шаблона
    if user_id_is_ok:
        # Токен введен верный.
        # Команда bash для записи token
        cmd = f"sed -i \"/USER_ID/d\" \"{CONFIG_FILE}\" && echo USER_ID={user_id_is_ok} >> \"{CONFIG_FILE}\""
        # узнаем установлен ли токен
        token = get_config_value(name=etag.token)
        if token:
            # если токен уже установлен
            # далее запускаем пакет
            cmd = f"{cmd} && {ETC_PATH}/init.d/{APP_INITD_NAME} restart"
            # отображаем статус запуска пакета
            cmd = f"{cmd} && {ETC_PATH}/init.d/{APP_INITD_NAME} status"
        #     запускаем на исполнение
        is_ok, mess = tools.run(command=cmd)
        # если команда прошла успешно
        if is_ok:
            # если все хорошо
            mess = f"Администратор бота установлен успешно.\n" \
                   f"Безопасность бота подтверждена.\n"
            if token:
                mess = f"{mess}\n" \
                       f"Запускаем бота...\n" \
                       f"{LINE}" \
                       f"{mess}\n" \
                       f"{LINE}" \
                       f"Готово."
            else:
                mess = f"{mess}\n" \
                       f"Для дальнейшей работы с ботом необходимо\n" \
                       f"установить его токен, для этого введите команду:\n" \
                       f"<b>zpu token <токен бота></b>"
        else:
            # если возникли проблемы
            mess = "При установке user_id возникли проблемы." \
                   f"{LINE}" \
                   f"{mess}"
    else:
        # если токен введен неверно
        mess = "Введено неверное значение user_id\n" \
               "Проверьте его посимвольно и введите вновь!"

    return mess


def cmd_set_token(token: str) -> str:
    """
    Функция установки Телеграмм токена

    :param token: строка с телеграмм токеном.
    :return: сообщение об успехе операции
    """
    # шаблон для проверки токена [10 цифр]:[35 букв или цифр]
    regex = r'([0-9]{10}:[\_a-zA-Z0-9\-]{35})'
    from re import findall
    # проверяем на совпадение с шаблоном
    token_is_ok = "".join(findall(regex, token))
    #  проверка на наличие токена после шаблона
    if token_is_ok:
        # Токен введен верный.
        # Команда bash для записи token
        cmd = f"sed -i \"/TOKEN/d\" \"{CONFIG_FILE}\" && echo TOKEN={token_is_ok} >> \"{CONFIG_FILE}\""
        # cmd = f"sed -i \"s/^TOKEN*=*/TOKEN={token_is_ok}/g\" \"{CONFIG_FILE}\""
        # далее запускаем пакет
        cmd = f"{cmd} && {ETC_PATH}/init.d/{APP_INITD_NAME} restart"
        # отображаем статус запуска пакета
        cmd = f"{cmd} && {ETC_PATH}/init.d/{APP_INITD_NAME} status"
        is_ok, mess = tools.run(command=cmd)
        if is_ok:
            # если все хорошо
            mess = f"Токен успешно установлен.\n" \
                   f"Запускаем бота...\n" \
                   f"{LINE}" \
                   f"{mess}" \
                   f"{LINE}" \
                   f"Готово.\n"
            user_id = get_config_value(name=etag.user_id)
            if user_id:
                # если user_id не установлен
                mess = f"{mess}\n" \
                       f"{LINE}" \
                       f"Безопасность бота имеет бреш.\n" \
                       f"Для ее устранения необходимо ввести user_id администратора бота.\n" \
                       f"С этой целью запустите следующую команду. \n" \
                       f"<b>zpu admin <user_id администратора></b>"
        else:
            # если возникли проблемы
            mess = "При установке токена возникли проблемы." \
                   f"{LINE}" \
                   f"{mess}"
    else:
        # если токен введен неверно
        mess = "Введено неверное значение токена\n" \
               "Проверьте его посимвольно и введите вновь!"

    return mess


def cmd_show_interface_list() -> str:
    """
    Функция возвращает сообщение о доступных интерфейсах
    Это просто надстройка над get_available_interface_list()
    :return: сообщение об интерфейсах
    """
    _list_inface, _list_inf_names, _connected = vpn_lib.get_available_interface_list(connected_only=False)
    _list_inface = "\n".join([f"{n}. {m} -> {i} [{rtag.StatusOn if c else rtag.StatusOff}]"
                              for (n, i, m, c) in
                              zip(range(1, len(_list_inface) + 1), _list_inface, _list_inf_names, _connected)]) \
        if len(_list_inface) > 1 else "".join(_list_inface)

    return f"Список доступных интерфейсов:\n" \
           f"{LINE}" \
           f"{_list_inface}"


# ------------------------------------------------------------------------------------------
def no_args() -> str:
    """
    Функция выводит сообщение в случае отсутствие каких либо аргументов

    :return:
    """
    mess = '\nТребуются аргументы для исполнения команды!\n' \
           f"{LINE}" \
           f"{cmd_show_help()}"
    return mess


if __name__ == "__main__":
    #
    #  Здесь разбираем аргументы, в случае
    #  запуска файла из командной строки
    #
    # считаем число переданных аргументов
    args_count = len(sys.argv) - 1
    if args_count >= 1:
        # получаем все аргументы после введенной команды
        args_str = " ".join(sys.argv[2:])
        # если их больше одного, то обрабатываем их
        match sys.argv[1]:

            # ДОБАВИТЬ ДОМЕНЫЕ ИМЕНА
            case etag.cmd.add | etag.cmd.new:
                # команда add host - добавления хостов в БС
                res = cmd_add_or_del_hosts_action(text_data=args_str,
                                                  action=ADD_ACTION) if args_count > 1 else no_args()

            # УДАЛИТЬ ДОМЕНЫЕ ИМЕНА
            case etag.cmd.delete | etag.cmd.rm:
                # Команда удаления доменов из БС
                res = cmd_add_or_del_hosts_action(text_data=args_str,
                                                  action=DEL_ACTION) if args_count > 1 else no_args()

            # ПОКАЗАТЬ ДОМЕНЫЕ ИМЕНА
            case etag.cmd.show | etag.cmd.list:
                # Команда выводит все доменные имена из БС
                res = cmd_show_hosts()

            # РАБЛТА С ТАЙМЕРОМ ОБНОВЛЕНИЯ ДОМЕННЫХ ИМЕН
            case etag.cmd.period:
                # Команда обработки таймера для обновления хостов
                if args_count == 2:
                    # если был задан второй аргумент, то проверя его
                    if sys.argv[2] == etag.cmd.delete or sys.argv[2] == etag.cmd.rm:
                        #  УДАЛИТЬ ТАЙМЕР ОБНОВЛЕНИЯ
                        # если это была команда del или rm,
                        # то удаляем таймер из crontab
                        res = vpn_lib.remove_timer()
                    else:
                        # ЗАДАТЬ СОСТОЯНИЕ ТАЙМЕРА
                        # если был иной второй аргумент, то предполагаем,
                        # что это был задан период таймера обновления
                        # и стараемся установить его
                        res = vpn_lib.set_timer_period(data=sys.argv[2])
                else:
                    # ПОКАЗАТЬ СОСТОЯНИЕ ТАЙМЕРА
                    # если был только один аргумент, то просто
                    # выводим информацию о текущем состоянии таймера обновления
                    res = vpn_lib.get_timer_period()

            # ОТОБРАЖАЕМ НОМЕР ВЕРСИИ ZPU
            case etag.cmd.version:
                # Выводим информацию о версии утилиты
                res = cmd_show_version()

            # ЗАДАЕМ ТОКЕН ДЛЯ РАБОТЫ БОТА
            case etag.cmd.token:
                if args_count == 2:
                    res = cmd_set_token(token=sys.argv[2])
                else:
                    res = "Токен не задан!\n" \
                          "Пожалуйста, введите токен третьим аргументом.\n" \
                          f"Пример: {DEMON_NAME} token <токен_вашего_бота>"

            # ЗАДАЕМ USER_ID ДЛЯ БЕЗОПАСНОЙ РАБОТЫ БОТА
            case etag.cmd.admin:
                if args_count == 2:
                    res = cmd_set_admin(user_id=sys.argv[2])
                else:
                    res = "user_id администратора не задан!\n" \
                          "Пожалуйста, введите user_id третьим аргументом.\n" \
                          f"Пример: {DEMON_NAME} admin <user_id администратора>"

            # АРХИВЫ
            case etag.cmd.backups:
                if args_count == 2:
                    if sys.argv[2] == etag.cmd.rm or sys.argv[2] == etag.cmd.delete:
                        # УДАЛЕНИЕ АРХИВОВ
                        res = cmd_delete_backup()
                else:
                    # ПОКАЗАТЬ СПИСОК АРХИВОВ
                    res = cmd_show_backup_list()

            # ОБНОВЛЯЕМ ДАННЫЕ ВСЕХ ДОМЕННОВ НА ВСЕХ ИНТЕРФЕЙСАХ
            case etag.cmd.update:
                # обновляем IP адреса хостов в БС
                res = cmd_update_hosts()

            # ИМПОРТ ДАННЫХ из файлового архива
            case etag.cmd.load:
                res = cmd_import_backup()

            # СОХРАНЕНИЕ/ЭКСПОРТ ДАННЫХ В ФАЙЛ АРХИВА
            case etag.cmd.export:
                # Команда экспорта БС в файл в папку BACKUP_PATH
                file_name = sys.argv[2] if args_count == 2 else None
                res = cmd_export_backup(backup_name=file_name)

            # УДАЛЕНИЕ ВСЕХ ДАННЫХ ИЗ БЕЛОГО СПИСКА
            case etag.cmd.purge | etag.cmd.clear:
                # Команда очищения всего БС
                res = cmd_purge_all_hosts()

            # ОТОБРАЖАЕМ СПИСОК ДОСТУПНЫХ ИНТЕРФЕЙСОВ
            case etag.cmd.interface | etag.cmd.infacelist:
                #  Получаем список всех доступных интерфейсов
                res = cmd_show_interface_list()
            # ОТОБРАЖАЕМ СПИСОК ДОСТУПНЫХ DNS в системе
            case etag.cmd.dns:
                # Выводим список доступных DNS в системе
                res = vpn_lib.get_system_dns_report()

            # ОТОБРАЖАЕМ СПРАВКУ ПО ИСПОЛЬЗОВАНИЮ ПРОГРАММЫ ZPU
            case _:
                # в случае, какой-либо иной команды, то
                # выводим справку о помощи
                res = cmd_show_help()

    else:
        # Если аргументы совсем не заданы, то
        # выводим справку о помощи
        res = cmd_show_help()

    print(tools.clean_html(res))
    sys.exit(1)
