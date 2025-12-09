#!/usr/bin/env python3
"""
Présentation interactive dans le terminal
Démontre les concepts async/await de manière visuelle
"""
import time
import sys
import asyncio
from typing import List
import subprocess


class Colors:
    """Codes couleur ANSI"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def clear_screen():
    """Efface l'écran"""
    subprocess.run(['clear'], check=False)


def print_header(text: str):
    """Affiche un header stylisé"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}\n")


def print_box(text: str, color=Colors.GREEN):
    """Affiche du texte dans une boîte"""
    lines = text.split('\n')
    max_len = max(len(line) for line in lines)

    print(f"{color}╔{'═' * (max_len + 2)}╗{Colors.ENDC}")
    for line in lines:
        print(f"{color}║ {line.ljust(max_len)} ║{Colors.ENDC}")
    print(f"{color}╚{'═' * (max_len + 2)}╝{Colors.ENDC}")


def animate_text(text: str, delay: float = 0.03):
    """Affiche du texte avec effet de frappe"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def wait_for_enter(message: str = "Press ENTER to continue..."):
    """Attend que l'utilisateur appuie sur ENTER"""
    input(f"\n{Colors.YELLOW}{message}{Colors.ENDC}")


def demo_sync_blocking():
    """Démontre le comportement synchrone bloquant"""
    print_header("DÉMONSTRATION 1: Synchrone Bloquant (Flask + WSGI)")

    print(f"{Colors.YELLOW}Simulation: 3 requêtes qui prennent chacune 1 seconde{Colors.ENDC}\n")

    print("Worker 1:")
    for i in range(3):
        print(f"  Request {i+1}: ", end='', flush=True)
        for _ in range(10):
            print("█", end='', flush=True)
            time.sleep(0.1)
        print(f" {Colors.GREEN}✓{Colors.ENDC} (1.0s)")

    print(f"\n{Colors.RED}Total: 3.0 secondes{Colors.ENDC}")
    print(f"{Colors.RED}Problème: Le worker était bloqué pendant toute la durée!{Colors.ENDC}")

    wait_for_enter()


async def demo_async_non_blocking():
    """Démontre le comportement async non-bloquant"""
    clear_screen()
    print_header("DÉMONSTRATION 2: Async Non-Bloquant (Quart)")

    print(f"{Colors.YELLOW}Simulation: 3 requêtes exécutées en parallèle{Colors.ENDC}\n")

    async def request_simulation(req_id: int):
        print(f"Request {req_id}: START")
        await asyncio.sleep(1)
        print(f"Request {req_id}: {Colors.GREEN}✓ DONE{Colors.ENDC}")

    start = time.time()
    await asyncio.gather(
        request_simulation(1),
        request_simulation(2),
        request_simulation(3)
    )
    duration = time.time() - start

    print(f"\n{Colors.GREEN}Total: {duration:.1f} secondes{Colors.ENDC}")
    print(f"{Colors.GREEN}Avantage: Les 3 requêtes se sont exécutées en parallèle!{Colors.ENDC}")

    wait_for_enter()


def demo_flask_async_trap():
    """Démontre le piège Flask + async"""
    clear_screen()
    print_header("DÉMONSTRATION 3: Le Piège Flask + Async")

    print(f"{Colors.RED}⚠️  ATTENTION: async/await dans Flask + WSGI ne fonctionne PAS!{Colors.ENDC}\n")

    code = """
@app.route('/parallel')
async def parallel():
    await asyncio.sleep(0.25)  # Async mais...
    await asyncio.sleep(0.25)  # Async mais...
    return {"status": "done"}
"""

    print(f"{Colors.CYAN}Code Flask:{Colors.ENDC}")
    print(code)

    print(f"{Colors.RED}Problème:{Colors.ENDC}")
    print("  1. Flask tourne sur WSGI (synchrone)")
    print("  2. Le mot-clé 'async' fonctionne mais...")
    print("  3. Le worker WSGI reste bloqué pendant await!")
    print("  4. Aucune autre requête ne peut être traitée")
    print("  5. Peut même être PLUS LENT (overhead)")

    print(f"\n{Colors.BOLD}{Colors.RED}C'EST UN PIÈGE! N'utilisez pas async avec WSGI!{Colors.ENDC}")

    wait_for_enter()


def demo_comparison():
    """Compare les différentes solutions"""
    clear_screen()
    print_header("COMPARAISON: 100 Requêtes Concurrentes")

    results = [
        ("Flask WSGI", "~25s", "4.0 req/s", Colors.YELLOW),
        ("Flask + Async", "~26s", "3.8 req/s", Colors.RED),
        ("Flask + ASGI Wrapper", "~29s", "3.4 req/s", Colors.RED),
        ("Quart Native", "~1.2s", "83.3 req/s", Colors.GREEN),
    ]

    print(f"{'Solution':<25} {'Temps Total':<15} {'Throughput':<15} {'Verdict'}")
    print("-" * 80)

    for solution, time_val, rps, color in results:
        if "Quart" in solution:
            verdict = "✅ 21x plus rapide!"
        elif "Async" in solution:
            verdict = "🚫 Pire que sync!"
        elif "ASGI" in solution:
            verdict = "🚫 Le pire (overhead)"
        else:
            verdict = "⚠️  Baseline"

        print(f"{color}{solution:<25} {time_val:<15} {rps:<15} {verdict}{Colors.ENDC}")

    print("\n" + "="*80)
    print(f"\n{Colors.GREEN}{Colors.BOLD}CONCLUSION:{Colors.ENDC}")
    print(f"{Colors.GREEN}Quart avec async natif est la solution pour les apps I/O-bound!{Colors.ENDC}")

    wait_for_enter()


def demo_when_to_use():
    """Montre quand utiliser chaque solution"""
    clear_screen()
    print_header("Quand Utiliser Chaque Solution?")

    print(f"\n{Colors.GREEN}✅ Utilisez Flask (WSGI) si:{Colors.ENDC}")
    print("  • Application CPU-bound (calculs intensifs)")
    print("  • Peu d'opérations I/O externes")
    print("  • Équipe pas familière avec async")
    print("  • Extensions Flask spécifiques nécessaires")

    print(f"\n{Colors.GREEN}✅ Utilisez Quart (ASGI) si:{Colors.ENDC}")
    print("  • Beaucoup d'appels API externes")
    print("  • Requêtes base de données fréquentes")
    print("  • Besoin de WebSocket ou Server-Sent Events")
    print("  • Charge haute avec ressources limitées")
    print("  • Application I/O-bound")

    print(f"\n{Colors.RED}🚫 N'utilisez JAMAIS:{Colors.ENDC}")
    print("  • Flask avec routes async sur WSGI")
    print("  • Flask wrappé avec WsgiToAsgi")
    print("  • async/await pour du code CPU-bound")

    print(f"\n{Colors.BOLD}Règle simple:{Colors.ENDC}")
    print("  Si vous avez besoin d'async → Utilisez Quart ou FastAPI")
    print("  Sinon → Flask WSGI fonctionne parfaitement")

    wait_for_enter()


def demo_migration_guide():
    """Guide de migration Flask → Quart"""
    clear_screen()
    print_header("Guide de Migration Flask → Quart")

    print(f"{Colors.YELLOW}La bonne nouvelle: L'API est quasi-identique!{Colors.ENDC}\n")

    comparisons = [
        ("Import", "from flask import Flask", "from quart import Quart"),
        ("App", "app = Flask(__name__)", "app = Quart(__name__)"),
        ("Route", "@app.route('/')\ndef index():", "@app.route('/')\nasync def index():"),
        ("HTTP", "requests.get(url)", "await httpx_client.get(url)"),
        ("Sleep", "time.sleep(1)", "await asyncio.sleep(1)"),
    ]

    for category, flask_code, quart_code in comparisons:
        print(f"{Colors.BOLD}{category}:{Colors.ENDC}")
        print(f"  {Colors.RED}Flask:  {Colors.ENDC}{flask_code}")
        print(f"  {Colors.GREEN}Quart:  {Colors.ENDC}{quart_code}")
        print()

    print(f"{Colors.YELLOW}Points d'attention:{Colors.ENDC}")
    print("  • Remplacer 'requests' par 'httpx' (async)")
    print("  • Ajouter 'await' pour les opérations I/O")
    print("  • Utiliser des drivers DB async (asyncpg, aiomysql, etc.)")
    print("  • Tester les extensions Flask (la plupart sont compatibles)")

    wait_for_enter()


def demo_live_test():
    """Test en direct si les services sont actifs"""
    clear_screen()
    print_header("Test en Direct (si services actifs)")

    print(f"{Colors.YELLOW}Tentative de connexion aux services...{Colors.ENDC}\n")

    services = [
        ("Flask WSGI", "http://localhost:5001/health"),
        ("Flask Async Trap", "http://localhost:5002/health"),
        ("Flask ASGI Wrapper", "http://localhost:5003/health"),
        ("Quart Native", "http://localhost:5004/health"),
    ]

    try:
        import requests

        for name, url in services:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"{Colors.GREEN}✓ {name:<25} - UP{Colors.ENDC}")
                else:
                    print(f"{Colors.RED}✗ {name:<25} - ERROR{Colors.ENDC}")
            except Exception:
                print(f"{Colors.YELLOW}⚠ {name:<25} - DOWN{Colors.ENDC}")

        print(f"\n{Colors.CYAN}Pour démarrer les services:{Colors.ENDC}")
        print("  make up")
        print("\n{Colors.CYAN}Pour lancer les benchmarks:{Colors.ENDC}")
        print("  make report")

    except ImportError:
        print(f"{Colors.YELLOW}Module 'requests' non installé.{Colors.ENDC}")
        print("Installez avec: pip install requests")

    wait_for_enter()


def main():
    """Point d'entrée principal"""
    clear_screen()

    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║         Flask vs Quart: Async/Await Explained                    ║")
    print("║         Présentation Interactive                                  ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

    animate_text("\nBienvenue dans cette présentation interactive sur async/await en Python!", 0.02)

    wait_for_enter("Press ENTER to start...")

    # Démonstrations
    demo_sync_blocking()
    asyncio.run(demo_async_non_blocking())
    demo_flask_async_trap()
    demo_comparison()
    demo_when_to_use()
    demo_migration_guide()
    demo_live_test()

    # Fin
    clear_screen()
    print_header("Merci!")

    print(f"{Colors.GREEN}Vous avez maintenant compris:{Colors.ENDC}")
    print("  ✓ Pourquoi async/await est important")
    print("  ✓ Pourquoi Flask + async ne fonctionne pas sur WSGI")
    print("  ✓ Pourquoi Quart est la solution pour async natif")
    print("  ✓ Quand utiliser Flask vs Quart")

    print(f"\n{Colors.YELLOW}Prochaines étapes:{Colors.ENDC}")
    print("  1. Lisez le README.md complet")
    print("  2. Lancez 'make demo' pour une démo interactive")
    print("  3. Lancez 'make report' pour les benchmarks")
    print("  4. Explorez le code des 4 implémentations")

    print(f"\n{Colors.BOLD}{Colors.CYAN}Happy coding! 🚀{Colors.ENDC}\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Présentation interrompue.{Colors.ENDC}\n")
        sys.exit(0)
