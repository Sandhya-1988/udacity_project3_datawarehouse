import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events;"
staging_songs_table_drop  = "DROP TABLE IF EXISTS staging_songs;"
songplay_table_drop       = "DROP TABLE IF EXISTS songplays;"
user_table_drop           = "DROP TABLE IF EXISTS users;"
song_table_drop           = "DROP TABLE IF EXISTS songs;"
artist_table_drop         = "DROP TABLE IF EXISTS artists;"
time_table_drop           = "DROP TABLE IF EXISTS time;"

# CREATE TABLES

staging_events_table_create= ("""
    CREATE TABLE staging_events(
      id INT IDENTITY(0,1) PRIMARY KEY NOT NULL,
      artist        varchar ,
      auth          varchar,
      firstName     varchar,
      gender        char(1),
      itemInSession varchar,
      lastName      varchar ,
      length        numeric ,
      level         varchar,
      location      varchar,
      method        varchar,
      page          varchar,
      registration  numeric,
      sessionId     integer,
      song          varchar,
      status        integer,
      ts            varchar,
      userAgent     varchar,
      userId        integer );
""")


staging_songs_table_create = ("""
   CREATE TABLE staging_songs(
     num_songs        integer,
     artist_id        varchar,
     artist_latitude  numeric,
     artist_longitude numeric,
     artist_location  varchar,
     artist_name      varchar,
     song_id          varchar,
     title            varchar,
     duration         numeric,
     year             integer);
""")

songplay_table_create = ("""
   CREATE TABLE songplays(
     songplay_id  INT IDENTITY(0,1) PRIMARY KEY  NOT NULL,
     start_time   timestamp NOT NULL,
     user_id      integer   NOT NULL,
     level        varchar,
     song_id      varchar,
     artist_id    varchar,
     session_id   integer,
     location     varchar,
     user_agent   varchar );
""")

user_table_create = ("""
    CREATE TABLE users(
      user_id    varchar PRIMARY KEY  NOT NULL,
      first_name varchar,
      last_name  varchar,
      gender     char(1),
      level      varchar) diststyle all;
""")

song_table_create = ("""
    CREATE TABLE songs(
       song_id   varchar PRIMARY KEY NOT NULL,
       title     varchar,
       artist_id varchar,
       year      integer,
       duration  numeric) diststyle all;
""")

artist_table_create = ("""
   CREATE TABLE artists(
      artist_id        varchar PRIMARY KEY NOT NULL,
      artist_name      varchar,
      artist_location  varchar,
      artist_latitude  numeric,
      artist_longitude numeric) diststyle all;
""")

time_table_create = ("""
   CREATE TABLE time(
      start_time   timestamp PRIMARY KEY NOT NULL,
      hour         integer NOT NULL,
      day          integer NOT NULL,
      week         integer NOT NULL,
      month        integer NOT NULL,
      year         integer NOT NULL,
      weekday      integer NOT NULL);
""")

# STAGING TABLES

staging_events_copy = ("""copy staging_events 
                          from{}
                          credentials 'aws_iam_role={}'     
                          compupdate off region 'us-west-2'
                          JSON {};
""").format(config.get('S3','LOG_DATA'),config.get('IAM_ROLE', 'ARN'),config.get('S3','LOG_JSONPATH'))

staging_songs_copy = ("""copy staging_songs 
                          from {}
                          credentials 'aws_iam_role={}'
                          compupdate off region 'us-west-2'
                          JSON 'auto' truncatecolumns;
""").format(config.get('S3','SONG_DATA'),config.get('IAM_ROLE', 'ARN'))

# FINAL TABLES

songplay_table_insert = ("""INSERT INTO songplays 
                               (start_time,user_id,
                               level,song_id,
                               artist_id,session_id,
                               location,user_agent)
                            
                            SELECT TIMESTAMP 'epoch' + stg_eve.ts/1000 * INTERVAL '1 second' as start_time,
                              stg_eve.userId,
                              stg_eve.level,
                              stg_song.song_id,
                              stg_song.artist_id,
                              CAST(stg_eve.sessionId AS INTEGER),
                              stg_eve.location,
                              stg_eve.userAgent
                              FROM staging_events stg_eve JOIN staging_songs stg_song ON
                              (stg_eve.artist = stg_song.artist_name and
                               stg_eve.song = stg_song.title)
                               WHERE stg_eve.page = 'NextSong'
                               AND stg_eve.artist IS NOT NULL
                               AND stg_eve.song IS NOT NULL;
""")

user_table_insert = (""" INSERT INTO users (
                           user_id, first_name,
                           last_name,gender,level
                           )
                         SELECT DISTINCT 
                           userId,firstName,
                           lastName,gender,
                           level 
                         FROM staging_events
                         WHERE page = 'NextSong';
""")

song_table_insert = (""" INSERT INTO songs (
                          song_id,title,
                          artist_id,year,
                          duration
                          )
                         SELECT DISTINCT 
                          song_id,title,
                          artist_id,
                          duration,year 
                          FROM staging_songs;
""")

artist_table_insert = (""" INSERT INTO artists (
                             artist_id,artist_name,
                             artist_location,
                             artist_latitude,artist_longitude
                             )
                           SELECT DISTINCT 
                             artist_id,artist_name,
                             artist_location,artist_latitude,
                             artist_longitude 
                             FROM staging_songs;
""")

time_table_insert = (""" INSERT INTO time (
                           start_time,hour,
                           day,week,month,
                           year,weekday
                           )
                         SELECT DISTINCT 
                           start_time,
                           EXTRACT(hour from start_time),
                           EXTRACT(day from start_time),
                           EXTRACT(week from start_time),
                           EXTRACT(month from start_time),
                           EXTRACT(year from start_time),
                           EXTRACT(weekday from start_time)
                           FROM songplays;
                           
""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
