import sys, os

class CommonHelper:
    def __init__(self):
        pass
 
    @staticmethod
    def readQss(style):
        with open(style, 'r', encoding='utf-8') as f:
            return f.read()
        
    def resource_path(relative_path):
        ''' Get the absolute path to the resource, works for dev and for PyInstaller '''
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)