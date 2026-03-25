from Plugins.Plugin import PluginDescriptor
from .screens import MainMenuScreen


def main(session, **kwargs):
    session.open(MainMenuScreen)


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="TVI Player",
            description="Ver programas e episódios do TVI Player",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main,
        )
    ]
