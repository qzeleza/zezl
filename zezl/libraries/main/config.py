#!/bin/python3

#
#  Copyright (c) 2022.
#
#  Автор: mail@zeleza 04.2022
#  Вся сила в правде!
#

#
#
#  Автор: mail@zeleza 04.2022
#  Вся сила в правде!
#

# Автор: master
# Email: info@zeleza.ru
# Дата создания: 24.04.2022 16:41
# Пакет: PyCharm

"""

Файл содержит функции для работы с файлом конфигурации проекта
    
"""
from libraries.main.tools import check
from setup.data import (
    CONFIG_FILE, CONFIG_PATH
)
from setup.autosets import FILE
# from setup.description import (
#     etag, ErrorTextMessage as Error
# )
from libraries.main import tools as tools


def check_config_file() -> bool:
    """
    Функция проверяет наличие файла конфигурации

    :return: True - файл конфигурации существует
             False - файл конфигурации отсутствует
    """
    return check(file=CONFIG_FILE, subject=FILE)


def get_config_value(name: str) -> str:
    """
    Функция получает значение из файла конфигурации

    :param name: имя получаемого параметра.
    :return: значение получаемого параметра.
    """
    # имя параметра в конфиге хранится в верхнем значении регистров
    param = name.upper()

    # Проверяем на наличие файла конфигурации
    if check_config_file():
        # если файл конфигурации существует, то
        # формируем bash команду для получения значения из файла
        cmd = f"cat < {CONFIG_FILE} | grep '{param}=' | cut -d'=' -f2"
        # исполняем команду
        is_ok, out = tools.run(command=cmd)
        # убираем из ответа конечный символ новой строки
        result = out.replace('\n', '') if is_ok else ''
    else:
        # если файла конфигурации не существует,
        # то создаем папку соответствующую
        tools.mkdir(CONFIG_PATH)
        # формируем команду добавления пустого значения
        # параметра в файл конфигурации
        cmd = f"echo '{param}=' > {CONFIG_FILE}"
        # исполняем команду
        tools.run(command=cmd)
        # возвращаем пустой результат
        result = ''

    return result


def set_config_value(name: str, value: str) -> bool:
    """
    Функция записывает значение переменной в файл конфигурации проекта
    :param name:
    :param value:
    :return:
    """
    # название переменной только в ВЕРХНЕМ регистре
    param = name.upper()
    # формируем команду для записи
    # и проверяем есть ли уже строка с переменной в файле конфигурации
    cmd = f"cat {CONFIG_FILE} | grep {param} | wc -l"
    is_ok, out = tools.run(command=cmd)
    #  если ошибок при выполнении не было
    if is_ok:
        #  проверяем ответ
        if out == '0\n':
            # переменной нет в файле, потому сразу ее добавляем
            cmd = f"echo '{param}={value}' >> {CONFIG_FILE}"
        else:
            #  переменная существует потому меняем ее значение
            cmd = f"sed -i 's/{param}=.*/{param}={value}/g' {CONFIG_FILE}"
        # исполняем команду записи переменой в файл
        is_ok, _ = tools.run(command=cmd)
        if not is_ok:
            raise Exception("ОШИБКА при записи в файл конфигурации.")
    else:
        raise Exception("ОШИБКА чтения данных из файла конфигурации.")

    return is_ok


