#!/opt/bin/python3
# -*- coding: UTF-8 -*-

#
#  Copyright (c) 2022.
#
#  Автор: mail@zeleza 04.2022
#  Вся сила в правде!
#

# Автор: zeleza
# Вся сила в правде!
# Email: info@zeleza.ru
# Дата создания: 24.04.2022 18:03
# Пакет: PyCharm

"""

 Файл содержит библиотеку работы со
 Сторожем Новостей (следит за обновлением сайтов)
    
"""
from datetime import datetime

import httplib2
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from libraries.main.decorators import func_name_logger
from libraries.main.dialog import alert
from libraries.main.tools import (
    get_file_content,
    run as bash, get_hash, match, clean_me, period_to_rus, check_url
)
from logs.logger import zlog
from setup.autosets import CALLBACK_TO_CLOSE_MENU
from setup.data import etag, LINK_LIST_FILE, LINE, WDOGS_DELAY_BEFORE_DELETE, WDOG_SAVE_FORMAT, ROUTER_LOG_DATE_FORMAT, \
    UPDATE_DATE_FORMAT
from setup.description import be, bs, cde, cds


@func_name_logger
def get_data_page(link: str) -> dict:
    """
    Функция получает данные по конкретной ссылке
    из файла конфигурации обновления ссылок

    :return: словарь со структурой данных ниже:
            'state':, состояние отслеживания страницы: True - включена и False - выключено
            'period':, код периода отслеживания ссылки
            'link':, ссылка на страницу отслеживаемого сайта
            'check_date':, дата крайнего обновления сайта
            'update_date':, дата крайней проверки обновления
            'last_hash':, вычисленный хеш страницы
            'login':, логин для страницы с паролем
            'password': пароль для страницы с паролем
    """

    #  оставляем только доменное имя
    link = check_url(link=link, check_for_validation=False, domain_only=True)
    # готовим команду для извлечения данных
    cmd = f"cat < \"{LINK_LIST_FILE}\" | grep \"{link}\""
    #  исполняем команду
    is_ok, out = bash(command=cmd)
    # проверяем - все ли исполнилось ладно
    if is_ok:
        # удаляем замыкающий символ новой строки, в случае его наличия
        out = out.replace('\n', '')
        # делим сроку и помещаем ее в список
        details = out.split(etag.divo)
        # конвертируем данные в словарь
        result = convert_datalink_to_dict(details)
    else:
        result = {}
        zlog.error(f"{cds}Ошибка чтения из файла '{LINK_LIST_FILE}'{cde}")

    return result


def convert_datalink_to_dict(details: list) -> dict:
    """
    Функция конвертирует данные из списка в словарь со структурой данных.
    Служит для того, чтобы сократить код и используется как минимум в двух функциях

    :param details: список данных из строк файла LINK_LIST_FILE.

    :return: словарь со структурой данных ниже:
            'state':, состояние отслеживания страницы: True - включена и False - выключено
            'period':, код периода отслеживания ссылки
            'link':, ссылка на страницу отслеживаемого сайта
            'check_date':, дата крайнего обновления сайта
            'update_date':, дата крайней проверки обновления
            'last_hash':, вычисленный хеш страницы
            'login':, логин для страницы с паролем
            'password': пароль для страницы с паролем
    """

    field_names = [
        etag.state,
        etag.period,
        etag.link_name,
        etag.link,
        etag.check_date,
        etag.update_date,
        etag.last_hash,
        etag.login,
        etag.password,
    ]
    # host = namedtuple(typename=etag.host, field_names=field_names, defaults=None)
    host = {}
    sims_to_del = ' \t\n\r'

    def map_details(_zip):
        _key, _value = _zip
        _vl = ''
        if etag.state in _key:
            _vl = True if etag.on in _value else False
        elif etag.period in _key:
            # _vl = period_to_rus(_value)
            _vl = _value
        else:
            _vl = _value.strip(sims_to_del)
        host.update({_key: _vl})
        return True

    _ = [map_details(k) for k in zip(field_names, details)]

    # host[etag.state] = True if etag.on in details[0] else False if len(details) > 0 else None
    # host[etag.period] = period_to_rus(details[1]) if len(details) > 1 else None
    # host[etag.link] = details[2].strip(sims_to_del) if len(details) > 2 else None
    # host[etag.link] = details[3].strip(sims_to_del) if len(details) > 3 else None
    # host[etag.check_date] = details[4].strip(sims_to_del) if len(details) > 4 else None
    # host[etag.update_date] = details[5].strip(sims_to_del) if len(details) > 5 else None
    # host[etag.last_hash] = details[6].strip(sims_to_del) if len(details) > 6 else None
    # host[etag.login] = details[7].strip(sims_to_del) if len(details) > 7 else None
    # host[etag.password] = details[8].strip(sims_to_del) if len(details) > 8 else None

    return host


def get_page_data_list(links_only: bool = False) -> list[dict | str]:
    """
    Функция получает список данных об отслеживаемых сайтах
    из файла конфигурации обновления ссылок.

    :param: links_only - флаг возврата только ссылок, а не всех данных.

    :return: список из словаря со следующей структурой:
            'state':, состояние отслеживания страницы: True - включена и False - выключено,
            'period':, код периода отслеживания ссылки,
            'link':, ссылка на страницу отслеживаемого сайта,
            'check_date':, дата крайнего обновления сайта,
            'update_date':, дата крайней проверки обновления,
            'last_hash':, вычисленный хеш страницы,
            'login':, логин для страницы с паролем,
            'password': пароль для страницы с паролем,
    """
    # получаем содержимое файла конфигурации
    line_list = get_file_content(file=LINK_LIST_FILE)
    sites, host = [], {}

    for line in line_list:
        # проходимся по каждой строке и удаляем конечный символ новой строки
        line = line.replace('\n', '')
        #  разбиваем данные сроки и помещаем в список
        details = line.split(etag.divo)
        # конвертируем данные в словарь
        data_dict = convert_datalink_to_dict(details)
        # если вернуть нужно только ссылки, то меняем данные
        data_to_save = data_dict[etag.link] if links_only else data_dict
        # добавляем данные из извлеченного словаря в список
        sites.append(data_to_save)

    return sites


@func_name_logger
def save_data_link_to_file(name: str,
                           link: str,
                           period: str,
                           state: bool = True,
                           login: str = None,
                           passwd: str = None) -> bool:
    """
    Функция сохраняет данные о ссылках в файл
    в виде строки следующего формата
    state|period|link|check_date|update_date|last_hash

    :param name: имя с которой будет ассоциирована записываемая ссылка
    :param link: ссылка для записи в файл
    :param period: код строки с периодом данных (3m, 2h, 5d) в формате английских букв
    :param state: состояние отслеживания страницы True(default) - включено и False - выключено
    :param login: логин для страницы с паролем
    :param passwd: пароль для страницы с паролем

    :return: True = в случае успеха и False - в обратном случае
    """
    mode = etag.on if state else etag.off
    # дата крайнего обновления сайта
    date_last_update = f"{etag.divo}{get_site_date_update(link).strftime(WDOG_SAVE_FORMAT)}"
    # дата крайней проверки обновления
    date_last_check = f"{etag.divo}{datetime.now().strftime(WDOG_SAVE_FORMAT)}"
    # получаем содержимое страницы
    page_text = get_site_content_for_hash(url=link)
    # получаем хеш страницы
    last_hash = f"{etag.divo}{get_hash(text=page_text)}"
    del page_text
    # устанавливаем пароль и логин, если они заданы
    login_txt = f"{etag.divo}{login}" if login else ''
    passwd_txt = f"{etag.divo}{passwd}" if passwd else ''
    line = f"{mode}{etag.divo}{period}{etag.divo}{name}{etag.divo}{link}" \
           f"{date_last_check}{date_last_update}{last_hash}{login_txt}{passwd_txt} "
    # Строка для записи в файл
    zlog.debug(f"{line}")
    # для верной записи в файл данных со слешами - экранируем их
    link_ = link.replace('/', '\/')
    # удаляем для начала строку с данными и затем добавляем в конец значение строки
    cmd = f"sed -i \"/{link_}/d\" \"{LINK_LIST_FILE}\" && echo \"{line}\" >> \"{LINK_LIST_FILE}\""
    is_ok, _ = bash(command=cmd)

    return is_ok


def update_link_data(name: str,
                     link: str,
                     period: str,
                     state: bool = True,
                     login: str = None,
                     passwd: str = None) -> str:
    """
    Функция служит для генерации сообщения после записи данных в файл
    state|period|link|check_date|update_date|last_hash

    :param name: имя с которой будет ассоциирована записываемая ссылка
    :param link: ссылка для записи в файл
    :param period: код строки с периодом данных (3m, 2h, 5d) в формате английских букв
    :param state: состояние отслеживания страницы True(default) - включено и False - выключено
    :param login: логин для страницы с паролем
    :param passwd: пароль для страницы с паролем

    :return: Сообщение о результате обновления данных
    """
    if save_data_link_to_file(name=name, link=link, period=period, state=state, login=login, passwd=passwd):
        mess = f"{bs}Данные{be} о периоде обновления {link} {bs}успешно обновлены{be}!"
    else:
        mess = f"{cds}Ошибка удаления данных из '{LINK_LIST_FILE}'{cde}"
        zlog.error(mess)

    return mess


def save_link_data(name: str,
                   link: str,
                   period: str,
                   state: bool = True,
                   login: str = None,
                   passwd: str = None) -> str:
    """
    Функция служит для генерации сообщения после записи данных в файл
    state|period|link|check_date|update_date|last_hash

    :param name: имя с которой будет ассоциирована записываемая ссылка
    :param link: ссылка для записи в файл
    :param period: код строки с периодом данных (3m, 2h, 5d) в формате английских букв
    :param state: состояние отслеживания страницы True(default) - включено и False - выключено
    :param login: логин для страницы с паролем
    :param passwd: пароль для страницы с паролем

    :return: Сообщение о результате добавления данных
    """

    if save_data_link_to_file(name=name, link=link, period=period, state=state, login=login, passwd=passwd):
        mess = f"{bs}Ссылка{be} '{link}' {bs}успешно добавлена{be} в список отслеживания!"
    else:
        mess = f"{cds}Ошибка удаления данных из '{LINK_LIST_FILE}'{cde}"
        zlog.error(mess)

    return mess


@func_name_logger
def remove_link_from_file(link: str) -> str:
    """
    Функция удаляет одну конкретную ссылку из файла ссылок.

    :param: link ссылка для удаления из файла.
    :return: True = в случае успеха и False - в обратном случае
    """
    # удаляем пустые строки и добавляем в конец значение строки
    cmd = f"sed -i '/{link}/d' {LINK_LIST_FILE}"
    is_ok, out = bash(command=cmd)

    if is_ok:
        mess = f"{bs}Ссылка{be} '{link}' {bs}успешно удалена{be} из списка отслеживания!"
    else:
        mess = f"{cds}Ошибка удаления данных из '{LINK_LIST_FILE}'{cde}"
        zlog.error(mess)

    return mess


@func_name_logger
def remove_all_links_from_file() -> str:
    """
    Функция удаляет все ссылки из файла ссылок

    :return: True = в случае успеха и False - в обратном случае
    """
    # удаляем пустые строки и добавляем в конец значение строки
    cmd = f"rm -f {LINK_LIST_FILE} && touch {LINK_LIST_FILE}"
    is_ok, out = bash(command=cmd)

    if is_ok:
        mess = f"Все {bs}ссылки{be} из списка отслеживания {bs}успешно удалены{be}!"
    else:
        mess = f"{cds}Ошибка удаления данных из '{LINK_LIST_FILE}'{cde}"
        zlog.error(mess)

    return mess


@func_name_logger
def get_site_date_update(url: str) -> datetime | None:
    """
    Функция получает время обновления ссылки сайта

    :param url: ссылка на страницу сайта.
    :return:
    """

    if url:
        h = httplib2.Http()
        # делаем HEAD запрос
        resp = h.request(url, etag.head)[0]
        # Получаем дату крайнего обновления страницы
        date_update_txt = resp.get(etag.last_modified)
        # переводим дату в формат даты
        date_site_update = datetime.strptime(date_update_txt, ROUTER_LOG_DATE_FORMAT) if date_update_txt else None
        zlog.debug(f"Дата обновления сайта '{url}' '{date_update_txt}'")
    else:
        zlog.debug(f"Переданная ссылка пуста '{url}'")
        date_site_update = None

    return date_site_update


@func_name_logger
def get_site_content_for_hash(url: str, user: str = None, passwd: str = None) -> str:
    """
    Функция очищает содержимое сайта и готовит его для хеширования

    :param url: ссылка на страницу сайта
    :param user: имя пользователя
    :param passwd: пароль
    :return:
    """
    http = httplib2.Http()
    # проверяем передали ли данные по авторизации
    if user and passwd:
        # если данные есть добавляем их в запрос
        http.add_credentials(user, passwd)
    # получаем содержимое страницы
    headers = {'connection': 'close'}
    _, content = http.request(url, headers=headers)
    # подключаем парсер страницы
    soup = BeautifulSoup(content, 'html.parser') if content else None
    # удаляем из страницы скрипты и теги стиля
    for script in soup(["script", "style"]):
        script.extract()
    # получаем текст
    text = soup.get_text()
    del soup, content, script
    # разделяем текст ан строки
    lines = (line.strip() for line in text.splitlines())
    # разделяем строки на слова.
    chunks = tuple(phrase.strip() for line in lines for phrase in line.split(" ") if phrase and match(phrase))
    # соединяем все слова и удаляем все слова которые меньше 4 букв
    text = "".join(clean_me(chunk.lower(), ',:.-_><!"\'')
                   for chunk in chunks if len(chunk) > 3 and chunk.isalpha())
    del lines, chunks

    zlog.debug(f"Текст для хеширования:\n"
               f"{text}")

    return text


def wdog_news_run(args: CallbackContext) -> None:
    """
    Функция Отправляет сообщения в случае обнаружения
    обновления содержимого на отслеживаемых сайтах.

    :param args: аргументы передаваемые в функцию.
    :return:
    """

    # удаляем текущее меню
    update = args.job.context.get(etag.update)
    context = args.job.context.get(etag.context)

    def check_url_update(url: str) -> (bool, datetime):
        """
        Функция проверяет по хешу изменилось
        ли содержимое страницы по ссылке

        :param url: ссылка проверяемой страницы (должна находиться).
        :return:
        """
        # проверяем дату обновления в заголовке сайта
        now_date_update = get_site_date_update(url=url)
        if now_date_update:
            # получаем предыдущие данные о ссылке записанные в файл
            site = get_data_page(link=url)
            if site:
                # prev_date_update = datetime.strptime(site[etag.update_date], WDOG_SAVE_FORMAT)
                # получаем содержимое страницы
                page_text = get_site_content_for_hash(url=url)
                # получаем хеш страницы
                now_hash = get_hash(text=page_text)
                # если дата обновления страницы больше, чем ранее записанная дата
                # или хеши не равны между собой, то страница подверглась изменениям
                # result = True if now_date_update > prev_date_update or now_hash != site[etag.last_hash] else False
                result = False if now_hash == site[etag.last_hash] else True
            else:
                # если данные были не получены из файла
                zlog.warning('Данные были не получены из файла.')
                result = False
        else:
            # если данные были не получены из файла
            zlog.warning('Ошибка при получении даты обновления из заголовка сайта.')
            result, now_date_update = False, None

        return result, now_date_update

    # производим запрос на наличие обновлений
    site_link = context.user_data.get(etag.site_link)
    zlog.info(f"<< Запуск функции проверки обновления сайта {site_link} >>")

    # проверяем обновлялся ли сайт
    has_updated, date_updated = check_url_update(url=site_link)
    if has_updated:
        # try:
        #     # удаляем предыдущее плавающее меню, если есть ошибки
        #     # на них прежде всего необходимо обратить внимание, поэтому и удаляем меню
        #     # если нужно будет его вызвать - пользователь это может сделать через меню
        #     update.callback_query.delete_message()
        #     zlog.info(f"Удалили предыдущее меню")
        # except BadRequest:
        #     pass

        zlog.info(f"Обнаружено обновление данных по ссылке {site_link}")
        date_updated_str = date_updated.strftime(UPDATE_DATE_FORMAT)
        mess = f"{bs}Страница была обновлена{be}\n" \
               f"{date_updated_str}\n" \
               f"{LINE}" \
               f"{site_link}\n" \
               f"{LINE}"

        keyboard = [
            [InlineKeyboardButton(text="Перейти на сайт", url=site_link)],
            [
                InlineKeyboardButton(text="Закрыть", callback_data=CALLBACK_TO_CLOSE_MENU)
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # получаем id текущего чата
        chat_id = update.effective_chat.id
        context.bot.send_message(text=mess, chat_id=chat_id, reply_markup=reply_markup)

        # обновляем данные об изменениях в файле
        mess = save_link_data(name=context.user_data[etag.link_name],
                              link=site_link, period=context.user_data[etag.period],
                              state=context.user_data[etag.state])
        alert(mess=mess, update=update, context=context,
              in_cmd_line=True, delay_time=WDOGS_DELAY_BEFORE_DELETE)

    return None
