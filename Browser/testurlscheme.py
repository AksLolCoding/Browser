import sys
from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebEngineCore import *
from PyQt5.QtWidgets import *

class MyWebEnginePage(QWebEnginePage):
    pass

class SchemeHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, app):
        super().__init__(app)

    def requestStarted(self, request: QWebEngineUrlRequestJob):
        url = request.requestUrl()
        print(f'SchemeHandler requestStarted: {url.toString()}')

        # Returns a sample image
        raw_html = open(r'C:\Akshaj\Coding\Python\My Programs\Browsers\Browser\icons\add.svg', 'rb').read()
        buf = QBuffer(parent=self)
        request.destroyed.connect(buf.deleteLater)
        buf.open(QIODevice.WriteOnly)
        buf.write(raw_html)
        buf.seek(0)
        buf.close()
        request.reply(b"text/svg", buf)
        return


class MyWebEngineUrlScheme(QObject):
    # Register scheme
    scheme = b"static"

    def __init__(self, parent=None):
        super().__init__(parent)
        scheme = QWebEngineUrlScheme(MyWebEngineUrlScheme.scheme)
        QWebEngineUrlScheme.registerScheme(scheme)
        self.m_functions = dict()

    def init_handler(self, profile=None):
        if profile is None:
            profile = QWebEngineProfile.defaultProfile()
        handler = profile.urlSchemeHandler(MyWebEngineUrlScheme.scheme)
        if handler is not None:
            profile.removeUrlSchemeHandler(handler)

        self.handler = SchemeHandler(self)
        print("registering %s to %s" % (MyWebEngineUrlScheme.scheme, self.handler))
        profile.installUrlSchemeHandler(MyWebEngineUrlScheme.scheme, self.handler)


schemeApp = MyWebEngineUrlScheme()
app = QApplication(sys.argv)
win = QMainWindow()
win.resize(800, 600)

html = """
<html>
<body>
<h1>test</h1>
<hr>
<p>First iframe (testing custom url scheme)</p>
<iframe src="static://testfile" /></iframe>
<hr>
<p>Second image</p>
<img src="https://store.storeimages.cdn-apple.com/4668/as-images.apple.com/is/iphone-xr-red-select-201809?wid=1200&hei=630&fmt=jpeg&qlt=95&op_usm=0.5,0.5&.v=1551226038669" />
</body>
</html>
"""

browser = QWebEngineView()
profile = QWebEngineProfile()
page = MyWebEnginePage(profile, browser)
schemeApp.init_handler(profile)

page.setHtml(html)
browser.setPage(page)
browser.show()

win.setCentralWidget(browser)
win.show()

sys.exit(app.exec())