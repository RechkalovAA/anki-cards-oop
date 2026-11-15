from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anki.anki import Anki, SessionStats


class TextUI:
    """Консольный интерфейс: меню, тренировка и редактирование словаря."""

    STOP_WORD: str = "СТОП"
    _anki_game: Anki
    _is_running: bool
    _command_definition: list[tuple[Callable[..., None], str, Callable[..., bool]]]

    def __init__(self, anki_game: Anki) -> None:
        """Сохраняет игру и список команд меню.

        Args:
            anki_game: Экземпляр Anki с колодой слов.
        """
        self._anki_game = anki_game
        self._is_running = False
        self._command_definition = [
            (
                self.start_game,
                "Начать игру",
                lambda: len(self._anki_game) > 0,
            ),
            (self.add_words, "Добавить слова", lambda: True),
            (
                self.train_until_mistake,
                "Тренировка до первой ошибки",
                lambda: len(self._anki_game) > 0,
            ),
            (
                self.train_until_time_runs_out,
                "Тренировка на время",
                lambda: len(self._anki_game) > 0,
            ),
            (
                self.find_translation,
                "Найти перевод",
                lambda: len(self._anki_game) > 0,
            ),
            (
                self.show_words,
                "Показать все слова",
                lambda: len(self._anki_game) > 0,
            ),
            (self.stop, "Выход", lambda: True),
        ]

    def stop(self) -> None:
        """Останавливает главный цикл меню."""
        self._is_running = False

    def get_available_commands(
        self,
    ) -> list[tuple[Callable[..., None], str]]:
        """Возвращает команды, которые сейчас можно показать в меню.

        Returns:
            Список пар из обработчика и подписи пункта. Номер пункта
            определяется порядком в этом списке.
        """
        commands = []
        for func, description, is_visible in self._command_definition:
            if is_visible():
                commands.append((func, description))
        return commands

    def find_translation(self) -> None:
        """Спрашивает слово и печатает его перевод или сообщение об отсутствии."""
        word = input("Введите слово: ")
        if word in self._anki_game:
            print(self._anki_game.get_translation(word))
            return
        print("Слово отсутствует в словаре.")

    def _is_stop_word(self, value: str) -> bool:
        """Проверяет, ввёл ли пользователь слово завершения."""
        return value.strip().lower() == self.STOP_WORD.lower()

    def start_game(self) -> None:
        """Спрашивает переводы случайных слов, пока не введено стоп-слово."""
        print(f"Чтобы закончить, введите {self.STOP_WORD}")
        while True:
            try:
                word = self._anki_game.get_random_word()
            except ValueError as error:
                print(error)
                return
            print(f"Ваше слово: {word}")
            answer = input("Ваш перевод: ")
            if self._is_stop_word(answer):
                break
            if self._anki_game.check_translation(word, answer):
                print("Верно!")
            else:
                correct = self._anki_game.get_translation(word)
                print(f"Неправильно, правильный ответ: {correct}")

    def add_words(self) -> None:
        """Запрашивает новые пары и добавляет их в игру до стоп-слова."""
        print(f"Чтобы закончить, введите {self.STOP_WORD}")
        while True:
            word = input("Введите слово: ")
            if self._is_stop_word(word):
                break
            translation = input("Введите перевод: ")
            if self._is_stop_word(translation):
                break
            self._anki_game.add_word(word, translation)

    def train_until_mistake(self) -> None:
        """Тренирует перевод до первой ошибки и печатает итог сессии."""
        print(f"Чтобы закончить, введите {self.STOP_WORD}")
        training = self._anki_game.start_zero_mistakes_training()
        while True:
            try:
                word = training.get_random_word()
            except ValueError as error:
                print(error)
                if training.active:
                    training.end_session()
                break
            print(f"Ваше слово: {word}")
            answer = input("Ваш перевод: ")
            if self._is_stop_word(answer):
                training.end_session()
                break
            if training.check_translation(word, answer):
                print("Верно!")
                continue
            correct = self._anki_game.get_translation(word)
            print(f"Неправильно, правильный ответ: {correct}")
            break
        self._print_training_stats(training.get_stat())

    def train_until_time_runs_out(self) -> None:
        """Тренирует перевод, пока не истечёт время, и печатает итог."""
        print(f"Чтобы закончить, введите {self.STOP_WORD}")
        raw_limit = input("Введите время тренировки в секундах: ")
        time_limit = float(raw_limit)
        training = self._anki_game.start_time_limited_training(time_limit)
        while training.active:
            try:
                word = training.get_random_word()
            except ValueError as error:
                print(error)
                if training.active:
                    training.end_session()
                break
            print(f"Ваше слово: {word}")
            answer = input("Ваш перевод: ")
            if self._is_stop_word(answer):
                training.end_session()
                break
            if training.check_translation(word, answer):
                print("Верно!")
            else:
                correct = self._anki_game.get_translation(word)
                print(f"Неправильно, правильный ответ: {correct}")
        self._print_training_stats(training.get_stat())

    def _print_training_stats(self, stats: SessionStats) -> None:
        """Печатает число верных ответов и длительность тренировки."""
        print(f'Правильных ответов: {stats["correct_answers"]}')
        print(f'Время игры: {stats["total_time"]:.2f} секунд')

    def show_words(self) -> None:
        """Печатает число слов и пары в формате «слово - перевод»."""
        print(f"Всего слов: {len(self._anki_game)}")
        for word, translation in self._anki_game:
            print(f"{word} - {translation}")

    def main_loop(self) -> None:
        """Показывает динамическое меню и выполняет выбранный пункт до выхода."""
        self._is_running = True
        while self._is_running:
            menu_choices: list[str] = []
            commands: dict[str, Callable[..., None]] = {}
            for index, (func, description) in enumerate(
                self.get_available_commands(),
                1,
            ):
                menu_choices.append(f"{index}. {description}")
                commands[str(index)] = func
            print("Меню:\n" + "\n".join(menu_choices))
            choice = input("Выберите пункт: ").strip()
            if choice in commands:
                commands[choice]()
            else:
                print("Неверный пункт меню")
            print()
