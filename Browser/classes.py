#Imports are here so we dont have to retype this in every script
from PyQt5 import *
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestJob
from PyQt5.QtWebEngineWidgets import QWebEngineFullScreenRequest, QWebEnginePage, QWebEngineView
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtWebEngineCore import *
from PyQt5.QtPrintSupport import *
from PyQt5.QtNetwork import *

import sys, os
import util
import resources

#Classes
class WebEngineView(QWebEngineView):
    viewSourceRequested = pyqtSignal(QUrl, name = "viewSourceRequested")
    newTabRequested = pyqtSignal(QWebEngineView, QWebEnginePage.WebWindowType, name = "newTabRequested")

    def __init__(self, profile = None, *args, **kwargs):
        super(WebEngineView, self).__init__(*args, **kwargs)

        self.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True) #we need these settings
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True) #only works in production
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)

        self.setProfile(profile)
    
    def setProfile(self, profile = None):
        page = WebEnginePage(self) if profile is None else WebEnginePage(profile, self)
        self.setPage(page)
    
    def profile(self):
        return self.page().profile()

    def contextMenuEvent(self, event: QContextMenuEvent):
        self.menu = self.page().createStandardContextMenu()

        for action in self.menu.actions():
            if action.isSeparator():
                continue

            #Here we can override default actions create signals for them
            match action.text():
                case "Back":
                    action.setIcon(QIcon(resources.icons["arrow-back"]))
                case "Forward":
                    action.setIcon(QIcon(resources.icons["arrow-forward"]))
                case "Reload":
                    action.setIcon(QIcon(resources.icons["reload"]))
                case "Save page":
                    action.setIcon(QIcon(resources.icons["save_as"]))

                    #printaction = QAction(QIcon(resources.icons["printer"]), "Print", self.menu) #for some reason this code causes pyinstaller to crash
                    #self.menu.insertAction(action, printaction)
                    #printaction.triggered.connect(lambda _, page = self.page(): page.printRequested.emit())
                case "Open link in new tab":
                    action.setIcon(QIcon(resources.icons["tab"]))
                case "Open link in new window":
                    action.setIcon(QIcon(resources.icons["window"]))
                case "Copy link address":
                    action.setText("Copy link")
                    action.setIcon(QIcon(resources.icons["link"]))
                case "View page source":
                    action.disconnect()
                    action.triggered.connect(lambda _, url = self.url(): self.viewSourceRequested.emit(url)) #this connects it to an external signal
                case "Copy":
                    action.setIcon(QIcon(resources.icons["content_copy"]))
                case "Paste":
                    action.setIcon(QIcon(resources.icons["content_paste"]))
                case "Cut":
                    action.setIcon(QIcon(resources.icons["content_cut"]))
                case _:
                    pass

        self.menu.popup(event.globalPos())
    
    def createTabContextMenu(self) -> QMenu:
        menu = QMenu()

        reload = QAction(resources.icons["reload"], "Reload", self)
        reload.triggered.connect(lambda _: self.reload())
        menu.addAction(reload)

        togglemute = QAction("Unmute" if self.page().isAudioMuted() else "Mute", self)
        togglemute.triggered.connect(lambda _: self.page().toggleMute())
        menu.addAction(togglemute)

        menu.triggered.connect(lambda action, menu = menu: menu.setVisible(False))

        return menu
    
    def createWindow(self, type):
        browser = WebEngineView(self.page().profile()) #do we need profile here?
        self.newTabRequested.emit(browser, type)
        return browser

class WebEnginePage(QWebEnginePage):
    def __init__(self, *args, **kwargs):
        super(WebEnginePage, self).__init__(*args, **kwargs)
        self.featurePermissionRequested.connect(self.on_featurePermissionRequested)

    def javaScriptConsoleMessage(self, level, msg, line, sourceID):
        pass

    def toggleMute(self):
        self.setAudioMuted(not self.isAudioMuted())

    def on_featurePermissionRequested(self, securityOrigin, feature):
        title = "Permission Request"
        question = {
            QWebEnginePage.Feature.Notifications: "Allow {feature} to send notifications?",
            QWebEnginePage.Feature.Geolocation: "Allow {feature} to access your location?",
            QWebEnginePage.Feature.MediaAudioCapture: "Allow {feature} to access your microphone?",
            QWebEnginePage.Feature.MediaVideoCapture: "Allow {feature} to access your camera?",
            QWebEnginePage.Feature.MediaAudioVideoCapture: "Allow {feature} to access your microphone and camera?",
            QWebEnginePage.Feature.MouseLock: "Allow {feature} to lock your mouse cursor?",
            QWebEnginePage.Feature.DesktopVideoCapture: "Allow {feature} to capture video of your desktop?",
            QWebEnginePage.Feature.DesktopAudioVideoCapture: "Allow {feature} to capture audio and video of your desktop?"
        }.get(feature)

        if question:
            question = question.format(feature = securityOrigin.host())
            answer = QMessageBox.question(self.view().window(), title, question)
            if answer == QMessageBox.Yes:
                self.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            elif answer == QMessageBox.No:
                self.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)
            else:
                self.setFeaturePermission(securityOrigin, feature, QWebEnginePage.PermissionPolicy.PermissionUnknown)
    
    def fullScreenRequested(self, request: QWebEngineFullScreenRequest):
        return request.accept()

class BrowserTabs(QTabWidget):
    def __init__(self, *args, **kwargs):
        super(BrowserTabs, self).__init__(*args, **kwargs)

class WebEngineUrlScheme(QWebEngineUrlSchemeHandler):
    def __init__(self, scheme, parent = None):
        super(WebEngineUrlScheme, self).__init__(parent)

        self.scheme = scheme
        self.qscheme = QWebEngineUrlScheme(self.scheme.encode())
        QWebEngineUrlScheme.registerScheme(self.qscheme)

    def connect(self, profile = None):
        if profile is None:
            return

        handler = profile.urlSchemeHandler(self.scheme.encode())
        if handler is not None:
            profile.removeUrlSchemeHandler(handler)

        profile.installUrlSchemeHandler(self.scheme.encode(), self)

class BrowserUrlScheme(WebEngineUrlScheme):
    def __init__(self, parent = None):
        super(BrowserUrlScheme, self).__init__("browser", parent)
        self.qscheme.setFlags(QWebEngineUrlScheme.Flag.LocalAccessAllowed)
    
    def file2buffer(self, path):
        try:
            file = open(path, 'rb').read()
            buf = QBuffer(parent = self)
            buf.open(QIODevice.WriteOnly)
            buf.write(file)
            buf.seek(0)
            buf.close()
            return buf
        except Exception:
            return False
    
    def requestStarted(self, job: QWebEngineUrlRequestJob):
        url = job.requestUrl()
        match url.host():
            #case "gpu":
                #buf = self.file2buffer(resources.html["gpu"])
                #job.destroyed.connect(buf.deleteLater)
                #job.reply(b"text/html", buf)
            case "settings":
                file = ""
                mime = ""
                match url.path().rstrip('/'):
                    case "/settings.css":
                        file = resources.css["settings"]
                        mime = "text/css"
                    case "/settings.js":
                        file = resources.js["settings"]
                        mime = "text/javascript"
                    case "":
                        file = resources.html["settings"]
                        mime = "text/html"
                    case _:
                        job.fail(QWebEngineUrlRequestJob.Error.UrlInvalid)
                        return
                buf = self.file2buffer(file)
                job.destroyed.connect(buf.deleteLater)
                job.reply(mime.encode(), buf)
            case _:
                job.fail(QWebEngineUrlRequestJob.Error.UrlInvalid)