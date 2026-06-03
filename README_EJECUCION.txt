ANTCLUSTER - EJECUCION PORTABLE EN WINDOWS

Instrucciones para usar la version en CD o memoria USB:

1. Copie la carpeta completa AntCluster al Escritorio de Windows.
   No ejecute la aplicacion directamente desde el CD si necesita guardar datos,
   porque el CD normalmente es de solo lectura.

2. Abra la carpeta copiada y ejecute:
   AntCluster.exe

3. No mueva ni elimine la carpeta data/.
   La aplicacion guarda y lee estos archivos:
   - data/gastos_usuario.csv
   - data/gastos_historicos.csv
   - data/ingresos_extra.csv
   - data/modelo_historico.json

4. Si la aplicacion no abre con doble clic, abra PowerShell o CMD dentro de la
   carpeta AntCluster y ejecute:
   .\AntCluster.exe

5. Requisitos minimos recomendados:
   - Windows 10 o Windows 11 de 64 bits
   - 4 GB de RAM
   - 500 MB de espacio libre
   - Permisos de escritura en la carpeta donde se copie AntCluster

6. Para entregar en CD:
   - Genere el ejecutable con build_exe.ps1.
   - Copie la carpeta dist\AntCluster completa al CD.
   - Indique al usuario final que primero copie esa carpeta al Escritorio.
