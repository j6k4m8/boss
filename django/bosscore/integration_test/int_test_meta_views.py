
from rest_framework.test import APITestCase
from ..models import *
from .setup_db import setupTestDB
import bossutils
import boto3
from bossutils.aws import *


from django.conf import settings
version  = settings.BOSS_VERSION

# Get the table name from boss.config
config = bossutils.configuration.BossConfig()
testtablename = config["aws"]["test-meta-db"]
aws_mngr = get_aws_manager()


class BossCoreMetaServiceViewTests(APITestCase):
    """
    Class to tests the bosscore views for the metadata service
    """
    @classmethod
    def setUpClass(cls):
        cls.__session = aws_mngr.get_session()

        # Get table
        dynamodb = cls.__session.resource('dynamodb')
        cls.table = dynamodb.create_table(
            TableName=testtablename,
            KeySchema=[
                {
                    'AttributeName': 'metakey',
                    'KeyType': 'HASH'  # Partition key
                },

            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'metakey',
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        cls.table.meta.client.get_waiter('table_exists').wait(TableName=testtablename)




    
    def setUp(self):
        """
        Initialize the  database with a some objects to test
        :return:
        """
        setupTestDB.insert_test_data()

    def test_meta_data_service_collection(self):
        """
        Test to make sure the meta URL for get, post, delete and update with all\
        datamodel params resolves to the meta view
        :return:
        """
        baseurl = '/' + version + '/meta/col1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metadata object for the collection
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    def test_meta_service_experiment(self):
        """
        Test to make sure the meta URL for get, post, delete and update with an experiment
        :return:
        """
        baseurl = '/' + version + '/meta/col1/exp1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metedata object for the collection
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    def test_meta_service_channel(self):
        """
        Test to make sure the meta URL for get, post, delete and update with a channel
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/channel1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metedata object for the collection
        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    def test_meta_service_layer(self):
        """
        Test to make sure the meta URL for get, post, delete and update with a channel
        :return:
        """

        baseurl = '/' + version + '/meta/col1/exp1/layer1/'
        argspost = '?key=testmkey&value=TestString'
        argsget = '?key=testmkey'

        # Post a new metedata object for the collection

        response = self.client.post(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Update the metadata
        argspost = '?key=testmkey&value=TestStringModified'
        response = self.client.put(baseurl + argspost)
        self.assertEqual(response.status_code, 201)

        # Get the metadata
        response = self.client.get(baseurl + argsget)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['key'], 'testmkey')
        self.assertEqual(response.data['value'], 'TestStringModified')

        # delete the metadata
        response = self.client.delete(baseurl + argsget)
        self.assertEqual(response.status_code, 201)

    @classmethod
    def tearDownClass(cls):
        cls.table.delete()
        cls.table.meta.client.get_waiter('table_not_exists').wait(TableName=testtablename)