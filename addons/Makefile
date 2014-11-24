


addons.xml.md5: addons.xml plugin.video.tvatom_tv_subscriber/addon.xml.md5 plugin.video.tvatom_tv_archive/addon.xml.md5 plugin.video.tvatom_movie_subscriber/addon.xml.md5 plugin.video.tvatom_movie_archive/addon.xml.md5
	./addons_xml_generator.py


plugin.video.tvatom_tv_subscriber/addon.xml.md5: plugin.video.tvatom_tv_subscriber/addon.xml plugin.video.tvatom_tv_subscriber/default.py plugin.video.tvatom_tv_subscriber/resources/settings.xml
	openssl md5 plugin.video.tvatom_tv_subscriber/addon.xml |cut -d ' ' -f2 > plugin.video.tvatom_tv_subscriber/addon.xml.md5
	git add plugin.video.tvatom_tv_subscriber/addon.xml plugin.video.tvatom_tv_subscriber/addon.xml.md5
	./addons_xml_generator.py
	mkdir -p ../zip/plugin.video.tvatom_tv_subscriber/ 2>/dev/null
	zip -r ../zip/plugin.video.tvatom_tv_subscriber/plugin.video.tvatom_tv_subscriber-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_tv_subscriber/addon.xml`.zip plugin.video.tvatom_tv_subscriber
	git add ../zip/plugin.video.tvatom_tv_subscriber/plugin.video.tvatom_tv_subscriber-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_tv_subscriber/addon.xml`.zip
	git commit -a --allow-empty-message -m "plugin.video.tvatom_tv_subscriber-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_tv_subscriber/addon.xml`"


plugin.video.tvatom_tv_archive/addon.xml.md5: plugin.video.tvatom_tv_archive/addon.xml plugin.video.tvatom_tv_archive/default.py plugin.video.tvatom_tv_archive/resources/settings.xml
	openssl md5 plugin.video.tvatom_tv_archive/addon.xml |cut -d ' ' -f2 > plugin.video.tvatom_tv_archive/addon.xml.md5
	git add plugin.video.tvatom_tv_archive/addon.xml plugin.video.tvatom_tv_archive/addon.xml.md5
	./addons_xml_generator.py
	mkdir -p ../zip/plugin.video.tvatom_tv_archive/ 2>/dev/null
	zip -r ../zip/plugin.video.tvatom_tv_archive/plugin.video.tvatom_tv_archive-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_tv_archive/addon.xml`.zip plugin.video.tvatom_tv_archive
	git add ../zip/plugin.video.tvatom_tv_archive/plugin.video.tvatom_tv_archive-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_tv_archive/addon.xml`.zip
	git commit -a --allow-empty-message -m "plugin.video.tvatom_tv_archive-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_tv_archive/addon.xml`"

#

plugin.video.tvatom_movie_subscriber/addon.xml.md5: plugin.video.tvatom_movie_subscriber/addon.xml plugin.video.tvatom_movie_subscriber/default.py plugin.video.tvatom_movie_subscriber/resources/settings.xml
	openssl md5 plugin.video.tvatom_movie_subscriber/addon.xml |cut -d ' ' -f2 > plugin.video.tvatom_movie_subscriber/addon.xml.md5
	git add plugin.video.tvatom_movie_subscriber/addon.xml plugin.video.tvatom_movie_subscriber/addon.xml.md5
	./addons_xml_generator.py
	mkdir -p ../zip/plugin.video.tvatom_movie_subscriber/ 2>/dev/null
	zip -r ../zip/plugin.video.tvatom_movie_subscriber/plugin.video.tvatom_movie_subscriber-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_movie_subscriber/addon.xml`.zip plugin.video.tvatom_movie_subscriber
	git add ../zip/plugin.video.tvatom_movie_subscriber/plugin.video.tvatom_movie_subscriber-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_movie_subscriber/addon.xml`.zip
	git commit -a --allow-empty-message -m "plugin.video.tvatom_movie_subscriber-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_movie_subscriber/addon.xml`"


plugin.video.tvatom_movie_archive/addon.xml.md5: plugin.video.tvatom_movie_archive/addon.xml plugin.video.tvatom_movie_archive/default.py plugin.video.tvatom_movie_archive/resources/settings.xml
	openssl md5 plugin.video.tvatom_movie_archive/addon.xml |cut -d ' ' -f2 > plugin.video.tvatom_movie_archive/addon.xml.md5
	git add plugin.video.tvatom_movie_archive/addon.xml plugin.video.tvatom_movie_archive/addon.xml.md5
	./addons_xml_generator.py
	mkdir -p ../zip/plugin.video.tvatom_movie_archive/ 2>/dev/null
	zip -r ../zip/plugin.video.tvatom_movie_archive/plugin.video.tvatom_movie_archive-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_movie_archive/addon.xml`.zip plugin.video.tvatom_movie_archive
	git add ../zip/plugin.video.tvatom_movie_archive/plugin.video.tvatom_movie_archive-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_movie_archive/addon.xml`.zip
	git commit -a --allow-empty-message -m "plugin.video.tvatom_movie_archive-`awk -F'"' '/addon id/{print $$6}' plugin.video.tvatom_movie_archive/addon.xml`"
