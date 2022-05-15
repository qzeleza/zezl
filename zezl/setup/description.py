# coding=utf-8

PERIOD_TABLE = {
    "s": "сек.",
    "m": "мин.",
    "h": "час.",
    "d": "дн.",
    "w": "нед.",
    "M": "мес.",
}

class TextTagsENG:
    false = 'false'
    quit = 'quit'
    exit = 'exit'
    true = 'true'
    debug = 'DEBUG'
    err_ignore = 'err_ignore'
    err_ignore_list = "err_ignore_list"
    site_name = 'site_name'
    link_name = 'link_name'
    password = 'password'
    login = 'login'
    last_hash = 'last_hash'
    update_date = 'update_date'
    check_date = 'check_date'
    period = 'period'
    level = 'level'
    description = "description"
    dot = "."
    menu = 'menu'
    terminal = 'terminal'
    info = "info"
    connected = "connected"
    message = "message"
    comment = "comment"
    state = "state"
    error = "error"
    interface = "interface"
    dns = "dns"
    yes = "yes"
    no = "no"
    on = 'on'
    off = 'off'
    openvpn = "OpenVPN"
    wireguard = "Wireguard"
    ike = "IKE"
    pppoe = 'PPPOE'
    dongle = 'CdcEthernet'
    l2tp = 'L2TP'
    sstp = 'SSTP'
    host = "host"
    hostname = 'hostname'
    active = 'active'
    mac = 'mac'
    link = 'link'
    chat_id = 'chat_id'
    menu_id = 'menu_id'
    id = 'id'
    registered = 'registered'
    name = 'name'
    auto = "auto"
    auto_on = "aut0_0n"
    auto_off = "aut0_0ff"
    localhost = "localhost"
    ip = "ip"
    count = "count"
    create = "create"
    status = 'status'
    update = "update"
    command = "command"
    backup = "backup"
    buffer = "buffer"
    action = "action"
    short = "+short"
    tls = "+tls"
    dig = 'kdig'
    empty_ip = '0.0.0.0'
    empty = 'empty'
    background = 'background'
    invisible = 'strong>'
    inside = 'b>'
    divhost = ' --> '
    pdot = ';'
    divo = '|'
    ddot = ':'
    slash = '/'
    callback = 'callback'
    backup_ext = 'zzl'
    divider = '@±§'
    all = 'all'
    context = 'context'
    update_time = 'update_time'
    token = 'TOKEN'
    user_id = 'USER_ID'
    error_state = 'error_state'
    error_interval = 'error_interval'
    error_engine = 'error_engine'
    error_job_name = 'error_job_name'
    error_content = 'error_content'
    error_last_id = 'error_last_id'
    error_type = 'error_type'
    site_interval = 'site_interval'
    site_state = 'site_state'
    site_link = 'site_link'
    timestamp = 'timestamp'
    ident = 'ident'
    log = 'log'
    http = 'http'
    https = 'https'
    last_modified = 'last-modified'
    head = 'HEAD'
    effective_chat = 'effective_chat'
    user_data = 'user_data'

    class html:
        bs = '<b>'
        be = '</b>'
        cds = '<code>'
        cde = '</code>'


    class cmd:
        admin = 'admin'
        backups = 'backups'
        start = "start"
        add = "add"
        new = "new"
        load = "import"
        delete = "del"
        rm = "rm"
        dns = "dns"
        export = "export"
        timer = "timer"
        watchdogs = 'watchdogs'
        clear = "clear"
        purge = "purge"
        infacelist = "infacelist"
        interface = "interface"
        show = "show"
        list = "list"
        period = "period"
        update = "update"
        version = "version"
        help = 'help'
        about = 'about'
        slash = '/'
        vpn = 'tunnels'
        backup = 'backup'
        setup = 'setup'
        imp = 'import'
        setimer = 'setimer'
        token = 'token'


etag = TextTagsENG
bs = etag.html.bs
be = etag.html.be
cds = etag.html.cds
cde = etag.html.cde

ErrorTags = [
    "fatal",
    "error",
    "critical",
    "failed",
    "unsupport",
    "unable",
    "unexpectedly",
    "no such command",
    "doesn't exist"
    "not found",
]


class SearchEngines:
    yandex = 'yandex'
    google = 'google'
    yahoo = 'yahoo'
    ecosia = 'ecosia'


class Icons:
    ok = '✅'
    stop = '❌'
    select = '🌕'
    unselect = '🌑'
    new = '✨'


icon = Icons


class TextTagsRUS:
    backup = '🗂 Архив'
    domain = '🌏 Домен: '
    condition = '🏁 Состояние:'
    count = '✅ Количество:'
    interface = "🔀 Интерфейс:"
    inface_type = "🔀 Тип:"
    all_right = 'успешно'
    TimerMenu = "⌛ Таймер обновлений"
    GroupModeText = "✊ Групповой режим"
    SingleModeText = "👍 Одиночной режим"
    BackToMainMenu = "📒 Главное"
    BackToButton = "⬅ Назад"
    RemoveAllButton = "⛔ Удалить все"
    AddButton = "🎁 Добавить"
    BackUpButton = "🗂 Архивы"
    SwitchOnItem = "❎ Отключить"
    SwitchOffItem = "✅ Включить"
    GroupCmdText = "Групповая обработка"
    TimerUpdateDone = "👍 Данные обновлены "
    TimerUpdateStart = "🔄 Обновление в процессе..."
    Auto = 'AUTO:'
    StatusOn = "ВКЛ."
    StatusOff = "ОТКЛ."
    UpdateButton = "🔄 Обновить"
    UpdateAllItem = "🔄 Обновить все"
    SetItem = "👍 Установить"
    NoSetItem = "👎 Отказаться"
    ActivateItem = "👍 Активировать"
    NoActivateItem = "⏹ Оставить"
    InterfaceItem = "🔀 Интерфейс"
    RemoveSomeButton = "⛔ Удалить"
    DeleteButton = "⛔ Удалить"
    AcceptButton = "👍 Подтвердить"
    RejectButton = "👎 Отменить"
    ChangeButton = "✨ Изменить"
    AddItem = "🗳 Добавить"
    CancelItem = "❎ Отмена"
    DomainListButton = "📜 Список"
    SetupButton = "👌 Настройки"
    VpnMenuItem = "🔐 VPN"
    RouterMenuItem = "🚀 Роутер"
    AboutMenuItem = "💁 О боте"
    Selected = "✨ Отобрано:"
    InfoButton = "📜 Детали"
    SelectAll = "🌑 Выбрать все"
    UnSelectAll = "🌕 Отменить выбор"
    CreateButton = "🎁 Создать архив"
    ImportButton = "🐫 Импорт"
    RenameButton = "🔄 Изменить имя"
    SaveButton = "👌 Сохранить"
    ExportButton = "🐝 Экспорт в Белый Список"
    RemoveBackupButton = "⛔ Удалить архив"
    ErrorIndicator = "ОШИБКА:"
    PleaseWait = "⌛ Немного терпения..."

    WatchDogsMenu = "👀 Сторожа"
    ErrorWDogsButton = '🔥 Ошибки системы'
    CallWDogsButton = '🛎 Звонки'
    WiFiWDogsButton = '⏲ Wifi клиенты'
    SitesWDogsButton = '🌐 Сайты'
    InternetWDogsButton = '🌍 Интернет'
    ChangeIPWDogsButton = '🍀 Внешний IP'
    ActivationOn = 'Включить'
    ActivationOff = 'Выключить'
    IntervalButton = "⏱ Интервал"
    SearchEngine = '🔍 Поисковик'
    LinksList = '🌐 Ссылки'
    PeriodButton = "⌛ Период проверки"
    GotoLinkButton = "🌐 Перейти по ссылке"


rtag = TextTagsRUS


class ErrorTextMessage:
    INDICATOR = 'ОШИБКА:'
    INVALID_BUTTON_MESSAGE = "Такой кнопки нет!"
