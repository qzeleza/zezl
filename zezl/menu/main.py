# coding=utf-8

from telegram import Update
from telegram.ext import CallbackContext

from libraries.main import tools as tools, dialog
from libraries.watchdogs.errors import get_errors_from_file
from libraries.watchdogs.jobs import run_wdogs_at_start
from setup.autosets import MAIN_MENU, SEND_TO_IGNORE_LIST
from setup.data import (
    VERSION,
    APP_PATH
)
from setup.description import (
    ErrorTextMessage as Error,
    be, bs, etag,
)
from setup.menu import Menu


@run_wdogs_at_start
def start_menu(update: Update, context: CallbackContext) -> int:
    """

    :param update:
    :param context:
    :return:
    """
    result, _ = dialog.show_list_core(message_id=-1,
                                      reply_text=Menu.Title,
                                      list_content=Menu.Items,
                                      cmd_buttons=[],
                                      back_buttons=[],
                                      menu_level=MAIN_MENU,
                                      update=update, context=context)
    return result


@run_wdogs_at_start
def show_bot_about(update: Update, context: CallbackContext) -> int:
    """

    :param update:
    :param context:
    :return:
    """
    text_about = f"{bs}Жезл™ [Zezl™]{be} бот для Keenetic\n" \
                 f"{bs}Все важное - под рукой!{be}\n" \
                 f"Версия {VERSION}\n\n" \
                 f"Zeleza© 03.2022\n" \
                 f"{bs}Россия{be}"

    dialog.alert(mess=text_about, update=update, context=context, popup=True, delay_time=10)
    return MAIN_MENU


def show_bot_history(update: Update, context: CallbackContext) -> int:
    """
    Функция отображает сообщение об истории изменений версий пакета Жезл

    :param update:
    :param context:
    :return:
    """
    text_about = "\n".join(tools.get_file_content(file=f"{APP_PATH}/HISTORY"))
    dialog.alert(mess=text_about, update=update, context=context, popup=True, delay_time=30)
    return MAIN_MENU


def cmdjust(cmd: str, max_len: int = 18) -> str:
    """
    Функция выравнивает строку по заданному числу знаков в строке

    :param cmd: команда или строка
    :param max_len: длина строки
    :return:
    """
    return f"{bs}{cmd}{be}".ljust(max_len)


@run_wdogs_at_start
def show_command_help(update: Update, context: CallbackContext) -> int:
    """

    :param update:
    :param context:
    :return:
    """
    ln = '----------------------------\n'
    add_cmd = cmdjust(f"{etag.cmd.new}{be} и {bs}{etag.cmd.add}", 30)
    del_cmd = cmdjust(f"{etag.cmd.delete}{be} и {bs}{etag.cmd.rm}", 30)
    menu_help = f"{bs}Команды меню{be}\n" \
                f"{ln}" \
                f"/{cmdjust(etag.cmd.start)} вызов {bs}Главного{be} меню.\n" \
                f"/{cmdjust(etag.cmd.vpn)} вызов меню {bs}VPN{be}.\n" \
                f"/{cmdjust(etag.cmd.setup)}вызов меню {bs}VPN Настройки{be}.\n" \
                f"/{cmdjust(etag.cmd.start)} вызов меню {bs}VPN Архивы{be}.\n" \
                f"{ln}" \
                f"/{cmdjust(etag.cmd.show)}показать {bs}Белый список{be}.\n" \
                f"/{cmdjust(etag.cmd.imp)}добавить домены к {bs}Белому списку{be}.\n" \
                f"/{cmdjust(etag.cmd.timer)} установить {bs}таймер обновления{be} доменов.\n"

    cmd_help = f"{bs}Команды с аргументами{be}\n" \
               f"{ln}" \
               f"{add_cmd}добавить хосты в список.\n" \
               f"{del_cmd}   удалить хосты из списка.\n" \
               f"{ln}" \
               f"Доменные имена могут разделяться {bs}\n" \
               f"запятой, пробелом, точкой с запятой, \n" \
               f"новой строкой{be}.\n" \
               f"{ln}" \
               f"Примеры:\n" \
               f"{bs}/new{be} yandex.ru google.ru; list.com, trust.com\n" \
               f"{bs}/del{be} yandex.ru;google.ru;list.com;trust.com"

    dialog.alert(mess=menu_help, update=update, context=context, has_remove=False)
    dialog.alert(mess=cmd_help, update=update, context=context, has_remove=False)

    return MAIN_MENU


def handle_invalid_button(update: Update, _: CallbackContext) -> int:
    """
    Функция информирует пользователя о том, что кнопка больше недоступна

    :param update:
    :param _:
    :return:
    """
    # update.callback_query.answer()
    update.effective_message.edit_text(Error.INVALID_BUTTON_MESSAGE)
    return MAIN_MENU


def close_menu(update: Update, _: CallbackContext) -> None:
    """
    Функция вызывается только с одной целью - закрыть текущее меню/окно/сообщение с текущим id.

    :param _:
    :param update:
    """
    if update.message:
        update.message.delete()

    if update.callback_query:
        update.callback_query.delete_message()

    return None


def send_to_ignore_list(update: Update, context: CallbackContext) -> None:
    """
    Функция вызывается только с одной целью - добавить в список игнорирования соответствущее сообщение.

    :param context:
    :param update:
    """
    num_err = "".join(update.callback_query.data.split(f'{SEND_TO_IGNORE_LIST}_'))
    err_list = get_errors_from_file(err_number=num_err)
    err_mess = "".join([m for n, _, m in err_list if n == num_err])

    if context.user_data.get(etag.err_ignore_list) is None:
        # если список еще пустой и не создан
        context.user_data[etag.err_ignore_list] = [err_mess]
    else:
        #  если список создан, то проверяем нет ли там уже такой записи
        if err_mess not in context.user_data[etag.err_ignore_list]:
            # если нет то добавляем
            context.user_data[etag.err_ignore_list].append(err_mess)

    return None
