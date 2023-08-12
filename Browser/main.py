from classes import *

#Constants
global VERSION, STORAGE_FOLDER, SETTINGS_FOLDER, HOME_URL
VERSION = "2.0.0"
STORAGE_FOLDER = os.path.join(os.environ.get("LOCALAPPDATA"), "AksLolCoding\\Browser\\User Data")
SETTINGS_FOLDER = os.path.join(os.environ.get("LOCALAPPDATA"), "AksLolCoding\\Browser\\Settings")
HOME_URL = "https://google.com"

windows = []

browserscheme = BrowserUrlScheme()

class BrowserWindow(QMainWindow):
    def __init__(self, urls = [], view = None, *args, **kwargs):
        super(BrowserWindow, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self.initProfile()
        self.initUI()

        if view is not None:
            self.add_tab_from_view(view, WebEnginePage.WebWindowType.WebBrowserTab)
        else:
            if urls == [] or urls is None:
                urls = [HOME_URL]

            for url in urls:
                self.add_tab(url)

        self.setWindowTitle("Browser by AksLolCoding")
        self.resize(1000, 800)
        self.showMaximized() #uncomment this for production

    def initProfile(self):
        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.profile.setCachePath(STORAGE_FOLDER)
        self.profile.setPersistentStoragePath(STORAGE_FOLDER)
        self.profile.downloadRequested.connect(self.on_downloadRequested)
        self.profile.setSpellCheckEnabled(False)

        #self.browserscheme = BrowserUrlScheme(self)
        browserscheme.connect(self.profile)

    def initUI(self):
        self.tabs = BrowserTabs()
        self.tabs.setDocumentMode(True)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.contextMenuEvent = self.tab_context_menu
        self.setCentralWidget(self.tabs)

        self.newtab = QToolButton(self)
        self.newtab.setIcon(QIcon(resources.icons["add"]))
        font = self.newtab.font()
        font.setBold(True)
        self.newtab.setFont(font)
        self.tabs.setCornerWidget(self.newtab)
        self.newtab.clicked.connect(lambda _: self.add_tab())

        #self.status = QStatusBar()
        #self.setStatusBar(self.status)
        self.navtb = QToolBar("Navigation")
        self.navtb.setMovable(False)
        self.navtb.setContextMenuPolicy(Qt.CustomContextMenu)
        self.navtb.customContextMenuRequested.connect(lambda: False)
        self.addToolBar(self.navtb)

        self.back_btn = QAction(QIcon(resources.icons["arrow-back"]), "Back", self)
        self.back_btn.setStatusTip("Back to previous page")
        self.back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        self.navtb.addAction(self.back_btn)

        self.next_btn = QAction(QIcon(resources.icons["arrow-forward"]), "Forward", self)
        self.next_btn.setStatusTip("Forward to next page")
        self.next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        self.navtb.addAction(self.next_btn)

        self.reload_btn = QAction(QIcon(resources.icons["reload"]), "Reload", self)
        self.reload_btn.setStatusTip("Reload page")
        self.reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        self.navtb.addAction(self.reload_btn)

        self.home_btn = QAction(QIcon(resources.icons["home"]), "Home", self)
        self.home_btn.setStatusTip("Go home")
        self.home_btn.triggered.connect(self.navigate_home)
        self.navtb.addAction(self.home_btn)

        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.urlbar_pressed)
        self.urlbar.mousePressEvent = lambda _: self.urlbar.selectAll()
        self.navtb.addWidget(self.urlbar)
 
        self.stop_btn = QAction("Stop", self)
        self.stop_btn.setStatusTip("Stop loading current page")
        self.stop_btn.triggered.connect(lambda: self.tabs.currentWidget().stop())
        #self.navtb.addAction(self.stop_btn)

        self.settings_btn = QAction(QIcon(resources.icons["settings"]), "Settings", self)
        self.settings_btn.setStatusTip("Settings")
        self.settings_btn.triggered.connect(lambda: self.open_settings())
        self.navtb.addAction(self.settings_btn)

        self.load_theme()

    def add_tab(self, qurl = None):
        if qurl is None:
            qurl = QUrl(HOME_URL)
        elif isinstance(qurl, str):
            qurl = QUrl(qurl)

        browser = WebEngineView()
        self.add_tab_from_view(browser, WebEnginePage.WebWindowType.WebBrowserTab)
        browser.load(qurl)
    
    def add_tab_from_view(self, browser: WebEngineView, type: WebEnginePage.WebWindowType):
        match type:
            case WebEnginePage.WebWindowType.WebBrowserTab:
                i = self.tabs.addTab(browser, "")
                self.tabs.setCurrentIndex(i)
                page = browser.page()
                
                browser.urlChanged.connect(lambda qurl, browser = browser: self.update_url(browser))
                browser.loadStarted.connect(lambda browser = browser: self.on_loadStarted(browser))
                browser.loadFinished.connect(lambda _, browser = browser: self.on_loadFinished(browser))
                browser.titleChanged.connect(lambda title, browser = browser: self.update_title(browser))
                browser.iconChanged.connect(lambda icon, browser = browser: self.update_icon(browser))

                browser.viewSourceRequested.connect(self.view_page_source)
                browser.newTabRequested.connect(self.add_tab_from_view)
                page.windowCloseRequested.connect(lambda browser = browser: self.close_tab(self.tabs.indexOf(browser)))
                page.printRequested.connect(lambda page = browser.page(): self.on_printRequested(page))#self.on_printRequested(page))
                browser.page().linkHovered.connect(lambda url: self.on_linkHovered(url))

            case WebEnginePage.WebWindowType.WebBrowserWindow:
                windows.append(BrowserWindow(view = browser))

            case WebEnginePage.WebWindowType.WebBrowserBackgroundTab:
                i = self.tabs.addTab(browser, "")
                page = browser.page()

                browser.urlChanged.connect(lambda qurl, browser = browser: self.update_url(browser))
                browser.loadStarted.connect(lambda browser = browser: self.on_loadStarted(browser))
                browser.loadFinished.connect(lambda _, browser = browser: self.on_loadFinished(browser))
                browser.titleChanged.connect(lambda title, browser = browser: self.update_title(browser))
                browser.iconChanged.connect(lambda icon, browser = browser: self.update_icon(browser))

                browser.viewSourceRequested.connect(self.view_page_source)
                browser.newTabRequested.connect(self.add_tab_from_view)
                browser.page().printRequested.connect(lambda page = page: print(page))#self.on_printRequested(page))

            case WebEnginePage.WebWindowType.WebDialog:
                windows.append(BrowserDialogWindow(view = browser))
  
    def current_tab_changed(self, i):
        browser = self.tabs.currentWidget()
        if browser is None:
            return

        self.update_url(browser)
        self.update_title(browser)
        self.update_nav(browser)

    def close_tab(self, i):
        if self.tabs.count() < 2:
            self.close()
            return

        self.tabs.widget(i).close()
        self.tabs.removeTab(i)
    
    def tab_context_menu(self, event: QContextMenuEvent):
        i = self.tabs.tabBar().tabAt(event.pos())
        browser = self.tabs.widget(i)
        if browser is None:
            return

        menu = browser.createTabContextMenu()
        menu.setParent(self.tabs)
        menu.exec(event.pos())

    def on_loadStarted(self, browser = None):
        if browser is None:
            return

        self.update_nav(browser)

    def on_loadFinished(self, browser = None):
        if browser is None:
            return
    
    def on_linkHovered(self, url):
        tip=QToolTip.showText(self.geometry().bottomLeft() - QPoint(3, 35), url, self)
        #self.geometry
    
    def on_downloadRequested(self, download):
        #Later: create a download manager where user can see all downloads
        path = download.path()
        suffix = QFileInfo(path).suffix()
        path, _ = QFileDialog.getSaveFileName(self, "Save File", path, f"*.{suffix}")
        if path:
            download.setPath(path)
            download.accept()
        else:
            download.cancel()
    
    def on_printRequested(self, page = None):
        if page is None:
            return

        #print(page)
        dialog = QPrintDialog(self)
        if dialog.exec():
            self.printer = dialog.printer()
            page.print(self.printer, lambda success: None)

    def update_title(self, browser = None):
        if browser is None:
            return

        i = self.tabs.indexOf(browser)
        title = util.shorten(browser.title(), 50)
        self.tabs.setTabText(i, title)

        if browser == self.tabs.currentWidget():
            self.setWindowTitle(f"{title} - Browser by AksLolCoding")

    def update_icon(self, browser = None):
        if browser is None:
            return

        i = self.tabs.indexOf(browser)
        icon = self.tabs.widget(i).icon()
        self.tabs.setTabIcon(i, icon)

    def update_nav(self, browser = None):
        if browser != self.tabs.currentWidget() or browser is None:
            return

        self.back_btn.setEnabled(browser.page().action(WebEnginePage.WebAction.Back).isEnabled())
        self.next_btn.setEnabled(browser.page().action(WebEnginePage.WebAction.Forward).isEnabled())

    def update_url(self, browser = None):
        if browser != self.tabs.currentWidget() or browser is None:
            return

        url = self.tabs.currentWidget().url().toString()
        self.urlbar.setText(url)
        self.urlbar.setCursorPosition(0)

    def navigate_home(self):
        self.navigate_to_url(HOME_URL)
    
    def urlbar_pressed(self, qurl = None):
        self.urlbar.clearFocus()
        self.navigate_to_url(qurl)

    def navigate_to_url(self, qurl = None):
        if qurl is None:
            qurl = QUrl.fromUserInput(util.navigate_url(self.urlbar.text()))
        if isinstance(qurl, str):
            qurl = QUrl(qurl)

        if qurl.scheme() == "":
            qurl.setScheme("https")

        browser = self.tabs.currentWidget()
        browser.load(qurl)

    def load_theme(self, theme = "light"):
        with open(resources.css[theme], "r") as css:
            self.setStyleSheet(css.read())
    
    def view_page_source(self, qurl = None):
        self.add_tab(f"view-source:{qurl.toString()}")
    
    def open_settings(self):
        self.add_tab("browser://settings")

    def closeEvent(self, event): #this will be called when the window is closed
        event.accept()
        windows.remove(self)

        #save all browser data (for some reason this still gives alerts)
        for i in range(self.tabs.count()):
            browser = self.tabs.widget(i)
            browser.deleteLater()

class BrowserDialogWindow(QMainWindow):
    def __init__(self, view = None, *args, **kwargs):
        super(BrowserDialogWindow, self).__init__(*args, **kwargs)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        if view is None:
            return

        view.page().windowCloseRequested.connect(lambda: self.close())

        super(BrowserDialogWindow, self).__init__(*args, **kwargs)

        self.browser = view
        self.resize(500, 800)
        self.setCentralWidget(self.browser)
        self.show()

    def closeEvent(self, event): #this will be called when the window is closed
        windows.remove(self)
        event.accept()

        #save all browser data (for some reason this still gives alerts)
        self.browser.deleteLater()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Browser")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("AksLolCoding")
    app.setOrganizationDomain("https://akslolcoding.tk/")
    app.setWindowIcon(QIcon(resources.icons["app"]))

    windows.append(BrowserWindow())

    app.exec()
    sys.exit()