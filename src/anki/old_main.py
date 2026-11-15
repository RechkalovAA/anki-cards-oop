import random
import sys
import time
from pathlib import Path

STOP_WORD = "СТОП"
WORDS_FILE = Path(__file__).resolve().parent / "words.txt"


def load_words(filename: str = "words.txt") -> dict[str, str]:
    """Загружает словарь пар слово-перевод из файла."""
    words: dict[str, str] = {}
    try:
        with open(filename, encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                parts = line.split(",")
                if len(parts) != 2:
                    continue
                word = parts[0].strip()
                translation = parts[1].strip()
                words[word] = translation
    except FileNotFoundError:
        print(f"Файл {filename} не найден.")
        sys.exit(1)
    return words


def print_statistics(score: int, total_time: float) -> None:
    """Выводит итоговый счёт и среднее время ответа."""
    print(f"Ваш итоговый счет: {score}")
    if score > 0:
        average = round(total_time / score, 2)
        print(
            f"Время игры: {total_time:.2f} секунд "
            f"(среднее время: {average:.2f} сек.)"
        )
    else:
        print(f"Время игры: {total_time:.2f} секунд " f"(среднее время: —)")


def ask_and_check(word: str, correct: str) -> tuple[bool, bool, float]:
    """Спрашивает перевод слова и проверяет ответ пользователя."""
    print("Ваше слово:", word)
    start_time = time.time()
    answer = input("Ваш перевод: ")
    end_time = time.time()
    if answer.strip().lower() == STOP_WORD.lower():
        return True, False, 0.0
    answer_time = end_time - start_time
    is_correct = answer.strip().lower() == correct.strip().lower()
    return False, is_correct, answer_time


def start_game(words: dict[str, str]) -> None:
    """Запускает обычную тренировку перевода случайных слов."""
    if not words:
        print("В словаре нет слов для игры.")
        return
    print("Чтобы закончить, введите СТОП")
    score = 0
    total_time = 0.0
    word_list = list(words.keys())
    while True:
        word = random.choice(word_list)
        correct = words[word]
        is_stop, is_correct, answer_time = ask_and_check(word, correct)
        total_time += answer_time
        if is_stop:
            break
        if is_correct:
            score += 1
            print(f"Верно! Время на ответ: {answer_time:.2f} секунд")
        else:
            print(
                f"Неправильно, правильный ответ: {correct} "
                f"(Время на ответ: {answer_time:.2f} секунд)"
            )
    print("Спасибо за игру!")
    print_statistics(score, total_time)


def train_until_mistake(words: dict[str, str]) -> None:
    """Запускает тренировку до первой ошибки или слова СТОП."""
    print("Режим: Игра до первой ошибки! " "Чтобы выйти вручную, введите СТОП")
    if not words:
        print("В словаре нет слов для игры.")
        return
    score = 0
    total_time = 0.0
    word_list = list(words.keys())
    while True:
        word = random.choice(word_list)
        correct = words[word]
        is_stop, is_correct, answer_time = ask_and_check(word, correct)
        total_time += answer_time
        if is_stop:
            print("Выход из режима по запросу пользователя.")
            break
        if is_correct:
            score += 1
            print(
                f"Верно! Всего очков: {score} " f"(ответ за {answer_time:.2f} секунд)"
            )
        else:
            print(f"Ошибка! Неверно. Правильный ответ: {correct}")
            break
    print_statistics(score, total_time)


def add_words(words: dict[str, str]) -> None:
    """Добавляет новые пары слово-перевод в словарь."""
    print("Чтобы закончить, введите СТОП")
    while True:
        word = input("Введите слово: ")
        if word.strip().lower() == STOP_WORD.lower():
            break
        translation = input("Введите перевод: ")
        if translation.strip().lower() == STOP_WORD.lower():
            break
        words[word] = translation


def show_all_words(words: dict[str, str]) -> None:
    """Выводит все пары словаря одной строкой."""
    pairs = []
    for word, translation in words.items():
        pairs.append(f"{word} - {translation}")
    print("; ".join(pairs))


def save_words(
    words: dict[str, str],
    filename: str = "words.txt",
) -> None:
    """Сохраняет словарь пар слово-перевод в файл."""
    with open(filename, "w", encoding="utf-8") as file:
        for word, translation in words.items():
            file.write(f"{word}, {translation}\n")
    print(f"Было сохранено {len(words)} слов в файл {filename}")


def main() -> None:
    """Запускает меню тренажёра слов."""
    words = load_words(str(WORDS_FILE))
    print(f"Было загружено {len(words)} слов из файла words.txt")
    while True:
        print("Меню:")
        print("    1. Начать игру")
        print("    2. Добавить слова")
        print("    3. Тренировка до первой ошибки")
        print("    4. Вывод всех слов")
        print("    5. Выход")
        menu_choice = input("Пункт меню: ")
        if menu_choice == "1":
            start_game(words)
        elif menu_choice == "2":
            add_words(words)
        elif menu_choice == "3":
            train_until_mistake(words)
        elif menu_choice == "4":
            show_all_words(words)
        elif menu_choice == "5":
            save_words(words, str(WORDS_FILE))
            sys.exit()
        else:
            print("Неизвестный пункт меню")
            print("Повторите ввод.")


if __name__ == "__main__":
    main()
