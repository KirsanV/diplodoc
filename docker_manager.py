import sys
import subprocess
import argparse


def run_command(command, description=""):
    """Выполнить команду и вывести результат"""
    if description:
        print(f"🚀 {description}...")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        print("✅ Успешно!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка: {e}")
        if e.stderr:
            print(f"Подробности: {e.stderr}")
        return False


def show_status():
    """Показать статус сервисов"""
    print("📊 Статус сервисов:")
    run_command("docker-compose ps")


def start_services():
    """Запустить все сервисы"""
    if run_command("docker-compose up -d", "Запускаем все сервисы"):
        show_status()


def stop_services():
    """Остановить все сервисы"""
    run_command("docker-compose down", "Останавливаем сервисы")


def restart_services():
    """Перезапустить сервисы"""
    if run_command("docker-compose restart", "Перезапускаем сервисы"):
        show_status()


def build_services():
    """Пересобрать образы"""
    run_command("docker-compose build --no-cache", "Пересобираем образы")


def show_logs():
    """Показать логи"""
    print("📋 Логи сервисов (Ctrl+C для выхода):")
    try:
        subprocess.run("docker-compose logs -f", shell=True)
    except KeyboardInterrupt:
        print("\n⏹️ Выход из логов")


def clean_system():
    """Полная очистка"""
    print("🧹 Полная очистка Docker...")
    run_command("docker-compose down -v", "Останавливаем сервисы и удаляем volumes")
    run_command("docker system prune -a -f", "Очищаем систему Docker")


def connect_database():
    """Подключиться к БД"""
    print("🗄️ Подключаемся к БД...")
    subprocess.run("docker-compose exec db psql -U user -d codeforces_db", shell=True)


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Docker Manager for Codeforces Bot")
    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "build", "logs", "clean", "status", "db", "help"],
        help="Команда для выполнения"
    )

    args = parser.parse_args()

    commands = {
        "start": start_services,
        "stop": stop_services,
        "restart": restart_services,
        "build": build_services,
        "logs": show_logs,
        "clean": clean_system,
        "status": show_status,
        "db": connect_database,
        "help": lambda: print_help()
    }

    if args.command in commands:
        commands[args.command]()
    else:
        print_help()


def print_help():
    """Показать справку"""
    print("🚀 Codeforces Bot Docker Management")
    print("Запускается прямо из PyCharm!")
    print("")
    print("📋 Использование: python docker_manager.py [команда]")
    print("")
    print("🛠️ Команды:")
    print("  start     - Запустить все сервисы")
    print("  stop      - Остановить все сервисы")
    print("  restart   - Перезапустить сервисы")
    print("  build     - Пересобрать образы")
    print("  logs      - Показать логи")
    print("  clean     - Полная очистка")
    print("  status    - Показать статус")
    print("  db        - Подключиться к БД")
    print("  help      - Показать эту справку")
    print("")
    print("💡 Пример: python docker_manager.py start")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_help()
    else:
        main()
