"""Modelo de la red del Metro con NetworkX y búsqueda de caminos mínimos."""
import argparse
from pathlib import Path
import unicodedata

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx

from datos import LINEAS, COLORES


def crear_grafo():
    """Unifica las correspondencias y conecta estaciones consecutivas."""
    grafo = nx.Graph(nombre='Metro de la Ciudad de México')
    for linea, estaciones in LINEAS.items():
        for estacion in estaciones:
            if estacion not in grafo:
                grafo.add_node(estacion, lineas=[])
            grafo.nodes[estacion]['lineas'].append(linea)
        for origen, destino in zip(estaciones, estaciones[1:]):
            grafo.add_edge(origen, destino, linea=linea, peso=1)
    return grafo


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold().strip())
                   if unicodedata.category(c) != 'Mn')


def resolver_estacion(grafo, nombre):
    for estacion in grafo:
        if normalizar(estacion) == normalizar(nombre):
            return estacion
    raise ValueError(f'Estación desconocida: {nombre}. Usa --estaciones para consultar los nombres.')


def ruta_minima(grafo, origen, destino):
    """BFS encuentra el menor número de aristas en un grafo sin pesos variables."""
    return nx.shortest_path(grafo, resolver_estacion(grafo, origen),
                            resolver_estacion(grafo, destino))


def describir_ruta(grafo, ruta):
    lineas = [grafo.edges[a, b]['linea'] for a, b in zip(ruta, ruta[1:])]
    transbordos = [ruta[i] for i in range(1, len(lineas)) if lineas[i] != lineas[i-1]]
    texto = ['Ruta: ' + ' -> '.join(ruta), f'Tramos recorridos: {len(ruta)-1}',
             f'Estaciones visitadas: {len(ruta)}', f'Transbordos: {len(transbordos)}']
    if transbordos:
        texto.append('Cambios de línea en: ' + ', '.join(transbordos))
    if lineas:
        texto.append('Líneas por tramo: ' + ' -> '.join(lineas))
    return '\n'.join(texto)


def resumen(grafo):
    correspondencias = [n for n, d in grafo.nodes(data=True) if len(d['lineas']) > 1]
    principales = sorted(grafo.degree, key=lambda par: (-par[1], par[0]))[:5]
    return '\n'.join([
        'MODELO DEL METRO DE LA CIUDAD DE MÉXICO',
        f'Líneas: {len(LINEAS)}', f'Estaciones únicas (vértices): {len(grafo)}',
        f'Conexiones (aristas): {grafo.number_of_edges()}',
        f'Estaciones de correspondencia: {len(correspondencias)}',
        f'Componentes conexas: {nx.number_connected_components(grafo)}',
        f'Grado promedio: {sum(dict(grafo.degree).values()) / len(grafo):.2f}',
        f'Diámetro: {nx.diameter(grafo)} tramos',
        'Mayor grado: ' + ', '.join(f'{n} ({g})' for n, g in principales)])


def dibujar(grafo, ruta, carpeta):
    """El dibujo topológico es determinista; no representa distancias reales."""
    posiciones = nx.spring_layout(grafo, seed=42, iterations=400, method='force')
    fig, ax = plt.subplots(figsize=(24, 20), facecolor='#faf9f5')
    ax.set_facecolor('#faf9f5')
    for linea, color in COLORES.items():
        aristas = [(a, b) for a, b, d in grafo.edges(data=True) if d['linea'] == linea]
        nx.draw_networkx_edges(grafo, posiciones, edgelist=aristas, edge_color=color,
                               width=2.6, ax=ax)
    transbordos = [n for n, d in grafo.nodes(data=True) if len(d['lineas']) > 1]
    nx.draw_networkx_nodes(grafo, posiciones, node_size=32, node_color='white',
                           edgecolors='#666666', linewidths=.5, ax=ax)
    nx.draw_networkx_nodes(grafo, posiciones, nodelist=transbordos, node_size=100,
                           node_color='white', edgecolors='#222222', linewidths=1.3, ax=ax)
    if len(ruta) > 1:
        nx.draw_networkx_edges(grafo, posiciones, edgelist=list(zip(ruta, ruta[1:])),
                               edge_color='#131313', width=5, alpha=.65, ax=ax)
    nx.draw_networkx_labels(grafo, posiciones, font_size=6, verticalalignment='bottom', ax=ax)
    leyenda = [Line2D([0], [0], color=c, lw=4, label=f'Línea {l}') for l, c in COLORES.items()]
    ax.legend(handles=leyenda, loc='upper left', ncol=4, frameon=False)
    ax.set_title('METRO CDMX · MODELO EN GRAFO\n12 líneas · correspondencias como vértices compartidos',
                 fontsize=23, weight='bold', pad=24)
    fig.text(.5, .025, 'Esquema topológico sin escala geográfica · Negro: ruta consultada',
             ha='center', fontsize=12)
    ax.margins(.12)
    ax.axis('off')
    fig.savefig(carpeta / 'red_metro.png', dpi=180, bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origen', default='Observatorio')
    parser.add_argument('--destino', default='Universidad')
    parser.add_argument('--estaciones', action='store_true', help='Lista las estaciones por línea')
    parser.add_argument('--salida', type=Path, default=Path(__file__).parent / 'resultados')
    args = parser.parse_args()
    grafo = crear_grafo()
    if args.estaciones:
        for linea, estaciones in LINEAS.items():
            print(f'Línea {linea}: ' + ' -> '.join(estaciones))
        return
    try:
        ruta = ruta_minima(grafo, args.origen, args.destino)
    except (ValueError, nx.NetworkXNoPath) as error:
        parser.error(str(error))
    args.salida.mkdir(parents=True, exist_ok=True)
    reporte = resumen(grafo) + '\n\n' + describir_ruta(grafo, ruta)
    print(reporte)
    (args.salida / 'analisis.txt').write_text(reporte + '\n', encoding='utf-8')
    # GraphML exige atributos escalares: se serializa la lista de líneas.
    exportable = grafo.copy()
    for _, datos in exportable.nodes(data=True):
        datos['lineas'] = ','.join(datos['lineas'])
    nx.write_graphml(exportable, args.salida / 'red_metro.graphml')
    dibujar(grafo, ruta, args.salida)
    print(f'Archivos generados en: {args.salida.resolve()}')


if __name__ == '__main__':
    main()
