import sys
import unittest
import os
import subprocess

class TestMainProcess(unittest.TestCase):
    def setUp(self):
        # Ruta de entrada para los archivos txt
        self.entrada_dir = os.path.join('data', 'entrada')
        
        # Ruta de salida para los PDFs
        self.pdf_output = os.path.join('data', 'PDF')
        
        # Crear directorios si no existen
        os.makedirs(self.entrada_dir, exist_ok=True)
        os.makedirs(self.pdf_output, exist_ok=True)

    def test_main_process(self):
        nit = "123456789"  # NIT que también es el nombre del archivo de texto
        tamano_letra = 'N'  # Tamaño de letra normal

        # Ruta del archivo de texto basado en el NIT
        ruta_txt = os.path.join(self.entrada_dir, f'{nit}.txt')
        
        # Verificar que el archivo de prueba existe
        self.assertTrue(os.path.exists(ruta_txt), f"Error: No se encontró el archivo de prueba en {ruta_txt}")

        # Ruta del intérprete de Python en el entorno virtual
        python_path = sys.executable  # Usar el intérprete de Python actual (del entorno virtual)

        # Ejecutar main.py con los parámetros
        comando = [
            python_path,  # Usar el intérprete de Python del entorno virtual
            'main.py',
            ruta_txt,  # Ruta del archivo txt
            nit,       # NIT (simulado)
            tamano_letra  # Tamaño de letra
        ]
        
        # Ejecutar el comando y capturar la salida
        resultado = subprocess.run(comando, capture_output=True, text=True)
        
        # Imprimir la salida y el error para depuración
        print("\n--- Salida estándar (stdout) ---")
        print(resultado.stdout)
        
        print("\n--- Error estándar (stderr) ---")
        print(resultado.stderr)

        # Verificar que el proceso terminó correctamente (código de salida 0)
        self.assertEqual(resultado.returncode, 0, f"Error en main.py: {resultado.stderr}")

        # Verificar que el PDF se generó correctamente
        nombre_pdf = os.path.splitext(os.path.basename(ruta_txt))[0] + '.pdf'
        ruta_pdf = os.path.join(self.pdf_output, nombre_pdf)
        
        self.assertTrue(os.path.exists(ruta_pdf), f"Error: No se generó el PDF en {ruta_pdf}")
        print(f"\nPDF generado: {ruta_pdf}")

if __name__ == '__main__':
    unittest.main(verbosity=2)