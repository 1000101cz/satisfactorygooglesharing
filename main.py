import ctypes
myappid = 'satisfactorygooglesharing'
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from src.start import launch_app

if __name__ == '__main__':
    launch_app()
