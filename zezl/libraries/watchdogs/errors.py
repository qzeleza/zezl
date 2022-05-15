#!/bin/python3
# coding=utf-8

#
#  Copyright (c) 2022.
#
#  Автор: mail@zeleza 04.2022
#  Вся сила в правде!
#

# Автор: master
# Email: info@zeleza.ru
# Дата создания: 30.04.2022 14:11
# Пакет: PyCharm

"""
Описание файла:
    
"""
import json
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.error import BadRequest
from telegram.ext import CallbackContext

from libraries.main.dialog import get_value
from libraries.main.tools import (
    run as bash, get_digits, has_inside, clean_me, check_file, mkfile
)
from logs.logger import zlog
from setup.autosets import ERRORS_ONLY, ERROR_TAGS, CALLBACK_TO_CLOSE_MENU, SEND_TO_IGNORE_LIST
from setup.data import etag, LINE, CMD_GET_SYSLOG, ROUTER_LOG_DATE_FORMAT, ERR_FILE, MAX_RECORDS_IN_ERR_FILE
from setup.description import ErrorTags, be, bs, SearchEngines, cds, cde
from setup.menu import engineList


def system_log_background_stop(retry_action: int = 3) -> bool:
    """
    Функция останавливает логирование в фоне на роутере

    :param: retry_action - число неудачных попыток остановки процесса (по умолчанию 3).
    :return: None
    """
    cmd = f"curl -X DELETE {CMD_GET_SYSLOG}"
    # это результат возврата в случае полной остановки процесса
    null_result, i = '{\n}', 1
    while True:
        if i <= retry_action:
            # вызываем команду остановки
            is_ok, out = bash(command=cmd)
            # в случае, если команда исполнена верно и результат нулевой...
            if is_ok and out == null_result:
                # то выходим из цикла остановки процесса
                zlog.debug('Процесс запроса системных событий роутера остановлен!')
                ret = True
                break
        else:
            zlog.debug(
                    f'Процесс остановки системных событий роутера превысил допустимое число попыток ({retry_action}).')
            ret = False
            break
        i += 1

    return ret


def get_system_log_errors(errors_type: int = ERROR_TAGS, interval_sec: int = 3) -> list[int, str, str]:
    """
    Функция получает порцию сообщений об ошибках в зависимости от интервала опроса

    :param errors_type: типы поиска ошибок в системном логе
                         ERRORS_ONLY - ищем только ошибки
                         ERROR_TAGS - ищем признаки ошибок.
    :param interval_sec: интервал опроса сторожем системного лога, здесь
                         максимальной число строк в возвращаемом запросе приравнивается к интервалу в секундах
                         т.е. число записей в логе равно интервалу опроса в секундах.
    :return: список ошибок в виде (номер_ошибки, дата_ошибки, сообщение_об_ошибке) или [] при отсутствии ошибок или ошибки вывода
    """
    cmd = f"curl -s '{CMD_GET_SYSLOG}'"
    # значение вывода в случае успешного запуска в фоне
    result_ok = '"continued": true'

    def get_sys_error_list(command: str, errors_type_: int = ERROR_TAGS, ) -> list[int, str, str]:
        """

        :param command:
        :param errors_type_:
        :return:
        """

        def check_inside(list_tags: list, mess_dict: dict) -> bool:
            """

            :param list_tags:
            :param mess_dict:
            :return:
            """
            if errors_type_ == ERRORS_ONLY:
                _result = etag.error in mess_dict[etag.level]
            elif errors_type_ == ERROR_TAGS:
                _result = has_inside(list_tags, mess_dict[etag.message])
            else:
                raise Exception("ОШИБКА в коде: используется неизвестный тип переменной в system_log_background_start")
            return _result

        # вызываем команду запуска процесса запроса системных событий роутера
        is_ok, out = bash(command=command)
        if is_ok:
            if result_ok in out:
                # преобразуем json в словарь
                all_in_dict = json.loads(out)
                if all_in_dict.get(etag.log):
                    # фильтруем результат на наличие ошибок
                    res = [(int(n), mess[etag.timestamp], f"{clean_me(mess[etag.ident], digits_rm=True)} "
                                                             f"{mess[etag.message][etag.message]}")
                           for n, mess in all_in_dict[etag.log].items()
                           if check_inside(ErrorTags, mess[etag.message])]
                else:
                    res = []
            else:
                # формируем строку запроса - за запуск в фоне отвечает параметр "once": false
                command = f'curl -s -d \'{{"once": false, "max-lines": {interval_sec * 2}}}\' \'{CMD_GET_SYSLOG}\''
                # останавливаем предыдущие запросы логирования
                system_log_background_stop()
                # делаем запрос на получения результата
                zlog.info("Производим запуск в фоне отслеживания ошибок в системном журнале роутера.")
                res = get_sys_error_list(command, errors_type)
        else:
            zlog.error("Произошла ошибка при запуске в фоне процесса получения системного журнала!")
            res = []

        return res

    result = get_sys_error_list(cmd, errors_type)
    save_errors_to_file(result)

    return result


def wdog_system_errors_alert_run(args: CallbackContext) -> None:
    """
    Функция Отправляет сообщения в случае обнаружения системных ошибок в роутере.

    :param args:
    :return:
    """
    zlog.info("<< Запуск функции проверки системных ошибок >>")
    # удаляем текущее меню
    update = args.job.context.get(etag.update)
    context = args.job.context.get(etag.context)
    # если заданы типы отслеживаемых ошибок и интервал опроса, то...
    error_type_watch = get_value(name=etag.error_type, default=ERROR_TAGS, context=context)
    error_interval_watch = get_value(name=etag.error_interval, default=3, context=context)
    error_engine = get_value(name=etag.error_engine, default=SearchEngines.yandex, context=context)
    # производим запрос на наличие ошибок
    errors = get_system_log_errors(errors_type=error_type_watch, interval_sec=get_digits(error_interval_watch))
    # проверяем - есть ли ошибки в потоке данных
    if errors:
        # try:
        #     # удаляем предыдущее плавающее меню, если есть ошибки
        #     # на них прежде всего необходимо обратить внимание, поэтому и удаляем меню
        #     # если нужно будет его вызвать - пользователь это может сделать через меню
        #     if update.callback_query:
        #         update.callback_query.delete_message()
        # except BadRequest:
        #     pass
        zlog.info("Обнаружена ошибка в журнале роутера!")

        def error_alert_show():
            """
            Функция отображает сообщение об ошибке
            """
            request = ''.join([s[error_engine] for s in engineList if s.get(error_engine)])
            link = f"{request}=opkg+{mess.replace(' ', '+')}"
            # переформатируем дату в свой формат 22 Мая 2022 12:22:44
            long_date_format = "%d %B %Y %H:%M:%S %Z"
            try:
                dt = datetime.strptime(date, ROUTER_LOG_DATE_FORMAT).strftime(long_date_format)
            except ValueError:
                dt = datetime.strptime(date, "%b %d %H:%M:%S").strftime("%d %B %H:%M:%S")

            request = f"{bs}СИСТЕМНАЯ ОШИБКА № {num}{be} от {bs}{dt}{be}\n" \
                      f"{LINE}" \
                      f"{cds}{mess}{cde}"
            # f"<a href='{link}'>{mess}</a>"

            # получаем id текущего чата
            chat_id = update.effective_chat.id
            # если установлен флаг вывода в командную строку,
            # то публикуем сообщение именно в этом режиме
            callback_data = f'{SEND_TO_IGNORE_LIST}_{num}'
            # Три кнопки для отображения вместе с сообщением об ошибке.
            # Одна кнопка в первом ряду и две во втором ряду.
            keyboard = [
                [InlineKeyboardButton(text="Информация об ошибке", url=link)],
                [
                    InlineKeyboardButton(text="Игнорировать", callback_data=callback_data),
                    InlineKeyboardButton(text="Закрыть", callback_data=CALLBACK_TO_CLOSE_MENU)
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(text=request, chat_id=chat_id, reply_markup=reply_markup)

        for num, date, mess in errors:
            if context.user_data.get(etag.err_ignore_list) is None:
                error_alert_show()
            else:
                if mess not in context.user_data[etag.err_ignore_list]:
                    error_alert_show()

    return None


def save_errors_to_file(errors_list: list[int, str, str]) -> bool:
    """
    Функция записывает ошибки в файл системных ошибок - ERR_FILE

    :param errors_list: список ошибок [(номер, дата, сообщение)]
    :return: True - записано, False - не записано
    """
    result = False
    if errors_list:
        if not check_file(file=ERR_FILE):
            mkfile(file=ERR_FILE)
        # Вычисляем сколько должно быть максимум строк в файле ошибок
        max_lines = MAX_RECORDS_IN_ERR_FILE - len(errors_list)
        tmp_file = '/opt/tmp/tmp_b533'
        # готовим команду для обрезки файла до заданного числа строк
        cdm_tail = f'cat < {ERR_FILE} | tail -{max_lines} > {tmp_file} && mv {tmp_file} {ERR_FILE}'
        # готовим данные для записи - форматируем их соответствующим образом
        data_to_save = "\n".join([f'{n}{etag.divo}{d}{etag.divo}{m}' for n, d, m in errors_list])
        # готовим полную команду для исполнения.
        cmd = f'{cdm_tail} && echo "{data_to_save}" >> {ERR_FILE}'
        # вызываем команду запуска процесса запроса системных событий роутера
        is_ok, out = bash(command=cmd)
        result = True if is_ok else False
    return result


def get_errors_from_file(err_number: str) -> list[str, str, str]:
    """
    Функция получает ошибки/у из файла системных ошибок - ERR_FILE

    :param err_number: номер ошибки в журнале роутера.
    :return: список ошибок [(номер, дата, сообщение)]
    """
    result = []
    cmd = f"cat < {ERR_FILE} | grep {err_number}" if err_number else f"cat < {ERR_FILE}"
    # вызываем команду запуска процесса запроса системных событий роутера
    is_ok, out = bash(command=cmd)
    if is_ok:
        out = out.splitlines()
        result = [(line.split(etag.divo)) for line in out if line]

    return result
