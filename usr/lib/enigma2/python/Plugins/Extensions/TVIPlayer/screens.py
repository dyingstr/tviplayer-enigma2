import os
import threading
import logging

log = logging.getLogger("tviplayer")

from enigma import eServiceReference, eTimer
from twisted.internet import reactor

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen

try:
    from Screens.InfoBar import MoviePlayer as _MoviePlayer

    class TVIMoviePlayer(_MoviePlayer):
        """MoviePlayer subclass: stop returns to TVI Player; OSD on pause/ok."""

        def __init__(self, session, service):
            _MoviePlayer.__init__(self, session, service)
            self._osdTimer = eTimer()
            self._osdTimer.callback.append(self._forceShow)

        def leavePlayer(self):
            self.session.nav.stopService()
            self.close()

        def leavePlayerConfirmed(self, answer):
            self.session.nav.stopService()
            self.close()

        def doEofInternal(self, playing):
            self.close()

        def _seekRelative(self, seconds):
            service = self.session.nav.getCurrentService()
            seek = service and service.seek()
            if seek:
                seek.seekRelative(1 if seconds > 0 else -1, abs(seconds) * 90000)

        def seekFwd(self):
            self._seekRelative(30)

        def seekBack(self):
            self._seekRelative(-10)

        def seekFwdManual(self):
            self._seekRelative(30)

        def seekBackManual(self):
            self._seekRelative(-10)

        def _forceShow(self):
            try:
                self.show()
                self.startHideTimer()
            except Exception as e:
                log.debug("_forceShow error: %s", e)

        def pauseService(self):
            _MoviePlayer.pauseService(self)
            self._osdTimer.start(200, True)

        def unPauseService(self):
            _MoviePlayer.unPauseService(self)
            self._osdTimer.start(200, True)

        def playpauseService(self):
            _MoviePlayer.playpauseService(self)
            self._osdTimer.start(200, True)

        def okButton(self):
            self._forceShow()

    _HAVE_MOVIEPLAYER = True
except Exception:
    TVIMoviePlayer = None
    _HAVE_MOVIEPLAYER = False

from .api import TVIPlayerAPI, CATEGORIES
from .config import load_config

SERVICE_TYPE = 4097  # GStreamer — proper HLS seeking and position reporting

api = TVIPlayerAPI()


def _run_async(fn, *args, on_success=None, on_error=None):
    def _worker():
        try:
            log.debug("_run_async: calling %s", fn.__name__)
            result = fn(*args)
            log.debug("_run_async: %s OK", fn.__name__)
            if on_success:
                reactor.callFromThread(on_success, result)
        except Exception as e:
            log.exception("_run_async: %s FAILED: %s", fn.__name__, e)
            if on_error:
                reactor.callFromThread(on_error, e)
    threading.Thread(target=_worker, daemon=True).start()


# ---------------------------------------------------------------------------
# Skin
# ---------------------------------------------------------------------------

SKIN = """
<screen name="TVIMainMenu" position="center,center" size="720,580" title="TVI Player">
    <widget name="menu" position="10,10" size="700,520" scrollbarMode="showOnDemand"
        font="Regular;30" itemHeight="55"
        backgroundColor="#0f0f0f" backgroundColorSelected="#1a3a6e"
        foregroundColor="#ffffff" foregroundColorSelected="#ffffff" />
    <widget name="status" position="10,540" size="700,36" font="Regular;24" halign="center" />
</screen>

<screen name="TVIShowList" position="center,center" size="740,620" title="TVI Player">
    <widget name="list" position="10,10" size="720,564" scrollbarMode="showOnDemand"
        font="Regular;30" itemHeight="55"
        backgroundColor="#0f0f0f" backgroundColorSelected="#1a3a6e"
        foregroundColor="#ffffff" foregroundColorSelected="#ffffff" />
    <widget name="status" position="10,582" size="720,34" font="Regular;22" halign="center" />
</screen>

<screen name="TVIEpisodeList" position="center,center" size="740,620" title="TVI Player">
    <widget name="list" position="10,10" size="720,564" scrollbarMode="showOnDemand"
        font="Regular;30" itemHeight="55"
        backgroundColor="#0f0f0f" backgroundColorSelected="#1a3a6e"
        foregroundColor="#ffffff" foregroundColorSelected="#ffffff" />
    <widget name="status" position="10,582" size="720,34" font="Regular;22" halign="center" />
</screen>

"""


# ---------------------------------------------------------------------------
# MainMenuScreen
# ---------------------------------------------------------------------------

class MainMenuScreen(Screen):
    skin = '<screen name="TVIMainMenu"' + SKIN.split('<screen name="TVIMainMenu"')[1].split('</screen>')[0] + '</screen>'

    def __init__(self, session):
        Screen.__init__(self, session)
        self.setTitle("TVI Player")

        items = [(cat, cat) for cat in CATEGORIES]
        self["menu"] = MenuList(items)
        self["status"] = Label("")

        self["actions"] = ActionMap(
            ["OkCancelActions"],
            {
                "ok": self._on_ok,
                "cancel": self.close,
            },
            -1,
        )

        cfg = load_config()
        if cfg is None:
            self["status"].setText("Aviso: sem ficheiro /etc/enigma2/tviplayer.json")
        else:
            _run_async(api.login, cfg["email"], cfg["password"])

    def _on_ok(self):
        sel = self["menu"].getCurrent()
        if sel:
            self.session.open(ShowListScreen, sel[0])


# ---------------------------------------------------------------------------
# ShowListScreen
# ---------------------------------------------------------------------------

class ShowListScreen(Screen):
    skin = '<screen name="TVIShowList"' + SKIN.split('<screen name="TVIShowList"')[1].split('</screen>')[0] + '</screen>'

    def __init__(self, session, category):
        Screen.__init__(self, session)
        self.setTitle("TVI Player \u2014 " + category)
        self._category = category
        self._shows = []

        self["list"] = MenuList([])
        self["status"] = Label("A carregar programas...")

        self["actions"] = ActionMap(
            ["OkCancelActions"],
            {
                "ok": self._on_ok,
                "cancel": self.close,
            },
            -1,
        )

        self.onLayoutFinish.append(self._on_layout_finish)

    def _on_layout_finish(self):
        _run_async(api.get_shows, self._category,
                   on_success=self._on_loaded, on_error=self._on_error)

    def _on_loaded(self, shows):
        self._shows = shows
        self["status"].setText(
            "{} programa(s)".format(len(shows)) if shows else "Nenhum programa dispon\u00edvel."
        )
        items = [(s["title"], s) for s in shows]
        self["list"].setList(items)

    def _on_error(self, exc):
        msg = str(exc)[:100]
        log.error("ShowListScreen error: %s", exc)
        self["status"].setText("Erro: " + msg)

    def _on_ok(self):
        sel = self["list"].getCurrent()
        if sel:
            show = sel[1]
            self.session.open(EpisodeListScreen, show["slug"], show["show_id"], show["title"])


# ---------------------------------------------------------------------------
# EpisodeListScreen
# ---------------------------------------------------------------------------

class EpisodeListScreen(Screen):
    skin = '<screen name="TVIEpisodeList"' + SKIN.split('<screen name="TVIEpisodeList"')[1].split('</screen>')[0] + '</screen>'

    def __init__(self, session, slug, show_id, show_title=""):
        Screen.__init__(self, session)
        self.setTitle("TVI Player \u2014 " + show_title)
        self._slug = slug
        self._show_id = show_id
        self._episodes = []

        self["list"] = MenuList([])
        self["status"] = Label("A carregar epis\u00f3dios...")

        self["actions"] = ActionMap(
            ["OkCancelActions"],
            {
                "ok": self._on_ok,
                "cancel": self.close,
            },
            -1,
        )

        self.onLayoutFinish.append(self._on_layout_finish)

    def _on_layout_finish(self):
        _run_async(api.get_episodes, self._slug, self._show_id,
                   on_success=self._on_loaded, on_error=self._on_error)

    def _on_loaded(self, episodes):
        self._episodes = episodes
        if not episodes:
            self["status"].setText("Nenhum epis\u00f3dio dispon\u00edvel.")
            return
        self["status"].setText("{} epis\u00f3dio(s)".format(len(episodes)))
        items = []
        for ep in episodes:
            parts = [ep.get("air_date", ""), ep.get("ep_num", ""), ep["title"]]
            label = "  \u2022  ".join(p for p in parts if p)
            items.append((label, ep))
        self["list"].setList(items)

    def _on_error(self, exc):
        msg = str(exc)[:100]
        log.error("EpisodeListScreen error: %s", exc)
        self["status"].setText("Erro: " + msg)

    def _on_ok(self):
        sel = self["list"].getCurrent()
        if not sel:
            return
        ep = sel[1]
        self._current_title = ep["title"]
        self["status"].setText("A carregar stream...")
        _run_async(api.get_stream_url, ep["url"],
                   on_success=self._on_stream, on_error=self._on_stream_error)

    def _on_stream(self, stream_url):
        self["status"].setText("")
        log.debug("Opening player for: %s", stream_url[:80])
        ref = eServiceReference(SERVICE_TYPE, 0, stream_url)
        if _HAVE_MOVIEPLAYER:
            log.debug("Using TVIMoviePlayer with service type %d", SERVICE_TYPE)
            self.session.open(TVIMoviePlayer, ref)
        else:
            log.debug("MoviePlayer unavailable, using playService")
            self.session.nav.playService(ref)

    def _on_stream_error(self, exc):
        log.error("Stream error: %s", exc)
        self.session.open(
            MessageBox,
            "Erro ao obter stream:\n" + str(exc),
            MessageBox.TYPE_ERROR,
            timeout=5,
        )
        self["status"].setText("")


