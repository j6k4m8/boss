# Copyright 2019 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf import settings

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework.test import force_authenticate
from rest_framework import status
import numpy as np

from bossspatialdb.views import CutoutToBlack, Cutout

from bosscore.test.setup_db import DjangoSetupLayer

import redis
import blosc


version = settings.BOSS_VERSION


class CutoutToBlackView8BitTests(APITestCase):
    layer = DjangoSetupLayer

    def test_uint8_cutout_to_black(self):
        """Cutout_to_black integration test with uint8 data"""
        test_mat = np.random.randint(1, 254, (16, 128, 128))
        test_mat = test_mat.astype(np.uint8)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=8)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        factory = APIRequestFactory()
        request = factory.put('/' + version + '/cutout/to_black/col1/exp1/channel1/0/0:64/0:64/0:16/',
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Delete a portion of Data
        response = CutoutToBlack.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:64', y_range='0:64', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Create Request to get original posted data
        request = factory.get('/' + version + '/cutout/col1/exp1/channel1/0/0:128/0:128/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint8)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        test_mat[:,0:64, 0:64] = np.zeros((16,64,64), dtype=np.uint8)
        np.testing.assert_array_equal(data_mat, test_mat)


    def setUp(self):
        """ Copy params from the Layer setUpClass
        """
        # Setup config
        self.kvio_config = self.layer.kvio_config
        self.state_config = self.layer.state_config
        self.object_store_config = self.layer.object_store_config
        self.user = self.layer.user

        # Log Django User in
        self.client.force_login(self.user)

        # Flush cache between tests
        client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
        client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()

        self.dbsetup = self.layer.django_setup_helper

    def tearDown(self):
        # Flush cache between tests
        client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
        client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()

        self.layer.clear_flush_queue()


class CutoutToBlackView16BitTests(APITestCase):
    layer = DjangoSetupLayer

    def test_uint16_cutout_to_black(self):
        """Cutout_to_black integration test with uint16 data"""
        test_mat = np.random.randint(1, 254, (16, 128, 128))
        test_mat = test_mat.astype(np.uint16)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=16)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/channel2/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        factory = APIRequestFactory()
        request = factory.put('/' + version + '/cutout/to_black/col1/exp1/channel2/0/0:64/0:64/0:16/',
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Delete a portion of Data
        response = CutoutToBlack.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:64', y_range='0:64', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Create Request to get original posted data
        request = factory.get('/' + version + '/cutout/col1/exp1/channel2/0/0:128/0:128/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='channel2',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint16)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        test_mat[:,0:64, 0:64] = np.zeros((16,64,64), dtype=np.uint16)
        np.testing.assert_array_equal(data_mat, test_mat)


    def setUp(self):
        """ Copy params from the Layer setUpClass
        """
        # Setup config
        self.kvio_config = self.layer.kvio_config
        self.state_config = self.layer.state_config
        self.object_store_config = self.layer.object_store_config
        self.user = self.layer.user

        # Log Django User in
        self.client.force_login(self.user)

        # Flush cache between tests
        client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
        client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()

        self.dbsetup = self.layer.django_setup_helper

    def tearDown(self):
        # Flush cache between tests
        client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
        client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()

        self.layer.clear_flush_queue()


class CutoutToBlackView64BitTests(APITestCase):
    layer = DjangoSetupLayer

    def test_uint64_cutout_to_black(self):
        """Cutout_to_black integration test with uint64 data"""
        test_mat = np.random.randint(1, 254, (16, 128, 128))
        test_mat = test_mat.astype(np.uint64)
        h = test_mat.tobytes()
        bb = blosc.compress(h, typesize=64)

        # Create request
        factory = APIRequestFactory()
        request = factory.post('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:16/', bb,
                               content_type='application/blosc')
        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        factory = APIRequestFactory()
        request = factory.put('/' + version + '/cutout/to_black/col1/exp1/layer1/0/0:64/0:64/0:16/',
                               content_type='application/blosc-python')
        # log in user
        force_authenticate(request, user=self.user)

        # Delete a portion of Data
        response = CutoutToBlack.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:64', y_range='0:64', z_range='0:16', t_range=None)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Create Request to get original posted data
        request = factory.get('/' + version + '/cutout/col1/exp1/layer1/0/0:128/0:128/0:16/',
                              accepts='application/blosc')

        # log in user
        force_authenticate(request, user=self.user)

        # Make request
        response = Cutout.as_view()(request, collection='col1', experiment='exp1', channel='layer1',
                                    resolution='0', x_range='0:128', y_range='0:128', z_range='0:16', t_range=None).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Decompress
        raw_data = blosc.decompress(response.content)
        data_mat = np.fromstring(raw_data, dtype=np.uint64)
        data_mat = np.reshape(data_mat, (16, 128, 128), order='C')

        # Test for data equality (what you put in is what you got back!)
        test_mat[:,0:64, 0:64] = np.zeros((16,64,64), dtype=np.uint64)
        np.testing.assert_array_equal(data_mat, test_mat)


    def setUp(self):
        """ Copy params from the Layer setUpClass
        """
        # Setup config
        self.kvio_config = self.layer.kvio_config
        self.state_config = self.layer.state_config
        self.object_store_config = self.layer.object_store_config
        self.user = self.layer.user

        # Log Django User in
        self.client.force_login(self.user)

        # Flush cache between tests
        client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
        client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()

        self.dbsetup = self.layer.django_setup_helper

    def tearDown(self):
        # Flush cache between tests
        client = redis.StrictRedis(host=self.kvio_config['cache_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()
        client = redis.StrictRedis(host=self.state_config['cache_state_host'],
                                   port=6379, db=1, decode_responses=False)
        client.flushdb()

        self.layer.clear_flush_queue()

