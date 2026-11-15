from __future__ import annotations

import copy
import random
import time
from collections.abc import Iterator
from typing import TypedDict


class SessionStats(TypedDict):
    """Итог одной тренировочной сессии."""

    correct_answers: int
    total_time: float


class TrainingSession:
    """Общая тренировка поверх колоды Anki.

    Хранит активность, время и счёт. Правила начисления очков
    и завершения остаются в классах-наследниках.
    """

    active: bool
    _anki: Anki
    _start_time: float
    _end_time: float
    _user_score: int
    _last_word: str | None

    def __init__(self, anki: Anki) -> None:
        """Запоминает колоду и отмечает начало тренировки.

        Args:
            anki: Колода, из которой берутся слова и проверка перевода.
        """
        self.active = True
        self._anki = anki
        self._start_time = time.time()
        self._end_time = self._start_time
        self._user_score = 0
        self._last_word = None

    def get_random_word(self) -> str:
        """Возвращает случайное слово и запоминает его как последнее выданное.

        Returns:
            Слово из колоды.

        Raises:
            ValueError: Если тренировка уже завершена.
        """
        if not self.active:
            raise ValueError("Нельзя получить слово: тренировка не активна.")
        word = self._anki.get_random_word()
        self._last_word = word
        return word

    def check_translation(self, word: str, translation: str) -> bool:
        """Проверяет перевод только для последнего выданного слова.

        Args:
            word: Слово, которое переводит пользователь.
            translation: Перевод, который ввёл пользователь.

        Returns:
            True, если перевод совпадает с сохранённым.

        Raises:
            ValueError: Если тренировка не активна или слово не последнее
                выданное.
        """
        if not self.active:
            raise ValueError("Нельзя проверять перевод: тренировка не активна.")
        normalized_word = self._anki.normalize_word(word)
        if normalized_word != self._last_word:
            self.end_session()
            raise ValueError(
                "Можно проверять только последнее слово, "
                "выданное методом get_random_word()."
            )
        self._last_word = None
        return self._anki.check_translation(word, translation)

    def end_session(self) -> None:
        """Завершает тренировку и снимает блокировку колоды.

        Raises:
            ValueError: Если тренировка уже завершена.
        """
        if not self.active:
            raise ValueError("Нельзя завершить неактивную тренировку.")
        self.active = False
        self._end_time = time.time()
        self._anki.end_session()

    def get_stat(self) -> SessionStats:
        """Возвращает число верных ответов и длительность тренировки.

        Returns:
            Словарь с ключами correct_answers и total_time.
        """
        if self.active:
            total_time = time.time() - self._start_time
        else:
            total_time = self._end_time - self._start_time
        return {
            "correct_answers": self._user_score,
            "total_time": total_time,
        }


class ZeroMistakesTraining(TrainingSession):
    """Тренировка, которая заканчивается на первой ошибке."""

    def check_translation(self, word: str, translation: str) -> bool:
        """Проверяет перевод и завершает тренировку при ошибке.

        Args:
            word: Слово, которое переводит пользователь.
            translation: Перевод, который ввёл пользователь.

        Returns:
            True, если перевод верный.
        """
        is_correct = super().check_translation(word, translation)
        if is_correct:
            self._user_score += 1
        else:
            self.end_session()
        return is_correct


class TimeLimitedTraining(TrainingSession):
    """Тренировка с лимитом времени.

    Последний ответ принимается даже если время уже вышло.
    После этого ответа сессия завершается.
    """

    _time_limit: float

    def __init__(self, anki: Anki, time_limit: float = 60.0) -> None:
        """Запоминает колоду и лимит времени в секундах.

        Args:
            anki: Колода, из которой берутся слова.
            time_limit: Сколько секунд длится тренировка.
        """
        super().__init__(anki)
        self._time_limit = time_limit

    def check_translation(self, word: str, translation: str) -> bool:
        """Проверяет перевод и завершает тренировку, если время вышло.

        Остаток времени смотрится до проверки ответа, но сам ответ
        всё равно принимается.

        Args:
            word: Слово, которое переводит пользователь.
            translation: Перевод, который ввёл пользователь.

        Returns:
            True, если перевод верный.
        """
        time_is_up = (time.time() - self._start_time) >= self._time_limit
        is_correct = super().check_translation(word, translation)
        if is_correct:
            self._user_score += 1
        if time_is_up:
            self.end_session()
        return is_correct


class Anki:
    """Хранит словарь слов и переводов для игры.

    Принимает новые пары только через нормализацию, а наружу отдаёт копию
    словаря, чтобы внешний код не менял внутреннее состояние.
    """

    _words: dict[str, str]
    _session_active: bool

    def __init__(self, *, words: dict[str, str] | None = None) -> None:
        if words is None:
            words = {}
        self._words = self._normalize_dict(words)
        self._session_active = False

    @staticmethod
    def normalize_word(word: str) -> str:
        """Приводит слово к единому виду для хранения и сравнения.

        Args:
            word: Строка, которую нужно нормализовать.

        Returns:
            Строка без пробелов по краям, приведённая к нижнему регистру.

        Raises:
            ValueError: Если word не является строкой.
        """
        if not isinstance(word, str):
            raise ValueError("Значение параметра word должно быть строкой.")
        return word.strip().lower()

    def add_word(self, word: str, translation: str) -> None:
        """Добавляет в словарь нормализованную пару «слово — перевод».

        Args:
            word: Слово, которое нужно сохранить.
            translation: Перевод этого слова.

        Raises:
            ValueError: Если word или translation не являются строками.
        """
        if not isinstance(word, str) or not isinstance(translation, str):
            raise ValueError("Слово и перевод должны быть строками.")
        self._words[self.normalize_word(word)] = self.normalize_word(translation)

    def _normalize_dict(self, words: dict[str, str]) -> dict[str, str]:
        """Возвращает словарь, в котором ключи и значения нормализованы.

        Args:
            words: Словарь пар «слово — перевод».

        Returns:
            Новый словарь с нормализованными строками.

        Raises:
            ValueError: Если words не словарь или внутри есть нестроковые данные.
        """
        if not isinstance(words, dict):
            raise ValueError("Параметр words должен быть словарём.")
        normalized: dict[str, str] = {}
        for word, translation in words.items():
            normalized[self.normalize_word(word)] = self.normalize_word(translation)
        return normalized

    @property
    def words(self) -> dict[str, str]:
        """Возвращает копию словаря слов и переводов.

        Returns:
            Новый словарь с теми же парами. Его изменение не меняет колоду.
        """
        return copy.copy(self._words)

    @words.setter
    def words(self, value: dict[str, str]) -> None:
        """Заменяет колоду нормализованной копией словаря value.

        Args:
            value: Новый словарь. Ключи и значения должны быть строками.

        Raises:
            ValueError: Если value не словарь, данные не строки
                или тренировка уже идёт.
        """
        if self._session_active:
            raise ValueError(
                "Нельзя полностью заменять словарь слов во время "
                "активной тренировки."
            )
        self._words = self._normalize_dict(value)

    def __contains__(self, word: str) -> bool:
        """Проверяет, есть ли слово среди ключей словаря.

        Args:
            word: Искомое слово. Перед поиском оно нормализуется.

        Returns:
            True, если нормализованное слово есть в словаре.

        Raises:
            ValueError: Если word не является строкой.
        """
        return self.normalize_word(word) in self._words

    def __iter__(self) -> Iterator[tuple[str, str]]:
        """Возвращает итератор пар «слово — перевод».

        Returns:
            Итератор элементов словаря слов.
        """
        return iter(self._words.items())

    def __len__(self) -> int:
        """Возвращает количество слов в колоде.

        Returns:
            Число пар в словаре.
        """
        return len(self._words)

    def __str__(self) -> str:
        """Возвращает краткое описание колоды.

        Returns:
            Строка с количеством сохранённых слов.
        """
        return f"Колода карт Anki, total_words: {len(self._words)}"

    def get_random_word(self) -> str:
        """Возвращает случайное слово из словаря.

        Returns:
            Ключ словаря без перевода.

        Raises:
            ValueError: Если в словаре нет слов.
        """
        if not self._words:
            raise ValueError("В словаре нет слов.")
        return random.choice(list(self._words))

    def start_zero_mistakes_training(self) -> ZeroMistakesTraining:
        """Начинает тренировку до первой ошибки.

        Returns:
            Сессия, которая завершится на неверном переводе.

        Raises:
            RuntimeError: Если тренировка уже идёт.
        """
        self._begin_session()
        return ZeroMistakesTraining(self)

    def start_time_limited_training(
        self,
        time_limit: float = 60.0,
    ) -> TimeLimitedTraining:
        """Начинает тренировку с ограничением по времени.

        Args:
            time_limit: Длительность тренировки в секундах.

        Returns:
            Сессия, которая завершится по истечении time_limit.

        Raises:
            RuntimeError: Если тренировка уже идёт.
        """
        self._begin_session()
        return TimeLimitedTraining(self, time_limit)

    def _begin_session(self) -> None:
        """Включает блокировку колоды на время тренировки.

        Raises:
            RuntimeError: Если тренировка уже идёт.
        """
        if self._session_active:
            raise RuntimeError("Нельзя начать тренировку, если она уже начата.")
        self._session_active = True

    def end_session(self) -> None:
        """Снимает блокировку колоды после тренировки.

        Raises:
            RuntimeError: Если тренировка не была начата.
        """
        if not self._session_active:
            raise RuntimeError("Нельзя завершить неактивную сессию тренировки.")
        self._session_active = False

    def check_translation(self, word: str, translation: str) -> bool:
        """Проверяет, совпадает ли перевод с сохранённым.

        Args:
            word: Слово, перевод которого нужно проверить.
            translation: Перевод, который ввёл пользователь.

        Returns:
            True, если нормализованный перевод совпадает с сохранённым.

        Raises:
            ValueError: Если слова нет в словаре или аргументы не строки.
        """
        normalized_word = self.normalize_word(word)
        normalized_translation = self.normalize_word(translation)
        if normalized_word not in self._words:
            raise ValueError(f"Слово {normalized_word} отсутствует в словаре.")
        return self._words[normalized_word] == normalized_translation

    def get_translation(self, word: str) -> str:
        """Возвращает сохранённый перевод слова.

        Args:
            word: Слово, для которого нужен перевод.

        Returns:
            Нормализованный перевод.

        Raises:
            ValueError: Если слова нет в словаре или word не строка.
        """
        normalized_word = self.normalize_word(word)
        if normalized_word not in self._words:
            raise ValueError(f"Перевод для слова {normalized_word} отсутствует.")
        return self._words[normalized_word]
