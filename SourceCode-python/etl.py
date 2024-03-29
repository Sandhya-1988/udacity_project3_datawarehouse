import configparser
import psycopg2
import boto3
from sql_queries import copy_table_queries, insert_table_queries
from create_tables import redshift

delCluster = False

# Insert data from S3 bucket into redshift
def load_staging_tables(cur, conn):
    try:
        for query in copy_table_queries:
            cur.execute(query)
            conn.commit()
    except Exception as e:
        print(e)

# Insert data into analytical tables from staging tables
def insert_tables(cur, conn):
    try:
        for query in insert_table_queries:
            cur.execute(query)
            conn.commit()
    except Exception as e:
        print(e)
        
def main():
    config = configparser.ConfigParser()
    config.read('dwh.cfg')

    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
    cur = conn.cursor()
    
    load_staging_tables(cur, conn)
    insert_tables(cur, conn)
    
    if(delCluster):
        response = redshift.delete_cluster(
        ClusterIdentifier=config.get("DWH","DWH_CLUSTER_IDENTIFIER"),
        SkipFinalClusterSnapshot=True
        )

    conn.close()

if __name__ == "__main__":
    main()