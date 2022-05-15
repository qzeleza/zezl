# coding=utf-8
from datetime import datetime
from typing import Callable

from telegram import Update
from telegram.ext import CallbackContext

import libraries.main.config as cfg
import setup.autosets as st
from libraries.main.decorators import set_menu_level
from libraries.main.dialog import get_value, show_list_core, alert, dialog_to_accept, run_background
from libraries.main.tools import check_url, period_to_eng
from libraries.watchdogs.errors import (
    wdog_system_errors_alert_run,
)
from libraries.watchdogs.jobs import (
    wdogs_job_start,
    wdogs_job_stop, run_wdogs_at_start,
)
from libraries.watchdogs.news import get_page_data_list, save_link_data, remove_all_links_from_file, get_data_page, \
    wdog_news_run, remove_link_from_file, update_link_data
from libraries.main.dialog import exit_from_text_mode
from setup.data import LINE, WDOG_SAVE_FORMAT, UPDATE_DATE_FORMAT
from setup.description import (etag, rtag, icon, SearchEngines, bs, be)
from setup.menu import Menu


class WatchdogsMenuAction:
    """
    Класс предназначен для генерации и
    обработки действий страниц меню "Сторожа"

    """

    def __init__(self):
        self.message_id = -1

    # --------------------------------------------------------------------------------------------------
    #
    #       Уровень Меню Сторожей
    #
    # --------------------------------------------------------------------------------------------------
    @run_wdogs_at_start
    @set_menu_level(menu_level=st.WD_MAIN_MENU_LEVEL)
    def wdogs_menu_show(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает "плавающее" (inline) меню Сторожей

        :param update:
        :param context:

        :return: код уровня вложенности меню
        """
        callback, self.message_id = show_list_core(message_id=self.message_id,
                                                   reply_text=Menu.WatchdogsMenu.TitleList,
                                                   list_content=[],
                                                   cmd_buttons=Menu.WatchdogsMenu.Items,
                                                   back_buttons=Menu.WatchdogsMenu.BackButtons,
                                                   menu_level=st.WD_MAIN_MENU_LEVEL,
                                                   update=update, context=context)
        return callback

    # --------------------------------------------------------------------------------------------------
    #
    #   Генерация и обработка страниц СТОРОЖА обработки системных ошибок
    #
    # --------------------------------------------------------------------------------------------------
    @set_menu_level(menu_level=st.WD_ERRORS_LEVEL)
    def sys_errors_show(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает станицу с кнопками для сторожа обработки системных ошибок

        :param update:
        :param context:
        :return:
        """

        # базовый класс для сокращения кода
        base_class = Menu.WatchdogsMenu.ErrorsMenu

        # Проверяем активирован ли режим опроса системных ошибок
        mode = context.user_data.get(etag.error_state).lower() == etag.true
        # при запуске, по умолчанию, он всегда включен
        fstate = cfg.get_config_value(name=etag.error_state).lower() == etag.true
        mode = fstate if fstate else True if mode is None else mode
        # Проверяем установлен ли интервал таймера проверки опроса системных ошибок
        interval = get_value(etag.error_interval, 3, context)
        # Получаем поисковую машину для генерации строки поиска ошибки
        engine = get_value(etag.error_engine, SearchEngines.yandex, context)
        # переключаемся только в случае смены режимов
        if mode != fstate:
            # переключаем режим в зависимости от записанного значения в файле или переменной
            self.sys_errors_state_toggle(state=mode, interval=interval, update=update, context=context)

        # формируем заголовок страницы
        state = rtag.StatusOn if mode else rtag.StatusOff
        title = base_class.TitleList.replace('@1', state).replace('@2', str(interval)).replace('@3', engine)

        # кнопка активации режима
        activation_button = {f"{icon.unselect} {rtag.ActivationOff} ": st.WD_ERR_ACTIVATION} \
            if mode else {f"{icon.select} {rtag.ActivationOn} ": st.WD_ERR_ACTIVATION}
        # Добавляем снизу кнопку активации режима отслеживания системных ошибок
        cmd_buttons = [[activation_button]] + base_class.CmdItems
        # отрисовываем страницу
        callback, self.message_id = show_list_core(message_id=self.message_id,
                                                   reply_text=title,
                                                   list_content=[],
                                                   cmd_buttons=cmd_buttons,
                                                   back_buttons=base_class.BackButtons,
                                                   menu_level=st.WD_ERRORS_LEVEL,
                                                   update=update, context=context)
        return callback

    @staticmethod
    def sys_errors_state_toggle(state: bool, interval: str, update: Update, context: CallbackContext) -> None:
        """
        СЛУЖЕБНАЯ Функция переключает режим отслеживания системных ошибок
        Включает и отключает запуск в фоне сторожа отслеживания ошибок

        :param state:
        :param interval:
        :param update:
        :param context:
        :return:
        """
        # проверяем режим запуска сторожа
        if state:
            # сторож запущен
            wdogs_job_start(func_to_run=wdog_system_errors_alert_run, interval=interval, update=update, context=context)
        else:
            # статус сменился на "сторож остановлен" - останавливаем сторожа
            # имя задания является название вызываемой функции на исполнения задания
            wdogs_job_stop(job_name_value=wdog_system_errors_alert_run.__name__, context=context)

        return None

    # --------------------------------------------------------------------------------------------------
    #   Обработка нажатия на кнопку смены режима ВКЛ/ОТКЛ
    # --------------------------------------------------------------------------------------------------
    def sys_errors_state_press_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция обработки смены режима сторожа отлавливания системных ошибок

        :param update:
        :param context:
        :return:
        """
        # меняем значение флага на противоположное значение
        try:
            _ = context.user_data[etag.error_state]
            context.user_data[etag.error_state] = not context.user_data[etag.error_state]
        except KeyError:
            context.user_data[etag.error_state] = True

        # записываем текущий режим в файл
        cfg.set_config_value(name=etag.error_state, value=context.user_data[etag.error_state])
        self.sys_errors_state_toggle(state=context.user_data[etag.error_state],
                                     interval=context.user_data[etag.error_interval],
                                     update=update, context=context)
        # отрисовываем измененное значение на странице
        return self.sys_errors_show(update, context)

    # --------------------------------------------------------------------------------------------------
    #   СЛУЖЕБНЫЕ функции
    # --------------------------------------------------------------------------------------------------
    def _mark_list_and_show(self, tag: str, value_default: str,
                            base_class: object, menu_level: int,
                            update: Update, context: CallbackContext) -> int:
        """
        Функция СЛУЖЕБНАЯ, применяется при вызове построения страницы с существующим списком,
        где есть необходимость маркировать этот список значением по умолчанию

        :param tag:
        :param value_default:
        :param base_class:
        :param menu_level:
        :param update:
        :param context:
        :return:
        """
        # записываем значение в память
        context.user_data[tag] = value_default
        # помечаем иконкой значение по умолчанию в списке поисковых машин
        list_content = [{f"{icon.select if ''.join(di.keys()) == value_default else ''} {''.join(di.keys())}":
                             ''.join(di.values())} for di in base_class.ItemsList]

        # отрисовываем страницу
        callback, self.message_id = show_list_core(message_id=self.message_id,
                                                   reply_text=base_class.Title,
                                                   list_content=list_content,
                                                   cmd_buttons=[],
                                                   back_buttons=base_class.BackButtons,
                                                   menu_level=menu_level,
                                                   content_list_in_row=2,
                                                   update=update, context=context)
        return callback

    @staticmethod
    def _save_chosen_item_callback(button_list: list, tag: str, callback_func: Callable,
                                   update: Update, context: CallbackContext) -> int:
        """
        Функция сохраняет выбранное значение из списка данных

        :param button_list: список кнопок
        :param tag: метка данных
        :param callback_func: функция для последующего вызова после основного блока задач
        :param update:
        :param context:
        :return:
        """
        # получаем выбранную поисковую машину
        chosen_val = update.callback_query.data
        chosen_key = "".join(
            [''.join(k.keys()) for k in button_list if ''.join(k.values()) == chosen_val])
        # записываем значение в файл конфигурации
        cfg.set_config_value(name=tag, value=chosen_key)
        # записываем значение в память
        context.user_data[tag] = chosen_key
        # возвращаемся на страницу выбора поисковой машины
        return callback_func(update, context)

    # --------------------------------------------------------------------------------------------------
    #   Отрисовка страницы выбора поисковой машины
    # --------------------------------------------------------------------------------------------------
    @set_menu_level(menu_level=st.WD_ERR_SEARCH_ENGINES_LEVEL)
    def sys_errors_engine_choose_request(self, update: Update, context: CallbackContext) -> int:
        """
        Функция показывает страницу выбора поисковой машины для поиска системных ошибок в логе

        :param update:
        :param context:
        :return:
        """
        base_class = Menu.WatchdogsMenu.ErrorsMenu.EngineSearchMenu
        # получаем текущую поисковую машину по умолчанию
        default_engine = get_value(etag.error_engine, SearchEngines.yandex, context)
        # записываем значение в память
        return self._mark_list_and_show(tag=etag.error_engine,
                                        value_default=default_engine,
                                        base_class=base_class,
                                        menu_level=st.WD_ERR_SEARCH_ENGINES_LEVEL,
                                        update=update, context=context)

    # --------------------------------------------------------------------------------------------------
    #   Записываем выбранную поисковую машину в файл конфигурации
    # --------------------------------------------------------------------------------------------------
    def sys_errors_engine_choose_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция записывает выбранную поисковую машину в файл конфигурации

        :param update:
        :param context:
        :return:
        """
        engine_list = Menu.WatchdogsMenu.ErrorsMenu.EngineSearchMenu.ItemsList
        return self._save_chosen_item_callback(button_list=engine_list,
                                               tag=etag.error_engine,
                                               callback_func=self.sys_errors_show,
                                               update=update, context=context)

    # --------------------------------------------------------------------------------------------------
    #   Отрисовка страницы выбора интервала опроса системных ошибок
    # --------------------------------------------------------------------------------------------------
    @set_menu_level(menu_level=st.WD_ERR_INTERVAL_LEVEL)
    def sys_errors_interval_choose_request(self, update: Update, context: CallbackContext) -> int:
        """
        Функция показывает страницу выбора интервала опроса журнала системных ошибок в логе

        :param update:
        :param context:
        :return:
        """
        base_class = Menu.WatchdogsMenu.ErrorsMenu.IntervalMenu
        # получаем текущее значение интервала опроса по умолчанию
        default_interval = get_value(etag.error_interval, '3 сек.', context)
        # записываем значение в память
        return self._mark_list_and_show(tag=etag.error_interval,
                                        value_default=default_interval,
                                        base_class=base_class,
                                        menu_level=st.WD_ERR_INTERVAL_LEVEL,
                                        update=update, context=context)

    # --------------------------------------------------------------------------------------------------
    #   Записываем выбранную поисковую машину в файл конфигурации
    # --------------------------------------------------------------------------------------------------
    def sys_errors_interval_choose_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция записывает выбранную поисковую машину в файл конфигурации

        :param update:
        :param context:
        :return:
        """
        interval_list = Menu.WatchdogsMenu.ErrorsMenu.IntervalMenu.ItemsList
        return self._save_chosen_item_callback(button_list=interval_list,
                                               tag=etag.error_interval,
                                               callback_func=self.sys_errors_show,
                                               update=update, context=context)

    # --------------------------------------------------------------------------------------------------
    #
    #   Генерация и обработка страниц СТОРОЖА отслеживания сайтов
    #
    # --------------------------------------------------------------------------------------------------
    @set_menu_level(menu_level=st.WD_SITES_WATCH_LEVEL)
    def news_show(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает страницу доменных имен для
        отслеживания изменения содержимого страниц со ссылками

        :param update:
        :param context:
        :return:
        """
        # обозначаем базовый класс
        base_class = Menu.WatchdogsMenu.SitesMenu
        # получаем список доступных ссылок
        site_list = get_page_data_list()
        # проверяем на их наличие
        if site_list:
            # Если ссылки имеются в файле ссылок
            # получаем число ссылок
            links_count = len(site_list)
            list_content = []
            # генерируем список кнопок со ссылками.
            for site in site_list:
                name_butt = f"{icon.select if site[etag.state] else icon.unselect} [{site[etag.period]}] {site[etag.link_name]}"
                list_content.append({name_butt: site[etag.link]})
            # сортируем данные в отображаемом списке элементов списке
            list_content = sorted(list_content, key=lambda d: list(d.values())[0])
            del site_list, name_butt
            # генерируем заголовок
            title = base_class.Title.replace('@1', str(links_count))
            cmd_list = base_class.CmdItems
        else:
            # Если список доменов пуст
            list_content = []
            title = base_class.TitleNoItems
            cmd_list = base_class.CmdNoItems
        # отрисовываем страницу
        callback, self.message_id = show_list_core(message_id=self.message_id,
                                                   reply_text=title,
                                                   list_content=list_content,
                                                   cmd_buttons=cmd_list,
                                                   back_buttons=base_class.BackButtons,
                                                   menu_level=st.WD_SITES_WATCH_LEVEL,
                                                   update=update, context=context)
        return callback

    # --------------------------------------------------------------------------------------------------
    #   Делаем запрос на добавление ссылки
    # --------------------------------------------------------------------------------------------------
    # @set_menu_level(menu_level=st.WD_SITES_WATCH_LEVEL)
    @staticmethod
    def news_add_name_link_action_and_request(update: Update, _: CallbackContext) -> int:
        """
            Функция отображает запрос о вводе новых ссылок через строку ввода

            :param update:
            :param _:
            :return:
            """
        # запрос на добавление домена
        reply_text = Menu.WatchdogsMenu.SitesMenu.AddLinkMenu.AddNameRequestText

        # удаляем предыдущее сообщение
        update.callback_query.delete_message()
        update.callback_query.answer()
        # ожидаем ввода
        update.callback_query.message.reply_text(reply_text)

        # фиксируем и возвращаем текущий уровень меню
        return st.WD_SITES_WATCH_LEVEL

    # --------------------------------------------------------------------------------------------------
    #   Добавляем название ссылки
    # --------------------------------------------------------------------------------------------------
    # @set_menu_level(menu_level=st.WD_SITES_ADD_LEVEL)

    def news_add_link_request(self, update: Update, context: CallbackContext) -> int:
        """
        Функция добавляет название последующей ссылки
        :param update:
        :param context:
        """
        #  если ввели слова по выходу из режима ввода
        callback = exit_from_text_mode(update.message.text, self.news_show, update, context)
        if callback:
            return callback

        context.user_data[etag.link_name] = update.message.text.capitalize()
        # запрос на добавление домена
        reply_text = Menu.WatchdogsMenu.SitesMenu.AddLinkMenu.AddLinkRequestText
        # update.callback_query.answer()
        # ожидаем ввода
        update.message.reply_text(reply_text)
        # фиксируем и возвращаем текущий уровень меню
        return st.WD_SITES_ADD_LEVEL

    # --------------------------------------------------------------------------------------------------
    #   Добавляем ссылку в файл
    # --------------------------------------------------------------------------------------------------
    def news_add_new_link_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция реализует добавление данных в файл отслеживания ссылок

        :param update:
        :param context:
        :return:
        """
        #  если ввели слова по выходу из режима ввода
        callback = exit_from_text_mode(update.message.text, self.news_show, update, context)
        if callback:
            return callback

        entered_text = update.message.text.lower()
        link = check_url(entered_text)
        if link:
            # если период не задан, то получаем устанавливаем его по умолчанию
            period = get_value(name=etag.site_interval, default='1d', context=context)
            period = period_to_eng(period)
            func_start_args = dict(name=context.user_data[etag.link_name], link=link, period=period)
            del context.user_data[etag.link_name]
            # запускаем сохранение
            result = run_background(func_start=save_link_data,
                                    func_start_args=func_start_args,
                                    func_finish=self.news_show,
                                    menu_level=st.WD_SITES_WATCH_LEVEL,
                                    update=update, context=context)
        else:
            answer = f"{bs}Данные введены не верно \n" \
                     f"или ссылка не существует!{be}\n" \
                     "Введите ссылку повторно"
            alert(mess=answer, update=update, context=context, in_cmd_line=True)
            result = st.WD_SITES_WATCH_LEVEL

        return result

    # --------------------------------------------------------------------------------------------------
    #   Делаем запрос на удаление всех ссылок в файле
    # --------------------------------------------------------------------------------------------------
    @staticmethod
    @set_menu_level(menu_level=st.WD_SITES_WATCH_LEVEL)
    def news_del_all_links_request(update: Update, _: CallbackContext) -> int:
        """
        Функция реализует удаление всех ссылок в файле отслеживания ссылок

        :param update:
        :param _:
        :return:
        """
        reply_text = f"Будут удалены все ссылки из файла!\n" \
                     f"Подтвердите удаление."
        buttons = Menu.WatchdogsMenu.SitesMenu.RemoveAllButtons
        dialog_to_accept(reply_text=reply_text, buttons=buttons, update=update)

        return st.WD_SITES_WATCH_LEVEL

    # --------------------------------------------------------------------------------------------------
    #   Удаляем все ссылки из файла
    # --------------------------------------------------------------------------------------------------
    def news_del_all_links_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция реализует удаление всех ссылок в файле отслеживания ссылок

        :param update:
        :param context:
        :return:
        """
        # запускаем удаление
        return run_background(func_start=remove_all_links_from_file,
                              func_finish=self.news_show,
                              menu_level=st.WD_SITES_WATCH_LEVEL,
                              update=update, context=context)

    # --------------------------------------------------------------------------------------------------
    #   Отрисовываем страницу редактирования свойств выбранной ссылки
    # --------------------------------------------------------------------------------------------------
    @set_menu_level(menu_level=st.WD_SITES_EDIT_LINK_LEVEL)
    def news_edit_link_show(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отрисовывает страницу редактирования свойств выбранной ссылки

        :param :
        :return:
        """
        base_class = Menu.WatchdogsMenu.SitesMenu.EditLinkMenu
        # Проверяем активирован ли режим опроса системных ошибок
        state = context.user_data.get(etag.site_state)
        # получаем выбранную ссылку
        chosen_link = update.callback_query.data
        chosen_link = chosen_link if etag.http in chosen_link else context.user_data[etag.site_link]

        site = get_data_page(link=chosen_link)
        # при запуске, по умолчанию, он всегда False
        state = True if state is None else state

        context.user_data[etag.site_state] = site[etag.state]
        context.user_data[etag.site_name] = site[etag.link_name]
        context.user_data[etag.site_interval] = site[etag.period]
        context.user_data[etag.site_link] = chosen_link
        context.user_data[etag.update_date] = site[etag.update_date]
        context.user_data[etag.check_date] = site[etag.check_date]


        interval = context.user_data[etag.site_interval]
        link_name = context.user_data[etag.site_name]
        last_update = datetime.strptime(context.user_data[etag.update_date], WDOG_SAVE_FORMAT)
        last_update = last_update.strftime(UPDATE_DATE_FORMAT)
        last_check = datetime.strptime(context.user_data[etag.check_date], WDOG_SAVE_FORMAT)
        last_check = last_check.strftime(UPDATE_DATE_FORMAT)

        # переключаемся только в случае смены режимов
        if state != cfg.get_config_value(name=etag.site_state):
            # переключаем режим при показе страницы меню
            self.news_state_toggle(state=state, interval=interval, update=update, context=context)
        # заголовок страницы
        state_text = rtag.StatusOn if state else rtag.StatusOff
        title = base_class.Title.replace('@1', link_name).replace('@2', chosen_link)
        title = title.replace('@3', state_text).replace('@4', interval)
        title = title.replace('@5', last_check).replace('@6', last_update)

        # кнопка активации режима
        activation_button = {f"{icon.unselect} {rtag.ActivationOff}": st.WD_SITE_EDIT_LINK_WATCH_ACTIVATION} \
            if state else {f"{icon.select} {rtag.ActivationOn}": st.WD_SITE_EDIT_LINK_WATCH_ACTIVATION}
        cmd_buttons = [[activation_button]] + base_class.CmdItemsList
        # отрисовываем страницу
        callback, self.message_id = show_list_core(message_id=self.message_id,
                                                   reply_text=title,
                                                   list_content=[],
                                                   cmd_buttons=cmd_buttons,
                                                   back_buttons=base_class.BackButtons,
                                                   menu_level=st.WD_SITES_EDIT_LINK_LEVEL,
                                                   update=update, context=context)
        return callback

    @staticmethod
    def news_state_toggle(state: bool, interval: str, update: Update, context: CallbackContext) -> None:
        """
        СЛУЖЕБНАЯ Функция переключает режим отслеживания системных ошибок
        Включает и отключает запуск в фоне сторожа отслеживания ошибок

        :param state:
        :param interval:
        :param update:
        :param context:
        :return:
        """

        # проверяем режим запуска сторожа
        if state:
            # сторож запущен
            wdogs_job_start(func_to_run=wdog_news_run, interval=interval, update=update, context=context)
        else:
            # статус сменился на "сторож остановлен" - останавливаем сторожа
            # имя задания является название вызываемой функции на исполнения задания
            wdogs_job_stop(job_name_value=wdog_news_run.__name__, context=context)

        return None

    # --------------------------------------------------------------------------------------------------
    #   Обработка нажатия на кнопку смены режима ВКЛ/ОТКЛ
    # --------------------------------------------------------------------------------------------------
    def news_state_press_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция обработки смены режима сторожа отлавливания системных ошибок

        :param update:
        :param context:
        :return:
        """
        # меняем значение флага на противоположное значение
        context.user_data[etag.site_state] = not context.user_data[etag.site_state]
        # записываем текущий режим в файл
        cfg.set_config_value(name=etag.site_state, value=context.user_data[etag.site_state])
        self.news_state_toggle(state=context.user_data[etag.site_state],
                               interval=context.user_data[etag.site_interval],
                               update=update, context=context)
        # отрисовываем измененное значение на странице
        return self.news_edit_link_show(update, context)

    # --------------------------------------------------------------------------------------------------
    #   Отрисовка страницы выбора интервала опроса системных ошибок
    # --------------------------------------------------------------------------------------------------
    @set_menu_level(menu_level=st.WD_SITES_EDIT_LINK_LEVEL)
    def news_interval_choose_request(self, update: Update, context: CallbackContext) -> int:
        """
        Функция показывает страницу выбора интервала опроса журнала системных ошибок в логе

        :param update:
        :param context:
        :return:
        """
        base_class = Menu.WatchdogsMenu.SitesMenu.EditLinkMenu.IntervalMenu
        # получаем текущее значение интервала опроса по умолчанию
        default_interval = get_value(etag.site_interval, '1 дн.', context)
        # записываем значение в память
        return self._mark_list_and_show(tag=etag.site_interval,
                                        value_default=default_interval,
                                        base_class=base_class,
                                        menu_level=st.WD_SITES_EDIT_LINK_INTERVAL_LEVEL,
                                        update=update, context=context)

    # --------------------------------------------------------------------------------------------------
    #   Записываем выбранный интервал обновления в файл конфигурации
    # --------------------------------------------------------------------------------------------------
    def news_interval_choose_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция записывает выбранный интервал обновления в файл конфигурации

        :param update:
        :param context:
        :return:
        """
        interval_list = Menu.WatchdogsMenu.SitesMenu.EditLinkMenu.IntervalMenu.ItemsList
        # получаем выбранный интервал обновления
        chosen_val = update.callback_query.data
        chosen_key = "".join(
            [''.join(k.keys()) for k in interval_list if ''.join(k.values()) == chosen_val])
        # записываем значение в файл конфигурации
        state = context.user_data[etag.site_state]
        chosen_link = context.user_data[etag.site_link]
        name = context.user_data[etag.site_name]
        func_start_args = dict(name=name, link=chosen_link, state=state, period=chosen_key)
        # записываем значение в память
        context.user_data[etag.site_interval] = chosen_key
        return run_background(func_start=update_link_data,
                              func_finish=self.news_edit_link_show,
                              menu_level=st.WD_SITES_EDIT_LINK_LEVEL,
                              update=update, context=context,
                              func_start_args=func_start_args)

    # --------------------------------------------------------------------------------------------------
    #   Делаем запрос на удаление всех ссылок в файле
    # --------------------------------------------------------------------------------------------------
    @staticmethod
    @set_menu_level(menu_level=st.WD_SITES_EDIT_LINK_LEVEL)
    def news_del_link_request(update: Update, context: CallbackContext) -> int:
        """
        Функция реализует удаление всех ссылок в файле отслеживания ссылок

        :param update:
        :param context:
        :return:
        """
        chosen_link = context.user_data[etag.site_link]
        reply_text = f"{bs}{chosen_link}{be}\n" \
                     f"{LINE}" \
                     f"{bs}Подтвердите удаление.{be}\n"
        buttons = Menu.WatchdogsMenu.SitesMenu.EditLinkMenu.RemoveLinkButtons
        dialog_to_accept(reply_text=reply_text, buttons=buttons, update=update)
        return st.WD_SITES_EDIT_LINK_LEVEL

    # --------------------------------------------------------------------------------------------------
    #   Удаляем все ссылки из файла
    # --------------------------------------------------------------------------------------------------
    def news_del_link_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция реализует удаление всех ссылок в файле отслеживания ссылок

        :param update:
        :param context:
        :return:
        """
        chosen_link = context.user_data[etag.site_link]
        # запускаем удаление
        return run_background(func_start=remove_link_from_file,
                              func_start_args=dict(link=chosen_link),
                              func_finish=self.news_show,
                              menu_level=st.WD_SITES_WATCH_LEVEL,
                              update=update, context=context)


wdogs = WatchdogsMenuAction()
