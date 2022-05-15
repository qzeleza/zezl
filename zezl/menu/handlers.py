# coding=utf-8
from typing import Callable

from telegram import (
    BotCommand,
    CallbackQuery, Update,
)
from telegram.ext import (
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    ConversationHandler,
    CommandHandler, CallbackContext,
)

import setup.autosets as st
import setup.data as dt
from libraries.main.config import get_config_value
from libraries.main.tools import check_url
from menu import main as main
from menu.router import router
from menu.vpn import vpn
from menu.watchdogs import wdogs
from setup.description import etag, rtag
from setup.menu import Menu


def get_user_id() -> list[int]:
    """
    Получаем из файла конфигурации user_id

    :return: user_id

    """
    try:
        # в случае, если работа в режиме отладки на удаленной машине
        from debug import remote_data
        # то берем user_id из файла
        user_id = remote_data.USER_ID
    except ImportError or ModuleNotFoundError:
        user_id = get_config_value(name=etag.user_id)

    # Для отладки подключаем разработчика к доступу отправки ошибок.
    result = [int(user_id)]
    # получаем значение флага DEBUG
    debug_flag = get_config_value(name=etag.debug, default=etag.yes).lower()
    # если в файле конфигурации установлен флаг DEBUG в значение YES или TRUE
    if debug_flag == etag.yes or debug_flag == etag.true:
        #  добавляем разработчика в список доверенных лиц для отправки сообщений об ошибках.
        result.append(dt.DEVELOPER_USER_ID)

    return result


def rep_auto_switch():
    """
    Функция возвращает регулярное
    выражение для кнопки "Включить" и "Отключить" флага auto у домена

    :return: регулярное выражение для кнопки.
    """
    return f"^({'|'.join([st.WL_11_AUTO_SWITCH_ON_ACTION, st.WL_12_AUTO_SWITCH_OFF_ACTION])})$"


def rep_select_all_hosts():
    """
    Функция возвращает регулярное
    выражение для фильтрации кнопки "Выбрать все" и "Отменить все"

    :return: регулярное выражение для кнопки.
    """
    return f"^({'|'.join([st.WL_13_SELECT_ALL, st.WL_14_UNSELECT_ALL])})$"


def rep_select_all_backup_hosts():
    """
    Функция возвращает регулярное
    выражение для фильтрации кнопки "Выбрать все" и "Отменить все"

    :return: регулярное выражение для кнопки.
    """
    return f"^({'|'.join([st.BCT_5_SELECT_ALL, st.BCT_6_UNSELECT_ALL])})$"


def rep_interface_list():
    """
    Функция возвращает регулярное
    выражение для фильтрации типов интерфейсов

    :return: регулярное выражение для типов интерфейсов.
    """
    return f"^({'|'.join(dt.INTERFACE_TYPES)})"


def rep_dns_list():
    """
    Функция возвращает регулярное
    выражение для фильтрации DNS имен (IP адреса)

    :return: регулярное выражение для IP адреса.
    """
    return r"^.*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"


def rep_backup_names_filter():
    # prefix = f"{rtag.backup} {etag.backup}".split()[0]
    return f"^{etag.divider}"


def rep_host():
    """
    Функция возвращает регулярное
    выражение для фильтрации доменных имен

    :return: регулярное выражение для домена.
    """
    res = r'^(.*[a-zA-Z\d-]{2,63}\.[a-zA-Z\d-]{2,6})'
    # res = r'(\w\.|\w[A-Za-z0-9-]{2,63}\w\.{1,3}[A-Za-z]{2,6})*'
    return res


def check_link(attr: CallbackQuery.data) -> bool:
    """
    Функция вызывается из CallbackQueryHandler
    с единственным аргументом attr: telegram.CallbackQuery.data
    для проверки полученного значения из строки ввода
    и возвращает результат проверки в виде True - проверка пройдена
    или False - проверка не пройдена

    :param attr:
    :return:
    """
    res = check_url(link=attr, check_for_validation=False)
    return True if res else False


def rep(args: str | list) -> str:
    """
    Функция возвращает готовый паттерн регулярного
    выражения, в зависимости от типа передаваемого
    аргумента: строки или списка

    :param args: строка или список для создания паттерна.
    :return: паттерн регулярного выражения
    """
    return r".*({}).*".format("|".join(args)) if isinstance(args, list) else rf"^{args}"


engines_list = ["".join(en.keys()) for en in Menu.WatchdogsMenu.ErrorsMenu.EngineSearchMenu.ItemsList]
interval_sys_error_list = ["".join(en.values()) for en in Menu.WatchdogsMenu.ErrorsMenu.IntervalMenu.ItemsList]
interval_site_watch_list = ["".join(en.values()) for en
                            in Menu.WatchdogsMenu.SitesMenu.EditLinkMenu.IntervalMenu.ItemsList]

HANDLER = {

    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню Основное  - обработка событий
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.MAIN_MENU: [
        # Обработка нажатий на кнопку вызова VPN меню
        CallbackQueryHandler(vpn.menu_vpn_show, pattern=rep(st.MAIN_1_VPN_MENU_SHOW)),
        # Обработка нажатий на кнопку вызова меню Роутер
        CallbackQueryHandler(router.show_router_menu, pattern=rep(st.MAIN_3_ROUTER_MENU_SHOW)),
        # Меню Сторожей
        CallbackQueryHandler(wdogs.wdogs_menu_show, pattern=rep(st.MAIN_WHATCHDOGS_MENU_SHOW)),
        # Обработка нажатий на кнопку "О проекте"
        CallbackQueryHandler(main.show_bot_about, pattern=rep(st.MAIN_2_ROUTER_ABOUT)),
    ],

    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню VPN  - обработка событий меню VPN
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.VPN_MENU: [
        # Обработка нажатий на кнопку вызова списка интерфейсов
        CallbackQueryHandler(vpn.vpn_hosts_interface_list_show, pattern=rep(st.VPN_1_INTERFACE_LIST_SHOW)),
        # Обработка нажатий на кнопку вызова меню "Архивы"
        CallbackQueryHandler(vpn.vpn_backup_list_show, pattern=rep(st.VPN_2_BACKUP_MENU_SHOW)),
        # Обработка нажатий на кнопку вызова меню "Таймер обновлений"
        CallbackQueryHandler(vpn.vpn_timer_menu_show, pattern=rep(st.TM_1_TIMER_SHOW)),

        # Обработка нажатий на кнопку возврата в основное меню
        CallbackQueryHandler(main.start_menu, pattern=rep(st.VPN_4_BACK_ACTION)),
    ],
    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню VPN выбор интерфейса - обработка событий
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.VPN_INTERFACE_LIST_SHOW: [
        # Обработка нажатий на кнопки с именами интерфейсов
        CallbackQueryHandler(vpn.vpn_hosts_white_list_show, pattern=rep_interface_list()),

        # Обработка нажатий на кнопку возврата в основное меню и на уровень выше
        CallbackQueryHandler(main.start_menu, pattern=rep(st.INL_2_BACK_TO_MAIN_ACTION)),
        CallbackQueryHandler(vpn.menu_vpn_show, pattern=rep(st.INL_3_BACK_ACTION)),

    ],
    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню VPN список хостов - обработка событий со списком доменов
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.VPN_HOSTS_ACTIONS: [
        # обработка нажатий на кнопку смены режима auto
        CallbackQueryHandler(vpn.vpn_hosts_switch_auto_action, pattern=rep_auto_switch()),
        # обработка нажатий на кнопки с именами доменных имен
        CallbackQueryHandler(vpn.vpn_hosts_press_on_host_button_action, pattern=rep_host()),
        # обработка нажатий на кнопки "Выбрать все" "Отменить выбор"
        CallbackQueryHandler(vpn.vpn_hosts_press_on_select_all_button_action, pattern=rep_select_all_hosts()),
        # обработка нажатий на кнопку выбора интерфейсов и на кнопки самих интерфейсов
        CallbackQueryHandler(vpn.vpn_hosts_change_interface_request, pattern=rep(st.WL_7_INTERFACE_CHANGE_REQUEST)),
        CallbackQueryHandler(vpn.vpn_hosts_change_interface_action, pattern=rep_interface_list()),

        # обработка нажатий на кнопку EditButton - просмотра информации о выбранных домене/ах
        CallbackQueryHandler(vpn.vpn_hosts_details_show_action, pattern=rep(st.WL_8_HOST_INFO_SHOW)),

        # обработка нажатий на кнопки RemoveItem/PurgeButton/RejectItem
        # Удаление выбранных или всего белого списка доменных имен
        CallbackQueryHandler(vpn.vpn_hosts_remove_request, pattern=rep(st.WL_3_PURGE_REQUEST)),
        CallbackQueryHandler(vpn.vpn_hosts_remove_action, pattern=rep(st.WL_5_REMOVE_ACCEPT_ACTION)),
        CallbackQueryHandler(vpn.vpn_hosts_white_list_show, pattern=rep(st.WL_6_REMOVE_REJECT_ACTION)),

        # обработка ввода данных при добавлении доменных имен
        MessageHandler(Filters.text & ~Filters.command, vpn.vpn_hosts_add_action),

        # обработка нажатия на клавишу записать
        CallbackQueryHandler(vpn.vpn_hosts_save_to_backup_action, pattern=rep(st.WL_15_SAVE_ACTION)),
        # обработка нажатий на кнопку AddButton - добавления доменных имен
        CallbackQueryHandler(vpn.vpn_hosts_add_request, pattern=rep(st.WL_2_HOST_ADD_REQUEST)),
        # обработка нажатий на кнопку BackUpButton - просмотр архивов доменных имен
        CallbackQueryHandler(vpn.vpn_backup_list_show, pattern=rep(st.WL_4_BACKUP_LIST_SHOW)),

        # обработка нажатий на кнопки возврата на главное и предыдущий уровень меню
        CallbackQueryHandler(main.start_menu, pattern=rep(st.WL_9_BACK_TO_MAIN_ACTION)),
        CallbackQueryHandler(vpn.vpn_hosts_interface_list_show, pattern=rep(st.WL_10_BACK_ACTION)),

    ],

    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню VPN  - обработка событий со списком архивов
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.VPN_INTERFACE_HOSTS_CHANGE: [
        # Реакция на кнопки возврата в верхний уровень меню
        # в меню выбора интерфейса при переносе доменов на другой интерфейс
        CallbackQueryHandler(vpn.vpn_hosts_white_list_show, pattern=rep(st.IFCH_2_BACK_ACTION)),
        CallbackQueryHandler(main.start_menu, pattern=rep(st.IFCH_1_BACK_TO_MAIN_ACTION)),
    ],
    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню VPN Архив - обработка событий со списком архивов
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.VPN_BACKUP_LIST: [

        # обработка нажатий на кнопку CreateButton - создать Архив.
        CallbackQueryHandler(vpn.vpn_backup_create_action, pattern=rep(st.BUP_4_CREATE_NEW_ACTION)),
        # обработка нажатий на кнопку RemoveAllButton - удалить Архив.
        CallbackQueryHandler(vpn.vpn_backup_remove_all_request, pattern=rep(st.BUP_8_REMOVE_REQUEST)),
        CallbackQueryHandler(vpn.vpn_backup_remove_all_action, pattern=rep(st.BUP_2_REMOVE_ACCEPT_ACTION)),
        CallbackQueryHandler(vpn.vpn_backup_list_show, pattern=rep(st.BUP_3_REMOVE_REJECT_ACTION)),

        # обработка нажатий на кнопки "Выбрать все" "Отменить выбор"
        CallbackQueryHandler(vpn.vpn_backup_list_content_show, pattern=rep_backup_names_filter()),

        # Реакция на кнопки возврата в верхний уровень меню
        # в меню выбора интерфейса при переносе доменов на другой интерфейс
        CallbackQueryHandler(vpn.menu_vpn_show, pattern=rep(st.BUP_7_BACK_ACTION)),
        CallbackQueryHandler(main.start_menu, pattern=rep(st.BUP_6_BACK_TO_MAIN_ACTION)),
    ],
    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню VPN Архив содержание выбранного архива - обработка событий
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.VPN_BACKUP_CONTENT: [
        # обработка нажатий на кнопки "Выбрать все" "Отменить выбор"
        CallbackQueryHandler(vpn.vpn_backup_press_on_select_all_button_action, pattern=rep_select_all_backup_hosts()),
        # обработка нажатий на кнопки "Выбрать все" "Отменить выбор"
        CallbackQueryHandler(vpn.vpn_backup_press_on_host_button_action, pattern=rep_host()),

        # обработка нажатий на кнопку RenameButton - переименовать Архив.
        CallbackQueryHandler(vpn.vpn_backup_rename_request, pattern=rep(st.BCT_7_RENAME_REQUEST)),
        # обработка ввода нового имени архива при его изменении
        MessageHandler(Filters.text & ~Filters.command, vpn.vpn_backup_rename_action),

        # обработка нажатий на кнопку RenameButton - переименовать Архив.
        CallbackQueryHandler(vpn.vpn_backup_export_request, pattern=rep(st.BCT_10_EXPORT_TO_WL_ACTION)),

        # обработка запроса на удаление текущего архива
        CallbackQueryHandler(vpn.vpn_backup_remove_one_request, pattern=rep(st.BCT_2_REMOVE_REQUEST)),
        CallbackQueryHandler(vpn.vpn_backup_remove_one_action, pattern=rep(st.BCT_3_REMOVE_ACCEPT_ACTION)),
        CallbackQueryHandler(vpn.vpn_backup_list_content_show, pattern=rep(st.BCT_4_REMOVE_REJECT_ACTION)),

        # обработка нажатий на имя интерфейса при экспорте данных
        CallbackQueryHandler(vpn.vpn_backup_press_on_select_inface_button_action, pattern=rep_interface_list()),

        # Реакция на кнопки возврата в верхний уровень меню
        # в меню выбора интерфейса при переносе доменов на другой интерфейс
        CallbackQueryHandler(vpn.vpn_backup_list_show, pattern=rep(st.BCT_9_BACK_ACTION)),
        CallbackQueryHandler(main.start_menu, pattern=rep(st.BCT_8_BACK_TO_MAIN_ACTION)),

    ],
    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню VPN Архив экспорт - обработка событий
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.VPN_BACKUP_EXPORT: [
        # обработка нажатий на кнопки названий интерфейсов при экспорте данных.
        CallbackQueryHandler(vpn.vpn_backup_export_action, pattern=rep_interface_list()),
        CallbackQueryHandler(vpn.vpn_backup_list_content_show, pattern=rep(st.BCT_11_BACK_INTERFACE_REQUEST)),
    ],
    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню VPN Таймер - обработка событий
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.VPN_TIMER: [
        # обработка нажатий клавиши "Обновить все"
        CallbackQueryHandler(vpn.vpn_timer_update_hosts_action, pattern=rep(st.TM_2_UPDATE_ACTION)),
        # обработка нажатий клавиши "Изменить период таймера"
        CallbackQueryHandler(vpn.vpn_timer_change_request, pattern=rep(st.TM_3_CHANGE_REQUEST)),
        # обработка ввода нового периода таймера
        MessageHandler(Filters.text & ~Filters.command, vpn.vpn_timer_change_action),

        # обработка нажатий клавиши "Удалить таймер" - запрос на удаление
        CallbackQueryHandler(vpn.vpn_timer_delete_request, pattern=rep(st.TM_4_DELETE_REQUEST)),
        # обработка нажатий клавиши "Подтвердить удаление"
        CallbackQueryHandler(vpn.vpn_timer_delete_action, pattern=rep(st.TM_5_DELETE_ACCEPT_ACTION)),
        CallbackQueryHandler(vpn.vpn_timer_menu_show, pattern=rep(st.TM_6_REMOVE_REJECT_ACTION)),

        CallbackQueryHandler(vpn.menu_vpn_show, pattern=rep(st.TM_8_BACK_ACTION)),
        CallbackQueryHandler(main.start_menu, pattern=rep(st.TM_7_BACK_TO_MAIN_ACTION)),
    ],

    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню Сторожей - обработка событий
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.WD_MAIN_MENU_LEVEL: [
        CallbackQueryHandler(wdogs.sys_errors_show, pattern=rep(st.WD_ERRORS_ALARM_MENU)),
        CallbackQueryHandler(wdogs.news_show, pattern=rep(st.WD_SITE_WATCHER_MENU)),
        CallbackQueryHandler(main.start_menu, pattern=rep(st.WD_BACK_ACTION)),
    ],

    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню Сторожа обработка системных ошибок - обработка событий меню
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.WD_ERRORS_LEVEL: [
        CallbackQueryHandler(wdogs.sys_errors_state_press_action, pattern=rep(st.WD_ERR_ACTIVATION)),
        CallbackQueryHandler(wdogs.sys_errors_engine_choose_request,
                             pattern=rep(st.WD_ERR_SEARCH_ENGINE_REQUEST)),
        CallbackQueryHandler(wdogs.sys_errors_interval_choose_request,
                             pattern=rep(st.WD_ERR_INTERVAL_REQUEST)),

        CallbackQueryHandler(wdogs.wdogs_menu_show, pattern=rep(st.WD_ERR_STEP_BACK_ACTION)),
        CallbackQueryHandler(main.start_menu, pattern=rep(st.WD_ERR_MAIN_MENU_BACK_ACTION)),
    ],

    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню Сторожа обработка системных ошибок - обработка поисковой машины
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.WD_ERR_SEARCH_ENGINES_LEVEL: [
        CallbackQueryHandler(wdogs.sys_errors_engine_choose_action, pattern=rep(engines_list)),

        CallbackQueryHandler(wdogs.sys_errors_show,
                             pattern=rep(st.WD_ERR_BACK_TO_ERR_PAGE_ACTION)),
    ],

    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню Сторожа обработка системных ошибок - обработка поисковой машины
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.WD_ERR_INTERVAL_LEVEL: [
        CallbackQueryHandler(wdogs.sys_errors_interval_choose_action, pattern=rep(interval_sys_error_list)),

        CallbackQueryHandler(wdogs.sys_errors_show,
                             pattern=rep(st.WD_ERR_BACK_TO_ERR_PAGE_ACTION)),
    ],

    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню Сторожа обработка событий страницы по отслеживанию изменений на страницах сайтов
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.WD_SITES_WATCH_LEVEL: [
        CallbackQueryHandler(wdogs.news_add_name_link_action_and_request, pattern=rep(st.WD_SITE_LINK_ADD_REQUEST)),
        # обработка ввода новой ссылки (имени для ссылки) для отслеживания из командной строки
        MessageHandler(Filters.text & ~Filters.command, wdogs.news_add_link_request),

        # обработка событий при нажатии на клавишу "Удалить все"
        CallbackQueryHandler(wdogs.news_del_all_links_request, pattern=rep(st.WD_SITE_LINK_DEL_ALL_REQUEST)),
        CallbackQueryHandler(wdogs.news_del_all_links_action, pattern=rep(st.WD_SITE_LINK_DEL_ALL_ACCEPT)),
        CallbackQueryHandler(wdogs.news_show, pattern=rep(st.WD_SITE_LINK_DEL_ALL_REJECT)),

        CallbackQueryHandler(wdogs.wdogs_menu_show, pattern=rep(st.WD_SITE_STEP_BACK_ACTION)),
        CallbackQueryHandler(main.start_menu, pattern=rep(st.WD_SITE_MAIN_MENU_BACK_ACTION)),

        CallbackQueryHandler(wdogs.news_edit_link_show, pattern=check_link),
    ],
    st.WD_SITES_ADD_LEVEL: [
        # обработка ввода новой ссылки для отслеживания из командной строки
        MessageHandler(Filters.text & ~Filters.command, wdogs.news_add_new_link_action),
    ],
    st.WD_SITES_EDIT_LINK_LEVEL: [
        CallbackQueryHandler(wdogs.news_state_press_action, pattern=rep(st.WD_SITE_EDIT_LINK_WATCH_ACTIVATION)),
        CallbackQueryHandler(wdogs.news_del_link_request, pattern=rep(st.WD_SITE_EDIT_LINK_DEL_REQUEST)),
        CallbackQueryHandler(wdogs.news_interval_choose_request, pattern=rep(st.WD_SITE_EDIT_LINK_INTERVAL_REQUEST)),

        CallbackQueryHandler(wdogs.news_del_link_action, pattern=rep(st.WD_SITE_EDIT_LINK_DEL_ACCEPT)),
        CallbackQueryHandler(wdogs.news_edit_link_show, pattern=rep(st.WD_SITE_EDIT_LINK_DEL_REJECT)),

        CallbackQueryHandler(wdogs.news_show, pattern=rep(st.WD_SITE_EDIT_LINK_STEP_BACK_ACTION)),
        CallbackQueryHandler(main.start_menu, pattern=rep(st.WD_SITE_EDIT_LINK_MAIN_MENU_BACK_ACTION)),
    ],

    st.WD_SITES_EDIT_LINK_INTERVAL_LEVEL: [
        CallbackQueryHandler(wdogs.news_interval_choose_action, pattern=rep(interval_site_watch_list)),
        CallbackQueryHandler(wdogs.news_edit_link_show, pattern=rep(st.WD_SITE_EDIT_INTERVAL_STEP_BACK_ACTION)),
    ],
    # -----------------------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------------------

    # -----------------------------------------------------------------------------------------------------------------

    #
    #        Меню Роутер - обработка событий меню
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.ROUTER_MENU: [
        CallbackQueryHandler(main.start_menu, pattern=f'^{rtag.BackToMainMenu}$'),

        CallbackQueryHandler(router.show_list_devices, pattern=f'^{Menu.RouterMenu.DevicesItem}$'),
        CallbackQueryHandler(router.show_model_info, pattern=f'^{Menu.RouterMenu.AboutModelItem}$'),
    ],

    # -----------------------------------------------------------------------------------------------------------------
    #
    #        Меню Роутер  - обработка событий списка
    #
    # -----------------------------------------------------------------------------------------------------------------
    st.ROUTER_LIST_MENU: [
        CallbackQueryHandler(router.show_router_menu, pattern=f'^{rtag.BackToMainMenu}$'),
        CallbackQueryHandler(main.start_menu, pattern=f'^{rtag.BackToMainMenu}$'),
    ],
}

# Вводим список команд для отображения их в списке ввода
#  etag.menu - уровень меню - нажатие кнопок в меню
#  etag.terminal - уровень ввода и исполнения команд из строки телеграмма


def make_handler_list(tag: str, cmd_handler: bool = True) -> list:
    """
    Функция генерирует обработчики событий и пункты всплывающего меню в телеграме,
    при помощи которых можно начать диалог с ботом.
    !!!
    ПОМНИМ о том, чтобы к любой из функция ниже необходимо добавить декоратор @run_wdogs_at_start.
    Чтобы обеспечить возможность запуска сторожей при старте любой из этих команд.
    !!!
    :param tag: etag.menu - тип пункта - меню, etag.terminal - тип пункта - команда в строке ввода телеграма
    :param cmd_handler: флаг True - создаем элементы CommandHandler, Fasle - BotCommand
    :return:
    """
    filter_user = None
    cmd_list = [
        (True, etag.cmd.start, "Главное меню.", etag.menu, main.start_menu),
        (True, etag.cmd.vpn, "Меню VPN", etag.menu, vpn.menu_vpn_show),
        (True, etag.cmd.list, "Меню VPN::Белый список.", etag.menu, vpn.vpn_hosts_interface_list_show),
        (True, etag.cmd.backup, "Меню VPN::Архивы.", etag.menu, vpn.vpn_backup_list_show),
        (True, etag.cmd.timer, "Меню VPN::Таймер обновления.", etag.menu, vpn.vpn_timer_menu_show),

        (True, etag.cmd.watchdogs, "Меню Сторожа", etag.menu, wdogs.wdogs_menu_show),

        (True, etag.cmd.help, "Справка по командам.", etag.menu, main.show_command_help),
        (True, etag.cmd.about, "Справка о проекте™.", etag.terminal, main.show_bot_about),

        (False, etag.cmd.add, "Терминал::Добавить хосты.", etag.terminal, vpn.vpn_hosts_add_action),
        (False, etag.cmd.rm, "Терминал::Удалить хосты", etag.terminal, vpn.vpn_hosts_remove_action),
        (False, etag.cmd.setimer, "Терминал::Установить таймер", etag.terminal, vpn.vpn_timer_change_action),
    ]

    if cmd_handler:
        filter_user = Filters.user()
        # создаем фильтр - работаем только с пользователем-администратором.
        admin = get_user_id()
        filter_user.add_user_ids(user_id=admin)

    return [
        CommandHandler(command=cmd, callback=fnc, filters=filter_user)
        if cmd_handler else BotCommand(cmd, hlp)
        for show, cmd, hlp, tp, fnc in cmd_list
        if show and tp in tag
    ]


# задаем список команд со справкой в подсказке бота
commands_list = make_handler_list(tag=etag.menu, cmd_handler=False)
# формируем список команд для работы с меню в режиме ввода команд.
cmd_handler_menu_list = make_handler_list(tag=etag.menu)
# формируем список команд в режиме ввода из строки ввода
cmd_handler_terminal_list = make_handler_list(tag=etag.terminal)

# error_handler = CallbackQueryHandler(main.handle_invalid_button, pattern=InvalidCallbackData)

CONVERSATION_HANDLER = ConversationHandler(
        entry_points=cmd_handler_menu_list,
        states=HANDLER,
        allow_reentry=True,
        # fallbacks=[CommandHandler(etag.cmd.start, main.start_menu)],
        fallbacks=[
            CallbackQueryHandler(main.close_menu, pattern=rep(st.CALLBACK_TO_CLOSE_MENU)),
            CallbackQueryHandler(main.send_to_ignore_list, pattern=rep(f'{st.SEND_TO_IGNORE_LIST}_')),
        ],
        # conversation_timeout=TIMEOUT_DEFAULT
        # fallbacks=[MessageHandler(Filters.regex('^Все'), done)],
        # name="vpn_about",
        # persistent=True,
)
