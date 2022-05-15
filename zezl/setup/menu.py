# coding=utf-8
import setup.autosets as st
from setup.data import LINE
from setup.description import (
    rtag,
    bs, be,
    icon,
    ErrorTextMessage as Error,
    SearchEngines as Engine
)


class Menu:
    """
    Основное /главное меню
    MAIN_MENU

    """
    Icon = "📒"
    Title = f"{Icon} {bs}Основное меню{be}"

    Items = [
        [
            {rtag.VpnMenuItem: st.MAIN_1_VPN_MENU_SHOW},
            {rtag.WatchDogsMenu: st.MAIN_WHATCHDOGS_MENU_SHOW},
        ],
        {rtag.AboutMenuItem: st.MAIN_2_ROUTER_ABOUT}
    ]
    TopLevel = [st.MAIN_MENU, st.VPN_MENU]

    class Vpn:
        """
        Меню VPN
        VPN_MENU

        """

        Icon = "🔐"
        TitleList = f"{Icon} {bs}Меню VPN{be}"
        TitleNoList = TitleList
        # Элементы списка в случае их наличия
        Items = [
            {rtag.DomainListButton: st.VPN_1_INTERFACE_LIST_SHOW},
            {rtag.BackUpButton: st.VPN_2_BACKUP_MENU_SHOW},
            {rtag.TimerMenu: st.TM_1_TIMER_SHOW},
        ]
        # Список кнопок при отсутствии элементов в списке
        ItemsNoList = Items
        # Кнопки возврата
        BackButtons = [
            {rtag.BackToButton: st.VPN_4_BACK_ACTION}
        ]

        class Interface:
            """
            Меню выбора интерфейса для последующего
            отображения белого списка
            INTERFACE_LIST_SHOW
            """
            Icon = "🔁"
            TitleList = f"Доступно несколько {bs}VPN интерфейсов{be}\n" \
                        f"{bs}Выберите{be} пожалуйста один из них."
            TitleNoList = f"Ни одного VPN интерфейса не обнаружено.\n" \
                          f"Создайте хотя бы один и попробуйте снова."

            # Список кнопок при наличии элементов в списке
            CmdButtonsWhenItemList = [
                {rtag.UpdateButton: st.INL_4_HOST_UPDATE_ACTION},
            ]
            # Список кнопок при отсутствии элементов в списке
            CmdButtonsWhenNoItems = []
            # Кнопки возврата
            BackButtons = [
                {rtag.BackToMainMenu: st.INL_2_BACK_TO_MAIN_ACTION},
                {rtag.BackToButton: st.INL_3_BACK_ACTION},
            ]

        class List:
            """
            Меню со списком доменных имен - белый список
            VPN_HOSTS_ACTIONS

            """

            Title = f"📃 {bs}Белый список{be}"

            # Список кнопок при наличии нескольких интерфейсов
            # и когда нет выбранных хостов
            CmdButtonsWhenManyInterfacesNoSelected = [
                # {rtag.RemoveAllButton: WL_3_PURGE_REQUEST},
                {rtag.AddButton: st.WL_2_HOST_ADD_REQUEST},
            ]
            # Список кнопок при наличии нескольких интерфейсов
            # и когда имеются выбранные хосты
            CmdButtonsWhenManyInterfacesSelected = [
                {rtag.InfoButton: st.WL_8_HOST_INFO_SHOW},
                {rtag.RemoveSomeButton: st.WL_3_PURGE_REQUEST},
                {rtag.SaveButton: st.WL_15_SAVE_ACTION},
                {rtag.InterfaceItem: st.WL_7_INTERFACE_CHANGE_REQUEST},
                {rtag.AddButton: st.WL_2_HOST_ADD_REQUEST},
            ]

            # Список кнопок при наличии только одного интерфейса
            # и когда нет выбранных хостов
            CmdButtonsWhenItemsNoSelectedOneInterface = [
                # {rtag.RemoveAllButton: WL_3_PURGE_REQUEST},
                {rtag.AddButton: st.WL_2_HOST_ADD_REQUEST},
            ]
            # Список кнопок при наличии только одного интерфейса
            # и когда имеются выбранные хосты
            CmdButtonsWhenItemsSomeSelectedOneInterface = [
                {rtag.InfoButton: st.WL_8_HOST_INFO_SHOW},
                {rtag.RemoveSomeButton: st.WL_3_PURGE_REQUEST},
                {rtag.SaveButton: st.WL_15_SAVE_ACTION},
                # {rtag.UpdateButton: INL_4_HOST_UPDATE_ACTION},
                {rtag.AddButton: st.WL_2_HOST_ADD_REQUEST},

            ]

            # Список кнопок при отсутствии элементов в списке
            CmdButtonsWhenNoItemList = [
                {rtag.BackUpButton: st.WL_4_BACKUP_LIST_SHOW},
                {rtag.AddButton: st.WL_2_HOST_ADD_REQUEST},
            ]
            # кнопки возврата на верхний уровень меню
            BackButtons = [
                {rtag.BackToMainMenu: st.WL_9_BACK_TO_MAIN_ACTION},
                {rtag.BackToButton: st.WL_10_BACK_ACTION},
            ]
            # Текст заголовка и кнопки для подтверждения удаления всех доменов в списке
            RemoveAllHostsTextRequest = "🔥 Все домены будут удалены!"
            RemoveAllHostsRequestButtons = [
                {rtag.RemoveAllButton: st.WL_5_REMOVE_ACCEPT_ACTION},
                {rtag.RejectButton: st.WL_6_REMOVE_REJECT_ACTION},
            ]
            # Текст заголовка и кнопки при удалении выбранных хостов
            RemoveSelectedHostsTextRequest = "🔥 Домены {}{}{} будут удалены!"
            RemoveSelectedOneHostTextRequest = "🔥 Домен {}{}{} будет удален!"
            RemoveSelectedHostsRequestButtons = [
                {rtag.RemoveSomeButton: st.WL_5_REMOVE_ACCEPT_ACTION},
                {rtag.RejectButton: st.WL_6_REMOVE_REJECT_ACTION},
            ]

            class AddHost:
                AddRequestText = f"Введите доменные имена или имя\n" \
                                 f"Допустимые разделители:\n" \
                                 f"{bs}запятая, точка с запятой, пробел,\n" \
                                 f"новая строка или табуляция{be}."
                NoCorrectedHostsText = "Данные доменов {}{}{} введены некорректно!"
                NoCorrectedOneHostText = "Данные домена {}{}{} введены некорректно!"
                AskToCorrectText = f"{bs}Исправьте данные и повторите ввод{be}."
                NoInterfaceError = "Ошибка: отсутствует интерфейс!"
                HostsAlreadyInList = "Эти домены {}{}{} уже присутствуют в списке!"
                OneHostAlreadyInList = "Этот домен {}{}{} уже присутствует в списке!"
                AskToEnterOtherName = f"{bs}Введите другое имя{be}"

            class InterfaceChange:
                SelectInterfaceOneHostText = f"Выберите {bs}новый интерфейс{be}\n для отобранного домена"
                SelectInterfaceHostsText = f"Выберите {bs}новый интерфейс{be}\nдля отобранных доменов:"

                # кнопки возврата на верхний уровень меню
                BackButtons = [
                    {rtag.BackToMainMenu: st.WL_9_BACK_TO_MAIN_ACTION},
                    {rtag.BackToButton: st.WL_10_BACK_ACTION},
                ]

        class BackUpMenu:
            # Заголовок когда есть в списке архивы
            TitleWhenHaveBackups = f"🗂 {bs}Меню Архивов{be}"
            # Элементы меню когда есть в списке архивы и
            # какой-либо из них выбран
            ItemsWhenHaveBackups = [
                # {rtag.RemoveAllButton: BUP_8_REMOVE_REQUEST},
                {rtag.CreateButton: st.BUP_4_CREATE_NEW_ACTION},
            ]
            # Заголовок когда архивов в списке нет
            TitleWhenHaveNOBackups = f"{bs}Архив пуст.{be}"

            # Список кнопок команд когда архивов в списке нет.
            NoItemsWhenHaveNOBackups = [
                {rtag.CreateButton: st.BUP_4_CREATE_NEW_ACTION},
            ]
            # Клавиши возврата в верхне-уровневые меню
            BackButtons = [
                {rtag.BackToMainMenu: st.BUP_6_BACK_TO_MAIN_ACTION},
                {rtag.BackToButton: st.BUP_7_BACK_ACTION},
            ]
            AskNewBackupName = f"{icon.new} Введите {bs}новое имя архива{be}, без расширения:"
            AskToRemoveAllHeader = f"Подтвердите удаление {bs}всех архивов{be}!"
            RemoveRequestButtons = [
                {rtag.RemoveAllButton: st.BUP_2_REMOVE_ACCEPT_ACTION},
                {rtag.RejectButton: st.BUP_3_REMOVE_REJECT_ACTION},
            ]

            class BackUpContent:
                # Элементы меню когда есть в списке архивы и
                # какой-либо из них выбран
                ItemsWhenHaveHosts = [
                    # {rtag.CreateButton: BCT_1_ADD_TO_WL_ACTION},
                    [
                        {rtag.RemoveBackupButton: st.BCT_2_REMOVE_REQUEST},
                        {rtag.RenameButton: st.BCT_7_RENAME_REQUEST},
                    ]
                    # [{rtag.ExportButton: BCT_10_EXPORT_TO_WL_ACTION}],
                ]
                UpperCommandButtons = [
                    [{rtag.ExportButton: st.BCT_10_EXPORT_TO_WL_ACTION}]
                ]
                # Заголовок когда архивов в списке нет
                TitleWhenHaveNoHosts = f"{bs}Записей нет.{be}"

                # Список кнопок команд когда архивов в списке нет.
                ItemsWhenHaveNoHosts = [
                    [
                        {rtag.RemoveBackupButton: st.BCT_2_REMOVE_REQUEST},
                        {rtag.RenameButton: st.BCT_7_RENAME_REQUEST},
                    ],
                ]
                # Клавиши возврата в верхне-уровневые меню
                BackButtons = [
                    {rtag.BackToMainMenu: st.BCT_8_BACK_TO_MAIN_ACTION},
                    {rtag.BackToButton: st.BCT_9_BACK_ACTION},
                ]

                MessageToRenameError = f"{rtag.ErrorIndicator} Данные введены неверно!\n" \
                                       f"{bs}Повторите ввод{be}!"
                ExportRequestHeader = f"{bs}Выберите интерфейс{be} для экспорта данных"
                BackToContent = [
                    {rtag.BackToButton: st.BCT_11_BACK_INTERFACE_REQUEST},
                ]

                AskToRemoveBackupHeader = "Подтвердите удаление {}{}{}!"
                # Список клавиш на удаление текущего архива
                RemoveRequestButtons = [
                    {rtag.AcceptButton: st.BCT_3_REMOVE_ACCEPT_ACTION},
                    {rtag.RejectButton: st.BCT_4_REMOVE_REJECT_ACTION},
                ]

        class TimerMenu:
            # Основной заголовок при входе в меню
            MainHeader = f"🕜 {bs}Таймер обновлений{be}"
            # Кнопки для исполнения команд в меню,
            # когда таймер установлен
            ItemButtonsWhenTimerOn = [
                {rtag.DeleteButton: st.TM_4_DELETE_REQUEST},
                {rtag.ChangeButton: st.TM_3_CHANGE_REQUEST},
                [{rtag.UpdateAllItem: st.TM_2_UPDATE_ACTION}],
            ]
            # Кнопки для исполнения команд в меню,
            # когда таймер НЕ установлен
            ItemButtonsWhenTimerOff = [
                {rtag.ChangeButton: st.TM_3_CHANGE_REQUEST},
                [{rtag.UpdateAllItem: st.TM_2_UPDATE_ACTION}],
            ]

            # Запрос на удаление таймер
            DeleteRequest = "⛔ Таймер обновления доменов будет удален!"
            DeleteItemButtons = [
                {rtag.AcceptButton: st.TM_5_DELETE_ACCEPT_ACTION},
                {rtag.RejectButton: st.TM_6_REMOVE_REJECT_ACTION},
            ]
            # Клавиши возврата в верхне-уровневые меню
            BackButtons = [
                {rtag.BackToMainMenu: st.TM_7_BACK_TO_MAIN_ACTION},
                {rtag.BackToButton: st.TM_8_BACK_ACTION},
            ]
            TimerSetHeader = '✅ Период обновления доменов каждые'
            TimerNotSetHeader = f'✅ Период обновления доменов {bs}не установлен{be}!'

            TimerEnterPeriodHeader = f"📲 Введите интервал обновления данных:\n" \
                                     f"Формат {bs}XX[mhdwM]{be}, " \
                                     f"где {bs}ХХ{be} - интервал времени\n" \
                                     f"{bs}m{be}-минуты, " \
                                     f"{bs}h{be}-часы, " \
                                     f"{bs}d{be}-дни, " \
                                     f"{bs}w{be}-недели, " \
                                     f"{bs}M{be}-месяц"
            NoDataEntered = f"{Error.INDICATOR} Текст отсутствует.\n" \
                            f"{bs}Повторите ввод{be}!"

    class WatchdogsMenu:
        """
        Меню Сторожей
        WATCHDOGS_MENU

        """

        TitleList = f"👀 {bs}Меню Сторожей{be}"
        TitleNoList = TitleList
        # Элементы списка в случае их наличия
        Items = [
            {rtag.ErrorWDogsButton: st.WD_ERRORS_ALARM_MENU},
            # {rtag.ChangeIPWDogsButton: st.WD_CHANGE_IP_ALERT_MENU},
            # {rtag.CallWDogsButton: st.WD_CALLS_ALARM_MENU},
            # {rtag.WiFiWDogsButton: st.WD_WIFI_CONNECT_ALARM_MENU},
            # {rtag.InternetWDogsButton: st.WD_INTERNET_ALARM_MENU},
            {rtag.SitesWDogsButton: st.WD_SITE_WATCHER_MENU}
        ]
        # Список кнопок при отсутствии элементов в списке
        ItemsNoList = Items
        # Кнопки возврата
        BackButtons = [
            {rtag.BackToButton: st.WD_BACK_ACTION}
        ]

        class ErrorsMenu:
            TitleList = f"🔥 {bs}Сторож системных ошибок{be}\n" \
                        f"{LINE}" \
                        f"Режим: {bs}@1{be}\n" \
                        f"Интервал: {bs}@2{be}\n" \
                        f"Сервис: {bs}@3{be}\n" \
                        f"{LINE}"

            # Элементы списка в случае их наличия
            CmdItems = [
                {rtag.IntervalButton: st.WD_ERR_INTERVAL_REQUEST},
                {rtag.SearchEngine: st.WD_ERR_SEARCH_ENGINE_REQUEST},
            ]
            # Кнопки возврата
            BackButtons = [
                {rtag.BackToMainMenu: st.WD_ERR_MAIN_MENU_BACK_ACTION},
                {rtag.BackToButton: st.WD_ERR_STEP_BACK_ACTION},
            ]

            class EngineSearchMenu:
                Title = f"🌏 Выберите {bs}сервис для поиска ошибок{be}:"

                ItemsList = [
                    {Engine.yandex: 'https://yandex.ru/search/?text'},
                    {Engine.google: 'https://www.google.com/search?q'},
                    {Engine.yahoo: 'https://search.yahoo.com/search?p'},
                    {Engine.ecosia: 'https://www.ecosia.org/search?q'}
                ]
                # Кнопки возврата
                BackButtons = [
                    {rtag.BackToButton: st.WD_ERR_BACK_TO_ERR_PAGE_ACTION},
                ]

            class IntervalMenu:
                Title = (f"⏱ Выберите {bs}интервал опроса{be}\n"
                         f"отслеживания системных ошибок:")

                ItemsList = [
                    {"1 сек.": '1s'},
                    {"10 сек.": '10s'},

                    {"2 сек.": '2s'},
                    {"15 сек.": '15s'},

                    {"3 сек.": '3s'},
                    {"30 сек.": '30s'},

                    {"5 сек.": '5s'},
                    {"60 сек.": '60s'},
                ]
                # Кнопки возврата
                BackButtons = [
                    {rtag.BackToButton: st.WD_ERR_BACK_TO_ERR_PAGE_ACTION},
                ]

        class SitesMenu:
            Title = f"🌐 {bs}Сторож изменений на сайтах{be}\n" \
                    f"{LINE}" \
                    f"{bs}Всего ссылок{be}: @1 шт.\n" \
                    f"{LINE}"

            TitleNoItems = f"🌐 {bs}Сторож изменений на сайтах{be}\n" \
                           f"{LINE}" \
                           f"Список ссылок пуст."
            # Элементы списка в случае их наличия
            CmdItems = [
                {rtag.RemoveAllButton: st.WD_SITE_LINK_DEL_ALL_REQUEST},
                {rtag.AddButton: st.WD_SITE_LINK_ADD_REQUEST},
            ]
            CmdNoItems = [
                {rtag.AddButton: st.WD_SITE_LINK_ADD_REQUEST},
            ]
            # Кнопки возврата
            BackButtons = [
                {rtag.BackToMainMenu: st.WD_SITE_MAIN_MENU_BACK_ACTION},
                {rtag.BackToButton: st.WD_SITE_STEP_BACK_ACTION},
            ]
            RemoveAllButtons = [
                {rtag.AcceptButton: st.WD_SITE_LINK_DEL_ALL_ACCEPT},
                {rtag.RejectButton: st.WD_SITE_LINK_DEL_ALL_REJECT}
            ]

            class AddLinkMenu:
                AddNameRequestText = f"{bs}Введите название{be} для отслеживаемого сайта."
                AddLinkRequestText = f"{bs}Введите ссылку{be} на отслеживаемый сайт"

            class EditLinkMenu:
                Title = f"{bs}Отслеживаем{be}:\n" \
                        f"{LINE}" \
                        f"Название: {bs}@1{be}\n" \
                        f"@2\n" \
                        f"Состояние: {bs}@3{be}\n" \
                        f"Период проверки: {bs}@4{be}\n" \
                        f"Крайняя проверка: {bs}@5{be}\n" \
                        f"Крайнее обновление: {bs}@6{be}\n" \
                        f"{LINE}"

                CmdItemsList = [
                    {rtag.DeleteButton: st.WD_SITE_EDIT_LINK_DEL_REQUEST},
                    {rtag.PeriodButton: st.WD_SITE_EDIT_LINK_INTERVAL_REQUEST},
                ]
                BackButtons = [
                    {rtag.BackToMainMenu: st.WD_SITE_EDIT_LINK_MAIN_MENU_BACK_ACTION},
                    {rtag.BackToButton: st.WD_SITE_EDIT_LINK_STEP_BACK_ACTION},
                ]
                RemoveLinkButtons = [
                    {rtag.AcceptButton: st.WD_SITE_EDIT_LINK_DEL_ACCEPT},
                    {rtag.RejectButton: st.WD_SITE_EDIT_LINK_DEL_REJECT}
                ]


                class IntervalMenu:
                    Title = f"⏱ Выберите {bs}интервал опроса ресурса{be}"

                    ItemsList = [
                        {"15 мин.": '15m'},
                        {"3 дн.": '3d'},

                        {"30 мин.": '30m'},
                        {"5 дн.": '5d'},

                        {"60 мин.": '60m'},
                        {"15 дн.": '15d'},

                        {"5 час.": '5h'},
                        {"25 дн.": '25d'},

                        {"10 час.": '10h'},
                        {"1 мес.": '1M'},

                        {"1 дн.": '1d'},
                        {"2 мес.": '2M'},
                    ]
                    # Кнопки возврата
                    BackButtons = [
                        {rtag.BackToButton: st.WD_SITE_EDIT_INTERVAL_STEP_BACK_ACTION},
                    ]

    class RouterMenu:
        icon = "🚀 "
        Title = f"{icon} {bs}Меню роутера{be}"

        DevicesItem = "🍳 Устройства"
        AboutModelItem = "Об устройстве"

        Items = [DevicesItem, AboutModelItem]

        class DevicesMenu:
            icon = "🐝"
            Title = f"{icon} {bs}Устройства в сети{be}"

            DevicesItem = "Ок"

            Items = [DevicesItem]


engineList = Menu.WatchdogsMenu.ErrorsMenu.EngineSearchMenu.ItemsList
