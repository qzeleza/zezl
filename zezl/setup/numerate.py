#!/bin/python3

# Автор: master
# Email: info@zeleza.ru
# Дата создания: 06.04.2022 07:29
# Пакет: PyCharm

"""
    В данном файле содержится описание класса
    который помогает автоматизировать генерацию
    кодов при создании кодов для функций захватов
    handlers при обслуживании реакций клавиш в меню

"""


class CodesEnumerate:
    """
    Класс предназначен для автоматического нумерования
    переменных и генерации кодов для них

    """

    # Список кодов, которые запрещены к выдаче данным классом
    forbidden_codes_list = "[](),*^%|\\/\"'\n\t\r\f\b +-$&.#@*:?><"

    def __init__(self):
        """
        Инициализатор класса
        """
        #  устанавливаем внутренний счетчик
        self.count = -1

    def __call__(self, count: int):
        """
        Функция повторного вызова класса для упрощенного вызова
        служит для автоматической нумерации уникальных переменных
        при ее вызове. Работает как итератор. Пример:
            generate = CodesEnumerate()
            var1, var2 = generate(2)
        Здесь будет сгенерировано несколько уникальных значений
        для переменных var1 и var2.

        :param count: количество генерируемых значений переменных.
        :return: код переменной в цикле
        """
        # общий счетчик цикла с учетом кодов,
        # которые запрещены к выдаче данным классом
        loop_count = count + self.count
        # работаем по циклу
        while self.count < loop_count:
            self.count += 1
            # генерируем символ
            result = str(chr(self.count))
            #  проверяем символ - находится ли он в списке запрещенных
            if result in self.forbidden_codes_list:
                #  если символ в списке запрещенных,
                #  то увеличиваем счетчик окончания цикла на единицу
                loop_count += 1
                # ...и делаем рекурсию
                self.__call__(self.count)
            else:
                # если символ в списке запрещенных отсутствует,
                # то возвращаем сгенерированный код
                yield result


# создаем удобное имя для обращения к генератору кодов
autoset = CodesEnumerate()