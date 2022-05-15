# coding=utf-8

from functools import wraps

from logs.logger import zlog
from setup.data import LINE
from setup.description import etag


def func_name_logger(func):
    """
    Декоратор, который позволяет
    логировать имя вызываемой функции

    :param func: декорируемая функция в качестве аргумента.
    :return:
    """

    @wraps(func)
    def decorator(*args, **kwargs):
        """
        Функция декоратор которая выводит в лог имя функции
        и сообщает в лог о завершении функции

        :param args:
        :param kwargs:
        :return:
        """
        zlog.info(f">> {func.__name__} {LINE}")
        result = func(*args, **kwargs)
        zlog.info(f"<< {func.__name__} {LINE}")

        return result

    return decorator


def set_menu_level(menu_level: int):
    """
    Функция декоратор, которая служит для того, чтобы фиксировать
    уровень текущего меню, для последующего запуска
    конечной функции или ее пропуска в dialog.run_background.

    :param menu_level:
    :return:
    """

    def actual_decorator(func):
        """
        Вызываемый декоратор для функции, который
        реверсно вызывается из внешнего декоратора

        :param func:
        :return:
        """

        def wrapper(*args, **kwargs):
            """
            Функциональный внутренний декоратор

            :param args:
            :param kwargs:
            :return:
            """
            if kwargs:
                # в случае наличия словаря с аргументами
                kwargs[etag.context].user_data[etag.callback] = menu_level
            elif args:
                # в случае наличия списка с аргументами
                data, chat = {}, {}
                # проходимся по списку аргументов и ищем элемент,
                # который содержит словарь user_data
                for arg in args:
                    try:
                        # получаем данные
                        data = getattr(arg, etag.user_data)
                    except AttributeError:
                        pass
                # после чего фиксируем уровень меню
                try:
                    data[etag.callback] = menu_level if data else -1

                except AttributeError:
                    raise Exception(f'Аргументы переданные в функцию отсутствуют: {args}')

            # args[0].selected_group = None
            return_value = func(*args, **kwargs)
            return return_value

        return wrapper

    return actual_decorator
