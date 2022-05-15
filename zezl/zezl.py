#!/opt/bin/python3
# coding=utf-8
# from sqlalchemy import create_engine

from telegram.ext import (
    Defaults,
    Updater,
    # PicklePersistence,
    MessageHandler, Filters,
)
from telegram import Update

from libraries.main.config import get_config_value
from setup.data import (
    etag, CONFIG_FILE
)
from menu.handlers import (
    CONVERSATION_HANDLER,
    commands_list,
    cmd_handler_terminal_list
)
from logs.logger import zlog
from libraries.main.tools import run
from logs.tracer import error_tracer


def get_token() -> str:
    """
    Функция возвращает Телеграм токен из файла конфигурации

    :return:
    """
    try:
        # в случае, если работа в режиме отладки на удаленной машине
        from debug import remote_data
        # то берем токен из файла
        result = remote_data.TOKEN
    except ImportError or ModuleNotFoundError:
        # формируем команду для получения токена из файла конфигурации
        cmd = f"cat < {CONFIG_FILE} | grep '{etag.token}=' | cut -d'=' -f2"
        # исполняем команду
        is_ok, out = run(command=cmd)
        # убираем из ответа конечный символ новой строки
        token = out.replace('\n', '') if is_ok else ''
        if not is_ok:
            # если результат отрицательный
            raise Exception("Возникла проблема при чтении файла конфигурации! Проверьте token")
        elif not token:
            # если вернулось пустое значение
            raise Exception("Токен не задан в файле конфигурации, без него работа невозможна!")
        else:
            result = token
    # если проблем не обнаружено, возвращаем токен
    return result


# функция обработки не распознанных команд
def unknown_command(update, context):
    """
    Функция для реакции на неизвестные команды

    :param update:
    :param context:
    """
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Повторите ввод, команда не распознана!")


def main() -> None:
    """Run the bot."""

    # engine = create_engine('sqlite:///sqlite3.db')  # используя относительный путь
    # engine.connect()

    #  Обозначаем имя бота
    # bot_name = f'{APP_NAME}-bot-z'

    # Устанавливаем по умолчанию режимы работы бота
    # парсинг сообщений согласно HTML правилам
    # и без квотирования текста
    defaults = Defaults(parse_mode='HTML', quote=False, run_async=True)

    # Создаем экземпляр бота с обозначенным именем для записи user_data в файл bot_name
    # persistence = PicklePersistence(filename=bot_name)

    # создаем обработчик нашего чата с заданным токеном и параметрами
    # up = Updater(get_token(), persistence=persistence, defaults=defaults)
    up = Updater(get_token(), defaults=defaults)
    # Регистрируем диспетчер бота - программу, которая будет обрабатывать все события бота
    dp = up.dispatcher

    # обработчик команд из меню в нашем боте
    dp.add_handler(CONVERSATION_HANDLER)

    #  обработчик команды ввода
    up.bot.set_my_commands(commands_list)

    # обработчик терминальных команд (не из меню) для исполнения ботом
    [dp.add_handler(handler) for handler in cmd_handler_terminal_list]

    # Заносим в журнал все возникшие ошибки при работе бота,
    # но только в режиме локальной работы
    try:
        # в режиме удаленной отладки все сообщения
        # выводим по умолчанию в консоль
        from debug.remote_data import REMOTE_ACCESS_CMD
        zlog.info(f"Запускаем бота на удаленной машине...")
    except ImportError:
        # отправляем сообщения разработчику,
        # если работаем локально на роутере
        zlog.info(f"Запускаем бота на роутере...")
        # получаем значение флага DEBUG
        debug_flag = get_config_value(name=etag.debug, default=etag.yes).lower()
        # если в файле конфигурации установлен флаг DEBUG в значение YES или TRUE
        if debug_flag == etag.yes or debug_flag == etag.true:
            dp.add_error_handler(error_tracer)

    # удаляем сообщения из лога которые идут из пакета telegram-bot и не имеют отношения к проекту Zezl
    dp.logger.addFilter((lambda s: not s.msg.startswith('/opt/apps/zezl/venv/lib/python3.10/site-packages/telegram')))

    # добавляем обработчик для не распознанных команд
    # этот обработчик должен быть самым крайним из всех доступных обработчиков бота
    unknown_handler = MessageHandler(Filters.command, unknown_command)
    dp.add_handler(unknown_handler)

    # Запускаем бота
    up.start_polling(allowed_updates=Update.ALL_TYPES)
    zlog.info(f"'Жезл' бот запущен успешно!")

    # Запускаем робота до нажатия Ctrl-C или до
    # получения сигналов SIGINT, SIGTERM или SIGABRT.
    up.idle()


if __name__ == '__main__':
    main()
