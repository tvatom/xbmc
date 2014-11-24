#!/usr/bin/python

## tkooda : 2014-09-06 : xbmc video add-on

import os
import sys
import urllib
import urllib2
import json
import urlparse
from operator import itemgetter

import xbmcgui
try:
    import xbmcplugin
except:
    pass

PATH_CACHE = "/storage/tvatom-cache"


DEBUG = 9


def do_debug( level, *args ):
    try:
        if level <= DEBUG:
            print >>sys.stderr, "##### TVATOM DEBUG: (%d): %s" % ( level, args )
    except:
        pass


def build_appurl( query ):
## tkooda : 2014-11-23 : 
    if sys.argv[ 0 ].startswith( "plugin://" ):
        return sys.argv[ 0 ] + '?' + urllib.urlencode( query )
    else: # full path to file?
        return "plugin://" + sys.argv[ 0 ][ len( "/storage/.xbmc/addons/" ) : ] + '?' + urllib.urlencode( query )


def fetch_url_with_auth( url ):
    request = urllib2.Request( url )
    
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password( None, url,
                                   xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "username" ),
                                   xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "password" ) )
    
    auth_manager = urllib2.HTTPBasicAuthHandler( password_manager )
    opener = urllib2.build_opener( auth_manager )
    
    urllib2.install_opener( opener )
    
    handler = urllib2.urlopen( request )
    
    # handler.getcode()
    # handler.headers.getheader('content-type')
    
    return handler.read()


def fetch_object_from_json_url_with_auth( url, sortkey = None ):
    data_json = fetch_url_with_auth( url )
    obj = json.loads( data_json )
    if sortkey:
        obj = sorted( obj, key = itemgetter( sortkey ) )
    return obj


def write_file( path_file, data ):
    tmp = path_file + ".tmp"
    num = 0
    try:
        fd = os.open( tmp, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0644 )
        num = os.write( fd, data )
        os.close( fd )
        os.rename( tmp, path_file )
    except:
        import traceback
        traceback.print_exc( file=sys.stderr )
        sys.stderr.flush()
        pass
    return num == len( data ) # return True == success


def cache_show( show, tvdb_id ):
    if not tvdb_id:
        return
    
    path_show = os.path.join( PATH_CACHE, show )
    if not os.path.isdir( path_show ):
        os.makedirs( path_show )
    
    path_show_nfo = os.path.join( path_show, "tvshow.nfo" )
    if os.path.exists( path_show_nfo ):
        return
    
    print "DEBUG: cache_show:", show, tvdb_id, path_show_nfo
    
    write_file( path_show_nfo,
                "http://thetvdb.com/?tab=series&id=%s" % tvdb_id )


def NOTYET_cache_episode( show, season, episode, url_strm ):
    path_episode = os.path.join( PATH_CACHE, show, season, episode )
    if not os.path.isdir( path_episode ):
        os.makedirs( path_episode )
    
    path_episode_strm = os.path.join( path_episode,
                                      os.path.basename( url_strm ) + ".strm" )
    if os.path.exists( path_episode_strm ):
        return
    
    print "DEBUG: cache_episode:", show, season, episode, url_strm, path_episode_strm
    
    write_file( path_episode_strm, url_strm )


def get_settings():
    setting_server = xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "server" )
    setting_username = xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "username" )
    setting_password = xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "password" )
    
    if not setting_server:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter server name:", "tvatom.com" )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).setSetting( "server", s )
            setting_server = s
        else:
            return False
    
    if not setting_username:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter username:" )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).setSetting( "username", s )
            setting_username = s
        else:
            return False
    
    if not setting_password:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter password:", type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).setSetting( "password", s )
            setting_password = s
        else:
            return False
    
    do_debug( 1, "settings:", setting_server, setting_username, setting_password )
    return setting_server, setting_username, setting_password



def main():
    print "DEBUG: args:", sys.argv
    
    ## init vars from args ..
    base_url = sys.argv[ 0 ]
    addon_handle = int( sys.argv[ 1 ] )
    args = urlparse.parse_qs( sys.argv[ 2 ][ 1: ] )
    arg_show = args.get( 'show', [ None ] )[ 0 ]
    arg_season = args.get( 'season', [ None ] )[ 0 ]
    arg_episode = args.get( 'episode', [ None ] )[ 0 ]
    
    ## set content type ..
    xbmcplugin.setContent( addon_handle, 'tvshows' )
    

    ## require (prompt for any missing) settings ..
    settings = False
    while not settings:
        settings = get_settings()
        if not settings:
            do_debug( 1, "not settings:", settings )
    
    setting_username = xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "username" )
    setting_password = xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "password" )
    setting_server = xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "server" )
    
    do_debug( 1, "settings:", settings )
    
    
    if not arg_show:
        url_index = "http://feed1.tvatom.com/index/tv-show.json"
        show_list = fetch_object_from_json_url_with_auth( url_index,
                                                          sortkey = "name" )
        
## tkooda : 2014-09-07 : DEBUG:
#        show_list = [  {
#  "code": "tt0496424", 
#  "imdb": "tt0496424", 
#  "dateadded": "2014-08-31 09:01:57", 
#  "name": "30.rock", 
#  "plot": "Emmy Award Winner Tina Fey writes, executive produces and stars as Liz Lemon, the head writer of a live variety programme in New York City. Liz's life is turned upside down when brash new network executive Jack Donaghy (Alec Baldwin in his Golden Globe winning role) interferes with her show, bringing the wildly unpredictable Tracy Jordan (Tracy Morgan) into the cast. Now its up to Liz to manage the mayhem and still try to have a life.", 
#  "premiered": "2006-10-11", 
#  "status": "Ended", 
#  "studio": "NBC", 
#  "tvdb_id": "79488", 
#  "tvdbid": "79488", 
#  "tvdb": "79488", 
#  "id": "79488", 
#  "tvshowtitle": "30 Rock",
#
#  "": "",

#    "genre": "Comedy",
#    "year": 2009,
#    "episode": 4,
#    "season": 1,
#    "top250": 192,
#    "tracknumber": 3,
#    "rating": 6.4, # - range is 0..10
#    "playcount": 2, # - number of times this item has been played
#    "overlay": 2, # - range is 0..8.  See GUIListItem.h for values
##    "cast": list (Michal C. Hall)
##    "castandrole": list (Michael C. Hall|Dexter)
#    "director": "Dagur Kari",
#    "mpaa": "PG-13",
#    "plot": "Long Description",
#    "plotoutline": "Short Description",
#    "title": "Big Fan",
#    "originaltitle": "Big Fan",
#    "duration": "3:18",
#    "studio": "Warner Bros.",
#    "tagline": "An awesome movie", # - short description of movie
#    "writer": "Robert D. Siegel",
#    "premiered": "2005-03-04",
#    "status": "Continuing", # - status of a TVshow
#    "code": "tt0110293", # - IMDb code
#    "aired": "2008-12-07",
#    "credits": "Andy Kaufman", # - writing credits
#    "lastplayed": "2009-04-05 23:16:04",
#    "album": "The Joshua Tree",
#    "votes": "12345 votes",
#    "trailer": "/home/user/trailer.avi",
#  "": "",
# }, 
# {
#  "code": "tt3101352", 
#  "dateadded": "2014-07-18 21:54:40", 
#  "name": "37.days", 
#  "plot": "Covering the final weeks before the outbreak of war, 37 Days follows the rapidly changing crisis through the eyes of the principal players, during a hot summer, from the assassination of Archduke Franz Ferdinand on 28 June 1914, to the declaration of war between Britain and Germany on 4 August.\n\nThe drama serial will overturn orthodox assumptions about the wars inevitability. Such a disaster did not happen by chance, and nor was it a foregone conclusion. It took considerable effort and terrific ingenuity, as well as staggering bad luck, to destroy a system that had kept the general peace in Europe for the 99 years that followed the Battle of Waterloo and the fall of Napoleon.\n\nWriter Mark Hayhurst comes fresh from the success of Hitler On Trial for BBC Two, which starred Ed Stoppard and Ian Hart. He has previously written award-winning docu-dramas for major broadcasters, such as Robespierre And The French Revolution, Last Days Of The Raj, The Somme and The Year London Blew Up", 
#  "premiered": "2014-03-06", 
#  "status": "Ended", 
#  "studio": "BBC Two", 
#  "tvdb_id": "274115", 
#  "tvshowtitle": "37 Days"
# }, 
#]

        for show in show_list:
#        for show in show_list[ 10 : 12 ]:  ## DEBUG
            appurl_show = build_appurl( base_url, { "show": show.get( "name" ) } )
            
            list_item = xbmcgui.ListItem( show.get( "tvshowtitle", show.get( "name" ) ),
                                          )
#                                          iconImage = "DefaultFolder.png" )

#            if show.get( "name" ) == "30.rock":
#                print "30.rock"
#                show[ "" ] = ""
#            print "#################################################"
#            print "DEBUG: ################### OBJECT:"
#            print json.dumps( show, sort_keys = True, indent = 2 )
#            print "#################################################"
            
            list_item.setInfo( "video", infoLabels = show )
            
            
            ## XXX FIXME TODO: add more info here: e.g. show name
            
            
            xbmcplugin.addDirectoryItem( handle = addon_handle,
                                         url = appurl_show,
                                         listitem = list_item,
                                         isFolder = True,
                                         totalItems = len( show_list ) )
            
#            cache_show( show.get( "name" ), show.get( "tvdb_id" ) )
        
        
        xbmcplugin.endOfDirectory( addon_handle )
        
        return # done building show index
    
    
    if arg_show and not arg_show or not arg_episode:
        url_show = "http://feed1.tvatom.com/show/%s.json" % arg_show
        episode_list = fetch_object_from_json_url_with_auth( url_show )
        
        for episode in episode_list:
            episode_season = episode.get( "Season" )
            episode_num = episode.get( "Episode" )
            episode_file = episode.get( "file" )
            
            if not episode_season:
                print "WARNING: MISSING: episode_season"
                continue
            
            if not episode_num:
                print "WARNING: MISSING: episode_num"
                continue
            
            if not episode_file:
                print "WARNING: MISSING: episode_file"
                continue
            
            list_item = xbmcgui.ListItem( "s%se%s - %s" % ( episode_season,
                                                            episode_num,
                                                            episode.get( "TVShowTitle" ) ),
                                          iconImage = "DefaultVideo.png" )
            
#            episode[
            
            list_item.setInfo( "video", episode )
            
            
            
            ## XXX FIXME TODO: add more info here: e.g. show name
            
            
            
            url_episode = os.path.join( "http://%s:%s@data11.%s/show/" % ( setting_username, setting_password, setting_server ),
                                        arg_show, episode_season, episode_num, episode_file ) #+ "|auth=any"
            
            xbmcplugin.addDirectoryItem( handle = addon_handle,
                                         url = url_episode,
                                         listitem = list_item,
                                         totalItems = len( episode_list ) )
            
        
        xbmcplugin.endOfDirectory( addon_handle )
        
        return # done building episode index


if __name__ == "__main__":
    main()

