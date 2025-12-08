#!/usr/bin/env python3
"""
Benchmark visuel avec graphiques
Génère des visualisations des performances
"""
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif
import numpy as np
from pathlib import Path

# Configuration des couleurs
COLORS = {
    'flask-wsgi': '#0066CC',
    'flask-async-trap': '#FF6600',
    'flask-asgi-wrapper': '#CC0000',
    'quart-native': '#00CC66'
}

LABELS = {
    'flask-wsgi': 'Flask WSGI\n(baseline)',
    'flask-async-trap': 'Flask Async\n(trap)',
    'flask-asgi-wrapper': 'Flask+ASGI\n(overhead)',
    'quart-native': 'Quart Native\n(true async)'
}


def load_results(filename: str = "benchmark_results.json"):
    """Charge les résultats du benchmark"""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data['results']
    except FileNotFoundError:
        print(f"ERROR: {filename} not found. Run test_all.py first!")
        return None


def plot_concurrent_requests_comparison(results, output_dir: Path):
    """Compare les temps totaux pour différents niveaux de concurrence"""
    test_names = ['concurrent_10', 'concurrent_50', 'concurrent_100']
    test_labels = ['10 requests', '50 requests', '100 requests']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Concurrent Requests Performance (/slow endpoint)', fontsize=16, fontweight='bold')

    x = np.arange(len(test_labels))
    width = 0.2

    # Graphique 1: Temps total
    for i, (service, label) in enumerate(LABELS.items()):
        times = []
        for test_name in test_names:
            try:
                time_val = results[service]['/slow'][test_name]['total_time']
                times.append(time_val)
            except (KeyError, TypeError):
                times.append(0)

        ax1.bar(x + i * width, times, width, label=label, color=COLORS[service])

    ax1.set_xlabel('Number of Concurrent Requests', fontsize=12)
    ax1.set_ylabel('Total Time (seconds)', fontsize=12)
    ax1.set_title('Total Execution Time (lower is better)', fontsize=14)
    ax1.set_xticks(x + width * 1.5)
    ax1.set_xticklabels(test_labels)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Graphique 2: Requests per second
    for i, (service, label) in enumerate(LABELS.items()):
        rps_values = []
        for test_name in test_names:
            try:
                rps = results[service]['/slow'][test_name]['requests_per_second']
                rps_values.append(rps)
            except (KeyError, TypeError):
                rps_values.append(0)

        ax2.bar(x + i * width, rps_values, width, label=label, color=COLORS[service])

    ax2.set_xlabel('Number of Concurrent Requests', fontsize=12)
    ax2.set_ylabel('Requests per Second', fontsize=12)
    ax2.set_title('Throughput (higher is better)', fontsize=14)
    ax2.set_xticks(x + width * 1.5)
    ax2.set_xticklabels(test_labels)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    output_file = output_dir / 'concurrent_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def plot_latency_percentiles(results, output_dir: Path):
    """Compare les percentiles de latence"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Latency Percentiles Comparison (100 concurrent requests)', fontsize=16, fontweight='bold')

    test_name = 'concurrent_100'
    metrics = [
        ('mean_latency', 'Mean Latency'),
        ('median_latency', 'Median (P50) Latency'),
        ('p95_latency', 'P95 Latency'),
        ('p99_latency', 'P99 Latency')
    ]

    for idx, (metric, title) in enumerate(metrics):
        ax = axes[idx // 2, idx % 2]

        services = []
        values = []

        for service, label in LABELS.items():
            try:
                value = results[service]['/slow'][test_name][metric]
                services.append(label)
                values.append(value)
            except (KeyError, TypeError):
                services.append(label)
                values.append(0)

        colors = [COLORS[service] for service in LABELS.keys()]
        bars = ax.barh(services, values, color=colors)

        # Ajouter les valeurs sur les barres
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f'{width:.2f}s',
                   ha='left', va='center', fontsize=10, fontweight='bold')

        ax.set_xlabel('Time (seconds)', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    output_file = output_dir / 'latency_percentiles.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def plot_speedup_comparison(results, output_dir: Path):
    """Montre le speedup de Quart vs les autres solutions"""
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.suptitle('Quart Speedup vs Other Solutions', fontsize=16, fontweight='bold')

    test_name = 'concurrent_100'

    # Calculer le speedup par rapport à chaque solution
    try:
        quart_time = results['quart-native']['/slow'][test_name]['total_time']
    except (KeyError, TypeError):
        print("ERROR: Quart results not found!")
        return

    speedups = []
    services = []

    for service, label in LABELS.items():
        if service == 'quart-native':
            continue

        try:
            service_time = results[service]['/slow'][test_name]['total_time']
            speedup = service_time / quart_time
            speedups.append(speedup)
            services.append(label)
        except (KeyError, TypeError):
            speedups.append(0)
            services.append(label)

    colors_list = [COLORS[service] for service in LABELS.keys() if service != 'quart-native']
    bars = ax.barh(services, speedups, color=colors_list)

    # Ajouter les valeurs sur les barres
    for bar in bars:
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2,
               f'{width:.1f}x',
               ha='left', va='center', fontsize=12, fontweight='bold')

    ax.set_xlabel('Speedup Factor (higher is better)', fontsize=12)
    ax.set_title('How many times faster is Quart? (100 concurrent requests)', fontsize=14)
    ax.axvline(x=1, color='green', linestyle='--', linewidth=2, label='Quart baseline')
    ax.grid(axis='x', alpha=0.3)
    ax.legend()

    plt.tight_layout()
    output_file = output_dir / 'quart_speedup.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def plot_endpoint_comparison(results, output_dir: Path):
    """Compare les performances sur différents endpoints"""
    endpoints = ['/slow', '/multi-io', '/cpu-intensive', '/db-simulation']
    endpoint_labels = ['Slow\n(1s sleep)', 'Multi I/O\n(3x0.5s)', 'CPU\nIntensive', 'DB\nSimulation']

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.suptitle('Single Request Latency by Endpoint', fontsize=16, fontweight='bold')

    x = np.arange(len(endpoints))
    width = 0.2

    for i, (service, label) in enumerate(LABELS.items()):
        latencies = []
        for endpoint in endpoints:
            try:
                latency = results[service][endpoint]['single_request']['duration']
                latencies.append(latency)
            except (KeyError, TypeError):
                latencies.append(0)

        ax.bar(x + i * width, latencies, width, label=label, color=COLORS[service])

    ax.set_xlabel('Endpoint', fontsize=12)
    ax.set_ylabel('Latency (seconds)', fontsize=12)
    ax.set_title('Single Request Performance Comparison', fontsize=14)
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(endpoint_labels)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    output_file = output_dir / 'endpoint_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def plot_scalability(results, output_dir: Path):
    """Montre comment chaque solution scale avec la charge"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Scalability Analysis', fontsize=16, fontweight='bold')

    test_configs = [
        ('concurrent_10', 10),
        ('concurrent_50', 50),
        ('concurrent_100', 100)
    ]

    # Graphique 1: Total time vs concurrency
    for service, label in LABELS.items():
        concurrency_levels = []
        times = []

        for test_name, concurrency in test_configs:
            try:
                time_val = results[service]['/slow'][test_name]['total_time']
                concurrency_levels.append(concurrency)
                times.append(time_val)
            except (KeyError, TypeError):
                continue

        if times:
            ax1.plot(concurrency_levels, times, marker='o', linewidth=2,
                    label=label, color=COLORS[service], markersize=8)

    ax1.set_xlabel('Number of Concurrent Requests', fontsize=12)
    ax1.set_ylabel('Total Time (seconds)', fontsize=12)
    ax1.set_title('Execution Time vs Load (lower is better)', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Graphique 2: Throughput vs concurrency
    for service, label in LABELS.items():
        concurrency_levels = []
        throughputs = []

        for test_name, concurrency in test_configs:
            try:
                rps = results[service]['/slow'][test_name]['requests_per_second']
                concurrency_levels.append(concurrency)
                throughputs.append(rps)
            except (KeyError, TypeError):
                continue

        if throughputs:
            ax2.plot(concurrency_levels, throughputs, marker='s', linewidth=2,
                    label=label, color=COLORS[service], markersize=8)

    ax2.set_xlabel('Number of Concurrent Requests', fontsize=12)
    ax2.set_ylabel('Throughput (req/s)', fontsize=12)
    ax2.set_title('Throughput vs Load (higher is better)', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    output_file = output_dir / 'scalability.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def generate_summary_image(results, output_dir: Path):
    """Génère une image récapitulative avec les chiffres clés"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.axis('off')

    # Titre
    fig.text(0.5, 0.95, 'Benchmark Summary: Flask vs Quart',
            ha='center', fontsize=20, fontweight='bold')

    # Sous-titre
    fig.text(0.5, 0.90, '100 Concurrent Requests - /slow endpoint (1 second I/O)',
            ha='center', fontsize=14, style='italic')

    # Tableau des résultats
    y_start = 0.80
    y_step = 0.12

    test_name = 'concurrent_100'

    for i, (service, label) in enumerate(LABELS.items()):
        y = y_start - i * y_step

        try:
            result = results[service]['/slow'][test_name]
            total_time = result['total_time']
            rps = result['requests_per_second']
            p95 = result['p95_latency']

            # Nom du service
            fig.text(0.15, y + 0.05, label.replace('\n', ' '),
                    fontsize=14, fontweight='bold', color=COLORS[service])

            # Métriques
            fig.text(0.15, y - 0.02, f"Total Time: {total_time:.2f}s",
                    fontsize=11)
            fig.text(0.45, y - 0.02, f"Throughput: {rps:.1f} req/s",
                    fontsize=11)
            fig.text(0.70, y - 0.02, f"P95 Latency: {p95:.2f}s",
                    fontsize=11)

        except (KeyError, TypeError):
            fig.text(0.15, y, label.replace('\n', ' ') + " - No data",
                    fontsize=12, color='red')

    # Conclusion
    fig.text(0.5, 0.20, 'Key Findings:',
            ha='center', fontsize=16, fontweight='bold')

    findings = [
        '• Flask WSGI: Limited by (workers × threads)',
        '• Flask Async: No improvement - WSGI blocks!',
        '• Flask + ASGI wrapper: Added overhead, no benefits',
        '• Quart: TRUE async - handles 100s of concurrent requests efficiently!'
    ]

    for i, finding in enumerate(findings):
        fig.text(0.5, 0.15 - i * 0.04, finding,
                ha='center', fontsize=12)

    output_file = output_dir / 'summary.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()


def main():
    """Point d'entrée principal"""
    print("\n" + "="*80)
    print("VISUAL BENCHMARK GENERATOR")
    print("="*80 + "\n")

    # Créer le dossier de sortie
    output_dir = Path('benchmark_graphs')
    output_dir.mkdir(exist_ok=True)

    # Charger les résultats
    results = load_results()
    if not results:
        return

    # Générer les graphiques
    print("\nGenerating visualizations...\n")

    plot_concurrent_requests_comparison(results, output_dir)
    plot_latency_percentiles(results, output_dir)
    plot_speedup_comparison(results, output_dir)
    plot_endpoint_comparison(results, output_dir)
    plot_scalability(results, output_dir)
    generate_summary_image(results, output_dir)

    print("\n" + "="*80)
    print("VISUALIZATION COMPLETE! 📊")
    print(f"Graphs saved to: {output_dir.absolute()}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
