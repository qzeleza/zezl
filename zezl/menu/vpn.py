# coding=utf-8

from telegram import Update
from telegram.ext import CallbackContext

from libraries.main import tools as tools, dialog, vpn as vpn_lib
from libraries.main.decorators import set_menu_level
from libraries.watchdogs.jobs import run_wdogs_at_start
from logs.logger import zlog
from libraries.main.dialog import exit_from_text_mode
from setup import autosets as st
from setup.autosets import (NET, )
from setup.data import DEMON_NAME, INTERFACE_TYPES, LINE, TIMER_FORMAT
from setup.description import (
    bs, be,
    etag, rtag,
    ErrorTextMessage as Error, icon
)
from setup.menu import Menu


class VpnMenuAction:
    """
    Класс предназначен для генерации и
    обработки действий страниц VPN меню

    """

    def __init__(self):
        self.timer_update = None
        self.selected_group = None
        self.backup_content_list = None
        self.backup_name = None
        self.backup_details = {}
        self.hosts_list = []
        self.interfaces_dict = {}
        self.interface_names = {}
        self.message_id = -1
        self.host = ''
        self.interface = ''
        self.call_zone = -1
        self.selected_host_list = []
        self.hosts_details = {}
        self.selected_backup_host_list = []

    def _init(self) -> None:
        """
        Функция стирает данные, которые должны обнуляться
        при каждом новом выборе интерфейса.

        :return: None
        """

        self.interfaces_dict = {}
        self.hosts_list = []
        self.selected_host_list = []
        self.hosts_details = {}

    # --------------------------------------------------------------------------------------------------
    #
    #       Уровень MAIN_MENU - Основное меню
    #
    # --------------------------------------------------------------------------------------------------
    @run_wdogs_at_start
    @set_menu_level(menu_level=st.VPN_MENU)
    def menu_vpn_show(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает "плавающее" (inline) VPN меню

        MAIN_MENU: LTOP_VPN_MENU_SHOW

        :param update:
        :param context:

        :return: код уровня вложенности меню
        """
        callback, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                          reply_text=Menu.Vpn.TitleList,
                                                          list_content=[],
                                                          cmd_buttons=Menu.Vpn.Items,
                                                          back_buttons=Menu.Vpn.BackButtons,
                                                          menu_level=st.VPN_MENU,
                                                          update=update, context=context)
        return callback

    # --------------------------------------------------------------------------------------------------
    #
    #       Уровень INTERFACE_LIST_SHOW - меню выбора интерфейса в VPN меню
    #
    # --------------------------------------------------------------------------------------------------
    @run_wdogs_at_start
    @set_menu_level(menu_level=st.VPN_INTERFACE_LIST_SHOW)
    def vpn_hosts_interface_list_show(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает меню со списком доступных интерфейсов
        как подключенных в данный момент, так и не подключенных

        INTERFACE_LIST_SHOW: L1_INTERFACE_LIST_SHOW

        :param update:
        :param context:

        :return: код уровня вложенности меню
        """

        # обнуляем списки данных
        self._init()
        # Устанавливаем флаг произведенного действия,
        # по нему определяем необходимость обновления данных (если True)
        context.user_data[etag.action] = False

        buttons_list, cmd_buttons = [], []
        # Получаем информацию о доступных интерфейсах
        inface_dict, inface_butt_list = vpn_lib.mark_interface_online()

        if inface_butt_list:
            # Если список имеется, то формируем словарь
            # для отображения кнопок и заголовок меню
            header = Menu.Vpn.Interface.TitleList
            # Формируем динамические кнопки с именами интерфейсов
            buttons_list = [{name: code} for name, code in zip(inface_butt_list, list(inface_dict.keys()))]
            # заполняем список интерфейсами
            self.interfaces_dict = inface_dict
            # cmd_buttons = dt.Menu.Vpn.Interface.CmdButtonsWhenItemList
        else:
            # если интерфейсов нет, то формируем также заголовок
            header = Menu.Vpn.Interface.TitleNoList

        # Вызываем функцию формирования и отображения меню
        callback, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                          reply_text=header,
                                                          list_content=buttons_list,
                                                          cmd_buttons=cmd_buttons,
                                                          back_buttons=Menu.Vpn.Interface.BackButtons,
                                                          menu_level=st.VPN_INTERFACE_LIST_SHOW,
                                                          update=update, context=context)
        return callback

    # --------------------------------------------------------------------------------------------------
    #
    #       Уровень VPN_HOSTS_ACTIONS - меню белого списка доменов
    #
    # --------------------------------------------------------------------------------------------------
    def _generate_auto_button(self, dict_hosts_details: dict) -> dict:
        """
        Функция обрабатывает общее состояние флага auto для выбранных кнопок
        и формирует общий код для кнопки переключающей состояние флага.
        :param: dict_hosts_details - словарь с детальной информацией по всем хостам.
        :return: код клавиши в виде [{host_auto: auto_code}]
        """

        # формируем общее состояние всех выбранных кнопок
        # состояние auto путем сложения их состояний
        auto = tools.mult([[el[etag.auto] for el in details][0] for host, details in dict_hosts_details.items()
                           if host in self.selected_host_list], False)
        # формируем код для кнопки auto
        auto_code = st.WL_11_AUTO_SWITCH_ON_ACTION if auto else st.WL_12_AUTO_SWITCH_OFF_ACTION
        # формируем текст для кнопки auto
        host_auto = rtag.SwitchOnItem if auto else rtag.SwitchOffItem
        return {host_auto: auto_code}

    @set_menu_level(menu_level=st.VPN_HOSTS_ACTIONS)
    def vpn_hosts_white_list_show(self, update: Update, context: CallbackContext) -> int:
        """
        Функция для отображения списка доступных доменов для выбранного интерфейса
        вызывается при нажатии на один из интерфейсов по шаблону в rep_interface_list()

        VPN_HOSTS_ACTIONS: rep_interface_list()

        :param update:
        :param context:

        :return: код уровня вложенности меню
        """

        # список динамических клавиш с доступными интерфейсами
        hosts_buttons, cmd_buttons = [], []

        # фиксируем базовый класс для краткости кода
        base_class = Menu.Vpn.List
        # Получаем данные о нажатой кнопке - в данному случае получаем название интерфейса
        data = update.callback_query.data if not context.user_data[
            etag.action] and update.callback_query else self.interface
        # в случае, если была нажата кнопка какого либо интерфейса,
        # то фиксируем интерфейс для корректной фильтрации хостов
        if tools.has_inside(INTERFACE_TYPES, data):
            # фиксируем интерфейс
            self.interface = data

        # принудительно обновляем данные о доменных именах,
        # если завершила свое действие какая-либо кнопка
        if not context.user_data[etag.action]:
            self.hosts_details = vpn_lib.get_hosts_details(interfaces=[self.interface])
        else:
            # Если кнопка команды не была нажата и self.hosts_details не содержит элементов,
            # то инициализируем ее - получаем детальную информацию о доменах по заданному интерфейсу,
            if not self.hosts_details:
                self.hosts_details = vpn_lib.get_hosts_details(selected_hosts=self.hosts_list,
                                                               interfaces=[self.interface])
        # получаем список доменов для выбранного интерфейса и фиксируем его
        self.hosts_list = list(self.hosts_details.keys())

        # проверка на наличие доменных имен в списке
        if self.hosts_list:
            # генерируем динамические клавиши с названием доменов и такими же кодами возврата
            for host in sorted(self.hosts_list):
                # проверяем, есть ли домен на выбранном интерфейсе
                # if self.interface in [inf['interface'] for inf in self.hosts_details[host]]:
                # формируем на клавише состояние флага auto
                icon_select = icon.select if host in self.selected_host_list else icon.unselect
                icon_auto = icon.ok if self.hosts_details[host][0][etag.auto] else icon.stop
                # icon_auto = etag.on if dict_hosts_details[host][etag.auto] else etag.off
                ip_count = len(self.hosts_details[host][0][etag.ip])

                # Генерируем текст на кнопке с надписью ДОМЕНА
                button_name = f"{icon_select} {host} [{ip_count}] {icon_auto}"
                hosts_buttons.append({button_name: host})

            # генерируем клавишу ВЫБРАТЬ ВСЕ или ОТМЕНИТЬ ВСЕ
            select_all_button = [[{rtag.UnSelectAll: st.WL_14_UNSELECT_ALL}]] if self.selected_host_list \
                else [[{rtag.SelectAll: st.WL_13_SELECT_ALL}]]

            # генерируем клавиши КОМАНД в зависимости от числа доступных интерфейсов
            if len(self.interfaces_dict) == 1:
                # доступен ТОЛЬКО ОДИН интерфейс
                cmd_buttons = base_class.CmdButtonsWhenItemsSomeSelectedOneInterface if self.selected_host_list \
                    else base_class.CmdButtonsWhenItemsNoSelectedOneInterface
            else:
                # доступно НЕСКОЛЬКО интерфейсов
                cmd_buttons = base_class.CmdButtonsWhenManyInterfacesSelected if self.selected_host_list \
                    else base_class.CmdButtonsWhenManyInterfacesNoSelected

            # есть ли выбранные хосты?
            if self.selected_host_list:
                # если есть, то сообщаем о числе хостов всего и о числе выбранных хостов
                selected_hosts_mess = f"{bs}{len(self.selected_host_list)}{be}/{bs}{len(self.hosts_list)}{be} шт.\n"
                # генерируем клавишу "Включить" флаг auto у выбранных хостов
                auto_button = self._generate_auto_button(dict_hosts_details=self.hosts_details)
                # клавишу "ВЫБРАТЬ ВСЕ"/"ОТМЕНИТЬ ВСЕ" и клавишу включения "AUTO"
                # ставим на первом месте после списка хостов
                cmd_buttons = [auto_button] + cmd_buttons
            else:
                # если не выбрано ни одного хоста - сообщаем о числе хостов всего
                selected_hosts_mess = f"{bs}{len(self.hosts_list)}{be} шт.\n"

            # клавишу ВЫБРАТЬ ВСЕ или ОТМЕНИТЬ ВСЕ ставим на первом месте после списка хостов
            cmd_buttons = select_all_button + cmd_buttons

            # если список есть, то выводим заголовок с числом хостов и названием интерфейса.
            header = f'{Menu.Vpn.List.Title}\n' \
                     f'{LINE}' \
                     f'{rtag.interface} {bs}{self.interfaces_dict[self.interface]}{be}\n' \
                     f'{rtag.inface_type} {bs}{self.interface}{be}\n' \
                     f'{rtag.count} {selected_hosts_mess}' \
                     f'{LINE}'
        else:
            # если нет доменов с выбранным интерфейсом
            header = f"{base_class.Title} для {bs}{self.interfaces_dict[self.interface]}{be} пуст."
            # клавиши управления списком
            cmd_buttons = base_class.CmdButtonsWhenNoItemList

        # Вызываем функцию формирования и отображения меню
        callback, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                          reply_text=header,
                                                          list_content=hosts_buttons,
                                                          cmd_buttons=cmd_buttons,
                                                          back_buttons=Menu.Vpn.List.BackButtons,
                                                          menu_level=st.VPN_HOSTS_ACTIONS,
                                                          update=update, context=context)

        return callback

    def vpn_hosts_press_on_select_all_button_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция занимается обработкой нажатий клавиши "Выбрать все" и "Отменить выбор"

        переход из VPN_HOSTS_ACTIONS: rep_select_all() в VPN_MENU_HOST_DETAIL

        :param update:
        :param context:
        :return:
        """
        if update.callback_query.data == st.WL_13_SELECT_ALL:
            # Добавляем все домены в список выбранных
            _ = [self.selected_host_list.append(hs) for hs in self.hosts_list if hs not in self.selected_host_list]
        elif update.callback_query.data == st.WL_14_UNSELECT_ALL:
            self.selected_host_list = []

        # Возвращаемся в обработку группы
        callback = self.vpn_hosts_white_list_show(update=update, context=context)

        return callback

    def vpn_hosts_press_on_host_button_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция занимается обработкой нажатий клавиш названий сайтов - их одиночным выбором в списке

        переход из VPN_HOSTS_ACTIONS: rep_host() в VPN_MENU_HOST_DETAIL

        :param update:
        :param context:
        :return:
        """
        # Получаем наименование выбранного домена
        host = update.callback_query.data
        # проверяем что нажали именно на кнопку выбора доменного имени
        if tools.get_url_only(host):
            if host in self.selected_host_list:
                # если хост есть уже в списке отобранных хостов,
                # то удаляем его из списка
                self.selected_host_list.remove(host)
            else:
                # если хоста нет в списке отобранных хостов,
                # то добавляем его в список
                self.selected_host_list.append(host)

        # Возвращаемся в обработку группы
        callback = self.vpn_hosts_white_list_show(update=update, context=context)

        return callback

    def vpn_hosts_preparing_action(self, update: Update, _: CallbackContext, make_count: bool = True) -> (
            list, int):
        """
        СЛУЖЕБНАЯ функция - повторяемый блок кода в функциях обработки данных
        c суффиксом - action. Функция обрабатывает данные как через меню,
        так и данные, которые были введены при помощи команды

        :param _:
        :param make_count: разрешает или запрещает операцию по подсчету IP адресов.
                           По умолчанию True - разрешает.
        :param update:
        :return: hosts_list - список хостов для дальнейшей обработки
                 count_ip - количество ip в списке хостов, если make_count=True,
                 в противном случае 0 (ноль)
        """

        # заменяем название кода, который был при нажатии
        # присвоен update.callback_query.setup на имя домена
        update.callback_query.data = self.host
        # Данный кусок кода отвечает за обработку команд введенных пользователем в ручную.
        if update.message and etag.cmd.slash in update.message.text:
            # если в строке передана команда на удаление домена (обнаружили слеш),
            # то в этом случае просто удаляем домен без ожидания и возвращаем результат
            hosts_list = tools.get_domain_list(update.message.text.lower())
            hosts_list = [el for el in hosts_list if etag.cmd.slash not in el]
        else:
            # обработка удаления, если нажата кнопка удаления
            hosts_list = self.selected_host_list
        #  получаем число всех ip в белом списке, для того,
        #  чтобы понять, нужно ли запускать задачу в фоне или нет.
        count_ip = vpn_lib.count_hosts_ip(hosts_list=hosts_list, interfaces=self.interface) if make_count else 0
        return hosts_list, count_ip

    @set_menu_level(menu_level=st.VPN_HOSTS_ACTIONS)
    def vpn_hosts_remove_request(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает запрос на удаление всех доменных имен из белого списка

        VPN_HOSTS_ACTIONS: L113_WL_PURGE_REQUEST

        :param update:
        :param context:
        :return:
        """

        base_class = Menu.Vpn.List
        # в зависимости от выбранного режима "Удаляем все" или "Удаляем выбранные"

        if self.selected_host_list:
            # находимся в режиме "Удаляем выбранные"
            # формируем текст заголовка для меню
            if len(self.selected_host_list) == 1:
                request = base_class.RemoveSelectedOneHostTextRequest.format(bs, "".join(self.selected_host_list), be)
            else:
                request = base_class.RemoveSelectedHostsTextRequest.format(bs, ", ".join(self.selected_host_list), be)
            # формируем клавиши запроса на удаление
            request_buttons = base_class.RemoveSelectedHostsRequestButtons
        else:
            # находимся в режиме "Удаляем выбранные"
            request = base_class.RemoveAllHostsTextRequest
            # формируем клавиши запроса на удаление
            request_buttons = base_class.RemoveAllHostsRequestButtons

        # выводим диалог об удалении
        callback, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                          reply_text=request,
                                                          list_content=[],
                                                          cmd_buttons=request_buttons,
                                                          back_buttons=[],
                                                          menu_level=st.VPN_HOSTS_ACTIONS,
                                                          update=update, context=context)
        return callback

    @run_wdogs_at_start
    def vpn_hosts_remove_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает результат удаления всех доменов в БС

        VPN_HOSTS_ACTIONS: L115_PURGE_ACCEPT_ACTION

        :param update:
        :param context:
        :return:
        """

        #  получаем список выбранных хостов и число ip в этом списке, для того,
        #  чтобы понять, нужно ли запускать задачу в фоне или нет.
        hosts_list, count = self.vpn_hosts_preparing_action(update=update, _=context)
        func_start_args = dict(hosts=hosts_list, interfaces=[self.interface], result_ok=True)
        # очищаем список выбранных хостов
        self.selected_host_list = []
        return dialog.run_background(func_start=vpn_lib.remove_hosts_list,
                                     func_start_args=func_start_args,
                                     func_finish=self.vpn_hosts_white_list_show,
                                     menu_level=st.VPN_HOSTS_ACTIONS,
                                     update=update, context=context,
                                     records_to_processing=count)

    @staticmethod
    @set_menu_level(menu_level=st.VPN_HOSTS_ACTIONS)
    def vpn_hosts_add_request(update: Update, _: CallbackContext) -> int:
        """
        Функция отображает запрос о вводе новых доменных имен через строку ввода

        VPN_HOSTS_ACTIONS: L112_WL_HOST_ADD_REQUEST

        :param update:
        :param _:
        :return:
        """
        # запрос на добавление домена
        reply_text = Menu.Vpn.List.AddHost.AddRequestText
        # удаляем предыдущее сообщение
        update.callback_query.delete_message()
        update.callback_query.answer()
        # ожидаем ввода
        update.callback_query.message.reply_text(reply_text)

        # фиксируем и возвращаем текущий уровень меню
        return st.VPN_HOSTS_ACTIONS

    @run_wdogs_at_start
    def vpn_hosts_add_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция реализует отображение результата после добавления хоста в БС

        переход из VPN_HOSTS_ACTIONS в VPN_MENU_HOST_DETAIL

        :param update:
        :param context:
        :return:
        """
        #  если ввели слова по выходу из режима ввода
        callback = exit_from_text_mode(update.message.text, self.vpn_hosts_white_list_show, update, context)
        if callback:
            return callback

        def add_new_domains(domains: list, in_face: str) -> int:
            """
            Считаем число записей для обработки, чтобы понять,
            как лучше обработать задачу: в фоне или обычным путем.

            :param domains: список доменов.
            :param in_face: интерфейс
            :return:
            """

            ip_count = vpn_lib.count_hosts_ip(hosts_list=domains, interfaces=[self.interface], method=NET)
            # запускаем в фоне задачу на добавление доменов
            func_start_args = dict(host_list=domains, interfaces=[in_face])
            # выводим сообщение с просьбой подождать,
            # при этом задержку даем на каждый ip по 3 сек.
            dialog.alert(mess=rtag.PleaseWait,
                         in_cmd_line=True,
                         delay_time=ip_count * 3,
                         update=update, context=context)
            # запускаем процедуру добавления в фоне
            return dialog.run_background(func_start=vpn_lib.load_hosts_to_white_list,
                                         func_start_args=func_start_args,
                                         func_finish=self.vpn_hosts_white_list_show,
                                         menu_level=st.VPN_HOSTS_ACTIONS,
                                         records_to_processing=ip_count,
                                         update=update, context=context)

        callback = st.VPN_HOST_DETAIL
        # получаем и обрабатываем введенные данные
        # hosts = libraries.get_domain_list(source=update.message.mess.lower(), is_uniq=True)
        domain_list = tools.get_domain_list(update.message.text.lower(), uniq=True)
        # удаляем из списка команду со слешем, если была задана команда не из меню, а из командной строки
        hosts_list = [el for el in domain_list if etag.cmd.slash not in el]

        # если списки НЕ совпадают по длине,
        # то была введена команда /add не из меню, а из командной строки
        if len(domain_list) != len(hosts_list):
            # установим время задержки удаления сообщений
            delay_time = 110
            # в этом случае удаляем интерфейс из списка хостов
            _ = [hosts_list.pop(ind) for ind, el in enumerate(hosts_list)
                 if tools.has_inside(checking_list=INTERFACE_TYPES, source=el)]
            scan_list = update.message.text.split()
            interface = [inf for inf in scan_list if tools.has_inside(checking_list=INTERFACE_TYPES, source=inf)]

            # если словарь системных интерфейсов не заполнен
            if not self.interfaces_dict:
                # то получаем информацию от системы о них
                self.interfaces_dict = vpn_lib.get_filtered_interfaces_details(
                        details=[etag.description, etag.connected])

            # Проверяем на число существующих интерфейсов,
            # если их всего один, то его можно не задавать в строке
            if len(self.interfaces_dict) == 1:
                # задаем номер интерфейса, который по умолчанию
                interface = "".join(self.interfaces_dict)
                # проверяем на правильность ввода интерфейса
                if interface not in self.interfaces_dict:
                    # если число интерфейсов было введено больше одного
                    mess = f"Введенного интерфейса {bs}{interface}{be} не существует!\n" \
                           f"Проверьте его написание - регистр учитывается!"
                    # то выдаем сообщение об ошибке
                    dialog.alert(mess=mess, update=update, context=context, delay_time=delay_time)
                    return callback
                else:
                    self.interface = interface
            else:
                # проверяем на наличие интерфейсов
                if interface:
                    # если интерфейсов в системе несколько
                    # и был задан хотя бы один из них в командной строке
                    if len(interface) > 1:
                        # если число интерфейсов было введено больше одного
                        mess = "При добавлении необходимо указать только ОДИН интерфейс"
                        # то выдаем сообщение об ошибке
                        dialog.alert(mess=mess, update=update, context=context, delay_time=delay_time)
                        return callback
                    else:
                        # если интерфейс был задан только один,
                        # то устанавливаем его для продолжения операции
                        self.interface = "".join(interface)
                else:
                    # если интерфейс не был задан в командной строке
                    mess = "В системе присутствует больше одного интерфейса\n" \
                           "Конкретизируйте интерфейс при добавлении домена.\n" \
                           "Введите один из перечисленных ниже:\n" \
                           f"{bs}{','.join(self.interfaces_dict)}{be}"
                    # то выдаем сообщение об ошибке
                    dialog.alert(mess=mess, update=update, context=context, delay_time=delay_time)
                    return callback

        # составляем два списка с корректно введенными доменами и с некорректно введенными доменами
        corrected = [h for h in hosts_list if etag.cmd.slash not in h and etag.dot in h and tools.is_host_valid(h)]
        not_corrected = [h for h in hosts_list if etag.cmd.slash not in h and h not in corrected]

        # сокращаем код
        base_class = Menu.Vpn.List.AddHost

        if not_corrected:
            # генерируем сообщение для всех некорректно введенных доменов
            # в зависимости от наличия множественного числа
            mess = base_class.NoCorrectedHostsText.format(bs, ', '.join(not_corrected), be) if len(not_corrected) > 1 \
                else base_class.NoCorrectedOneHostText.format(bs, ', '.join(not_corrected), be)
            _text = base_class.AskToCorrectText.format(bs, be)
            mess = f"{mess}\n{_text}"
            # выводим сообщение о некорректно введенных доменах
            dialog.alert(mess=mess, update=update, context=context)

        if corrected:
            # обрабатываем корректно введенные доменные имена
            current_hosts_list = self.hosts_list if self.hosts_list else vpn_lib.get_hosts(interfaces=[self.interface])
            # формируем список доменов, которые не повторяются в БС
            not_repeated = [h for h in corrected if h not in current_hosts_list]
            if not_repeated:
                # обрабатываем домены, которые не повторяются в БС
                if self.interface:
                    # добавляем доменные имена
                    callback = add_new_domains(not_repeated, self.interface)
                else:
                    # Интерфейс должен быть задан, в противном случае это ошибка в коде
                    zlog.error(base_class.NoInterfaceError)
                    raise Exception(base_class.NoInterfaceError)
            else:
                repeated = ", ".join([h for h in corrected if h in current_hosts_list])
                #  Формируем сообщение о повторяющихся доменных именах в списке
                if len(repeated) > 1:
                    #  множественное число
                    mess = base_class.HostsAlreadyInList.format(bs, repeated, be)
                    mess = f"{mess}\n{base_class.AskToCorrectText}"
                else:
                    #  единственное число
                    mess = base_class.OneHostAlreadyInList.format(bs, repeated, be)
                    mess = f"{mess}\n{base_class.AskToEnterOtherName}"
                #  Выводим сообщение
                dialog.alert(mess=mess, update=update, context=context)

        return callback

    def vpn_hosts_save_to_backup_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция сохраняет данные в файл архива с именем даты и времени
        пример названия файла архива 01-03-22_11-00.vpu

        :param update:
        :param context:
        :return:
        """

        #  получаем список выбранных хостов и число ip в этом списке, для того,
        #  чтобы понять, нужно ли запускать задачу в фоне или нет.
        hosts_list, count = self.vpn_hosts_preparing_action(update=update, _=context, make_count=False)
        func_start_args = dict(domains=hosts_list, interface=[self.interface])

        return dialog.run_background(func_start=vpn_lib.create_backup, func_start_args=func_start_args,
                                     records_to_processing=count, func_finish=self.vpn_hosts_white_list_show,
                                     menu_level=st.VPN_HOSTS_ACTIONS,
                                     update=update, context=context)

    def vpn_hosts_details_show_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция вызывается для отображения подробной информации о выбранных хостах

        VPN_MENU_HOST: WL_8_HOST_INFO_SHOW

        :param update:
        :param context:
        :return:
        """
        dict_hosts_details = {}
        context.user_data[etag.info] = True

        #  получаем список выбранных хостов и число ip в этом списке, для того,
        #  чтобы понять, нужно ли запускать задачу в фоне или нет.
        hosts_selected, ip_count = self.vpn_hosts_preparing_action(update=update, _=context)
        # формируем для отображения флаг auto для кнопки и для заголовка
        if hosts_selected == self.selected_host_list:
            # если не было вызова из командной строки, то оставляем данные
            _ = [dict_hosts_details.update({k: v}) for k, v in self.hosts_details.items() if k in hosts_selected]
        else:
            #  если был вызов из командной строки, то обновляем данные
            dict_hosts_details = vpn_lib.get_hosts_details(selected_hosts=self.selected_host_list,
                                                           interfaces=[self.interface])

        # удаляем текущее меню
        update.callback_query.delete_message()

        # временной интервал, после которого сообщение будет удалено = 1 минута
        delay_time = 60

        # формируем детальную информацию по каждому выбранному хосту
        for host in dict_hosts_details:
            auto = icon.ok if dict_hosts_details[host][0][etag.auto] else icon.stop
            ip_list = '\n'.join(dict_hosts_details[host][0][etag.ip])
            info = f"{auto} {bs}{host}{be} [{bs}{len(dict_hosts_details[host][0][etag.ip])} IP{be}]\n" \
                   f"{LINE}" \
                   f"{ip_list}\n" \
                   f"{LINE}" \
                   f"{rtag.interface} {bs}{self.interfaces_dict[self.interface]}{be}\n" \
                   f"{rtag.inface_type} {bs}{self.interface}{be}\n"
            # отправляем сообщение с последующим удалением через 1 минуту
            dialog.alert(mess=info, update=update, context=context, delay_time=delay_time, in_cmd_line=True)

        # Отображаем снова предыдущее меню
        callback = self.vpn_hosts_white_list_show(update=update, context=context)

        return callback

    # --------------------------------------------------------------------------------------------------
    #
    #       Уровень VPN_MENU_HOST_DETAIL - меню одного или нескольких выбранных доменов
    #
    # --------------------------------------------------------------------------------------------------

    def vpn_hosts_switch_auto_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция обрабатывает нажатие на кнопку "Включить AUTO" - отключить/включить

        :param update:
        :param context:
        :return:
        """
        selected_hosts_details = {}
        #  получаем список выбранных хостов и число ip в этом списке, для того,
        #  чтобы понять, нужно ли запускать задачу в фоне или нет.
        host_list, count = self.vpn_hosts_preparing_action(update=update, _=context)
        # auto_mode = None  # False if update.callback_query.setup == dt.L1112_AUTO_SWITCH_ON_ACTION else True

        # добавляем элементы для обработки для ВСЕХ имеющихся доменов и ВСЕХ интерфейсов
        # _ = [selected_hosts_details.update({k: v}) for k, v in self.hosts_details.items()]
        # func_start_args = dict(hosts_details=host_list, interface=None, auto_mode=None)

        # обновляем список ТОЛЬКО ОТОБРАННЫХ хостов выбранного интерфейса
        _ = [selected_hosts_details.update({k: v}) for k, v in self.hosts_details.items() if k in host_list]
        func_start_args = dict(hosts_details=selected_hosts_details, interfaces=[self.interface], auto_mode=None)
        #
        callback = dialog.run_background(func_start=vpn_lib.switch_host_auto_state,
                                         func_finish=self.vpn_hosts_white_list_show,
                                         menu_level=st.VPN_HOSTS_ACTIONS,
                                         update=update, context=context, records_to_processing=count,
                                         func_start_args=func_start_args)
        return callback

    @set_menu_level(menu_level=st.VPN_HOSTS_ACTIONS)
    def vpn_hosts_change_interface_request(self, update: Update, context: CallbackContext) -> int:
        """
        Функция выводит список доступных интерфейсов для выбора

        :param update:
        :param context:
        :return:
        """
        #  получаем список выбранных хостов
        hosts_list = self.selected_host_list  # if self.selected_host_list else [self.host]
        # получаем список доступных интерфейсов
        inface_dict, inface_butt_list = vpn_lib.mark_interface_online()
        if not inface_butt_list:
            error_text = "Ошибка в переданных аргументах!\n" \
                         "Список доступных интерфейсов не должен быть пустым!"
            zlog.error(f"{error_text}\n{inface_dict}")
            raise Exception(error_text)

        # Формируем динамические кнопки с именами интерфейсов
        # и удаляем интерфейс к которому сейчас принадлежат домены.
        buttons_list = [{name: code} for name, code in zip(inface_butt_list, list(inface_dict.keys()))
                        if self.interface not in code]
        # базовый клас для сокращения кода
        base_class = Menu.Vpn.List.InterfaceChange
        # Формируем заголовок в зависимости от числа обрабатываемых хостов
        if len(hosts_list) == 1:
            header = f"{base_class.SelectInterfaceOneHostText} {bs}{''.join(hosts_list)}{be}"
        else:
            list_text = '\n'.join(hosts_list)
            header = f"{base_class.SelectInterfaceHostsText}\n" \
                     f"{LINE}" \
                     f"{bs}{list_text}{be}\n" \
                     f"{LINE}"

        _, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                   reply_text=header,
                                                   list_content=buttons_list,
                                                   cmd_buttons=[],
                                                   back_buttons=base_class.BackButtons,
                                                   menu_level=st.VPN_HOSTS_ACTIONS,
                                                   update=update, context=context)

        # фиксируем и возвращаем текущий уровень меню
        return st.VPN_HOSTS_ACTIONS

    def vpn_hosts_change_interface_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отражает результат смены интерфейсов для выбранных хостов

        :param update:
        :param context:
        :return:
        """

        # получаем выбранный тип интерфейса
        interface = update.callback_query.data

        #  получаем список выбранных хостов и число ip в этом списке, для того,
        #  чтобы понять, нужно ли запускать задачу в фоне или нет.
        hosts_list, count = self.vpn_hosts_preparing_action(update=update, _=context)
        # # готовим аргументы для функции vpn_lib.switch_host_auto_state

        func_start_args = dict(hosts=hosts_list, new_inface=interface, old_inface=self.interface)
        # устанавливаем новый интерфейс
        self.interface = interface
        return dialog.run_background(func_start=vpn_lib.change_hosts_interface,
                                     func_finish=self.vpn_hosts_white_list_show,
                                     menu_level=st.VPN_HOSTS_ACTIONS,
                                     update=update, context=context, records_to_processing=count,
                                     func_start_args=func_start_args)

    # --------------------------------------------------------------------------------------------------
    #
    #       Уровень VPN_BACKUP - меню "Архивы"
    #
    # --------------------------------------------------------------------------------------------------
    def _get_backup_details(self) -> dict:
        """
        Получаем информацию об архивах

        :return:
        """
        # получаем информацию об архивах, в случае
        # ее наличия в кеше возвращаем кеш
        self.backup_details = self.backup_details if self.backup_details else vpn_lib.get_backup_details()

        return self.backup_details

    @run_wdogs_at_start
    @set_menu_level(menu_level=st.VPN_BACKUP_LIST)
    def vpn_backup_list_show(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает меню "Архивы"

        :param update:
        :param context:
        :return:
        """
        backup_list = []

        # фиксируем базовый класс для краткости кода
        base_class = Menu.Vpn.BackUpMenu

        # получаем информацию об архивах
        backup_details = self._get_backup_details()
        self.backup_details = self.backup_details if self.backup_details else vpn_lib.get_backup_details()
        #  проверяем на наличие архивов
        if backup_details:
            # формируем название КНОПОК с именами АРХИВОВ
            # с обязательной сортировкой с целью достижения
            # отображения одного и того же порядка при генерации кнопок
            # пример кода кнопки: '§@21-02-22_11-00_all.vpu'

            for name in sorted(backup_details.keys()):
                # текст кнопки АРХИВА: 'Архив 21-02-22_11-00_all (12 шт.)'
                text = f'{rtag.backup} {name} ({backup_details[name][etag.count]} шт.)'
                # КОД кнопки '§@21-02-22_11-00_all.vpu', по первым
                # двум символам определяем что нажата кнопка с названием архива
                code = f'{etag.divider}{name}'
                # обновляем список архивов
                backup_list.append({text: code})

            # обозначаем список кнопок КОМАНД, в случае когда есть или нет выбранных архивов
            cmd_buttons = base_class.ItemsWhenHaveBackups

            #  если они имеются - формируем заголовок
            header = f'{base_class.TitleWhenHaveBackups}\n' \
                     f'{LINE}' \
                     f'{rtag.count} {bs}{len(backup_list)}{be} шт.\n'

            # инициализируем переменные для корректной обработки
            # содержимого архивов в vpn_backup_content_show
            self.backup_content_list, self.selected_backup_host_list, self.backup_name = [], [], ''

        else:
            # при ОТСУТСТВИИ архивов выводим соответствующий заголовок
            header = base_class.TitleWhenHaveNOBackups
            cmd_buttons = base_class.NoItemsWhenHaveNOBackups

        context.user_data[etag.info] = True
        callback, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                          reply_text=header,
                                                          list_content=backup_list,
                                                          cmd_buttons=cmd_buttons,
                                                          menu_level=st.VPN_BACKUP_LIST,
                                                          back_buttons=base_class.BackButtons,
                                                          update=update, context=context)
        return callback

    def vpn_backup_create_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция создает архив с именем даты и времени для всех доменов
        для всех интерфейсов, пример названия файла архива 01-03-22_11-00_all.vpu

        :param update:
        :param context:
        :return:
        """
        # счетчик записей
        count = len(self.backup_details) * 3
        # обнуляем словарь с информацией об архивах, чтобы он снова
        # был обновлен, так как добавляем новый
        self.backup_details = {}

        return dialog.run_background(func_start=vpn_lib.create_backup, func_start_args={},
                                     records_to_processing=count,
                                     func_finish=self.vpn_backup_list_show,
                                     menu_level=st.VPN_BACKUP_LIST, instantly_update=False,
                                     update=update, context=context)

    @set_menu_level(menu_level=st.VPN_BACKUP_LIST)
    def vpn_backup_remove_all_request(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает запрос на удаление всех архивов в списке

        :param update:
        :param context:
        :return:
        """

        # для краткости создаем базу
        base_class = Menu.Vpn.BackUpMenu
        # формируем запрос на удаление
        result, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                        reply_text=base_class.AskToRemoveAllHeader,
                                                        list_content=[],
                                                        back_buttons=[],
                                                        cmd_buttons=base_class.RemoveRequestButtons,
                                                        menu_level=st.VPN_BACKUP_LIST,
                                                        update=update, context=context)
        return result

    def vpn_backup_remove_all_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция производит удаление ВСЕХ архивов в списке

        :param update:
        :param context:
        :return:
        """

        # формируем аргументы для передачи в функцию удаления архивов delete_backup
        func_start_args = dict(backup_list=list(self._get_backup_details().keys()))

        # получаем общее число циклов работы
        count = sum([n[etag.count] for n in self.backup_details.values()])

        # обнуляем данные об архивах
        self.backup_details = {}

        # запускаем удаление архивов
        return dialog.run_background(func_start=vpn_lib.delete_backup,
                                     func_finish=self.vpn_backup_list_show,
                                     menu_level=st.VPN_BACKUP_LIST,
                                     update=update, context=context,
                                     records_to_processing=count,
                                     func_start_args=func_start_args)

    # --------------------------------------------------------------------------------------------------
    #
    #       Уровень VPN_BACKUP_DETAIL - содержание конкретного архива в меню "Архивы"
    #
    # --------------------------------------------------------------------------------------------------
    @staticmethod
    def _get_values_from_backup_content_line(content_line: str) -> (str, str, str):
        # извлекаем данные из строки архива
        # пример содержимого строки www.astra.ru|OpenVPN0|off
        cont = content_line.split(etag.divo)
        len_ = len(cont)
        # получаем имя домена, интерфейс и флаг auto
        domain = cont[0] if len_ and len_ >= 1 else None
        inface = cont[1] if len_ and len_ >= 2 else ''
        auto = cont[2] if len_ and len_ >= 3 else ''

        return domain, inface, auto

    @set_menu_level(menu_level=st.VPN_BACKUP_CONTENT)
    def vpn_backup_list_content_show(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает меню, в котором отображается содержимое конкретного архива

        :param update:
        :param context:
        :return:
        """

        # фиксируем базовый класс для краткости кода
        base_class = Menu.Vpn.BackUpMenu.BackUpContent

        # получаем информацию (имя файла из кода кнопки и содержимое файла) о выбранном архиве
        filename = "".join(
                update.callback_query.data.split(etag.divider)) if update.callback_query else self.backup_name
        # фиксируем имя текущего архива
        self.backup_name = filename if update.callback_query and filename in self.backup_details.keys() \
            else self.backup_name
        # фиксируем содержимое текущего архива
        if self.backup_content_list:
            self.backup_content_list = self.backup_content_list
        else:
            lines = vpn_lib.get_backup_host_list(backup_name=self.backup_name)
            # генерируем переменную которая состоит из списка [(host, interface)]
            self.backup_content_list = [(ln.split(etag.divo)) for ln in lines if ln]

        host_list, inface, inface_txt, inface_count, icon_select = [], None, '', 0, ''
        # проверяем на наличие содержимого архива и на наличие ошибок при получении содержимого архива
        if self.backup_content_list and Error.INDICATOR not in sum(self.backup_content_list,[])[0]:

            # формируем название КНОПОК с именами хостов
            # с обязательной сортировкой с целью достижения
            # отображения одного и того же порядка при генерации кнопок
            for domain, inface, auto in sorted(self.backup_content_list):

                # извлекаем данные из строки архива
                # пример содержимого строки www.astra.ru|OpenVPN0|off
                # domain, inface, auto = self._get_values_from_backup_content_line(content_line=content_line)

                # если в коде возврата содержится знак "|", то значит была нажата клавиша какая либо
                # в этом случае получаем первую переменную до знака разделителя.
                pressed_but_val = filename.split(etag.divo)[0] if etag.divo in filename else filename
                # если была нажата кнопка фильтрации с именем интерфейса, то
                ok_inface = tools.has_inside(checking_list=INTERFACE_TYPES, source=pressed_but_val)
                # если была нажата кнопка "Выбрать все"
                ok_all = True if self.selected_group == etag.all else False
                # генерируем иконку - выбран, если он есть в списке выбранных
                host_pressed = not ok_inface and not ok_all
                if host_pressed:
                    icon_select = icon.select if (domain, inface) in self.selected_backup_host_list else icon.unselect

                elif ok_inface:
                    icon_select = icon.select if (domain, inface) in self.selected_backup_host_list else icon.unselect
                elif ok_all:
                    icon_select = icon.select

                #  получаем информацию о доступных интерфейсах в системе,
                #  чтобы была возможность отображать не тип, а имя интерфейса
                if inface:
                    # ведем подсчет числа интерфейсов в списке
                    inface_count += 1
                    # если имя интерфейса уже существует в списке класса,
                    if inface in self.interface_names:
                        #  то используем его
                        name = self.interface_names[inface]
                    else:
                        # в противном случае делаем запрос в роутер
                        name = vpn_lib.get_interface_name(interface=inface)
                        self.interface_names.update({inface: name})

                    # делаем обертку для сообщения
                    inface_txt = f" -> {name}" if name else ''

                # обрабатываем флаг auto
                if auto:
                    # если флаг auto есть, то генерируем иконку
                    auto = icon.ok if etag.on in auto else icon.stop
                    auto = f"{auto} "

                #  проверка на наличие хоста
                if domain:
                    # если хост извлечен верно
                    # текст кнопки ДОМЕНА: 'www.alfa.com [OpenVPN0][on]'
                    text = f'{icon_select} {domain}{inface_txt} {auto}'
                    # КОД кнопки - "имя_домена|интерфейс"
                    code = f"{domain}{etag.divo}{inface}"
                    # обновляем список архивов
                    host_list.append({text: code})

            # обозначаем список кнопок КОМАНД, в случае когда есть или нет выбранные хосты
            cmd_buttons = base_class.ItemsWhenHaveHosts if self.selected_backup_host_list \
                else base_class.ItemsWhenHaveNoHosts

            # есть ли выбранные хосты в списке данного архива?
            if self.selected_backup_host_list:
                # в случае если выбранные хосты ЕСТЬ,
                # то сообщаем об общем количестве хостов и о числе выбранных хостов
                selected_backup_mess = f"{bs}{len(self.selected_backup_host_list)}{be}/" \
                                       f"{bs}{len(host_list)}{be} шт.\n"
            else:
                # выбранных хостов нет - просто обозначаем общее число архивов
                selected_backup_mess = f"{bs}{len(host_list)}{be} шт.\n"

            # если они имеются - формируем заголовок
            header = f'{rtag.backup} {bs}{self.backup_name}{be}\n' \
                     f'{LINE}' \
                     f'{rtag.count} {selected_backup_mess}'

            if len(self.selected_backup_host_list) == len(self.backup_content_list):
                # если выбраны все хосты из списка, то активируем клавишу ВЫБРАТЬ ВСЕ или ОТМЕНИТЬ ВСЕ
                self.selected_group = etag.all
            # генерируем клавишу ВЫБРАТЬ ВСЕ или ОТМЕНИТЬ ВСЕ
            if self.selected_group == etag.all:
                # если включен режим выбора всех записей, то меняем надпись на противоположный смысл
                select_all_button = [[{rtag.UnSelectAll: st.BCT_6_UNSELECT_ALL}]]
            else:
                # если вЫключен режим выбора всех записей
                select_all_button = [[{rtag.SelectAll: st.BCT_5_SELECT_ALL}]]

            # генерируем клавиши фильтрации (подсвечиваем в меню) хостов по интерфейсу,
            # но только в том случае, если интерфейсов больше одного
            select_inface_buttons = [{f"{icon.select if inf == self.selected_group else icon.unselect} {nm}": inf}
                                     for inf, nm in self.interface_names.items()] if inface_count > 1 else {}

            # клавишу "ВЫБРАТЬ ВСЕ"/"ОТМЕНИТЬ ВСЕ" ставим на первом месте после списка хостов
            if select_inface_buttons:
                # если кнопки фильтрации по интерфейсу сгенерированы
                sel_buttons = select_all_button + cmd_buttons
                cmd_buttons = select_inface_buttons + sel_buttons
            else:
                # кнопки фильтрации по интерфейсу НЕ сгенерированы
                cmd_buttons = select_all_button + cmd_buttons

            # если есть выбранные элементы, то отображаем кнопку экспорта
            cmd_buttons = base_class.UpperCommandButtons + cmd_buttons if self.selected_backup_host_list \
                else cmd_buttons
        else:
            if Error.INDICATOR in self.backup_content_list[0]:
                # Если обнаружена ошибка чтения содержимого архива
                header = self.backup_content_list[0]
            else:
                # при ОТСУТСТВИИ архивов выводим соответствующий заголовок
                header = base_class.TitleWhenHaveNoHosts
            # обозначаем кнопки в случае отсутствия элементов
            cmd_buttons = base_class.ItemsWhenHaveNoHosts

        # self.backup_name = ''
        callback, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                          reply_text=header,
                                                          list_content=host_list,
                                                          cmd_buttons=cmd_buttons,
                                                          menu_level=st.VPN_BACKUP_CONTENT,
                                                          back_buttons=base_class.BackButtons,
                                                          update=update, context=context)
        return callback

    def vpn_backup_press_on_select_all_button_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция занимается обработкой нажатий клавиши "Выбрать все" и "Отменить выбор"
        в меню Архивы

        переход из VPN_BACKUP: rep_select_all() в VPN_MENU_BACKUP_DETAIL

        :param update:
        :param context:
        :return:
        """
        self.selected_backup_host_list = []
        if update.callback_query.data == st.BCT_5_SELECT_ALL:
            # Добавляем все доменные имена в список выбранных
            self.selected_backup_host_list = [(h, i) for h, i, _ in self.backup_content_list
                                              if (h, i) not in self.selected_backup_host_list]
            # установка флага выбора хостов в значение all
            self.selected_group = etag.all
        elif update.callback_query.data == st.BCT_6_UNSELECT_ALL:
            # установка флага выбора хостов в нулевое значение
            self.selected_group = ''

        # Возвращаемся в обработку группы
        return self.vpn_backup_list_content_show(update=update, context=context)

    def vpn_backup_press_on_host_button_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция занимается обработкой нажатий клавиш названий сайтов,
        их одиночным выбором в списке Архивов

        переход из VPN_BACKUP_LIST: rep_backup_host() в VPN_MENU_BACKUP_DETAIL

        :param update:
        :param context:
        :return:
        """
        # Получаем наименование выбранного домена
        key_code = update.callback_query.data
        # проверяем есть ли разделитель в коде
        selected = tuple(key_code.split(etag.divo)) if etag.divo in key_code else (key_code, '')
        # проверяем что нажали именно на кнопку выбора доменного имени
        sel_host = selected[0]
        if tools.get_url_only(sel_host):
            if selected in self.selected_backup_host_list:
                # если хост есть уже в списке отобранных хостов,
                # то удаляем его из списка
                [self.selected_backup_host_list.remove((h, i)) for h, i, _ in self.backup_content_list if sel_host in h]
                # self.selected_backup_host_list.remove(selected)
            else:
                # если хоста нет в списке отобранных хостов,
                # то добавляем его в список
                [self.selected_backup_host_list.append((h, i)) for h, i, _ in self.backup_content_list \
                 if (h, i) not in self.selected_backup_host_list and sel_host in h]

            # установка флага выбора хостов в нулевое значение
            self.selected_group = ''

        # Возвращаемся в обработку группы
        return self.vpn_backup_list_content_show(update=update, context=context)

    def vpn_backup_press_on_select_inface_button_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция занимается обработкой нажатий клавиш
        фильтрации определенного интерфейса для доменных имен

        VPN_MENU_BACKUP_DETAIL: rep_interface_list()

        :param update:
        :param context:
        :return:
        """
        # Получаем наименование выбранного домена
        interface_code = update.callback_query.data
        # invert_selected = False if update.callback_query.data not in self.selected_group else True
        # проверяем что нажали именно на кнопку выбора доменного имени
        if tools.has_inside(checking_list=INTERFACE_TYPES, source=interface_code):
            self.selected_backup_host_list = []
            for domain, inface, _ in self.backup_content_list:
                # извлекаем данные из строки архива
                # пример содержимого строки www.astra.ru|OpenVPN0|off
                # domain, inface, _ = self._get_values_from_backup_content_line(content_line=content_line)
                selected = (domain, inface)
                if interface_code in inface:
                    # если интерфейса нет в списке отобранных хостов,
                    # то добавляем его в список
                    self.selected_backup_host_list.append(selected)
                else:
                    # если хост есть уже в списке отобранных хостов,
                    # то удаляем его из списка
                    if selected in self.selected_backup_host_list:
                        self.selected_backup_host_list.remove(selected)

        # установка флага выбора хостов в нулевое значение
        self.selected_group = interface_code
        # Возвращаемся в обработку группы
        return self.vpn_backup_list_content_show(update=update, context=context)

    # --------------------------------------------------------------------------------------------------
    #
    #       Уровень VPN_BACKUP_DETAIL - отработка действий
    #       на странице меню содержание конкретного архива в меню "Архивы"
    #
    # --------------------------------------------------------------------------------------------------
    @staticmethod
    @set_menu_level(menu_level=st.VPN_BACKUP_CONTENT)
    def vpn_backup_rename_request(update: Update, _: CallbackContext) -> int:
        """
        Функция отображает запрос на ПЕРИМЕНОВАНИЕ АРХИВА

        :param update:
        :param _:
        :return:
        """

        # Выводим запрос на ввод нового имени архива и удаляем предыдущее меню
        reply_text = Menu.Vpn.BackUpMenu.AskNewBackupName
        update.callback_query.delete_message()
        update.callback_query.message.reply_text(reply_text)

        # фиксируем и возвращаем текущий уровень меню
        return st.VPN_BACKUP_CONTENT

    def vpn_backup_rename_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция производит переименование архива

        :param update:
        :param context:
        :return:
        """
        #  если ввели слова по выходу из режима ввода
        callback = exit_from_text_mode(update.message.text, self.vpn_backup_list_content_show, update, context)
        if callback:
            return callback

        # проверяем был ли введен текст
        if update.message.text:
            # если текст был введен, то производим переименование архива
            new_name = f"{update.message.text}.{DEMON_NAME}"
            result = vpn_lib.rename_backup(old_name=self.backup_name, new_name=new_name)

            # проверяем на наличие ошибок в результате переименования архива
            if Error.INDICATOR not in result:
                # в случае отсутствия ошибок
                # выводим сообщение об успешном результате переименования
                dialog.alert(mess=result, update=update, context=context)
                # обновляем текущее новое имя архива
                self.backup_name = new_name
                # обнуляем данные об именах архивов, для их перезагрузки
                self.backup_details = []

            # отображаем страницу с содержимым архива
            callback = self.vpn_backup_list_content_show(update, context)

        else:
            # если текст введен не был, то выводим соответствующее сообщение
            dialog.alert(mess=Menu.Vpn.BackUpMenu.BackUpContent.MessageToRenameError, update=update, context=context)
            callback = st.VPN_BACKUP_CONTENT

        return callback

    @set_menu_level(menu_level=st.VPN_BACKUP_CONTENT)
    def vpn_backup_export_request(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает запрос на загрузку выбранных хостов
        в текущий Белый Список (БС)

        :param update:
        :param context:
        :return:
        """

        # для краткого кода
        base_class = Menu.Vpn.BackUpMenu.BackUpContent
        # заголовок сообщения
        header = base_class.ExportRequestHeader

        # Получаем информацию о доступных интерфейсах
        inface_dict, inface_butt_list = vpn_lib.mark_interface_online()
        # если интерфейс всего один,
        if len(inface_dict) == 1:
            # то не запрашиваем ничего, а сразу экспортируем.
            update.callback_query.data = "".join(inface_dict.keys())
            callback = self.vpn_backup_export_action(update=update, context=context)
        else:
            # и формируем кнопки выбора интерфейса
            inface_list = [{f: n} for f, n in zip(inface_butt_list, inface_dict)]
            callback, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                              reply_text=header,
                                                              list_content=inface_list,
                                                              cmd_buttons=[],
                                                              menu_level=st.VPN_BACKUP_EXPORT,
                                                              back_buttons=base_class.BackToContent,
                                                              update=update, context=context)
        return callback

    def vpn_backup_export_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция осуществляет запрос на загрузку выделенных
        доменов в существующий белый список

        :param update:
        :param context:

        :return:
        """

        #  получаем номер интерфейса
        interface = update.callback_query.data

        #  получаем число всех ip в белом списке, для того,
        #  чтобы понять, нужно ли запускать задачу в фоне или нет.
        count_ip = vpn_lib.count_hosts_ip(hosts_list=self.selected_backup_host_list)
        # готовим список аргументов для vpn_lib.load_backup
        args = dict(backup_name=self.backup_name, interfaces=[interface], hosts_list=self.selected_backup_host_list)
        # запускаем функцию о фоне
        return dialog.run_background(func_start=vpn_lib.load_backup, func_start_args=args,
                                     menu_level=st.VPN_BACKUP_CONTENT,
                                     func_finish=self.vpn_backup_list_content_show,
                                     records_to_processing=count_ip,
                                     update=update, context=context)

    @set_menu_level(menu_level=st.VPN_BACKUP_LIST)
    def vpn_backup_remove_one_request(self, update: Update, context: CallbackContext) -> int:
        """
        Функция производит удаление ВСЕХ архивов в списке

        :param update:
        :param context:
        :return:
        """

        # базовое имя класса для краткости кода
        base_class = Menu.Vpn.BackUpMenu.BackUpContent
        #  текст запроса на удаление
        header = base_class.AskToRemoveBackupHeader.format(bs, self.backup_name, be)
        # кнопки подтверждения
        buttons = base_class.RemoveRequestButtons
        #  вызов диалога об удалении
        callback, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                          reply_text=header,
                                                          list_content=[],
                                                          cmd_buttons=buttons,
                                                          menu_level=st.VPN_BACKUP_CONTENT,
                                                          back_buttons=[],
                                                          update=update, context=context)
        return callback

    def vpn_backup_remove_one_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция производит удаление ВСЕХ архивов в списке

        :param update:
        :param context:
        :return:
        """
        if self.backup_name:
            # ставим фильтр на удаление ТОЛЬКО текущего архива
            func_start_args = dict(backup_list=[self.backup_name])
        else:
            err_mess = 'Переменная с именем архива self.backup_name не может быть пустой!'
            zlog.error(err_mess)
            raise Exception(err_mess)

        # удаляем информацию об удаляемом файле из кеша
        del self.backup_details[self.backup_name]

        # запускаем удаление архивов
        return dialog.run_background(func_start=vpn_lib.delete_backup,
                                     func_finish=self.vpn_backup_list_show,
                                     menu_level=st.VPN_BACKUP_LIST,
                                     update=update, context=context,
                                     records_to_processing=1,
                                     func_start_args=func_start_args)

    # --------------------------------------------------------------------------------------------------
    #
    #       Уровень VPN_TIMER - отработка действий на странице меню "Таймер обновления"
    #
    # --------------------------------------------------------------------------------------------------
    @run_wdogs_at_start
    @set_menu_level(menu_level=st.VPN_TIMER)
    def vpn_timer_menu_show(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает страницу меню VPN таймера

        :param update:
        :param context:
        :return:
        """
        base_class = Menu.Vpn.TimerMenu
        # в случае, если было произведено обновление доменных имен, то меняем заголовок
        if self.timer_update:
            # обновление только запущено
            update_header = f"{rtag.TimerUpdateStart}\n"
            self.timer_update = False

        elif self.timer_update is not None:
            try:
                _ = context.user_data[etag.action]
                # обновление завершено (action == False и self.timer_update запущен не в первый раз)
                # установим флаг обновления, чтобы в меню таймера
                # изменить заголовок при окончании работы обновлений
                from datetime import datetime
                time_done = datetime.now().strftime(TIMER_FORMAT)
                # фиксируем время обновления
                context.user_data[etag.update_time] = time_done
                # формируем часть заголовка
                update_header = f"{rtag.TimerUpdateDone} {bs}{time_done}{be}\n"
            except KeyError:
                update_header = ""
        else:
            try:
                update_header = f"{rtag.TimerUpdateDone} {bs}{context.user_data[etag.update_time]}{be}\n"
            except KeyError:
                update_header = ""

        period = vpn_lib.get_timer_period()
        if Error.INDICATOR in period:
            # в случае наличия ошибки выводим
            # соответствующее сообщение
            period_text = base_class.TimerNotSetHeader
            cmd_buttons = base_class.ItemButtonsWhenTimerOff
        else:
            # в случае успеха выводим период таймера
            period_text = f"{base_class.TimerSetHeader} {bs}{period}{be}"
            cmd_buttons = base_class.ItemButtonsWhenTimerOn

        # заголовок для меню
        header = f"{base_class.MainHeader}\n" \
                 f"{LINE}" \
                 f"{period_text}\n" \
                 f"{update_header}" \
                 f"{LINE}"

        # отображаем меню
        callback, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                          reply_text=header,
                                                          list_content=[],
                                                          cmd_buttons=cmd_buttons,
                                                          menu_level=st.VPN_TIMER,
                                                          back_buttons=base_class.BackButtons,
                                                          update=update, context=context)
        return callback

    def vpn_timer_update_hosts_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция обновляет ip всех доменных имен на всех интерфейсах в БС

        VPN_TIMER -> TM_2_UPDATE_ACTION

        :param update:
        :param context:
        :return:
        """

        #  получаем число всех ip в белом списке, для того,
        #  чтобы понять, нужно ли запускать задачу в фоне или нет.
        count_ip = vpn_lib.count_hosts_ip()
        self.timer_update = True
        # готовим аргументы для функции vpn_lib.update_host_list
        # func_start_args = dict(hosts=None, interface=None)
        return dialog.run_background(func_start=vpn_lib.update_host_list,
                                     func_finish=self.vpn_timer_menu_show,
                                     menu_level=st.VPN_TIMER,
                                     update=update, context=context,
                                     records_to_processing=count_ip)

    @staticmethod
    @set_menu_level(menu_level=st.VPN_TIMER)
    def vpn_timer_change_request(update: Update, _: CallbackContext) -> int:
        """
        Функция отображает запрос на ввод нового значения периода для таймера

        :param update:
        :param _:
        :return:
        """
        # вводим заголовок
        reply_text = Menu.Vpn.TimerMenu.TimerEnterPeriodHeader
        # удаляем предыдущее сообщение
        # update.callback_query.delete_message()
        update.callback_query.answer()
        # выводим сам запрос
        update.callback_query.edit_message_text(text=reply_text)

        return st.VPN_TIMER

    @run_wdogs_at_start
    def vpn_timer_change_action(self, update: Update, context: CallbackContext) -> int:
        """
        Функция производит анализ введенных данных и

        :param update:
        :param context:
        :return:
        """
        # Код возврата
        result = st.VPN_TIMER
        # Получаем текст введенного сообщения
        text_reply = update.message.text

        #  если ввели слова по выходу из режима ввода
        callback = exit_from_text_mode(update.message.text, self.vpn_timer_menu_show, update, context)
        if callback:
            return callback

        if text_reply:
            # если он не пустой устанавливаем таймер
            mess = vpn_lib.set_timer_period(text_reply)
            # проверяем введенный текст на наличие слеша - значит введена была команда
            if etag.cmd.slash not in text_reply:
                result = self.vpn_timer_menu_show(update, context)
            # выводим сообщение
            dialog.delete_messages(number=2, update=update, context=context)
            dialog.alert(mess=mess, update=update, context=context)
            # else:
            #     # если ввод был осуществлен из меню,
            #     # то вызываем его повторно
            #     try:
            #         result = self.vpn_timer_menu_show(update, context)
            #     except error.BadRequest:
            #         pass
        else:
            mess = Menu.Vpn.TimerMenu.NoDataEntered
            dialog.alert(mess=mess, update=update, context=context)

        return result

    @set_menu_level(menu_level=st.VPN_TIMER)
    def vpn_timer_delete_request(self, update: Update, context: CallbackContext) -> int:
        """
        Функция отображает запрос на удаление таймера обновления доменов из крона

        :param update:
        :param context:
        :return:
        """
        base_class = Menu.Vpn.TimerMenu
        callback, self.message_id = dialog.show_list_core(message_id=self.message_id,
                                                          reply_text=base_class.DeleteRequest,
                                                          list_content=[],
                                                          cmd_buttons=base_class.DeleteItemButtons,
                                                          menu_level=st.VPN_TIMER,
                                                          back_buttons=[],
                                                          update=update, context=context)
        return callback

    def vpn_timer_delete_action(self, update: Update, context: CallbackContext) -> int:
        """
         Функция производит удаление таймера обновления доменов

        :param update:
        :param context:
        :return:
        """

        # удаляем таймер
        result_mess = vpn_lib.remove_timer()
        # выводим сообщение о результате удаления
        dialog.alert(mess=result_mess, update=update, context=context)
        # try:
        # Отображаем меню таймера после операции удаления
        result = self.vpn_timer_menu_show(update, context)
        # except error.BadRequest:
        #     result = dt.VPN_TIMER

        return result


vpn = VpnMenuAction()
