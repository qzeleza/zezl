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
from typing import Callable

from telegram import Update
from telegram.ext import CallbackContext

# from libraries.main.dialog import get_value
from libraries.main.dialog import get_value
from libraries.main.tools import (
    period_to_sec, period_to_eng
)
from libraries.watchdogs.errors import wdog_system_errors_alert_run
from libraries.watchdogs.news import get_page_data_list, wdog_news_run
from logs.logger import zlog
from setup.description import etag

ALREADY_RUN = False


def run_wdogs_at_start(func):
    """
    Декоратор для функций которые можно вызвать из меню в телеграме.
    Служит для того, чтобы можно было при запуске любой из этих команд
    запустить всех сторожей при старте диалога, так как диалог можно начать из любого из них.

    :param func:
    :return:
    """
    def wrapper(*args, **kwargs):
        """
        Функциональный внутренний декоратор

        :param args:
        :param kwargs:
        :return:
        """
        def try_to_get(argument: dict, key: str) -> dict:
            """
            Функция пытается получить аргумент в словаре, если его нет, то
            возвращает пустой словарь.

            :param argument:
            :param key:
            :return:
            """
            var = {}
            try:
                # получаем данные
                var = getattr(argument, key)
                var = argument
            except AttributeError:
                pass
            return var

        def run_background_wdogs(update, context):
            global ALREADY_RUN
            wdogs_all_run_at_start(update=update, context=context)
            ALREADY_RUN = True
            del update, context

        global ALREADY_RUN
        update, context = {}, {}
        #  проверяем на доступность kwargs
        if kwargs:
            # в случае наличия словаря с аргументами
            if not ALREADY_RUN:
                update = kwargs[etag.update]
                context = kwargs[etag.context]
                run_background_wdogs(update, context)

        elif args:
            # проходимся по списку аргументов и ищем элемент,
            # который содержит словарь user_data
            if not ALREADY_RUN:
                for arg in args:
                    # получаем данные о текущей сессии телеграма.
                    update = update if update else try_to_get(arg, 'CALLBACK_QUERY')
                    context = context if context else try_to_get(arg, etag.user_data)
                run_background_wdogs(update, context)

        return_value = func(*args, **kwargs)
        return return_value

    return wrapper


def wdogs_job_start(func_to_run: Callable, interval: str, update: Update, context: CallbackContext) -> None:
    """
    Функция ставит в очередь на исполнение

    :param func_to_run: функция которую необходимо запустить
    :param interval: интервал с каким ее необходимо запустить
    :param update:
    :param context:
    :return:
    """
    # задаем имя для текущей работы: <имя_функции_для_запуска_задания>_<id чата>
    func_name = func_to_run.__name__
    job_name = f"{func_name}_{update.effective_chat.id}"
    # проверяем предыдущие ранее запущенные задания и в случае их наличия удаляем
    job_removed = wdogs_job_stop(func_name, context)
    # в аргументы функции передаем два значения
    func_to_run_args = dict(update=update, context=context)

    if job_removed:
        # если задания были в очереди, то сообщаем, что они остановлены
        mess = f"Сторож '{job_name}' остановлен!"
        zlog.debug(mess)
        # delay_time_min = period_to_sec(context.user_data[etag.error_interval])
        # alert(text=mess, update=update, context=context, delay_time=delay_time_min, in_cmd_line=True)

    # записываем в переменную имя задания, чтобы его можно было получить в любом месте бота
    try:
        getattr(context.user_data, func_name)
        context.user_data[func_name].append(job_name)
    except AttributeError:
        context.user_data.update({func_name: [job_name]})
    # переводим интервал сначала в английскую кодировку, а затем в секунды
    interval_sec = period_to_sec(period_to_eng(interval))
    # запускаем задание в фоне с периодом interval_sec и без пауз, сразу: first=0
    context.job_queue.run_repeating(callback=func_to_run,
                                    interval=interval_sec,
                                    context=func_to_run_args,
                                    first=0,
                                    name=job_name)
    return None


def wdogs_job_stop(job_name_value: str, context: CallbackContext) -> bool:
    """
        Функция удаляет из очереди задания
        по отслеживанию системных ошибок

        :param job_name_value: название переменной в которой хранится имя работы
        :param context:
        :return:
        """
    # получаем имя работы
    jobs_list = context.user_data.get(job_name_value)
    # возвращаем в случае успеха Правду
    res = True
    # проверяем удалось ли получить имя задания
    if jobs_list:
        for job in jobs_list:
            # если имя задания успешно получено, тогда получаем список работ (их ID)
            current_jobs = context.job_queue.get_jobs_by_name(job)
            if not current_jobs:
                # если список ID заданий не получен, то возвращаем ложь
                res = False
                zlog.warning(f"Список заданий для сторожа '{job}' пуст!")
            else:
                # если список заданий получен, то последовательно удаляем все задания
                for jb in current_jobs:
                    jb.schedule_removal()
    else:
        zlog.warning(f"Задачи для '{job_name_value}' отсутствуют, получить список заданий не удалось!")
        res = False

    return res


def wdogs_errors_run_at_start(update: Update, context: CallbackContext) -> None:
    """
    Функция проверяет данные из файла конфигурации и производит
    при старте системы запуск задания по поиску системных ошибок в фоне.

    :return:
    """
    interval = get_value(name=etag.error_interval, default=3, context=context)
    wdogs_job_start(func_to_run=wdog_system_errors_alert_run, interval=interval, update=update, context=context)


def wdogs_news_run_at_start(update: Update, context: CallbackContext) -> None:
    """
    Функция проверяет данные из файла конфигурации и производит
    при старте системы запуск задания по поиску обновлений сайтов в фоне.

    :return:
    """
    data_dict = get_page_data_list()
    for link in data_dict:
        interval = link[etag.period]
        wdogs_job_start(func_to_run=wdog_news_run, interval=interval, update=update, context=context)


def wdogs_all_run_at_start(update: Update, context: CallbackContext) -> None:
    """
    Функция производит первоначальный запуск всех
    заданий сторожей при старте системы в фоне.

    :return:
    """
    wdogs_errors_run_at_start(update, context)
    wdogs_news_run_at_start(update, context)
