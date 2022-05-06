#!/opt/bin/python3
# -*- coding: UTF-8 -*-

import hashlib
from re import findall
from subprocess import PIPE
from subprocess import run as bash
from urllib.parse import urlparse

from httplib2 import Http, error

from libraries.main.decorators import func_name_logger
from logs.logger import zlog
from setup.autosets import (
    ADD_TO_END,
    PATH, FILE,
)
from setup.data import (
    LINE,
)
from setup.description import etag, PERIOD_TABLE

try:
    from debug.remote_data import REMOTE_ACCESS_CMD

    ACCESS_REMOTE = True
except ImportError:
    REMOTE_ACCESS_CMD = None
    ACCESS_REMOTE = False


@func_name_logger
def get_hash(text: str) -> str:
    """
    Функция вычисляет хеш передаваемого содержимого

    :param text: текст, хеш, которого необходимо получить.
    :return:
    """
    hash_text = hashlib.md5()
    hash_text.update(text.encode())
    _hash = hash_text.hexdigest()

    zlog.debug(f"Хеш содержимого: {_hash}")
    return _hash


def match(text, alphabet=None) -> bool | None:
    """
    Функция определяет наличие символов в тексте
    По умолчанию это русские буквы

    :param text: передаваемый текст для проверки.
    :param alphabet: последовательноcть символов для проверки их наличия в тексте.
    :return:
    """
    res = None
    if alphabet is None:
        alphabet = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        res = not alphabet.isdisjoint(text.lower())

    return res


def period_to_rus(period_en: str) -> str:
    """
    Функция из получаемого периода в виде
    2m, 21d и пр. возвращает русское название 2 мин., 21 дн.

    :param period_en: код периода в виде 2m, 21d и пр.
    :return: возвращает русское название 2 мин., 21 дн.
    """

    interval = get_digits(period_en)
    period = get_alpha(period_en)

    return f"{interval} {PERIOD_TABLE[period]}"


def period_to_eng(period_rus: str) -> str:
    """
    Функция из получаемого периода в виде
    2 мин., 21 дн. и пр. возвращает английское название 2m, 21d

    :param period_rus: код периода в виде 2 мин., 21 дн. и пр.
    :return: возвращает английского кода 2m, 21d.
    """
    interval = get_digits(period_rus)
    period = get_alpha(period_rus)
    period = "".join([k for k, v in PERIOD_TABLE.items() if period in v])

    return f"{interval}{period}"


def period_to_sec(time_str: str) -> int:
    """
    Функция получает строку состоящую из периода - цифры
    и интервала буквы и преобразовывает его в секунды

    :param time_str: время и период.
    :return: секунды или -1 в случае ошибки
    """
    multiplier = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
        "w": 604800,
        "M": 2592000,
    }
    interval = get_digits(time_str)
    period = get_alpha(time_str)
    if interval and period:
        return multiplier[period] * interval
    else:
        raise Exception("Задан неверный интервал.")


def ask_input(ask_to_choose: str, list_to_choose: list, element_text: str = None, all_first: bool = True) -> list:
    """
    Функция запрашивает данные для ввода из командной строки

    :param ask_to_choose: запрос на выбор.
    :param list_to_choose: список элементов для выбора.
    :param element_text: название элемента в списке в именительном падеже, например "архив" или "интерфейс"
    :param all_first: флаг наличия первого элемента в списке с вариантом "1. Все варианты ниже"
    :return: список из одного выбранного элемента или список со всеми элементами (при наличии all_first)
    """

    def ljust(digit: int, width: int) -> str:
        """
        Функция преобразует цифру в строку и
        выравнивает для терминального вывода строку согласно заданной ширине.

        :param digit:
        :param width:
        :return:
        """
        return f"{str(digit)}.".ljust(width)

    # ориентируемся на число элементов в списке
    elem_count = len(list_to_choose)
    # число разрядов в количестве элементов в списке + точка
    digits = len(str(elem_count)) + 1
    # Проверяем на число элементов в списке.
    if elem_count > 1:
        # если в списке больше одного элемента
        if all_first:
            # Если задано - вывести "1. Все варианты ниже"
            # формируем название элемента
            element_text_a = f"{element_text}а " if element_text else ""
            # формируем список элементов для выбора
            ask_elem = "\n".join([f"{ljust(n, digits)} Только для {element_text_a}\"{elem}\""
                                  for n, elem in enumerate(list_to_choose, 2)])
            # формируем первый элемент для выбора всех вариантов
            call_text = f" {element_text}ов" if element_text else " элементов"
            for_all_text = f"{LINE}" + f"1. Для ВСЕХ{call_text} ниже.\n"
        else:
            # если задан вывод только элементов без выбора всех вариантов
            # формируем название элемента
            element_text = f"{element_text.capitalize()} " if element_text else ""
            # формируем список элементов для выбора
            ask_elem = "\n".join([f"{ljust(n, digits)} {element_text}{elem}"
                                  for n, elem in enumerate(list_to_choose, 1)])
            for_all_text = f"{LINE}"

        ask_to_choose = f"{LINE}" \
                        f"{ask_to_choose}\n" \
                        f"{for_all_text}" \
                        f"{ask_elem}\n" \
                        f"{LINE}" \
                        f"Пожалуйста, выберите номер варианта: "

        # количество элементов для выбора
        len_count = len(list_to_choose) + 1
        # через консоль запрашиваем выбор пользователя для продолжения
        while 1:
            # запрашиваем выбор пользователя через консоль
            chosen = int(input(ask_to_choose))
            # фильтруем введенные данные
            # chosen = re.findall(pattern=regex, string=chosen)
            # преобразуем данные в целое число
            # chosen = int("".join(chosen)) if chosen else -1
            # проводим анализ ввода
            if 1 <= chosen <= len_count:
                # если выбор пал на одно из указанных значений, то выходим из цикла
                if all_first:
                    # если первый пункт ВСЕ что ниже
                    chosen = list_to_choose if chosen == 1 else [list_to_choose[chosen - 2]]
                else:
                    # Если без выбора всех
                    chosen = [list_to_choose[chosen - 1]]
                break
            else:
                # если данные введены не верно, продолжаем опрос
                continue
    else:
        # в случае единственного интерфейса
        chosen = list_to_choose

    return chosen


def floor(num: float) -> int:
    """
    Функция округляет число в большую сторону

    :param num: число с плавающей запятой, которое необходимо округлить.
    :return: целочисленное.
    """
    return int(num + (0.5 if num > 0 else -0.5))


def is_url_valid(url: str) -> bool:
    """
    Функция проверяет ссылку на доступность

    :param url:
    :return:
    """

    h = Http()
    try:
        resp = h.request(url, 'HEAD')
        result = int(resp[0][etag.status]) < 400
    except error.HttpLib2Error:
        result = False

    return result


def is_host_valid(host: str) -> bool:
    """
    Функция проверяет на правильность введенного имени

    :param host: проверяемое имя хоста
    :return:
    """
    from socket import (gethostbyname, gaierror)
    try:
        gethostbyname(host)
        result = True
    except gaierror:
        result = False
    return result


def is_email_valid(email: str) -> bool:
    """
    Функция проверяет на правильность переданный email
    Источник: https://uproger.com/python-proveryaem-adresa-elektronnoj-pochty-s-pomoshhyu-regulyarnyh-vyrazhenij/
    :param email: передаваемый email для проверки
    :return: True - email верен, и False - если нет.
    """
    import re
    regex = re.compile(
            r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|"
            r"(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])")
    result = True if re.fullmatch(regex, email) else False
    return result


def get_alpha_digits_only(text: str) -> str:
    """
    Функция оставляет в строке только буквы и цифры, остальные символы убирает

    :param text:
    :return:
    """
    return ''.join(filter(lambda x: x.isdigit() or x.isalpha(), text))


def has_inside(checking_list: list, source: str) -> bool:
    """
    Функция проверят, содержится ли в передаваемой
    строке один или несколько элементов из списка.

    :param checking_list: список элементов для проверки.
    :param source: строка-источник в которой ищется совпадение элементов из списка.

    :return: True - один из элементов содержится в списке
             False - ни один из элементов не содержится в строке
    """
    # Проверяем на наличие записей
    if source:
        #  переводим все в нижний регистр
        _source = source.lower()
        #  Проверяем наличие
        result = True if [elem for elem in checking_list if elem.lower() in _source] else False
    else:
        #  если нет записей возвращаем False
        result = False

    return result


def get_inside(checking_list: list, source: str) -> list:
    """
    Функция возвращает, совпадающие подстроки в строке источнике, если они
    совпадают полностью или частично с одним из элементов из списка.

    :param checking_list: список элементов для проверки, которые ищутся в строке источнике source.
    :param source: строка-источник в которой ищется совпадение элементов из списка - checking_list.

    :return: список элементов, которые совпали с оригиналами и содержится в списке искомых элементов
    """

    # Проверяем на наличие записей
    if source:
        #  переводим все в нижний регистр
        _source = source.lower().split()
        source_ = source.split()
        result = []
        #  Проверяем наличие
        # result = [(sub_src for sub_fnd, sub_src in zip(_source, source_) if elem.lower() in sub_fnd) for elem in
        #           checking_list]
        for elem in checking_list:
            # объедением элементы списков для того, чтобы возвратить
            # именно исходный текст с сохранением регистра
            for sub_fnd, sub_src in zip(_source, source_):
                # проверяем на совпадение
                if elem.lower() in sub_fnd:
                    result.append(sub_src)
    else:
        #  если нет записей возвращаем пустой список
        result = []

    return result


def bold(text_to_bold: str) -> str:
    """
    Функция оборачивает текст в html тег
    :param text_to_bold: текст для обертки

    :return: текст обернутый в html тег "жирный"
    """

    return f"<b>{text_to_bold}</b>"


def mult(source: list[bool | int], and_mode: bool = True) -> bool | int:
    """
    Функция возвращает произведение или сложение элементов однородного списка

    :param and_mode: режим работы, если and_mode = True (по умолчанию),
            то производим операцию умножения, а если False, то сложения.
    :param source: однородный список булевых или целочисленных элементов.
    :return: произведение элементов однородного списка (bool или int)
    """
    n = False
    if source:
        typeof_bool = isinstance(source[0], int)
        # если тип данных логический и
        # задан режим сложения (and_mode = False)
        if typeof_bool and not and_mode:
            true = [1 for v in source if v]
            false = [1 for v in source if not v]
            n = True if true >= false else False
        else:
            n = source[0]
            for el in source:
                if and_mode:
                    n *= el
                else:
                    n += el
        n = bool(n) if typeof_bool else n

    return n


def clean_html(raw_html: str) -> str:
    """
    Функция удаляет все html теги из текста

    :param raw_html: текст с html тегами
    :return:
    """
    cleantext = raw_html
    if '<' in cleantext:
        # если внутри есть один из основных символов html кода
        import re
        reg_ex = re.compile('<.*?>')
        # применяем к строке регулярное выражение
        cleantext = re.sub(reg_ex, '', cleantext)

    return cleantext


def unite_list(mixed_list: list, is_uniq: bool = False) -> list:
    """
    Функция из смешанного списка, который может содержать много вложенных списков
    формирует один единый список из всех подсписков внутри источника mixed_list

    Например, есть список-источник [['aaa',222,'ggg', [222,[111,222,[222,444]]]]]
    результатом выполнения функции будет список ['aaa',222,'ggg',222,111,222,222,444],
    при выключенном флаге is_uniq и ['aaa',222,'ggg',111,444] при включенном флаге

    :param mixed_list: целевой смешанный список.
    :param is_uniq: флаг уникальности, если включен,
                    то возвращаются только уникальные значения в списке.
    :return: объединенный список из всех под-списков внутри mixed_list
    """
    flat_list = []

    def add_to_list(mixed: list) -> None:
        """
        Внутрення функция для обеспечения рекурсии.

        :param mixed: смешанный список с подсписками внутри.
        :return: готовый плоский список без вложенности
        """
        for elem in mixed:
            if isinstance(elem, list):
                # если элемент является вложенным списком,
                # то делаем рекурсию с этим элементом
                add_to_list(elem)
            else:
                # если это не список,
                # то добавляем в список
                flat_list.append(elem)

    # получаем в глобальной переменной
    # flat_list (по отношению к внутренней функции)
    # плоский список - необходимый результат
    add_to_list(mixed_list)
    #  возвращаем результат, и получаем уникальные значения, если задано
    return flat_list if not is_uniq else unique_list(flat_list)


def get_domain_list(source: str, uniq: bool = True) -> list:
    """
    Функция возвращает список отдельных элементов из строки.
    При этом, элементы в строке могут быть разделены, любыми
    из следующих символов: пробел, запятая, точка с запятой,
    символ новой строки и символ табуляции.

    Например, есть строка:
    site1.ru site5.ru; site3.ru
    site4.ru, site2.ru,    site3.ru
    результатом работы функции будет список состоящий из элементов:
    ['site1.ru', 'site5.ru', 'site3.ru', 'site4.ru', 'site2.ru']

    :param source: строка элементами, вместе с различными разделителями.
    :param uniq: флаг уникальности, если включен,
                    то возвращаются только уникальные значения в списке.
    :return: список из элементов внутри строки-источника
    """

    # строка символов разделителей
    sep_list = ' \n\t\r,;'
    result = source.lower()
    # первый символ разделитель будет являться основным разделителем
    base_sep = sep_list[0]
    # остальные разделители
    sep_list = sep_list[1:]
    # генерируем список разделителей, которые присутствуют в строке-источнике
    sep_lint_in = [sep for sep in sep_list if sep in source]
    # проходимся по каждому символу
    for sim in sep_lint_in:
        # заменяем остальные символы разделители на основной разделитель
        result = result.replace(sim, base_sep)
    # формируем список на базе основного разделителя
    result = result.split(base_sep)
    # в случае, если задан флаг уникальности, то
    # оставляем только уникальные значения без изменения их порядка в списке
    result = unique_list(result) if uniq else result
    # удаляем из списка пустые значения, если список не пустой
    result = [elem for elem in result if elem and etag.dot in elem] if result else [source]

    return result


def unique_list(list_elements: list) -> list:
    """
    Функция оставляет только уникальные
    значения без изменения их порядка в списке.

    :param list_elements: список исходных элементов.
    :return: список уникальных значений
    """
    un_list = []
    for item in list_elements:
        if item and item not in un_list:
            # если элемента нет в списке
            # уникальных значений, то добавляем его
            un_list.append(item)

    return un_list


def clean_me(source: str, sims_to_del='.,{}[]:/ ', digits_rm: bool = False) -> str:
    """
    Функция очищает строку от заданных символов
    
    :param source: строка для обработки
    :param sims_to_del: строка символов для удаления в целевой строке.
    :param digits_rm: если True - удаляем цифры из строки
    :return: очищенную строку
    """
    tr = source
    for sm in sims_to_del:
        tr = tr.replace(sm, '')

    return get_alpha(tr) if digits_rm else tr


def get_file_content(file: str) -> list:
    """
    Функция получает содержимое файла в виде списка строк.

    :param file: полный путь к файлу вместе с именем.
    :return: содержимое файла в виде списка строк.
    """
    cmd = f"cat {file}"
    result, out = run(command=cmd)
    if result and out:
        lines = out.splitlines()
        lines = [ln for ln in lines if ln]
    else:
        if 'No such file' in out:
            cmd = f"touch {file}"
            run(command=cmd)

        lines = []

    return lines


def get_time_creation(file: str) -> (str, str, str, str, str, str):
    """
    Функция возвращает дату создания файла в виде кортежа
    :param file: полный путь до файла
    :return: day, month, year, hh, mm, ss
    """
    cmd = f"stat '{file}' | grep 'Modify:' | cut -d' ' -f2-3 | cut -d'.' -f1"
    result, out = run(command=cmd)
    day, month, year, hh, mm, ss = -1, -1, -1, -1, -1, -1
    if result and out:
        _out = out.split()
        date_out = _out[0].split('-')
        time_out = _out[1].split(':')
        day, month, year = date_out[2], date_out[1], date_out[0]
        hh, mm, ss = time_out[0], time_out[1], time_out[2]

    return day, month, year, hh, mm, ss


def lines_in_file(file: str) -> int:
    """
    Функция осуществляет подсчет строк в файле

    :param file: полный путь до файла.
    :return: число строк в файле int
    """
    cmd = f"cat '{file}' | wc -l"
    result, out = run(command=cmd)
    return int(out) if result else -1


def rm_file(file: str) -> bool:
    """
    Функция удаляет указанный файл.
    :param file: полный путь до файла.
    :return: булевый результат выполнения
    """
    cmd = f"rm -f '{file}'"
    result, _ = run(command=cmd)
    return result


def listdir(path: str) -> list:
    """
    Функция возвращает список имен файлов в указанной папке

    :param: path: путь к папке.
    :return: список файлов
    """
    cmd = f"ls '{path}' | grep -v '/'"
    result, out = run(command=cmd)
    return [f for f in out.split('\n') if f] if result else []


def mkdir(path: str) -> bool:
    """
    Функция создает указанную папку с необходимыми вложениями.
    :param path: путь который необходимо создать.
    :return: булевый результат исполнения команды
    """
    cmd = f"mkdir -p '{path}'"
    result, _ = run(command=cmd)
    return result


def check(file: str, subject: int) -> bool:
    """
    Функция проверяет наличие указанных файла или папки

    :param file: полный путь к искомому субъекту (папке или файлу)
    :param subject: PATH - флаг-указатель на папку (параметр SUBJECT)
                    FILE - флаг-указатель на файл (параметр SUBJECT).
    :return: True - субъект существует
             False - субъект отсутствует
    """
    # если флаг проверки указан верно
    if subject == PATH or subject == FILE:
        # формируем флаг поиска для bash команды
        mode = 'f' if subject == FILE else 'd'
        # формируем bash команду для проверки субъекта
        cmd = f"if [ -{mode} '{file}' ]; then echo 1; else echo 0; fi"
        # исполняем команду
        result, out = run(command=cmd)
        # анализируем результат и возвращаем соответствующее знание
        result = True if result and out == '1\n' else False
    else:
        # если флаг проверки указан неверно, то вызываем исключение
        raise Exception(f'Неверно указан субъект "{subject}" проверки в функции check!')

    return result


def check_url(link: str, check_for_validation: bool = True, domain_only: bool = False) -> str:
    """
    Функция проверяет полученный текст ссылки
    и проверяет его на корректность.

    :param link: текст ссылки, который необходимо проверить.
    :param check_for_validation: флаг проверки на доступность ссылки.
    :param domain_only: Если True - возвращаем только доменное имя, False (по умолчанию) - полную ссылку с http...
    :return: пусто, в случае, если ссылка указана неверно с ошибками или саму ссылку (зависит от флага domain_only)

    """
    url = urlparse(link)
    # получаем доменное имя, если оно из-за ошибки в написании вдруг попало в url.path
    dm = url.path.split(etag.slash)[0]
    has_dot_in_path = etag.dot in dm
    regex = r'([a-zA-Z\d-]{2,63}){1,5}(\.[a-zA-Z\d-]{2,6})*'
    domain = findall(regex, dm) if not url.netloc and has_dot_in_path else url.netloc
    # если имя домена передано корректно
    if domain:
        # получаем префикс протокола
        scheme = f'{etag.https}://' if etag.https in url.scheme else f'{etag.http}://' if etag.http in url.scheme else ''
        # получаем путь после доменного имени
        path = url.path.replace(f"{etag.slash}{etag.slash}", f'{etag.slash}')
        # получаем данные get запроса после доменного имени
        query = f"?{url.query}" if url.query else ''
        # формируем полную проверенную ссылку
        link = f'{domain}' if domain_only else f'{scheme}{domain}{path}{query}'
        # проверяем флаг проверки доступности данных по ссылке
        result = (link if is_url_valid(link) else '') if check_for_validation and etag.http in link else link

    else:
        # если домен введен некорректно
        result = ''

    return result


def check_file(file: str) -> bool:
    """
    Функция проверяет наличие любого файла по его имени

    :param file: полный путь к проверяемому файлу.
    :return: True - файл существует
             False - файл отсутствует
    """
    return check(file=file, subject=FILE)


def check_path(path: str) -> bool:
    """
    Функция проверяет наличие любого пути или папки

    :param path: полный путь к проверяемой папке.
    :return: True - папка существует
             False - папка отсутствует
    """
    return check(file=path, subject=PATH)


def pwd(file_name: str) -> str:
    """
    Функция возвращает директорию в которой
    расположен файл с указанным именем

    :param file_name: имя файла.
    :return: путь до файла
    """
    cmd = f"find ./ | grep '{file_name}' | head -1"
    result, out = run(command=cmd)
    return out.split('/')[:-1] if result else ''
    # from os.path import (dirname, realpath)
    # return dirname(realpath(file_name))


def get_ip_only(text: str) -> str:
    """
    Функция извлекает из переданной строки только ip адрес
    остальное удаляет

    :param text: текст дя анализа.
    :return: строку с ip адресом6 если он есть
    """
    from re import findall
    regex = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    # ip = "".join([ch for ch in text if (ch.isdigit() or ch == '.')])
    return "".join(findall(regex, text))


def get_url_only(text: str) -> str:
    """
    Функция извлекает из переданной строки только имя хоста

    :param text: передаваемый текст
    :return: хост
    """
    from re import findall
    regex = r'[a-zA-Z\d-]{2,63}(\.[a-zA-Z\d-]{2,6})*'
    return "".join(findall(regex, text))


def base_name(path_to_file: str) -> str:
    """
    Функция возвращает имя файла исключая путь до него

    :param path_to_file: полный путь до файла с его именем.
    :return: только имя файла
    """
    return path_to_file.split("/")[-1]


def base_path(path_to_file: str) -> str:
    """
    Функция возвращает путь до файла, исключая его имя

    :param path_to_file: полный путь до файла с его именем.
    :return: только путь до файла
    """
    return "/".join(path_to_file.split('/')[:-1])


def get_digits(source: str | int) -> int:
    """
    Функция фильтрует строку и возвращает только цифры находящиеся в строке

    :param source: строка источник
    :return: цифры, содержащиеся в строке
    """
    res = source if isinstance(source, int) else int("".join([s for s in source if s.isdigit()]))
    return res if res else -1


def get_alpha(source: str) -> str:
    """
    Функция фильтрует строку и возвращает только цифры находящиеся в строке

    :param source: строка источник
    :return: цифры, содержащиеся в строке
    """

    return "".join([s for s in source if s.isalpha()])


def find_in_file(filename: str, to_find: str) -> str:
    """
    Функция возвращает строку по заданному вхождению

    :param filename: полный путь до файла
    :param to_find: искомый отрывок в строке
    :return:
    """
    cmd = f"cat '{filename}' | grep '{to_find}'"
    result, founded = run(command=cmd)
    # lines = open(filename, 'r').readlines()
    # return "".join([line for line in lines if line.find(to_find) > 1])
    return founded if result else ''


def write_to_file(file: str, lines: list, mode: str = ADD_TO_END) -> bool:
    """
    Функция записывает данные в файл

    :param file: имя файла с полным путем до него.
    :param lines: список данных, которые требуется записать в файл.
    :param mode: режим записи в файл
                 ADD_TO_END - добавить в конец файла (по умолчанию)
                 CREATE_NEW - создать новый файл.

    :return: результат создания.
    """

    # путь до файла без имени
    path_to_file = base_path(path_to_file=file)
    # проверяем путь до файла, если его нет создаем папку
    if not check_path(path=path_to_file):
        mkdir(path_to_file)
    # в зависимости от режима записи данных формируем команду
    mode_cmd = '>>' if mode == ADD_TO_END else '>'

    # избавляемся от пустых строк в данных
    lines = "\n".join([ln for ln in lines if ln])

    # записываем данные
    cmd = f'cat <<EOF {mode_cmd} {file}\n{lines}\nEOF'
    result, _ = run(command=cmd)
    # возвращаем результат
    return result

    # удаляем пустые строки
    # cmd = f'sed -i "/^$/d" {file}'
    # result_2, _ = run(command=cmd)
    # если оба результата прошли успешно, то и вся операция успешна
    # return result_1 and result_2


def has_error(target_list: list) -> bool:
    """
    Функция обнаруживает признак ошибки в переданном списке
    - подстроку с "error" и возвращает True, если это так

    :param target_list: целевой список
    :return: True - ошибка найдена, False - ошиок нет
    """
    return True if [i for i in target_list if i.lower().find(etag.error) > 1] else False


def run(command: str, stderr: int = PIPE) -> (bool, str):
    """
    Функция обработки и исполнения заданной команды в терминале bash

    :param command: срока с командой bash
    :param stderr: канал для вывода ошибок, по умолчению - консоль
    :return: result - True, все хорошо, False - ошибка при исполнении
             out - консольный вывод команды
    """
    global ACCESS_REMOTE
    # проверяем на исполнение удаленного запуска-отладки
    # if ACCESS_REMOTE is None:
    #     # если флаг ACCESS_REMOTE не определен, то
    #     # определяем наличие файла с именем текущей ОС
    #     file = '/etc/os-release'
    #     cmd = f"if [ -f '{file}' ]; then echo 1; else echo 0; fi"
    #     reply = bash(args=cmd, stdout=PIPE, text=True, shell=True)
    #     # устанавливаем флаг ACCESS_REMOTE в True, в случае, если файл имеется
    #     # (на роутере такого файла быть не должно)
    #     ACCESS_REMOTE = True if reply.returncode == 0 and reply.stdout == '1\n' else False

    if ACCESS_REMOTE:
        # если производится удаленный запуск команды bash
        # то производим подстановку заглушки для удаленного доступа к роутеру
        shell = True
        cmd = command.replace('"', '\\"')
        cmd = f'{REMOTE_ACCESS_CMD} "{cmd}"'

    else:
        # если производится запуск на роутере, то проверяем
        # на наличие в строке разделителей команд
        # и если они есть, то меняем режим исполнения - флаг shell
        cmd_chars = ["|", "{", "}", "/", ">", "<", "&&"]
        has_cmd_chars = mult([True for k in cmd_chars if k in command])
        cmd, shell = (command, True) if has_cmd_chars else (command.split(), False)

    zlog.info(f"Команда: '{command}'")
    # исполняем команду
    reply = bash(args=cmd, stdout=PIPE, text=True, shell=shell, stderr=stderr)
    # проверяем результат исполнения
    if reply.returncode == 0:
        # если все прошло хорошо
        result, out = True, reply.stdout
        zlog.debug(f"Результат: '{reply.stdout}'")
    else:
        # если была ошибка
        result, out = False, reply.stderr
        zlog.error(f"Ошибка: '{reply.stderr}'")

    return result, out
