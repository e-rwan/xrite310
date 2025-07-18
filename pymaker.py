import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--noconfirm',
    '--windowed',
    '--onedir',
    '--icon=ressources/kafarddensito.ico',
    '--add-data=measures;measures',
    '--add-data=docs;docs',
    '--add-data=ressources;ressources',
    '--distpath=dist',
    '--workpath=build',
    '--specpath=build',
])
