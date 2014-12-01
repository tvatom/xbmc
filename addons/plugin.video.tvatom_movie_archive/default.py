#!/usr/bin/python

## tkooda : 2014-09-06 : xbmc video add-on
## tkooda : 2014-11-28 : plugin.video.tvatom_movie_archive


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


def fetch_url_with_auth( url ):
    request = urllib2.Request( url )
    
    password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_manager.add_password( None, url,
                                   xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).getSetting( "username" ),
                                   xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).getSetting( "password" ) )
    
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


def get_settings():
    setting_server = xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).getSetting( "server" )
    setting_username = xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).getSetting( "username" )
    setting_password = xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).getSetting( "password" )
    
    if not setting_server:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter server name:", "tvatom.com" )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).setSetting( "server", s )
            setting_server = s
        else:
            return False
    
    if not setting_username:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter username:" )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).setSetting( "username", s )
            setting_username = s
        else:
            return False
    
    if not setting_password:
        dialog = xbmcgui.Dialog()
        s = dialog.input( "Enter password:", type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT )
        if s:
            xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).setSetting( "password", s )
            setting_password = s
        else:
            return False
    
    do_debug( 1, "settings:", setting_server, setting_username, setting_password )
    return setting_server, setting_username, setting_password



def main():
    do_debug( 1, "args:", sys.argv )
    
    ## init vars from args ..
    base_url = sys.argv[ 0 ]
    addon_handle = int( sys.argv[ 1 ] )
    
    ## set content type ..
    xbmcplugin.setContent( addon_handle, 'movies' )
    
    
    ## require (prompt for any missing) settings ..
    settings = False
    while not settings:
        settings = get_settings()
        if not settings:
            do_debug( 1, "not settings:", settings )
    
    setting_username = xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).getSetting( "username" )
    setting_password = xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).getSetting( "password" )
    setting_server = xbmcaddon.Addon( "plugin.video.tvatom_movie_archive" ).getSetting( "server" )
    
    if True:
        url_index = "http://feed1.%s/index/movie.json" % setting_server
        movie_list = fetch_object_from_json_url_with_auth( url_index, sortkey = "name" )
        
        for movie in movie_list:
#        for movie in movie_list[ 10 : 20 ]:  ## DEBUG
            appurl_movie = build_appurl( { "movie": movie.get( "name" ) } )
            
            movie_name = movie.get( "name" )
            movie_files = movie.get( "files" )
            movie_code = movie.get( "code" )
            
            if not movie_name:
                print "WARNING: MISSING: movie_name"
                continue
            
            if not movie_files:
                print "WARNING: MISSING: movie_files"
                continue
            
            append_multipart = ""
            append_num = 1
            for movie_file in movie_files:
                if len( movie_files ) > 1:
                    append_multipart = "  (part %d of %d)" % ( append_num, len( movie_files ) )
                
                list_item = xbmcgui.ListItem( movie_name + append_multipart,
                                              iconImage = "DefaultVideo.png" )
                
                list_item.setInfo( "video", movie )
                
                url_movie = os.path.join( "http://%s:%s@data1.%s/movie/" \
                                              % ( setting_username, setting_password, setting_server ),
                                          movie_file ) #+ "|auth=any"
                
                xbmcplugin.addDirectoryItem( handle = addon_handle,
                                             url = url_movie,
                                             listitem = list_item,
                                             totalItems = len( movie_list ) )
                
                append_num += 1
        
        
        xbmcplugin.endOfDirectory( addon_handle )
        
        return # done building movie index


if __name__ == "__main__":
    main()

