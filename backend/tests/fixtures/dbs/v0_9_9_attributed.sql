BEGIN TRANSACTION;
CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
INSERT INTO "alembic_version" VALUES('a1b2c3d4e5f6');
CREATE TABLE "connection" (
	name VARCHAR NOT NULL, 
	arr_type VARCHAR(6) NOT NULL, 
	url VARCHAR NOT NULL, 
	api_key VARCHAR NOT NULL, 
	monitor VARCHAR(15) NOT NULL, 
	id INTEGER NOT NULL, 
	added_at DATETIME NOT NULL, 
	external_url VARCHAR NOT NULL, machine_identifier VARCHAR, 
	CONSTRAINT connection_pkc PRIMARY KEY (id)
);
INSERT INTO "connection" VALUES('Fixture Radarr','RADARR','http://localhost:7878','k','MONITOR_MISSING',1,'2026-01-01 00:00:00','',NULL);
CREATE TABLE customfilter (
	filter_name VARCHAR NOT NULL, 
	filter_type VARCHAR(7) NOT NULL, 
	id INTEGER NOT NULL, 
	CONSTRAINT customfilter_pkc PRIMARY KEY (id)
);
INSERT INTO "customfilter" VALUES('Movie Trailers','TRAILER',1);
INSERT INTO "customfilter" VALUES('Series Trailers','TRAILER',2);
CREATE TABLE download (
	path VARCHAR NOT NULL, 
	file_name VARCHAR NOT NULL, 
	file_hash VARCHAR NOT NULL, 
	size INTEGER NOT NULL, 
	resolution INTEGER NOT NULL, 
	file_format VARCHAR NOT NULL, 
	video_format VARCHAR NOT NULL, 
	audio_format VARCHAR NOT NULL, 
	audio_language VARCHAR, 
	subtitle_format VARCHAR, 
	subtitle_language VARCHAR, 
	duration INTEGER NOT NULL, 
	youtube_id VARCHAR NOT NULL, 
	youtube_channel VARCHAR NOT NULL, 
	file_exists BOOLEAN NOT NULL, 
	profile_id INTEGER NOT NULL, 
	added_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	id INTEGER NOT NULL, 
	media_id INTEGER NOT NULL, 
	CONSTRAINT download_pkc PRIMARY KEY (id), 
	CONSTRAINT fk_download_media_id_media FOREIGN KEY(media_id) REFERENCES media (id) ON DELETE CASCADE
);
INSERT INTO "download" VALUES('/nonexistent/fixture/m1-trailer.mkv','m1-trailer.mkv','h1',1000,1080,'mkv','vp9','opus',NULL,NULL,NULL,120,'ytid','chan',1,1,'2026-01-01 00:00:00','2026-01-01 00:00:00',1,1);
INSERT INTO "download" VALUES('/nonexistent/fixture/m2-trailer.mkv','m2-trailer.mkv','h2',1000,1080,'mkv','vp9','opus',NULL,NULL,NULL,120,'ytid','chan',1,1,'2026-01-01 00:00:00','2026-01-01 00:00:00',2,2);
CREATE TABLE "event" (
	event_type VARCHAR(19) NOT NULL, 
	source VARCHAR(6) DEFAULT 'USER' NOT NULL, 
	source_detail VARCHAR DEFAULT ('') NOT NULL, 
	old_value VARCHAR, 
	new_value VARCHAR, 
	id INTEGER NOT NULL, 
	media_id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	CONSTRAINT event_pkc PRIMARY KEY (id), 
	CONSTRAINT fk_event_media_id_media FOREIGN KEY(media_id) REFERENCES media (id) ON DELETE CASCADE
);
CREATE TABLE filefolderinfo (
	type VARCHAR(7) NOT NULL, 
	name VARCHAR NOT NULL, 
	size INTEGER NOT NULL, 
	path VARCHAR NOT NULL, 
	is_trailer BOOLEAN NOT NULL, 
	modified DATETIME NOT NULL, 
	id INTEGER NOT NULL, 
	media_id INTEGER NOT NULL, 
	parent_id INTEGER, 
	CONSTRAINT filefolderinfo_pkc PRIMARY KEY (id), 
	CONSTRAINT fk_filefolderinfo_media_id_media FOREIGN KEY(media_id) REFERENCES media (id) ON DELETE CASCADE, 
	CONSTRAINT fk_filefolderinfo_parent_id_filefolderinfo FOREIGN KEY(parent_id) REFERENCES filefolderinfo (id)
);
CREATE TABLE "filter" (
	filter_by VARCHAR NOT NULL, 
	filter_condition VARCHAR(18) NOT NULL, 
	filter_value VARCHAR NOT NULL, 
	id INTEGER NOT NULL, 
	customfilter_id INTEGER, 
	CONSTRAINT filter_pkc PRIMARY KEY (id), 
	CONSTRAINT fk_filter_customfilter_id_customfilter FOREIGN KEY(customfilter_id) REFERENCES customfilter (id) ON DELETE CASCADE
);
INSERT INTO "filter" VALUES('trailer_exists','EQUALS','false',1,1);
INSERT INTO "filter" VALUES('is_movie','EQUALS','true',2,1);
INSERT INTO "filter" VALUES('trailer_exists','EQUALS','false',3,2);
INSERT INTO "filter" VALUES('is_movie','EQUALS','false',4,2);
CREATE TABLE "media" (
	connection_id INTEGER NOT NULL, 
	arr_id INTEGER NOT NULL, 
	is_movie BOOLEAN NOT NULL, 
	title VARCHAR NOT NULL, 
	year INTEGER NOT NULL, 
	language VARCHAR NOT NULL, 
	overview VARCHAR, 
	runtime INTEGER NOT NULL, 
	youtube_trailer_id VARCHAR, 
	folder_path VARCHAR, 
	imdb_id VARCHAR, 
	txdb_id VARCHAR NOT NULL, 
	poster_url VARCHAR, 
	fanart_url VARCHAR, 
	poster_path VARCHAR, 
	fanart_path VARCHAR, 
	trailer_exists BOOLEAN NOT NULL, 
	monitor BOOLEAN NOT NULL, 
	arr_monitored BOOLEAN NOT NULL, 
	id INTEGER NOT NULL, 
	added_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	downloaded_at DATETIME, 
	status VARCHAR(11) DEFAULT 'MISSING' NOT NULL, 
	clean_title VARCHAR DEFAULT ('') NOT NULL, 
	studio VARCHAR DEFAULT ('') NOT NULL, 
	media_exists BOOLEAN DEFAULT 0 NOT NULL, 
	media_filename VARCHAR DEFAULT ('') NOT NULL, 
	title_slug VARCHAR DEFAULT ('') NOT NULL, 
	season_count INTEGER DEFAULT '0' NOT NULL, 
	plex_rating_key VARCHAR, 
	plex_section_key VARCHAR, 
	plex_connection_id INTEGER, 
	plex_trailer BOOLEAN, tmdb_id INTEGER, tvdb_id INTEGER, 
	CONSTRAINT media_pkc PRIMARY KEY (id), 
	CONSTRAINT fk_media_connection_id_connection FOREIGN KEY(connection_id) REFERENCES connection (id) ON DELETE CASCADE, 
	CONSTRAINT fk_media_plex_connection_id_connection FOREIGN KEY(plex_connection_id) REFERENCES connection (id) ON DELETE SET NULL
);
INSERT INTO "media" VALUES(1,1,1,'Fixture Movie A',2024,'en',NULL,100,NULL,'/nonexistent/fixture/Fixture Movie A',NULL,'fx-1',NULL,NULL,NULL,NULL,1,0,1,1,'2026-01-01 00:00:00','2026-01-01 00:00:00',NULL,'MISSING','fixture movie a','',0,'','fx-1',0,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "media" VALUES(1,2,1,'Fixture Movie B',2024,'en',NULL,100,NULL,'/nonexistent/fixture/Fixture Movie B',NULL,'fx-2',NULL,NULL,NULL,NULL,1,1,1,2,'2026-01-01 00:00:00','2026-01-01 00:00:00',NULL,'MISSING','fixture movie b','',0,'','fx-2',0,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "media" VALUES(1,3,1,'Fixture Movie C',2024,'en',NULL,100,NULL,'/nonexistent/fixture/Fixture Movie C',NULL,'fx-3',NULL,NULL,NULL,NULL,0,1,1,3,'2026-01-01 00:00:00','2026-01-01 00:00:00',NULL,'MISSING','fixture movie c','',0,'','fx-3',0,NULL,NULL,NULL,NULL,NULL,NULL);
CREATE TABLE "pathmapping" (
	id INTEGER NOT NULL, 
	connection_id INTEGER, 
	path_from VARCHAR NOT NULL, 
	path_to VARCHAR NOT NULL, plex_section_key VARCHAR, 
	CONSTRAINT pathmapping_pkc PRIMARY KEY (id), 
	CONSTRAINT fk_pathmapping_connection_id_connection FOREIGN KEY(connection_id) REFERENCES connection (id) ON DELETE CASCADE
);
CREATE TABLE scheduledtaskconfig (
	task_key VARCHAR NOT NULL, 
	task_name VARCHAR NOT NULL, 
	interval_seconds FLOAT NOT NULL, 
	delay_seconds FLOAT NOT NULL, 
	id INTEGER NOT NULL, 
	CONSTRAINT scheduledtaskconfig_pkc PRIMARY KEY (id), 
	CONSTRAINT uq_scheduledtaskconfig_task_key UNIQUE (task_key)
);
INSERT INTO "scheduledtaskconfig" VALUES('api_refresh','Arr Data Refresh',3600.0,30.0,1);
INSERT INTO "scheduledtaskconfig" VALUES('update_check','Docker Update Check',86400.0,240.0,2);
INSERT INTO "scheduledtaskconfig" VALUES('scan_disk','Scan All Media Folders',3600.0,480.0,3);
INSERT INTO "scheduledtaskconfig" VALUES('download_trailers','Download Missing Trailers',3600.0,900.0,4);
INSERT INTO "scheduledtaskconfig" VALUES('image_refresh','Image Refresh',21600.0,720.0,5);
INSERT INTO "scheduledtaskconfig" VALUES('cleanup','Cleanup Task',86400.0,14400.0,6);
CREATE TABLE "trailerprofile" (
	enabled BOOLEAN NOT NULL, 
	file_format VARCHAR NOT NULL, 
	file_name VARCHAR NOT NULL, 
	folder_enabled BOOLEAN NOT NULL, 
	folder_name VARCHAR NOT NULL, 
	audio_format VARCHAR NOT NULL, 
	audio_volume_level INTEGER NOT NULL, 
	video_resolution INTEGER NOT NULL, 
	video_format VARCHAR NOT NULL, 
	subtitles_enabled BOOLEAN NOT NULL, 
	subtitles_format VARCHAR NOT NULL, 
	subtitles_language VARCHAR NOT NULL, 
	embed_metadata BOOLEAN NOT NULL, 
	exclude_words VARCHAR NOT NULL, 
	include_words VARCHAR NOT NULL, 
	min_duration INTEGER NOT NULL, 
	max_duration INTEGER NOT NULL, 
	remove_silence BOOLEAN NOT NULL, 
	search_query VARCHAR NOT NULL, 
	id INTEGER NOT NULL, 
	customfilter_id INTEGER, 
	always_search BOOLEAN DEFAULT '0' NOT NULL, 
	priority INTEGER DEFAULT '0' NOT NULL, 
	ytdlp_extra_options VARCHAR DEFAULT ('') NOT NULL, 
	stop_monitoring BOOLEAN NOT NULL, 
	custom_folder VARCHAR NOT NULL, 
	notify_plex BOOLEAN NOT NULL, retry_count INTEGER DEFAULT '2' NOT NULL, skip_if_plex_trailer BOOLEAN DEFAULT '0' NOT NULL, skip_if_plex_trailer_resolution INTEGER DEFAULT '1080' NOT NULL, uploader_ids VARCHAR DEFAULT '' NOT NULL, 
	CONSTRAINT trailerprofile_pkc PRIMARY KEY (id), 
	CONSTRAINT uq_trailerprofile_customfilter_id UNIQUE (customfilter_id), 
	CONSTRAINT fk_trailerprofile_customfilter_id_customfilter FOREIGN KEY(customfilter_id) REFERENCES customfilter (id) ON DELETE CASCADE
);
INSERT INTO "trailerprofile" VALUES(1,'mkv','{title} ({year})-trailer.{ext}',0,'Trailers','opus',100,1080,'vp9',0,'srt','en',1,'','',30,600,0,'{title} {year} {is_movie} trailer',1,1,0,0,'',1,'{media_folder}',0,2,0,1080,'');
INSERT INTO "trailerprofile" VALUES(1,'mkv','{title} ({year})-trailer.{ext}',1,'Trailers','opus',100,1080,'vp9',0,'srt','en',1,'','',30,600,0,'{title} {year} {is_movie} trailer',2,2,0,0,'',1,'{media_folder}',0,2,0,1080,'');
CREATE INDEX ix_media_clean_title ON media (clean_title);
CREATE INDEX ix_media_imdb_id ON media (imdb_id);
CREATE INDEX ix_media_year ON media (year);
CREATE INDEX ix_media_arr_id ON media (arr_id);
CREATE INDEX ix_media_is_movie ON media (is_movie);
CREATE INDEX ix_media_txdb_id ON media (txdb_id);
CREATE INDEX ix_media_title ON media (title);
CREATE INDEX ix_media_language ON media (language);
CREATE INDEX ix_media_title_slug ON media (title_slug);
CREATE INDEX ix_media_connection_id ON media (connection_id);
CREATE INDEX ix_event_source ON event (source);
CREATE INDEX ix_event_media_id ON event (media_id);
CREATE INDEX ix_event_created_at ON event (created_at);
CREATE INDEX ix_event_source_detail ON event (source_detail);
CREATE INDEX ix_event_event_type ON event (event_type);
CREATE INDEX ix_media_tmdb_id ON media (tmdb_id);
CREATE INDEX ix_media_tvdb_id ON media (tvdb_id);
COMMIT;
