#!/bin/python3
# coding=utf-8

#
#  Copyright (c) 2022.
#
#  Автор: mail@zeleza 03.2022
#  Вся сила в правде!
#

# Автор: master
# Email: info@zeleza.ru
# Дата создания: 11.04.2022 18:08
# Пакет: PyCharm

"""
Обработчик ошибок, который отправляет
разработчику полную информацию об ошибке
Первоисточник:
https://docs-python.ru/packages/biblioteka-python-telegram-bot-python/obrabotka-oshibok/
    
"""
import html
import json
import sys
import traceback

from telegram import ParseMode, Update
from telegram.utils.helpers import mention_html

from setup.data import DEVELOPER_USER_ID


def error_tracer(update, context):
    """
    Это общая функция обработчика ошибок.
    Если нужна дополнительная информация о конкретном типе сообщения,
    добавьте ее в полезную нагрузку в соответствующем предложении `if ...`

    :param update:
    :param context:
    """
    # Добавьте все идентификаторы разработчиков в этот список.
    # Можно добавить идентификаторы каналов или групп.
    devs = [DEVELOPER_USER_ID]
    # Уведомление пользователя об этой проблеме.
    # Уведомления будут работать, только если сообщение НЕ является
    # обратным вызовом, встроенным запросом или обновлением опроса.
    # В случае, если это необходимо, то имейте в виду, что отправка
    # сообщения может потерпеть неудачу
    if update.effective_message:
        text = "К сожалению произошла ошибка в момент обработки сообщения. " \
               "Мы уже работаем над этой проблемой."
        update.effective_message.reply_text(text)
    # Трассировка создается из `sys.exc_info`, которая возвращается в
    # как третье значение возвращаемого кортежа. Затем используется
    # `traceback.format_tb`, для получения `traceback` в виде строки.
    # trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # попробуем получить как можно больше информации из обновления telegram
    payload = []
    # Обычно всегда есть пользователь. Если нет, то это
    # либо канал, либо обновление опроса.
    if update.effective_user:
        bad_user = mention_html(update.effective_user.id, update.effective_user.first_name)
        payload.append(f' с пользователем {bad_user}')
    # есть ситуаций, когда что-то с чатом
    if update.effective_chat:
        if update.effective_chat.title:
            payload.append(f' внутри чата <i>{update.effective_chat.title}</i>')
        if update.effective_chat.username:
            payload.append(f' (@{update.effective_chat.username})')
    # полезная нагрузка - опрос
    if update.poll:
        payload.append(f' с id опроса {update.poll.id}.')

    # `traceback.format_exception` возвращает обычное сообщение python
    # об исключении в виде списка строк, поэтому объединяем их вместе.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Трассировка создается из `sys.exc_info`, которая возвращается в
    # как третье значение возвращаемого кортежа. Затем используется
    # `traceback.format_tb`, для получения `traceback` в виде строки.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))

    # Создаем сообщение с некоторой разметкой и дополнительной
    # информацией о том, что произошло. Возможно, придется добавить некоторую
    # логику для работы с сообщениями длиной более 4096 символов.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'Возникло исключение при обработке сообщения.\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f"Ошибка <code>{context.error}</code> случилась{''.join(payload)}. \n"
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>\n\n'
        f"Полная трассировка:\n\n<code>{trace}</code>"
    )
    # и отправляем все разработчикам
    for dev_id in devs:
        context.bot.send_message(dev_id, message, parse_mode=ParseMode.HTML)
    # Необходимо снова вызывать ошибку, для того, чтобы модуль `logger` ее записал.
    # Если вы не используете этот модуль, то самое время задуматься.
    raise
