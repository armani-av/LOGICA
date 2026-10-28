"""Verificaciones del modelo y de la búsqueda de rutas."""
import unittest
import networkx as nx
from datos import LINEAS
from metro import crear_grafo, ruta_minima, describir_ruta


class ModeloMetroTest(unittest.TestCase):
    def setUp(self):
        self.grafo = crear_grafo()

    def test_estructura_completa(self):
        self.assertEqual(len(LINEAS), 12)
        self.assertEqual(sum(map(len, LINEAS.values())), 195)
        self.assertEqual(len(self.grafo), 163)
        self.assertEqual(self.grafo.number_of_edges(), 183)
        self.assertTrue(nx.is_connected(self.grafo))
        self.assertEqual(nx.number_of_selfloops(self.grafo), 0)

    def test_correspondencias(self):
        self.assertEqual(set(self.grafo.nodes['Pantitlán']['lineas']), {'1', '5', '9', 'A'})
        self.assertEqual(set(self.grafo.nodes['Chabacano']['lineas']), {'2', '8', '9'})

    def test_camino_y_transbordo(self):
        ruta = ruta_minima(self.grafo, 'observatorio', 'universidad')
        self.assertEqual(len(ruta)-1, 12)
        self.assertEqual(ruta[0], 'Observatorio')
        self.assertEqual(ruta[-1], 'Universidad')
        self.assertIn('Transbordos:', describir_ruta(self.grafo, ruta))
        for a, b in zip(ruta, ruta[1:]):
            self.assertTrue(self.grafo.has_edge(a, b))

    def test_extremos(self):
        self.assertEqual(ruta_minima(self.grafo, 'Pantitlan', 'Pantitlán'), ['Pantitlán'])
        self.assertEqual(ruta_minima(self.grafo, 'Tacubaya', 'Observatorio'), ['Tacubaya', 'Observatorio'])
        with self.assertRaises(ValueError):
            ruta_minima(self.grafo, 'No existe', 'Universidad')


if __name__ == '__main__':
    unittest.main()
