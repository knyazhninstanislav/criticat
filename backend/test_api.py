import requests
import json
import sys

BASE_URL = "http://localhost:26000"


def test_health():
    """Проверка health check"""
    print("=" * 50)
    print("1. Проверка health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   Статус: {response.status_code}")
        print(f"   Ответ: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def test_send_result():
    """Проверка отправки результата"""
    print("\n" + "=" * 50)
    print("2. Отправка тестового результата...")

    test_result = {
        "ids": 1002,
        "department": "Терапевтическое отделение",
        "test_name": "Гемоглобин",
        "result_value": 85.5,
        "ref_lower": 1200000,
        "ref_upper": 160,
        "deviation_percent": 28.75,
        "monitor_type": "lower"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/results",
            json=test_result,
            timeout=5
        )
        print(f"   Статус: {response.status_code}")
        print(f"   Ответ: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def test_get_pending_results():
    """Проверка получения ожидающих результатов"""
    print("\n" + "=" * 50)
    print("3. Получение ожидающих результатов...")

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/results/pending",
            timeout=5
        )
        print(f"   Статус: {response.status_code}")
        print(f"   Количество: {len(response.json())}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def test_add_user():
    """Проверка добавления пользователя"""
    print("\n" + "=" * 50)
    print("4. Добавление тестового пользователя...")

    test_user = {
        "chat_id": "-1003053932494",
        "username": "dophamine428",
        "full_name": "Test User",
        "department": "Test Department"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/users",
            json=test_user,
            timeout=5
        )
        print(f"   Статус: {response.status_code}")
        print(f"   Ответ: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def test_get_users():
    """Проверка получения списка пользователей"""
    print("\n" + "=" * 50)
    print("5. Получение списка пользователей...")

    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/users",
            timeout=5
        )
        print(f"   Статус: {response.status_code}")
        print(f"   Пользователи: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def main():
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ CRITICAT SERVER")
    print("=" * 50)

    tests = [
        ("Health check", test_health),
        #("Отправка результата", test_send_result),
        #("Получение результатов", test_get_pending_results),
        ("Добавление пользователя", test_add_user),
        #("Получение пользователей", test_get_users),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"ИТОГО: {passed} пройдено, {failed} не пройдено")
    print("=" * 50)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
