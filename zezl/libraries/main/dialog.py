#!/opt/bin/python3
# -*- coding: UTF-8 -*-


#
#  Copyright (c) 2022.
#
#  Автор: mail@zeleza 04.2022
#  Вся сила в правде!
#

from typing import Callable

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    error
)
from telegram.ext import (
    CallbackContext,
)

import libraries.main.config as cfg
from libraries.main import tools as tools
from logs.logger import zlog
from setup.data import (
    DELAY_BEFORE_DELETE,
    LIMIT_RECORDS_FOR_BACKGROUND,
    InRow, etag,
)
from setup.description import ErrorTextMessage as Error


def exit_from_text_mode(text: str, callback_func: Callable, update: Update, context: CallbackContext) -> int | None:
    """
    Функция проверяет на наличие слов-команд exit и quit

    :param text: текст для проверки
    :param callback_func: команду которую необходимо вызвать при наличии слов-команд exit и quit
    :param update:
    :param context:
    :return:
    """
    #  если ввели слова по выходу из режима ввода
    res = None
    if text.lower() in [etag.exit, etag.quit]:
        update.message.delete()
        res = callback_func(update, context)
    return res


def get_value(name: str, default: str | bool | int, context: CallbackContext) -> str | bool:
    """
    Функция последовательно старается получить данные из
    внутреннего словаря, файла конфигурации и если этих
    значений нет, то задает значения по умолчанию

    :param name: имя переменной.
    :param default: значение по умолчанию в случае отсутствия данных.
    :param context:

    :return: полученное значение переменной
    """

    # Проверяем активирован ли режим опроса системных ошибок
    value = context.user_data.get(name)
    if value is None:
        # если режим не установлен - то читаем из файла конфигурации
        value = cfg.get_config_value(name=name)
        if not value:
            # если в файле конфигурации не установлен, то по умолчанию режим ВЫКЛЮЧЕН
            value = default
        # установим внутреннею переменную
        context.user_data[name] = value

    return value


# def get_button_dict(button_names: str | list) -> list:
#     """
#     Функция возвращает динамическую кнопку или кнопки (в виде словаря) с кодом возврата callback
#     Кодом возврата при этом является очищенный от мусора текст на кнопке
#     Пример: [{name: clear_name}] или [{name1: clear_name1}, [{name2: clear_name2}]]
#
#     :param button_names: текст на кнопке
#     :return: кнопки (в виде словаря) с кодом возврата callback
#     """
#     res = []
#     button_names = button_names if isinstance(button_names, list) else [button_names]
#     # если передан список, то проходимся по всем элементам
#     for name in button_names:
#         # Первым идет иконка, далее название и третий элемент это id интерфейса
#         butt_text = name.split()
#         # получаем список отдельных слов в тексте кнопки
#         # и затем ищем название интерфейса в этом списке (оно должно быть одно)
#         index = [n for n, _id in enumerate(butt_text) if libraries.check_inside(INTERFACE_TYPES, _id)][0]
#         res.append({name: butt_text[index]})
#     #  возвращаем результат
#     return res


# def error_log(update: Update, context: CallbackContext) -> None:
#     """
#     Функция оповещения об ошибках при обновлении чата
#
#     :param update:
#     :param context:
#
#     :return: None
#     """
#     # Выводим в консоль сообщение об ошибке
#     if update:
#         button = update.callback_query.data if update.callback_query else update.message.chat_id
#         mess = update.callback_query.message.mess if update.callback_query else update.message.mess
#         zlog.error(f'{Error.INDICATOR} При обновлении данных: \n"{context.error}"\n'
#                    f'Ошибка возникла при нажатии на кнопку: "{button}"\n'
#                    f'Сообщение: "{mess}"')


def list_chunk(elem_list: list, buttons_in_row: int):
    """
    Функция подготавливает вложенный список, из элементов
    согласно заданному числу элементов в ряду, например,
    из списка в один ряд необходимо сделать три ряда numbers_in_row=3
    [{'kn_1':1},{'kn_2':2},{'kn_3':3},{'kn_4':4},{'kn_5':5},{'kn_6':6},{'kn_7':7},{'kn_8':8}]
    вернется список с элементами
    [
        [{'kn_1':1},{'kn_2':2},{'kn_3':3}],
        [{'kn_4':4},{'kn_5':5},{'kn_6':6}],
        [{'kn_7':7},{'kn_8':8}]
    ]
    Так же, можно самостоятельно конфигурировать ряды кнопок,
    которые будут сгенерированы крайними в списке.
    Это возможно в случае, если вместо элемента словаря отправить
    список с элементами в переменной elems_list, например при заданных аргументах
    elems_list = [{'kn_1':1},{'kn_2':2},{'kn_3':3},{'kn_4':4},[{'kn_5':5},{'kn_6':6},{'kn_7':7}],{'kn_8':8}],
    buttons_in_row = 3, функция вернет следующий список:
    [
        [{'kn_1':1},{'kn_2':2},{'kn_3':3}],
        [{'kn_4':4},{'kn_8':8}],
        [{'kn_5':5},{'kn_6':6},{'kn_7':7}]
    ]
    :param elem_list: список элементов для распределения.
    :param buttons_in_row: количество элементов в ряду.

    :return: вложенный список с элементами разделенными по рядно.
    """
    # Вычисляем длину списка
    len_list = len(elem_list)
    for i in range(0, len_list, buttons_in_row):
        yield elem_list[i:i + buttons_in_row]


def make_inline_keyboard(chunk_list: list) -> InlineKeyboardMarkup:
    """
    Функция подготавливает элементы плавающей клавиатуры.

    :param chunk_list: вложенный список элементов, как пример [[1,2,3], [4,5,6], [7,8]]
    :return: сформированная плавающей клавиатура
    """

    keyboard = []

    def create_inline_keyboard(source_row: list[list | dict] | dict) -> list[InlineKeyboardButton]:
        row_list = []
        is_dict = isinstance(source_row, dict)
        for elem in source_row:
            # идем по каждому ряду кнопок
            if is_dict and isinstance(elem, str):
                # в случае, если элемент единственный
                # в ряду - обрабатываем соответственно
                name = elem
                callback = source_row[name]
            else:
                # если в ряду несколько словарей с кнопками
                name = "".join(elem[0].keys()) if isinstance(elem, list) else list(elem)[0]
                callback = "".join(elem[0].values()) if isinstance(elem, list) else elem[name]
            # добавляем очередной ряд в клавиатуру
            row_list.append(InlineKeyboardButton(text=name, callback_data=callback))
        return row_list

    # проходимся по списку рядов ранее сформированных плавающих кнопок
    for row in chunk_list:
        # копируем источник, чтобы не менять его
        row_copy = row[:]
        # находим под ряды внутри (или элементы состоящие из списков)
        sub_row_inside = [row_copy.pop(ind) for ind, sub in enumerate(row_copy) if isinstance(sub, list)]
        if sub_row_inside:
            # еси внутри есть подряд, то добавляем его как отдельный ряд
            for sub_row in sub_row_inside:
                keyboard.append(create_inline_keyboard(sub_row))
        keyboard.append(create_inline_keyboard(row_copy))

    return InlineKeyboardMarkup(keyboard)


def delete_messages(number: int, update: Update, context: CallbackContext) -> None:
    """
    Функция удаляет одно или несколько предыдущих сообщений бота по порядку следования

    :param number: количество удаляемых предыдущих сообщений бота
    :param update:
    :param context:
    :return:
    """
    message = update.callback_query.message if update.callback_query else update.message
    chat_id = message.chat_id
    for mess_count in range(1, number + 1):
        mess_id = message.message_id - mess_count
        try:
            context.bot.delete_message(chat_id=chat_id, message_id=mess_id)
        except error.BadRequest:
            pass


def dialog_to_accept(reply_text: str, buttons: list, update: Update) -> int:
    reply_markup = make_inline_keyboard([buttons])
    # update.callback_query.answer()
    return update.callback_query.edit_message_text(text=reply_text,
                                                   reply_markup=reply_markup,
                                                   timeout=DELAY_BEFORE_DELETE).message_id


def alert(mess: str, update: Update, context: CallbackContext,
          popup: bool = False, in_cmd_line: bool = False, has_remove: bool = True,
          delay_time: int = DELAY_BEFORE_DELETE,
          url_button_name: str = None, url_button_link: str = None) -> int:
    """
    Функция выводит сообщение с текстом и с кнопкой для поиска.

    :param in_cmd_line: если True - отправка в режиме командной строки,
                        а не в виде всплывающей подсказки.
    :param mess: текст выводимый на экран, можно использовать HTML теги,
           только в случае, если это НЕ callback_query окно.
    :param update: обновленные данные по чату.
    :param context: текущий контекст сообщения.
    :param popup: флаг - будет ли всплывать окно, по умолчанию НЕ всплывает.
    :param has_remove: флаг удаления окна в режиме отличном от callback_query
    :param delay_time: пауза в секундах после которой сообщение удаляется
    :param url_button_name: имя кнопки для ссылки
    :param url_button_link: ссылка, которая откроется при нажатии на кнопку

    :return:
    """

    def __del_alert__(_context: CallbackContext) -> None:
        """
        Функция удаляет оповещения об окончании работы
        :param _context: текущий контекст
        :return: None
        """
        args = _context.job.context
        try:
            context.bot.delete_message(chat_id=args[etag.chat_id], message_id=args[etag.id])
        except error.BadRequest:
            pass

    # получаем id текущего чата
    chat_id = update.effective_chat.id

    if in_cmd_line:
        # если установлен флаг вывода в командную строку,
        # то публикуем сообщение именно в этом режиме
        # '{"inline_keyboard":[[{"mess":"'"$name"'","url":"'"$url"'"}]]}'
        if url_button_name and url_button_link:
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text=url_button_name, url=url_button_link)]])
            # reply_markup = f'{{"inline_keyboard":[[{{"mess":"{url_button_name}","url":"{url_button_link}"}}]]}}'
            mess_id = context.bot.send_message(text=mess, chat_id=chat_id, reply_markup=reply_markup).message_id
        else:
            mess_id = context.bot.send_message(text=mess, chat_id=chat_id).message_id
    else:
        if update.callback_query:
            # Если в сообщение встречается индикатор ошибки, то принудительно выводим окно с кнопкой
            show_alert = True if (Error.INDICATOR in mess or popup is True) else False
            mess = tools.clean_html(raw_html=mess)
            update.callback_query.answer(text=mess, show_alert=show_alert)
            mess_id = -1
            # chat_id = update.callback_query.message.chat_id
        else:
            # update.callback_query.answer()
            mess_id = update.message.reply_text(f"{mess}").message_id
            # chat_id = update.message.chat_id

    # В случае, если режим вывода отличен от всплывающих сообщений, то...
    if has_remove and mess_id > 0:
        # запускаем отложенное удаление уведомления, где задержка
        # удаления сообщения DELAY_BEFORE_DELETE измеряется в секундах
        context.job_queue.run_once(callback=__del_alert__, when=delay_time,
                                   context=dict(chat_id=chat_id, id=mess_id))

    return mess_id


def show_list_core(message_id, reply_text: str,
                   list_content: list, cmd_buttons: list, back_buttons: list,
                   menu_level: int, update: Update, context: CallbackContext,
                   content_list_in_row: int = 1) -> (int, int):
    """
    Функция формирует сообщение для отправки в чат и затем отправляет его
    Основные моменты, это подготовка "плавающих" клавиатур для вывода

    :param message_id: идентификатор сообщения.
    :param reply_text: текст сообщения.
    :param list_content: список пунктов к сообщению (отображаются в виде кнопок).
    :param cmd_buttons: список кнопок-команд, которые отображаются ниже списка пунктов.
    :param back_buttons: список кнопок-возврата, которые отображаются ниже кнопок-команд.
    :param menu_level: уровень меню, который должна вернуть функция.
    :param update:
    :param context:
    :param content_list_in_row: количество кнопок в ряду для списка контента

    :return: menu_level - идентификатор уровня меню и
             message_id - идентификатор опубликованного функцией сообщения для последующих действий с ним.
    """

    # устанавливаем значения по умолчанию для переменных
    chunk_list = []

    # формируем список пунктов к сообщению (отображаются в виде кнопок)
    if list_content:
        buttons_in_row = content_list_in_row if content_list_in_row else InRow.INLINE_LISTITEMS_INROW
        chunk_list = list(list_chunk(elem_list=list_content, buttons_in_row=buttons_in_row))

    if cmd_buttons:
        # в случае наличия кнопок-команд
        # проверяем наличие подсписков в переданному списке команд
        # делаем копию списка, так как нам необходимо
        butt_list = cmd_buttons[:]
        buttons_in_one_row = []
        # len_list = len(butt_list)
        # извлекаем кнопки заключенные в отдельный список (подсписок)
        for i, k in enumerate(cmd_buttons):
            if isinstance(k, list):
                butt_list.pop(i - len(buttons_in_one_row))
                buttons_in_one_row.append((i, k))
        # формируем плавающую клавиатуру из них с обозначенным числом кнопок в ряду
        cmd_list = list(list_chunk(elem_list=butt_list, buttons_in_row=InRow.CMD_BUTT_INROW))
        # в случае наличия отдельного ряда кнопок, возвращаем их крайними (в самом низу)
        if buttons_in_one_row:
            for num, (n, row) in enumerate(buttons_in_one_row):
                num_chunk = (tools.floor(n / InRow.CMD_BUTT_INROW) if n >= InRow.CMD_BUTT_INROW else 0) + num
                cmd_list.insert(num_chunk, list(list_chunk(elem_list=row, buttons_in_row=InRow.CMD_BUTT_INROW)))

        # если в списке команд всего один ряд кнопок, то извлекаем его и
        # плюсуем к основной клавиатуре кнопок
        chunk_list += cmd_list

    # добавляем кнопки возврата
    chunk_list += list(list_chunk(back_buttons, buttons_in_row=InRow.CMD_BUTT_INROW))

    #  формируем плавающую клавиатуру
    reply_markup = make_inline_keyboard(chunk_list)
    # обозначаем callback_query для упрощенного обращения
    query = update.callback_query
    if query:
        # если находимся в режиме плавающих сообщений, то ...
        try:
            # пытаемся отправить сообщение в чат
            # query.answer()
            message_id = query.edit_message_text(text=reply_text, reply_markup=reply_markup).message_id

        except error.BadRequest:
            # если попытка не увенчалась успехом, то
            # этого говорит нам о том, что текст сообщения, скорее всего,
            # НЕ был обновлен - не менялся, поэтому делаем хитрый прием
            # встраиваем в сообщение "невидимый" символ, который каждый раз обновляем
            if etag.ddot in reply_text:
                # при наличии внутри тела сообщения 'невидимого' тега
                # подменяем на пустое значение - удаляем его
                reply_text = reply_text.replace(etag.ddot, etag.pdot)
            else:
                # при его отсутствии добавляем "невидимый" символ в сообщение
                # reply_text = f"{reply_text} {etag.invisible}"
                reply_text = reply_text.replace(etag.pdot, etag.ddot)
            # отправляем сообщение вновь
            # query.answer()
            chat_id = update.callback_query.message.chat_id
            if context.user_data.get(etag.info):
                message_id = context.bot.send_message(text=reply_text, reply_markup=reply_markup,
                                                      chat_id=chat_id).message_id
                context.user_data[etag.info] = False
            else:
                message_id = query.edit_message_text(text=reply_text, reply_markup=reply_markup).message_id
    else:
        # если режим плавающих сообщений не доступен, то
        if message_id > 0:
            # и message_id существует, то удаляем предыдущее сообщение
            delete_messages(number=1, update=update, context=context)
        # и отправляем новое сообщение
        message_id = update.message.reply_text(text=reply_text, reply_markup=reply_markup).message_id

    # возвращаем идентификатор уровня меню и идентификатор опубликованного функцией сообщения
    return menu_level, message_id


def run_background(func_start: Callable, update: Update, context: CallbackContext,
                   func_finish: Callable, menu_level: int, records_to_processing: int = None,
                   func_start_args: object = None, has_start_alert: bool = True,
                   instantly_update: bool = True) -> int:
    """
    Функция запускает в фоне необходимый процесс/функцию func

    :param func_start: запускаемый процесс или функция, указывается без скобок
    :param update: данные обновления
    :param context: данные контекста
    :param func_finish: функция отображения меню после завершения фонового процесса
    :param menu_level: идентификатор уровня вложенности меню
    :param records_to_processing: число записей передаваемых для обработки в func_start
    :param func_start_args: аргументы передаваемые в вызываемую функцию в виде словаря
    :param has_start_alert: флаг показа уведомления о запуске работы функции
    :param instantly_update: флаг немедленного обновления результатов исполнения
                            другими словами если флаг НЕ установлен, то вызов func_finish
                            не станет осуществляться сразу. а только после завершения func_start

    :return: идентификатор уровня вложенности меню
    """

    if records_to_processing and records_to_processing > LIMIT_RECORDS_FOR_BACKGROUND:
        # Если число записей для обработки больше,
        # чем установленный лимит, то обрабатываем записи в фоне...

        # Проверяем наличие входных аргументов для исполняемой функции
        if func_start_args is None:
            func_start_args = {}

        result = menu_level

        def _del_mess(_context: CallbackContext) -> None:
            """
            Функция удаляет оповещения об окончании работы
            :param _context: текущий контекст
            :return: None
            """

            args = _context.job.context
            # удаляем сообщение
            try:
                context.bot.delete_message(chat_id=args[etag.chat_id], message_id=args[etag.id])
            except error.BadRequest:
                pass

        def _run_func_start_background(_context: CallbackContext) -> None:
            """
            Функция запускает в фоне необходимую программу func c параметрами func_args
            :param _context: текущий контекст
            :return:
            """
            zlog.debug(f'Функция "{func_start.__name__}" была запущена в фоне')
            # Запускаем функцию в фоне и устанавливаем соответствующий флаг
            context.user_data[etag.action] = True
            _message = func_start(**func_start_args)
            # получаем id чата
            _chat_id = _context.job.context[etag.chat_id]
            # возвращаемый ею результат отправляем в качестве уведомления об окончании работы
            _mess_id = _context.bot.send_message(chat_id=_chat_id, text=_message).message_id
            # Производим отложенный запуск удаления уведомления
            context.job_queue.run_once(callback=_del_mess,
                                       when=DELAY_BEFORE_DELETE,
                                       context=dict(chat_id=_chat_id, id=_mess_id))

            # фиксируем завершение фоновой функции
            context.user_data[etag.action] = False

            try:
                # Пытаем вызов функции и в случае,
                # если не будет обновления меню, то вызовет ошибку...
                callback = __show_finish_menu(func_finish, menu_level, update=update, context=context)

            except error.BadRequest:
                # которую мы отлавливаем здесь
                callback = _context.job.context[etag.menu_id]

            return callback

        # Получаем идентификатор чата
        chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
        if context.job_queue.get_jobs_by_name(name=etag.background):
            mess = 'Еще не завершены задачи запущенные ранее!\n' \
                   'Дождитесь их завершения и попробуйте снова.'
            alert(mess=mess, update=update, context=context, popup=True)
        else:
            # если необходимо отправить уведомление о начале запуска, то отправляем его
            if has_start_alert:
                message = "Процедура может занять время.\nОб окончании сообщим отдельно!"
                mess_id = alert(mess=message, update=update, context=context, has_remove=False)
                # В случае, если режим вывода отличен от всплывающих сообщений, то...
                if mess_id > 0:
                    # запускаем отложенное удаление уведомления, где задержка
                    # удаления сообщения DELAY_BEFORE_DELETE измеряется в секундах
                    context.job_queue.run_once(callback=_del_mess, when=DELAY_BEFORE_DELETE,
                                               context=dict(chat_id=chat_id, id=mess_id))
            # Запускаем без задержек функцию на исполнение в фоне.
            context.job_queue.run_once(callback=_run_func_start_background, when=0, name=etag.background,
                                       context=dict(chat_id=chat_id, menu_id=menu_level,
                                                    con=context, upd=update))
            # delete_messages(0, update=update, context=context)
            if instantly_update:
                result = __show_finish_menu(func_finish, menu_level, update=update, context=context)
            else:
                result = menu_level
    else:
        # Если число записей для обработки меньше, чем установленный лимит,
        # то обрабатываем в обычном порядке, сначала исполняем функцию
        message = func_start(**func_start_args)
        # затем выдаем оповещение об результате работы функции
        alert(mess=message, update=update, context=context)
        # вызываем соответствующее меню
        result = __show_finish_menu(func_finish, menu_level, update=update, context=context)

    # возвращаем идентификатор уровня вложенности меню
    return result


def __show_finish_menu(func_finish: Callable, menu_level: int, update: Update, context: CallbackContext) -> int:
    """
    СЛУЖЕБНАЯ функция заботится о выставлении флагов при отрисовки меню
    Если уровни меню (текущий и предыдущий) отличны, то меню не отрисовываем

    :param func_finish: финишная функция отрисовки уровня меню.
    :param menu_level: текущий уровень меню.
    :param update:
    :param context:
    :return: текущий уровень меню.
    """
    # сверяем уровни меню
    if context.user_data[etag.callback] == menu_level:
        # в случае, если уровень меню не изменился, то обновляем меню
        callback = func_finish(update=update, context=context)
    else:
        # в случае, если уровень меню изменился,
        # устанавливаем код возврата = текущему уровню меню
        callback = menu_level

    return callback
