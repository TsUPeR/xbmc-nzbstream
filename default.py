"""
 Copyright (c) 2010 Popeye

 Permission is hereby granted, free of charge, to any person
 obtaining a copy of this software and associated documentation
 files (the "Software"), to deal in the Software without
 restriction, including without limitation the rights to use,
 copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following
 conditions:

 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 OTHER DEALINGS IN THE SOFTWARE.
"""

import urllib
import urllib2

import re

import xbmcaddon
import xbmcgui
import xbmcplugin

from xml.dom.minidom import parse, parseString

__settings__ = xbmcaddon.Addon(id='plugin.video.nzbstream')
__language__ = __settings__.getLocalizedString

NZBS_URL = "plugin://plugin.video.nzbs"

NS_REPORT = "http://www.newzbin.com/DTD/2007/feeds/report/"
NS_NEWZNAB = "http://www.newznab.com/DTD/2010/feeds/attributes/"

MODE_LIST = "list"
MODE_DOWNLOAD = "download"
MODE_INCOMPLETE = "incomplete"
MODE_HIDE = "hide"
           
SITE_URL = __settings__.getSetting("nzbstream_site")
SITE_CAPS = "http://" + SITE_URL + "/api?t=caps"

RE_RATING = __settings__.getSetting("nzbstream_re_rating")
RE_PLOT = __settings__.getSetting("nzbstream_re_plot")
RE_YEAR = __settings__.getSetting("nzbstream_re_year")
RE_GENRE = __settings__.getSetting("nzbstream_re_genre")
RE_DIRECTOR = __settings__.getSetting("nzbstream_re_director")
RE_ACTORS = __settings__.getSetting("nzbstream_re_actors")
RE_THUMB = __settings__.getSetting("nzbstream_re_thumb").replace("SITE_URL", SITE_URL)

HIDE_CAT = __settings__.getSetting("nzbstream_hide_cat")

MODE_NZBSTREAM = "nzbstream"
MODE_NZBSTREAM_SEARCH = "nzbstream&nzbstream=search"
MODE_NZBSTREAM_MY = "nzbstream&nzbstream=mycart"

NZBSTREAM_URL = ("http://" + __settings__.getSetting("nzbstream_site") + "/rss?dl=1&i=" + __settings__.getSetting("nzbstream_id") + 
            "&r=" + __settings__.getSetting("nzbstream_key"))
NZBSTREAM_URL_SEARCH = ("http://" + __settings__.getSetting("nzbstream_site") + "/api?dl=1&apikey=" + __settings__.getSetting("nzbstream_key"))

        
def site_caps(url):
    doc, state = load_xml(url)
    if doc and not state:
        table = []
        for category in doc.getElementsByTagName("category"):
            row = []
            row.append(category.getAttribute("name"))
            row.append(category.getAttribute("id"))
            table.append(row)
            if category.getElementsByTagName("subcat"):
                for subcat in category.getElementsByTagName("subcat"):
                    row = []
                    row.append((" - " + subcat.getAttribute("name")))
                    row.append(subcat.getAttribute("id"))
                    table.append(row)
    return table

def nzbstream(params):
    if not(__settings__.getSetting("nzbstream_id") and __settings__.getSetting("nzbstream_key")):
        __settings__.openSettings()
    else:
        if params:
            get = params.get
            catid = get("catid")
            nzbstream = get("nzbstream")
            url = None
            if nzbstream:
                if nzbstream == "mycart":
                    url = NZBSTREAM_URL + "&t=-2"
                if nzbstream == "search":
                    search_term = search('SITE_URL')
                    if search_term:
                        url = (NZBSTREAM_URL_SEARCH + "&t=search" + "&cat=" + catid + "&q=" 
                        + search_term)
            elif catid:
                url = NZBSTREAM_URL + "&t=" + catid
                key = "&catid=" + catid
                addPosts('Search...', key, MODE_NZBSTREAM_SEARCH)
            if url:
                list_feed_nzbstream(url)
        else:
            for name, catid in site_caps(SITE_CAPS):
                if not re.search(HIDE_CAT, catid, re.IGNORECASE) or not HIDE_CAT:
                    key = "&catid=" + str(catid)
                    addPosts(name, key, MODE_NZBSTREAM)
            addPosts("My Cart", '', MODE_NZBSTREAM_MY)
            addPosts('Incomplete', '', MODE_INCOMPLETE)
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    return

def list_feed_nzbstream(feedUrl):
    doc, state = load_xml(feedUrl)
    if doc and not state:
        for item in doc.getElementsByTagName("item"):
            title = get_node_value(item, "title")
            description = get_node_value(item, "description")
            rating = re.search(RE_RATING, description, re.IGNORECASE|re.DOTALL)
            if rating:
                rating = float(rating.group(1))
            else:
                rating = 0
            plot = re.search(RE_PLOT, description, re.IGNORECASE|re.DOTALL)
            if plot:
                plot = plot.group(1)
            else:
                plot = ""
            year = re.search(RE_YEAR, description, re.IGNORECASE|re.DOTALL)
            if year:
                year = int(year.group(1))
            else:
                year = 0
            genre = re.search(RE_GENRE, description, re.IGNORECASE|re.DOTALL)
            if genre:
                genre = genre.group(1)
            else:
                genre = ""
            director = re.search(RE_DIRECTOR, description, re.IGNORECASE|re.DOTALL)
            if director:
                director = director.group(1)
            else:
                director = ""
            actors = re.search(RE_ACTORS, description, re.IGNORECASE|re.DOTALL)
            if actors:
                actors = actors.group(1)
            else:
                actors = ""
            nzb = get_node_value(item, "link")
            thumb_re = re.search(RE_THUMB, description, re.IGNORECASE|re.DOTALL)
            if thumb_re:
                regex = re.compile(RE_THUMB,re.IGNORECASE)
                thumb = regex.findall(description)[0]
            else:
                thumb = ""
            nzb = "&nzb=" + urllib.quote_plus(nzb) + "&nzbname=" + urllib.quote_plus(title.encode('utf-8'))
            mode = MODE_LIST
            addPosts(title, nzb, mode, plot, thumb, rating, year, genre, director, actors)
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    else:
        if state == "site":
            xbmc.executebuiltin('Notification("NzbStream","Site down")')
        else:
            xbmc.executebuiltin('Notification("NzbStream","Malformed result")')
    return

def addPosts(title, url, mode, description='', thumb='', rating = 0, year = 0, genre = '', director = '', actors = '', folder=True):
    listitem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=thumb)
    listitem.setInfo(type="Video", infoLabels={ "Title": title, "Plot" : description, "Rating" : rating, "Year" : year, 
                    "Genre" : genre, "Director" : director, "Actors" : actors})    
    if mode == MODE_NZBSTREAM:
        cm = []
        cm_mode = MODE_HIDE
        cm_label = "Hide"
        cm_url_hide = sys.argv[0] + '?mode=' + cm_mode + url
        cm.append((cm_label , "XBMC.RunPlugin(%s)" % (cm_url_hide)))
        listitem.addContextMenuItems(cm, replaceItems=False)
        xurl = "%s?mode=%s" % (sys.argv[0],mode)
    if mode == MODE_LIST:
        cm = []
        cm_mode = MODE_DOWNLOAD
        cm_label = "Download"
        if (xbmcaddon.Addon(id='plugin.video.nzbs').getSetting("auto_play").lower() == "true"):
            folder = False
        cm_url_download = NZBS_URL + '?mode=' + cm_mode + url
        cm.append((cm_label , "XBMC.RunPlugin(%s)" % (cm_url_download)))
        listitem.addContextMenuItems(cm, replaceItems=False)
        xurl = "%s?mode=%s" % (NZBS_URL,mode)
    elif mode == MODE_INCOMPLETE:
        xurl = "%s?mode=%s" % (NZBS_URL,mode)
    else:
        xurl = "%s?mode=%s" % (sys.argv[0],mode)
    xurl = xurl + url
    listitem.setPath(xurl)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=xurl, listitem=listitem, isFolder=folder)

def hide_cat(params):
    get = params.get
    catid = get("catid")
    re_cat = '(\d)000'
    if re.search(re_cat, catid, re.IGNORECASE):
        regex = re.compile(re_cat,re.IGNORECASE)
        new_cat = regex.findall(catid)[0] + "\d\d\d"
        if HIDE_CAT:
            new_cat = new_cat + "|" +  HIDE_CAT
    else:
        new_cat = catid
        if HIDE_CAT:
            new_cat = new_cat + "|" +  HIDE_CAT
    __settings__.setSetting("nzbstream_hide_cat", new_cat)
    xbmc.executebuiltin("Container.Refresh")
    return

# FROM plugin.video.youtube.beta  -- converts the request url passed on by xbmc to our plugin into a dict  
def getParameters(parameterString):
    commands = {}
    splitCommands = parameterString[parameterString.find('?')+1:].split('&')
    
    for command in splitCommands: 
        if (len(command) > 0):
            splitCommand = command.split('=')
            name = splitCommand[0]
            value = splitCommand[1]
            commands[name] = value
    
    return commands

def get_node_value(parent, name, ns=""):
    if ns:
        return parent.getElementsByTagNameNS(ns, name)[0].childNodes[0].data
    else:
        return parent.getElementsByTagName(name)[0].childNodes[0].data

def load_xml(url):
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
    except:
        xbmc.log("plugin.video.nzbstream: unable to load url: " + url)
        return None, "site"
    xml = response.read()
    response.close()
    try:
        out = parseString(xml)
    except:
        xbmc.log("plugin.video.nzbstream: malformed xml from url: " + url)
        return None, "xml"
    return out, None

def search(dialog_name):
    searchString = unikeyboard(__settings__.getSetting( "latestSearch" ), ('Search ' + SITE_URL) )
    if searchString == "":
        xbmcgui.Dialog().ok('NzbStream','Missing text')
    elif searchString:
        latestSearch = __settings__.setSetting( "latestSearch", searchString )
        dialogProgress = xbmcgui.DialogProgress()
        dialogProgress.create(dialog_name, 'Searching for: ' , searchString)
        #The XBMC onscreen keyboard outputs utf-8 and this need to be encoded to unicode
    encodedSearchString = urllib.quote_plus(searchString.decode("utf_8").encode("raw_unicode_escape"))
    return encodedSearchString

#From old undertexter.se plugin    
def unikeyboard(default, message):
    keyboard = xbmc.Keyboard(default, message)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return keyboard.getText()
    else:
        return ""

if (__name__ == "__main__" ):
    if not (__settings__.getSetting("firstrun") and __settings__.getSetting("nzbstream_id")
        and __settings__.getSetting("nzbstream_key")):
        # Try import from nzbs
        try:
            __nzbs_settings__ = xbmcaddon.Addon(id='plugin.video.nzbs')
            __settings__.setSetting("nzbstream_id", __nzbs_settings__.getSetting("nzbstream_id"))
            __settings__.setSetting("nzbstream_key", __nzbs_settings__.getSetting("nzbstream_key"))
        except:
            xbmc.log("plugin.video.nzbstream - nothing to import from plugin.video.nzbs")
        __settings__.openSettings()
        __settings__.setSetting("firstrun", '1')
    if (not sys.argv[2]):
        nzbstream(None)
    else:
        params = getParameters(sys.argv[2])
        get = params.get
        if get("mode")== MODE_NZBSTREAM:
            nzbstream(params)
        if get("mode")== MODE_HIDE:
            hide_cat(params)

xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=True, cacheToDisc=True)