import configparser
import psycopg2
import pandas as pd
import json
import time
import boto3
from sql_queries import create_table_queries, drop_table_queries

# INSERT YOUR KEY AND SECRET ACCESS HERE GLOBALLY
    
#create_clients for ec2,s3,iam and redshift   
ec2 = boto3.resource('ec2',
                  region_name = "us-west-2",
                  aws_access_key_id = KEY,
                  aws_secret_access_key = SECRET)

s3 = boto3.resource('s3',
                  region_name = "us-west-2",
                  aws_access_key_id = KEY,
                  aws_secret_access_key = SECRET)

iam = boto3.client('iam',
                  region_name = "us-west-2",
                  aws_access_key_id = KEY,
                  aws_secret_access_key = SECRET)

redshift = boto3.client('redshift',
                     region_name = "us-west-2",
                     aws_access_key_id = KEY,
                     aws_secret_access_key = SECRET)

def launch_redshift_cluster(config):
# load datawarehouse parameters from dwh.cfg file
    DWH_CLUSTER_TYPE       = config.get("DWH","DWH_CLUSTER_TYPE")
    DWH_NUM_NODES          = config.get("DWH","DWH_NUM_NODES")
    DWH_NODE_TYPE          = config.get("DWH","DWH_NODE_TYPE")

    DWH_CLUSTER_IDENTIFIER = config.get("DWH","DWH_CLUSTER_IDENTIFIER")
    DWH_DB                 = config.get("CLUSTER","DB_NAME")
    DWH_DB_USER            = config.get("CLUSTER","DB_USER")
    DWH_DB_PASSWORD        = config.get("CLUSTER","DB_PASSWORD")
    DWH_PORT               = config.get("CLUSTER","DB_PORT")

    DWH_IAM_ROLE_NAME      = config.get("DWH", "DWH_IAM_ROLE_NAME")

    (DWH_DB_USER, DWH_DB_PASSWORD, DWH_DB)

    pd.DataFrame({"Param":
                  ["DWH_CLUSTER_TYPE", "DWH_NUM_NODES", "DWH_NODE_TYPE", "DWH_CLUSTER_IDENTIFIER", "DWH_DB", "DWH_DB_USER",                            "DWH_DB_PASSWORD","DWH_PORT", "DWH_IAM_ROLE_NAME"],"Value":[DWH_CLUSTER_TYPE, DWH_NUM_NODES, DWH_NODE_TYPE,                         DWH_CLUSTER_IDENTIFIER, DWH_DB,DWH_DB_USER, DWH_DB_PASSWORD, DWH_PORT, DWH_IAM_ROLE_NAME]})
    

#create iam role with S3 read only access
    try:
        print('1.1 Creating a new IAM Role')
        dwhRole = iam.create_role(
        Path = '/',
        RoleName = DWH_IAM_ROLE_NAME,
        Description = "Allows Redshift clusters to call AWS services on your behalf.",
        AssumeRolePolicyDocument = json.dumps(
            {'Statement':[{'Action' :'sts:AssumeRole',
               'Effect': 'Allow',
               'Principal':{'Service':'redshift.amazonaws.com'}}],
             'Version': '2012-10-17'})    
       )
    
    except Exception as e:
        print(e)
    
    print('1.2 Attaching Policy')

    iam.attach_role_policy(RoleName = DWH_IAM_ROLE_NAME,
                      PolicyArn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
                      )['ResponseMetadata']['HTTPStatusCode']
    
    print('1.3 Get the IAM role ARN')
    roleArn = iam.get_role(RoleName = DWH_IAM_ROLE_NAME)['Role']['Arn']

    print(roleArn)    

#create a redshift cluster to which database will be connected
    try:
        response = redshift.create_cluster(        
        # parameters for hardware
           ClusterType = DWH_CLUSTER_TYPE,
           NodeType = DWH_NODE_TYPE,
           NumberOfNodes = int(DWH_NUM_NODES),

        # parameters for identifiers & credentials
           DBName = DWH_DB,
           ClusterIdentifier = DWH_CLUSTER_IDENTIFIER,
           MasterUsername = DWH_DB_USER,
           MasterUserPassword = DWH_DB_PASSWORD,
        
        # parameter for role (to allow s3 access)
           IamRoles = [roleArn] 
    )
    except Exception as e:
        print(e)
        
    resp = response['Cluster']['ClusterStatus']

# Wait until the status of the cluster becomes available, then only proceed to the next step
    while(resp =='creating'):
        myClusterProps = redshift.describe_clusters(ClusterIdentifier=DWH_CLUSTER_IDENTIFIER)['Clusters'][0]
        if(myClusterProps['ClusterStatus'] == 'available'):
            break
        else:
            time.sleep(2)    
        
# describe the cluster to see its status
    def prettyRedshiftProps(props):
        pd.set_option('display.max_colwidth', -1)
        keysToShow = ["ClusterIdentifier", "NodeType", "ClusterStatus", "MasterUsername", "DBName", "Endpoint",
                      "NumberOfNodes", 'VpcId']
        x = [(k, v) for k, v in props.items() if k in keysToShow]
        return pd.DataFrame(data=x, columns=["Key", "Value"])

    myClusterProps = redshift.describe_clusters(ClusterIdentifier=DWH_CLUSTER_IDENTIFIER)['Clusters'][0]
    prettyRedshiftProps(myClusterProps)        
        
        
#openTCPPort
    try:
        vpc = ec2.Vpc(id=myClusterProps['VpcId'])
        defaultSg = list(vpc.security_groups.all())[0]
        print(defaultSg)
    
        defaultSg.authorize_ingress(
           GroupName= defaultSg.group_name,  
           CidrIp='0.0.0.0/0', 
           IpProtocol='TCP', 
           FromPort=int(DWH_PORT),
           ToPort=int(DWH_PORT)
        )
    except Exception as e:
        print(e)
        
    DWH_ENDPOINT = myClusterProps['Endpoint']['Address']
    DWH_ROLE_ARN = myClusterProps['IamRoles'][0]['IamRoleArn']
  #  print("DWH_ENDPOINT :: ", endpoint)
    print("DWH_ROLE_ARN :: ", roleArn)    
        
#connect_cluster with required parameters
    conn_string="postgresql://{}:{}@{}:{}/{}".format(DWH_DB_USER, DWH_DB_PASSWORD, DWH_ENDPOINT, DWH_PORT,DWH_DB)
    print(conn_string)
    #%sql $conn_string
    
def drop_tables(cur, conn):
    for query in drop_table_queries:
        cur.execute(query)
        conn.commit()


def create_tables(cur, conn):
    for query in create_table_queries:
        cur.execute(query)
        conn.commit()


def main():
    config = configparser.ConfigParser()
    config.read('dwh.cfg')
    
    # launching a redshift cluster and creating iam role with access to S3
    launch_redshift_cluster(config)
    
    conn = psycopg2.connect("host={} dbname={} user={} password={} port={}".format(*config['CLUSTER'].values()))
    cur = conn.cursor()

    drop_tables(cur, conn)
    create_tables(cur, conn)

    conn.close()


if __name__ == "__main__":
    main()