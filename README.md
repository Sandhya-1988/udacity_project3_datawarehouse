# Purpose of the database for sparkify in respect to their analytical goals
Since the 1st project,the size of the database of Sparkify has grown and they wish to move it to the cloud. Their data resides in S3 bucket. So, we need to create an ETL pipeline for it. After this the data can be used for analytics to find out what songs are users listening to. We can test the database by running multiple analytical queries.

# DB Schema design and ETL Pipeline
Our entire DB Schema design & ETL pipeline consists of following steps:
1. Creating an ETL pipeline which will involve the following:
   - Extracting the data from S3 buckets.
   - Loading the data from S3 bucket into staging tables.
   - Inserting the data into fact and dimension tables, after step2.

2. To access data from S3 bucket we need to create clients for EC2,IAM,S3 and RedShift. Configuration data to create redshift      
   cluster can be ffetched from dwh.cfg(configuration file).This is how data is contained in S3 buckets
   - Song data: s3://udacity-dend/song_data
   - Log data: s3://udacity-dend/log_data
   - s3://udacity-dend/log_json_path.json
  
3. Staging tables:
   - Staging_events- it contains data activity logs from an imaginary music app.
   - Staging_songs - contains metadata about a song and its artist.

4. Fact and Dimension tables:
   - Songplays - Its the fact table with references from other tables and other data.
   - Artists - This table contains the artists data like name,location,latitude and longitude.
   - Users - This table contains user data like first name,last name , gender and level.
   - Songs - This table contains song data like title,year, duration,etc.
   - Time - This table contains the time related data.

# Example queries and their results  

1. SELECT * FROM staging_events
!(IMAGE OF RESULTS OF STAGING EVENTS)
(https://sandhyapractice.s3-us-west-2.amazonaws.com/Screen+Shot+2019-06-20+at+11.10.53+PM.png)

2. SELECT * FROM songplays
!(IMAGE OF RESULTS OF SONGPLAYS)
(https://sandhyapractice.s3-us-west-2.amazonaws.com/Screen+Shot+2019-06-20+at+11.11.36+PM.png)

3. SELECT * FROM users
!(IMAGE OF RESULTS OF USERS)
(https://sandhyapractice.s3-us-west-2.amazonaws.com/Screen+Shot+2019-06-20+at+11.12.15+PM.png)


**Important note:
 For testing purpose, I have set the value of "delCluster = False" in etl.py. This will not delete the cluster. In case cluster needs to be deleted, change the initial value i.e; delCluster = True. This will enable the code at line no.37(etl.py) to execute, thereby deleting cluster.
