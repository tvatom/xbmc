#!/usr/bin/python

## tkooda : 2014-09-06 : xbmc video add-on

## tkooda : 2014-09-08 : modified to be subscriber interface

## FIXME: this should probably be named a "script" to show up in programs, and not a video plugin??



import os
import sys
import urllib
import urllib2
import json
import urlparse
from operator import itemgetter
import shutil

import xbmc
import xbmcgui
#import resources.lib.utils as utils
import xbmcaddon
import xbmcplugin


PATH_STRM = "/storage/tvatom-strm/tv"
PATH_CACHE = "/storage/tvatom-cache/tv"
PATH_SUBSCRIBED = "/storage/.cache/tvatom/tv-subscribed"

PLAY_THROUGH_ADDON = True

FILE_SUB_UNSUB = "%s.s99e99.%s"
NFO_SUB_UNSUB = """<episodedetails>
  <title>Click to %s to %s</title>
  <season>99</season>
  <episode>99</episode>
</episodedetails>
"""

NFO_EPISODE = """<episodedetails>
  <title>%s</title>
  <season>%s</season>
  <episode>%s</episode>
</episodedetails>
"""

DEBUG = 9


def do_debug( level, *args ):
    try:
        if level <= DEBUG:
            print >>sys.stderr, "##### TVATOM DEBUG: %s (%d): %s" % ( os.path.basename( sys.argv[0]), level, args )
    except:
        pass


def build_appurl( query ):
## tkooda : 2014-11-23 : 
    if sys.argv[ 0 ].startswith( "plugin://" ):
        return sys.argv[ 0 ] + '?' + urllib.urlencode( query )
    else: # full path to file?
        return "plugin://" + sys.argv[ 0 ][ len( "/storage/.xbmc/addons/" ) : ] + '?' + urllib.urlencode( query )



def fetch_url_with_auth( url, warn_errors = False ):
    request = urllib2.Request( url )
    
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password( None, url,
                                   xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "username" ),
                                   xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "password" ) )
    
    auth_manager = urllib2.HTTPBasicAuthHandler( password_manager )
    opener = urllib2.build_opener( auth_manager )
    
    urllib2.install_opener( opener )
    
    handler = None
    try:
        handler = urllib2.urlopen( request )
    except urllib2.HTTPError, err:
        do_debug( 1, "HTTPError: %s" % err, url )
        pass
    except urllib2.URLError, err:
        do_debug( 1, "URLError: %s" % err, url )
        pass
    
    # handler.headers.getheader('content-type')
    # handler.getcode()
    
    if handler:
        return handler.read()
    
    if warn_errors:
        dialog = xbmcgui.Dialog()
        dialog.ok( "TV Atom Connection Error:", str( err ), url )
        sys.exit( 1 )
    
    return None # hit this upon valid auth but 401 FNF or something..



def fetch_object_from_json_url_with_auth( url, sortkey = None, warn_errors = False ):
    data_json = fetch_url_with_auth( url, warn_errors )
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



def toggle_sub_unsub_files( show, sub_unsub, tvdb_id = None ):
    if not show or not sub_unsub:
        return
    
    path_show = os.path.join( PATH_STRM, show, "99/99" )
    if not os.path.isdir( path_show ):
        os.makedirs( path_show )
    
    path_show_file_sub_unsub = os.path.join( path_show,
                                       FILE_SUB_UNSUB % ( show, sub_unsub ) )
    path_show_file_sub_unsub_strm = path_show_file_sub_unsub + ".strm"
    path_show_file_sub_unsub_nfo  = path_show_file_sub_unsub + ".nfo"
    
    
    ## create Subscribe/Unsubscribe strm/nfo files..
    if not os.path.exists( path_show_file_sub_unsub_strm ):
        do_debug( 1, "toggle_sub_unsub_files():", show, sub_unsub, path_show_file_sub_unsub )
        write_file( path_show_file_sub_unsub_strm,
                    build_appurl( { "action": sub_unsub.lower(),
                                    "show": show } ) )
    
    if not os.path.exists( path_show_file_sub_unsub_nfo ):
        write_file( path_show_file_sub_unsub_nfo,
                    NFO_SUB_UNSUB % ( sub_unsub, show ) )
    
    
    ## delete old Unsubscribe/Subscribe strm/nfo files..
    if sub_unsub == "Subscribe":
        delete_sub_unsub = "Unsubscribe"
    else:
        delete_sub_unsub = "Subscribe"
    
    path_show_file_sub_unsub = os.path.join( path_show,
                                             FILE_SUB_UNSUB % ( show, delete_sub_unsub ) )
    for ext in [ "strm", "nfo" ]:
        try:
            os.unlink( path_show_file_sub_unsub + "." + ext )
        except:
            pass

## tkooda : 2014-11-23 : add tvshow.nfo symlinks to prevent XBMC from adding garbage show/series names when it finds a season directory that contains show directories
    path_episode_season_symlink = os.path.join( PATH_STRM, show, "99/tvshow.nfo" )
    if not os.path.lexists( path_episode_season_symlink ):
        os.symlink( "../tvshow.nfo", path_episode_season_symlink )


def cache_show_info( show, tvdb_id ):
    if not show or not tvdb_id:
        return
    
    path_show = os.path.join( PATH_STRM, show )
    if not os.path.isdir( path_show ):
        os.makedirs( path_show )
    
    path_show_nfo = os.path.join( path_show, "tvshow.nfo" )
    if not os.path.exists( path_show_nfo ):
        do_debug( 1, "cache_show_info: nfo:", show, tvdb_id, path_show_nfo )
        write_file( path_show_nfo,
                    "http://thetvdb.com/?tab=series&id=%s" % tvdb_id )
    
    toggle_sub_unsub_files( show, "Subscribe" )


def DEBUG_cache_tvdbid_to_subdir( subdir, tvdb_id ):  # e.g.: ("30.rock/01", "79488")
    if not subdir or not tvdb_id:
        return
    
    path_subdir = os.path.join( PATH_STRM, subdir )
    if not os.path.isdir( path_subdir ):
        os.makedirs( path_subdir )
    
    path_subdir_nfo = os.path.join( path_subdir, "tvshow.nfo" )
    if not os.path.exists( path_subdir_nfo ):
        do_debug( 1, "cache_subdir_info: nfo:", subdir, tvdb_id, path_subdir_nfo )
        write_file( path_subdir_nfo,
                    "http://thetvdb.com/?tab=series&id=%s" % tvdb_id )




def cache_nfo_for_all_shows():
    do_debug( 1, "cache_nfo_for_all_shows()" )
    
    cancelled = False
    
    url_index = "http://feed1.tvatom.com/index/tv-show.json"
    show_list = fetch_object_from_json_url_with_auth( url_index,
                                                      sortkey = "name" )
    
    if xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "rating" ) != "adult":
        for show in show_list:
            if show.get( "adult" ):
                show_list.remove( show ) # censor adult shows for users w/out "adult" rating setting
    
    
    progress = xbmcgui.DialogProgress()
    progress.create('Progress', 'Caching info for all TV Shows..')
    show_num = 1
    show_total = len( show_list )
    
    for show in show_list:
#    for show in show_list[ 10 : 12 ]:  ## FIXME XXX: TVATOM DEBUG
        cache_show_info( show.get( "name" ), show.get( "tvdb_id" ) )
        progress_message = "%d out of %d" % ( show_num, show_total ) 
        progress.update( int( ( show_num / float( show_total ) ) * 100 ), "", progress_message, "" )
        if progress.iscanceled():
            cancelled = True
            break
        show_num += 1
    progress.close()
    
    
    ## FIXME:  delete strm cache dirs for shows that aren't in the show_list json?  (e.g. if I delete or rename a show; WARNING: won't work with two sources, as this only takes one json source for now)
    progress = xbmcgui.DialogProgress()
    progress.create('Progress', 'Looking for undesired TV Shows in cache..')
    show_list_names = [ item[ "name" ] for item in show_list ]
    shows_to_possibly_delete = []
    show_num = 0
    for show in os.listdir( PATH_STRM ):
        progress_message = "%d out of %d" % ( show_num, show_total ) 
        progress.update( int( ( show_num / float( show_total ) ) * 100 ), "", progress_message, "" )
        if progress.iscanceled():
            cancelled = True
            break
        
        if show not in show_list_names: ## tkooda : 2014-11-24 : XXXX FIXME: THIS LIST LOOKUP IS SLOW!, TRY USING A set() for show_list_names instead
            do_debug( 2, "FIXME: show NOT in show_list from json, possibly delete it?:", show )
            shows_to_possibly_delete.append( show )
        
        show_num += 1
    
    if shows_to_possibly_delete and len( shows_to_possibly_delete ) < 20: ## guard against deleting ALL shows if ever empty list from json
        do_debug( 1, "DELETING SHOWS:", shows_to_possibly_delete )
        for show in shows_to_possibly_delete:
            path_show_to_delete = os.path.join( PATH_STRM, show )
            do_debug( 1, "DELETING SHOW AT PATH:", path_show_to_delete )
            shutil.rmtree( path_show_to_delete )
    else:
        do_debug( 2, "WARNING: cache_nfo_for_all_shows(): TOO MANY SHOWS TO DELETE, NOT DELETING:", len( shows_to_possibly_delete ), shows_to_possibly_delete )
    progress.close()
    
    
## tkooda : 2014-11-24 : two progress dialog boxes
##    if not progress.iscanceled():
    if not canceled:
        ## XXX FIXME TODO: trigger updating of library for this tv show cache path..
        if not xbmc.Player().isPlaying(): # or utils.getSetting( "run_during_playback" ) == "true":
            do_debug( 1, "cache_nfo_for_all_shows(): CleanLibrary(video)" )
            xbmc.executebuiltin( "CleanLibrary(video)" ) # detect removed (e.g. newly deleted "Subscribe" file) files
## tkooda : 2014-11-23 : TRY UPDATING ALL
##            import time
##            time.sleep( 3 )
##            print "TVATOM DEBUG: UpdateLibrary(video,%s)" % PATH_STRM
##            xbmc.executebuiltin( "UpdateLibrary(video,%s)" % PATH_STRM )
            do_debug( 1, "cache_nfo_for_all_shows(): UpdateLibrary(video)" )
            xbmc.executebuiltin( "UpdateLibrary(video)" )
        else:
            do_debug( 1, "cache_nfo_for_all_shows(): WARNING: xbmc.Player().isPlaying() WAS PLAYING" )
    else:
        do_debug( 1, "cache_nfo_for_all_shows(): WARNING: progress.iscanceled() WAS CANCELLED" )


def cache_episode_strm( show, season, episode, url_strm, filename = None ): # specify filename ("myshow.s01e03.hdtv.avi") if using local app URL
    path_episode = os.path.join( PATH_STRM, show, season, episode )
    if not os.path.isdir( path_episode ):
        os.makedirs( path_episode )
    
    if not filename:
        filename = os.path.basename( url_strm )
    path_episode_strm = os.path.join( path_episode,
                                      filename + ".strm" )
    if os.path.exists( path_episode_strm ):
        return
    
    do_debug( 1, "cache_episode_strm:", show, season, episode, url_strm, path_episode_strm )
    
    write_file( path_episode_strm, url_strm )



def cache_episode_strm_and_nfo( show, season, episode, url_strm, filename, show_title ): # specify filename ("myshow.s01e03.hdtv.avi") if using local app URL
    path_episode = os.path.join( PATH_STRM, show, season, episode )
    if not os.path.isdir( path_episode ):
        os.makedirs( path_episode )
    
    ## make *.strm file for episode
    path_episode_strm = os.path.join( path_episode,
                                      filename + ".strm" )
    
    do_debug( 1, "cache_episode_strm_and_nfo(): strm:", show, season, episode, url_strm, path_episode_strm )
    
    write_file( path_episode_strm, url_strm )
    
    
    ## make *.nfo file for episode
    path_episode_nfo = os.path.join( path_episode,
                                     filename + ".nfo" )
    
    do_debug( 1, "cache_episode_strm_and_nfo(): nfo:", show, season, episode, path_episode_nfo )
    
    write_file( path_episode_nfo, NFO_EPISODE % ( show_title, season, episode ) )



#def is_show_subscribed( show ):
#    if not show:
#        return False
#    
#    path_show_subfile = os.path.join( PATH_STRM, show, FILE_SUB + ".strm" )
#    return os.path.isfile( path_show_subfile )



#def delete_sub_files( show ):
#XXXXX
#    path_show_subscriber = os.path.join( show, FILE_SUB_UNSUB % ( show, "Subscribe" ) + ".strm" )
#    if os.path.exists( path_show_subscriber ):
#        os.unlink( path_show_subscriber )


def show_update( show ):
    path_show = os.path.join( PATH_STRM, show )
    if not os.path.isdir( path_show ):
        os.makedirs( path_show )
    
    url_show = "http://feed1.tvatom.com/show/%s.json" % show
    episode_list = fetch_object_from_json_url_with_auth( url_show )
    
## tkooda : 2014-11-23 : 
    for episode in episode_list:
##    for episode in episode_list[ : 25 ] : ## tkooda : 2014-11-23 : FIXME XXX DEBUG: only cache 25 episodes
        episode_season = episode.get( "season" )
        episode_num = episode.get( "episode" )
        episode_file = episode.get( "file" )
        episode_title = episode.get( "tvshowtitle" )
        
#        if not episode_season:
#            print "WARNING: MISSING: episode_season"
#            continue
#        
#        if not episode_num:
#            print "WARNING: MISSING: episode_num"
#            continue
#        
#        if not episode_file:
#            print "WARNING: MISSING: episode_file"
#            continue
        
        url_episode = os.path.join( "http://%s:%s@data1.tvatom.com/show/" % ( \
                xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "username" ),
                xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "password" ) ),
                                    show, episode_season, episode_num, episode_file ) #+ "|auth=any"
        if PLAY_THROUGH_ADDON:
## tkooda : 2014-09-22 : 
#            cache_episode_strm( show, episode_season, episode_num,
#                                build_appurl( { "action": "play",
#                                                "show": show,
#                                                "season": episode_season,
#                                                "episode": episode_num } ),
#                                episode_file )
            cache_episode_strm_and_nfo( show,
                                        episode_season,
                                        episode_num,
                                        build_appurl( { "action": "play",
                                                        "show": show,
                                                        "season": episode_season,
                                                        "episode": episode_num } ),
                                        episode_file,
                                        episode_title )
        else:
            cache_episode_strm( show, episode_season, episode_num, url_episode )
        
## tkooda : 2014-11-23 : add tvshow.nfo symlinks to prevent XBMC from adding garbage show/series names when it finds a season directory that contains show directories
        path_episode_season_symlink = os.path.join( path_show, episode_season, "tvshow.nfo" )
        if not os.path.lexists( path_episode_season_symlink ):
            os.symlink( "../tvshow.nfo", path_episode_season_symlink )
        
    
    


def subscribe_show( show ):
    if not show:
        return
    
#    if is_show_subscribed( show ):
#        print "TVATOM DEBUG: subscribe_show: is_show_subscribed() == True" 
#        return
    
## tkooda : 2014-11-23 : record list of subscribed shows in a cache
    if not os.path.isdir( PATH_SUBSCRIBED ):
        os.makedirs( PATH_SUBSCRIBED )
    path_file_subcribed = os.path.join( PATH_SUBSCRIBED, show )
    if not os.path.isfile( path_file_subcribed ):
        write_file( path_file_subcribed, "" )
    
    show_update( show )
    
    toggle_sub_unsub_files( show, "Unsubscribe" )
    
    path_show = os.path.join( PATH_STRM, show )
    do_debug( 1, "UpdateLibrary(video,%s)" % path_show )
    xbmc.executebuiltin( "UpdateLibrary(video,%s)" % path_show ) # detect any new files (e.g. newly added "Unsubscribe" file)
    xbmc.executebuiltin( "CleanLibrary(video)" ) # detect removed (e.g. newly deleted "Subscribe" file) files



def unsubscribe_show( show ):
    if not show:
        return
    
#    if not is_show_subscribed( show ):
#        print "TVATOM DEBUG: unsubscribe_show: is_show_subscribed() == False" 
#        return
    
    path_show = os.path.join( PATH_STRM, show )
    if not os.path.isdir( path_show ):
        return
    
## tkooda : 2014-11-23 : 
    path_cache_subscribed = os.path.join( PATH_SUBSCRIBED, show )
    if os.path.isfile( path_cache_subscribed ):
        os.unlink( path_cache_subscribed )
    
    shutil.rmtree( path_show )
    
    # re-cache show info..
    url_index = "http://feed1.tvatom.com/index/tv-show.json"
    show_list = fetch_object_from_json_url_with_auth( url_index )
    
    for s in show_list:
        if s.get( "name" ) == show:
            cache_show_info( s.get( "name" ), s.get( "tvdb_id" ) )
    
    xbmc.executebuiltin( "CleanLibrary(video)" ) # http://wiki.xbmc.org/index.php?title=List_of_built-in_functions
    do_debug( 1, "UpdateLibrary(video,%s)" % path_show )
    xbmc.executebuiltin( "UpdateLibrary(video,%s)" % path_show ) # tell the library that this directory has been removed?



def play_episode( show, season, episode ):
    do_debug( 1, "play_episode:", show, season, episode )
    xbmc.executebuiltin( "Playlist.Clear" )

    url_show = "http://feed1.tvatom.com/show/%s.json" % show
    episode_list = fetch_object_from_json_url_with_auth( url_show )
    
    for e in episode_list:
        episode_season = e.get( "season" )
        episode_num = e.get( "episode" )
        episode_file = e.get( "file" )
        
        if not episode_season == season:
            continue
        
        if not episode_num == episode:
            continue
        
        url_episode = os.path.join( "http://%s:%s@data1.tvatom.com/show/" % \
                                        ( xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "username" ),
                                          xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "password" ) ),
                                    show, episode_season, episode_num, episode_file ) #+ "|auth=any"
        do_debug( 1, "play_episode:", show, season, episode, url_episode )
        
        player = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
        
        listitem = xbmcgui.ListItem( label=e.get( "tvshowtitle" ),
                                     path=url_episode,
                                     iconImage='DefaultVideo.png',
                                     thumbnailImage='DefaultVideo.png' )
        listitem.setInfo( type='Video', infoLabels=episode )
#        listitem.setProperty( 'IsPlayable', 'true' )
        
        xbmcplugin.setResolvedUrl( handle=int(sys.argv[1]), succeeded=True, listitem=listitem )  ## workaround for "Error playing" bug, similar to: http://trac.xbmc.org/ticket/14192
        
        do_debug( 1, "player done" )
        
        return


## tkooda : 2014-11-23 : file locking doesn't work because they're all spawned from the same parent process??
##def cron_shows_locking():
##    ## update new episodes for shows from cron..
##    import posixfile
##    
##    path_file_lock = "/tmp/lock.tvatom_tv_subscriber"
##    fp = posixfile.open( path_file_lock, "w" )
##    try:
##        fp.lock( "w" ) # try to obtain lock
##        do_debug( 1, "cron_shows(): SUCCESSFUL LOCK OBTAINED" )
##    except:
##        # already locked
##        do_debug( 1, "cron_shows(): ALREADY LOCKED" )
##        fp.close()
##        return
##    
##    do_debug( 1, "cron_shows(): SLEEPING" )
##    import time
##    time.sleep( 30 )
##    
##    
##    setting_update_during_playback = xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "update_during_playback" )
##    if xbmc.Player().isPlaying() and not update_during_playback: # or utils.getSetting( "run_during_playback" ) == "true":
##        print "TVATOM DEBUG: cron_shows(): xbmc.Player().isPlaying() WAS PLAYING"
##        fp.close()
##        return
##    
##    updated = 0
##    for show in os.listdir( PATH_SUBSCRIBED ):
##        do_debug( 1, "cron_shows(): SHOW:", show )
##        if show_update( show ):
##            updated += 1
##    
##    if updated:
##        path_show = os.path.join( PATH_STRM, show )
##        do_debug( 1, "cron_update(): UpdateLibrary(video,%s)" % path_show )
##        xbmc.executebuiltin( "UpdateLibrary(video,%s)" % path_show ) # detect any new files (e.g. newly added "Unsubscribe" file)
##        xbmc.executebuiltin( "CleanLibrary(video)" ) # detect removed (e.g. newly deleted "Subscribe" file) files
##    
##    fp.close()



## CRONTAB:
##    */5 xbmc-send --action="RunPlugin(plugin://plugin.video.tvatom_tv_subscriber?action=cron_shows)"

def cron_shows():
    ## update new episodes for shows from cron..
    
    setting_update_during_playback = xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "update_during_playback" )
    if xbmc.Player().isPlaying() and not update_during_playback: # or utils.getSetting( "run_during_playback" ) == "true":
        do_debug( 1, "cron_shows(): xbmc.Player().isPlaying() WAS PLAYING" )
        fp.close()
        return
    
    updated = 0
    for show in os.listdir( PATH_SUBSCRIBED ):
        do_debug( 1, "cron_shows(): SHOW:", show )
        if show_update( show ):
            updated += 1
    
    if updated:
        path_show = os.path.join( PATH_STRM, show )
        do_debug( 1, "cron_update(): UpdateLibrary(video,%s)" % path_show )
        xbmc.executebuiltin( "UpdateLibrary(video,%s)" % path_show ) # detect any new files (e.g. newly added "Unsubscribe" file)
        xbmc.executebuiltin( "CleanLibrary(video)" ) # detect removed (e.g. newly deleted "Subscribe" file) files



def get_settings():
    setting_server = xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "server" )
    setting_username = xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "username" )
    setting_password = xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "password" )
    setting_dynamic_urls = xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "dynamic_urls" )
    setting_debug = xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "debug" )
    
    if not setting_server:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter server name:", "tvatom.com" )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).setSetting( "server", s )
            setting_server = s
        else:
            return False
    
    if not setting_username:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter username:" )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).setSetting( "username", s )
            setting_username = s
        else:
            return False
    
    if not setting_password:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter password:", type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).setSetting( "password", s )
            setting_password = s
        else:
            return False
    
    do_debug( 1, "settings:", setting_server, setting_username, setting_password, setting_dynamic_urls, setting_debug )
    return setting_server, setting_username, setting_password, setting_dynamic_urls, setting_debug
    




def main():
    do_debug( 1, "args:", sys.argv )
    
    ## init vars from args ..
    addon_handle = int( sys.argv[ 1 ] )
    args = urlparse.parse_qs( sys.argv[ 2 ][ 1: ] )
    arg_action = args.get( 'action', [ None ] )[ 0 ]
    arg_show = args.get( 'show', [ None ] )[ 0 ]
    arg_season = args.get( 'season', [ None ] )[ 0 ]
    arg_episode = args.get( 'episode', [ None ] )[ 0 ]
    
    
    ## Headless:
    if arg_action == "cron_shows": # update subscribed shows (cache any new episodes)
        cron_shows()
        return
    
    
    ## require settings ..
    settings = False
    while not settings:
        settings = get_settings()
        if not settings:
            do_debug( 1, "not settings:", settings )
    
    do_debug( 1, "settings:", settings )
    
    
    
    ## FIXME BEGIN HERE  TEST (and prompt for changing?) settings !!!

    data = fetch_url_with_auth( "http://xbmc.%s/sources/tv-show.json" % \
                                xbmcaddon.Addon( "plugin.video.tvatom_tv_subscriber" ).getSetting( "server" ),
                                warn_errors = True )
    do_debug( 1, "auth check:", data )
    
    
    
    if not arg_action:  # no action specified, this is initial cache of all shows
        cache_nfo_for_all_shows()
        return
    
    elif arg_action == "subscribe" and arg_show:
        subscribe_show( arg_show )
        return
    
    elif arg_action == "unsubscribe" and arg_show:
        unsubscribe_show( arg_show )
        return
    
    elif arg_action == "play" and arg_show and arg_season and arg_episode:
        play_episode( arg_show, arg_season, arg_episode )
        return
    
    elif arg_action == "update":
        do_debug( 1, "UpdateLibrary(video)" )
        xbmc.executebuiltin( "UpdateLibrary(video)" )
        return
    
    elif arg_action == "clean":
        xbmc.executebuiltin( "CleanLibrary(video)" )
        return
    
    


if __name__ == "__main__":
    main()

