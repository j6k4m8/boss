# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
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

import re

from .models import Collection, Experiment, Channel
from .lookup import LookUpKey
from .error import BossHTTPError, BossError, ErrorCodes, BossRestArgsError
from .permissions import BossPermissionManager

META_CONNECTOR = "&"


class BossRequest:
    """
    Validator for all requests that are made to the endpoint.
    """

    def __init__(self, request, bossrequest):
        """
        Parse the request and initialize an instance of BossRequest
        Args:
            request (stream): Django Uwsgi request

        Raises:
            BossError:  If the request is invalid

        """
        self.bossrequest = bossrequest
        # Datamodel objects
        self.collection = None
        self.experiment = None
        self.channel = None

        self.default_time = None
        self.coord_frame = None

        # Endpoint service and version number from the request
        self.service = None
        self.version = None

        # Boss key representing the datamodel for a valid request
        self.base_boss_key = None

        # Meta data key and value
        self.key = None
        self.value = None

        # Cutout args from the request
        self.resolution = None
        self.x_start = 0
        self.y_start = 0
        self.z_start = 0
        self.x_stop = 0
        self.y_stop = 0
        self.z_stop = 0

        # Timesample argument
        self.time_start = 0
        self.time_stop = 0

        # Request variables
        self.user = request.user
        self.method = request.method
        self.version = request.version

        # Validate the request based on the service
        self.service = self.bossrequest['service']

        if self.service == 'meta':
            self.validate_meta_service()

        elif self.service == 'view':
            raise BossError("Views not implemented. Specify the full request", ErrorCodes.FUTURE)

        elif self.service == 'image':
            self.validate_image_service()

        elif self.service == 'tile':
            self.validate_tile_service()

        else:
            self.validate_cutout_service()

    def validate_meta_service(self):
        """
        "Validate all meta data requests.

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

        if 'key' in self.bossrequest:
            self.set_key(self.bossrequest['key'])
        if 'value' in self.bossrequest:
            self.set_value(self.bossrequest['value'])

    def validate_cutout_service(self):
        """

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

        time = self.bossrequest['time_args']
        if not time:
            # get default time
            self.time_start = self.channel.default_time_step
            self.time_stop = self.channel.default_time_step + 1
        else:
            self.set_time(time)

        self.set_cutoutargs(int(self.bossrequest['resolution']), self.bossrequest['x_args'],
                            self.bossrequest['y_args'], self.bossrequest['z_args'])

    def validate_image_service(self):
        """

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

        time = self.bossrequest['time_args']
        if not time:
            # get default time
            self.time_start = self.channel.default_time_step
            self.time_stop = self.channel.default_time_step + 1
        else:
            self.set_time(time)

        self.set_imageargs(self.bossrequest['orientation'], self.bossrequest['resolution'], self.bossrequest['x_args'],
                           self.bossrequest['y_args'], self.bossrequest['z_args'])

    def validate_tile_service(self):
        """

        Args:
            webargs:

        Returns:

        """
        self.initialize_request(self.bossrequest['collection_name'], self.bossrequest['experiment_name'],
                                self.bossrequest['channel_name'])

        time = self.bossrequest['time_args']
        if not time:
            # get default time
            self.time_start = self.channel.default_time_step
            self.time_stop = self.channel.default_time_step + 1
        else:
            self.set_time(time)

        self.set_tileargs(self.bossrequest['tile_size'], self.bossrequest['orientation'], self.bossrequest['resolution'],
                          self.bossrequest['x_args'], self.bossrequest['y_args'], self.bossrequest['z_args'])

    def initialize_request(self, collection_name, experiment_name, channel_name):
        """
        Initialize the request

        Parse and validate all the resource names in the request

        Args:
            collection_name: Collection name from the request
            experiment_name: Experiment name from the request
            channel_name: Channel name from the request

        """
        if collection_name:
            colstatus = self.set_collection(collection_name)
            if experiment_name and colstatus:
                expstatus = self.set_experiment(experiment_name)
                if channel_name and expstatus:
                    self.set_channel(channel_name)

        self.check_permissions()
        self.set_boss_key()

    def set_cutoutargs(self, resolution, x_range, y_range, z_range):
        """
        Validate and initialize cutout arguments in the request
        Args:
            resolution: Integer indicating the level in the resolution hierarchy (0 = native)
            x_range: Python style range indicating the X coordinates  (eg. 100:200)
            y_range: Python style range indicating the Y coordinates (eg. 100:200)
            z_range: Python style range indicating the Z coordinates (eg. 100:200)

        Raises:
            BossError: For invalid requests

        """
        try:
            # validate the resolution
            if int(resolution) in range(0, self.experiment.num_hierarchy_levels):
                self.resolution = int(resolution)
            else:
                raise BossError("Invalid resolution {} in cutout args. The resolution has to be between 0 and {}".
                                format(resolution, self.experiment.num_hierarchy_levels), ErrorCodes.INVALID_CUTOUT_ARGS)

            # TODO --- Get offset for that resolution. Reading from  coordinate frame right now, This is WRONG

            x_coords = x_range.split(":")
            y_coords = y_range.split(":")
            z_coords = z_range.split(":")


            self.x_start = int(x_coords[0])
            self.x_stop = int(x_coords[1])

            self.y_start = int(y_coords[0])
            self.y_stop = int(y_coords[1])

            self.z_start = int(z_coords[0])
            self.z_stop = int(z_coords[1])

            # Check for valid arguments
            if (self.x_start >= self.x_stop) or (self.y_start >= self.y_stop) or (self.z_start >= self.z_stop) or \
                    (self.x_start < self.coord_frame.x_start) or (self.x_stop > self.coord_frame.x_stop) or \
                    (self.y_start < self.coord_frame.y_start) or (self.y_stop > self.coord_frame.y_stop) or\
                    (self.z_start < self.coord_frame.z_start) or (self.z_stop > self.coord_frame.z_stop):
                raise BossError("Incorrect cutout arguments {}/{}/{}/{}".format(resolution, x_range, y_range, z_range),
                                ErrorCodes.INVALID_CUTOUT_ARGS)

        except TypeError:
            raise BossError("Type error in cutout argument{}/{}/{}/{}".format(resolution, x_range, y_range, z_range),
                            ErrorCodes.TYPE_ERROR)

    def set_imageargs(self, orientation, resolution, x_args, y_args, z_args):
        """
        Validate and initialize tile service arguments in the request
        Args:
            resolution: Integer indicating the level in the resolution hierarchy (0 = native)
            x_range: Python style range indicating the X coordinates  (eg. 100:200)
            y_range: Python style range indicating the Y coordinates (eg. 100:200)
            z_range: Python style range indicating the Z coordinates (eg. 100:200)

        Raises:
            BossError: For invalid requests

        """

        try:

            if int(resolution) in range(0, self.experiment.num_hierarchy_levels):
                self.resolution = int(resolution)

            # TODO --- Get offset for that resolution. Reading from  coordinate frame right now, This is WRONG

            if orientation == 'xy':
                x_coords = x_args.split(":")
                y_coords = y_args.split(":")
                z_coords = [int(z_args) , int(z_args)+1]

            elif orientation == 'xz':
                x_coords = x_args.split(":")
                y_coords = [int(y_args), int(y_args) + 1]
                z_coords = z_args.split(":")

            elif orientation == 'yz':
                x_coords = [int(x_args), int(x_args) + 1]
                y_coords = y_args.split(":")
                z_coords = z_args.split(":")
            else:
                raise BossError("Incorrect orientation {}".format(orientation), ErrorCodes.INVALID_URL)

            self.x_start = int(x_coords[0])
            self.x_stop = int(x_coords[1])

            self.y_start = int(y_coords[0])
            self.y_stop = int(y_coords[1])

            self.z_start = int(z_coords[0])
            self.z_stop = int(z_coords[1])

            # Check for valid arguments
            if (self.x_start >= self.x_stop) or (self.y_start >= self.y_stop) or (self.z_start >= self.z_stop) or \
                    (self.x_start < self.coord_frame.x_start) or (self.x_stop > self.coord_frame.x_stop) or \
                    (self.y_start < self.coord_frame.y_start) or (self.y_stop > self.coord_frame.y_stop) or \
                    (self.z_start < self.coord_frame.z_start) or (self.z_stop > self.coord_frame.z_stop):
                raise BossError("Incorrect cutout arguments {}/{}/{}/{}".format(resolution, x_args, y_args, z_args),
                                ErrorCodes.INVALID_CUTOUT_ARGS)
        except TypeError:
            raise BossError("Type error in cutout argument{}/{}/{}/{}".format(resolution, x_args, y_args, z_args),
                            ErrorCodes.TYPE_ERROR)

    def set_tileargs(self, tile_size, orientation, resolution, x_idx, y_idx, z_idx):
        """
        Validate and initialize tile service arguments in the request
        Args:
            resolution: Integer indicating the level in the resolution hierarchy (0 = native)
            orientation:
            x_idx: X tile index
            y_idx: Y tile index
            z_idx: Z tile index

        Raises:
            BossError: For invalid requests

        """
        tile_size = int(tile_size)
        x_idx = int(x_idx)
        y_idx = int(y_idx)
        z_idx = int(z_idx)

        try:

            if int(resolution) in range(0, self.experiment.num_hierarchy_levels):
                self.resolution = int(resolution)

            # TODO --- Get offset for that resolution. Reading from  coordinate frame right now, This is WRONG

            # Get the params to pull data out of the cache
            if orientation == 'xy':
                corner = (tile_size * x_idx, tile_size * y_idx, z_idx)
                extent = (tile_size, tile_size, 1)
            elif orientation == 'yz':
                corner = (x_idx, tile_size * y_idx, tile_size * z_idx)
                extent = (1, tile_size, tile_size)
            elif orientation == 'xz':
                corner = (tile_size * x_idx, y_idx, tile_size * z_idx)
                extent = (tile_size, 1, tile_size)
            else:
                raise BossHTTPError("Invalid orientation: {}".format(orientation),
                                         ErrorCodes.INVALID_CUTOUT_ARGS)

            self.x_start = int(corner[0])
            self.x_stop = int(corner[0]+ extent[0])

            self.y_start = int(corner[1])
            self.y_stop = int(corner[1]+ extent[1])

            self.z_start = int(corner[2])
            self.z_stop = int(corner[2]+ extent[2])


            # Check for valid arguments
            if (self.x_start >= self.x_stop) or (self.y_start >= self.y_stop) or (self.z_start >= self.z_stop) or \
                    (self.x_start < self.coord_frame.x_start) or (self.x_stop > self.coord_frame.x_stop) or \
                    (self.y_start < self.coord_frame.y_start) or (self.y_stop > self.coord_frame.y_stop) or \
                    (self.z_start < self.coord_frame.z_start) or (self.z_stop > self.coord_frame.z_stop):
                raise BossError("Incorrect cutout arguments {}/{}/{}/{}".format(resolution, x_idx, y_idx, z_idx),
                                ErrorCodes.INVALID_CUTOUT_ARGS)
        except TypeError:
            raise BossError("Type error in cutout argument{}/{}/{}/{}".format(resolution, x_idx, y_idx, z_idx),
                            ErrorCodes.TYPE_ERROR)


    def initialize_view_request(self, webargs):
        """
        Validate and initialize views
        Args:
            webargs:


        """
        print(webargs)

    def set_service(self, service):
        """
        Set the service variable. The service can be 'meta', 'view' or 'cutout'
        Args:
            service: Service requested in the request

        Returns: None

        """
        self.service = service

    def set_collection(self, collection_name):
        """
        Validate the collection and set collection object for a valid collection.
        Args:
            collection_name: Collection name from the request

        Returns:
            Bool : True

        Raises : BossError is the collection is not found.

        """
        if Collection.objects.filter(name=str(collection_name)).exists():
            self.collection = Collection.objects.get(name=collection_name)
            return True
        else:
            raise BossError("Collection {} not found".format(collection_name), ErrorCodes.RESOURCE_NOT_FOUND)

    def get_collection(self):
        """
        Get the collection name for the current collection

        Returns:
            collection_name : Name of the collection

        """
        if self.collection:
            return self.collection.name

    def set_experiment(self, experiment_name):
        """
        Validate and set the experiment
        Args:
            experiment_name: Experiment name from the request

        Returns: BossError is the experiment with the matching name is not found in the db

        """
        if Experiment.objects.filter(name=experiment_name, collection=self.collection).exists():
            self.experiment = Experiment.objects.get(name=experiment_name, collection=self.collection)
            self.coord_frame = self.experiment.coord_frame
        else:
            raise BossError("Collection {} not found".format(experiment_name), ErrorCodes.RESOURCE_NOT_FOUND)

        return True

    def get_experiment(self):
        """
        Return the experiment name for the current experiment

        Returns:
            self.experiment.name (str): Experiment name for the data model representing the current experiment

        """
        if self.experiment:
            return self.experiment.name

    def set_channel(self, channel_name):
        """
        Validate and set the channel
        Args:
            channel_name: Channel name specified in the request

        Returns:

        """
        if Channel.objects.filter(name=channel_name, experiment=self.experiment).exists():
            self.channel = Channel.objects.get(name=channel_name, experiment=self.experiment)
            return True
        else:
            raise BossError("Channel {} not found".format(channel_name), ErrorCodes.RESOURCE_NOT_FOUND)

    def get_channel(self):
        """
        Return the channel name for the channel

        Returns:
            self.channel.name (str) : Name of channel

        """
        if self.channel:
            return self.channel.name

    def set_key(self, key):
        """
        Set the meta data key. This is an optional argument used by the metadata service
        Args:
            key: Meta data key specified in the request

        """
        self.key = key

    def get_key(self):
        """
        Return the meta data key
        Returns:
            self.key (str) : Metadata key

        """
        return self.key

    def set_value(self, value):
        """
        Set the meta data value. This is an optional argument used by the metadata service
        Args:
            value: String representing the meta data value

        """
        self.value = value

    def get_value(self):
        """
        Return the value associated with the metadata
        Returns:
            self.value (str) : Meta data value

        """
        return self.value

    def get_default_time(self):
        """
        Return the default timesample for the channel
        Returns:
            self.default_time (int) : Default timestep for the channel

        """
        return self.default_time

    def get_coordinate_frame(self):
        """
        Returns the coordinate frame for the experiment
        Returns:
            self.coord_frame.name (str) : Name of coordinate frame

        """
        return self.coord_frame.name

    def get_resolution(self):
        """
        Return the resolution specified in the cutout arguments of the request
        Returns:
            self.resolution (int) : Resolution

        """
        return self.resolution

    def get_x_start(self):
        """
        Return the lower X bounds for the request
        Returns:
            self.x_start(int) : Lower bounds for X range

        """
        return self.x_start

    def get_x_stop(self):
        """
        Return the upper X bounds specified in the cutout arguments

        Returns:
            self.x_stop (int) : Upper bounds for X range
        """
        return self.x_stop

    def get_y_start(self):
        """
        Get the lower Y bounds specified in the cutout arguments of the request
        Returns:
            self.y_start (int) : lower bounds for Y range
        """
        return self.y_start

    def get_y_stop(self):
        """
        Get the upper Y bounds specified in the cutout arguments of the request
        Returns:
            self.y_stop (int) : Upper bounds for Y range
        """
        return self.y_stop

    def get_z_start(self):
        """
        Get the lower Z bounds specified in the cutout arguments of the request
        Returns:
            self.z_start (int) :  Lower bounds for Z range
        """
        return self.z_start

    def get_z_stop(self):
        """
        Get the lower Z bounds specified in the cutout arguments of the request
        Returns:
             self.z_stop (int) : Upper bounds for Z range
        """
        return self.z_stop

    def get_x_span(self):
        """
        Get the x span for the request
        Returns:
            x_span (int) : X span
        """
        return self.x_stop - self.x_start

    def get_y_span(self):
        """
        Get the Y span for the request
        Returns:
            y_span (int) : Y span
        """
        return self.y_stop - self.y_start

    def get_z_span(self):
        """
        Get the z span for the request
        Returns:
            z_span (int): Z span
        """
        return self.z_stop - self.z_start

    def set_boss_key(self):
        """ Set the base boss key for the request

        The boss key concatenates the names of the datamodel stack to create a string represting the request.
        Returns:
            self.bosskey(str) : String that represents the boss key for the current request
        """
        if self.collection and self.experiment and self.channel:
            self.base_boss_key = self.collection.name + META_CONNECTOR + self.experiment.name + META_CONNECTOR \
                                 + self.channel.name
        elif self.collection and self.experiment and self.service == 'meta':
            self.base_boss_key = self.collection.name + META_CONNECTOR + self.experiment.name
        elif self.collection and self.service == 'meta':
            self.base_boss_key = self.collection.name
        else:
            return BossHTTPError("Error creating the boss key", ErrorCodes.UNABLE_TO_VALIDATE)

    def check_permissions(self):
        """ Set the base boss key for the request

        The boss key concatenates the names of the datamodel stack to create a string represting the request.
        Returns:
            self.bosskey(str) : String that represents the boss key for the current request
        """
        if self.service =='cutout' or self.service == 'image' or self.service == 'tile':
            perm = BossPermissionManager.check_data_permissions(self.user, self.channel,
                                                                  self.method)
        elif self.service =='meta':
            if self.collection and self.experiment and self.channel:
                obj = self.channel
            elif self.collection and self.experiment:
                obj = self.experiment
            elif self.collection:
                obj = self.collection
            else:
                return BossHTTPError("Error encountered while checking permissions for this request",
                                     ErrorCodes.UNABLE_TO_VALIDATE)
            perm = BossPermissionManager.check_resource_permissions(self.user, obj, self.method)
        if not perm:
            return BossHTTPError("This user does not have the required permissions", ErrorCodes.MISSING_PERMISSION)

    def get_boss_key(self):
        """
        Get the boss key for the current object

        The boss key is the compound identifier using the "name" attribute of the data model resources used
        in the request

        Returns:
            self.boss_key (str) : The base boss key for the request
        """
        return self.base_boss_key

    def get_boss_key_list(self):
        """
        Get the boss_key list for the current object including the resolution and time samples

        The boss key is the compound identifier using the "name" attribute of the data model resources used
        in the request

        Returns:
            self.boss_key (list(str)) : List of boss keys for the request
        """
        request_boss_keys = []

        # For services that are not part of the core services, append resolution and time to the key
        if self.service == 'meta':
            request_boss_keys = [self.base_boss_key]
        else:
            for time_step in range(self.time_start, self.time_stop):
                request_boss_keys.append(self.base_boss_key + '&' + str(self.resolution) + '&' + str(time_step))

        return request_boss_keys

    def get_lookup_key(self):
        """
        Returns the base lookup key for the request, excluding the resolution and time sample

        The lookup key is the compound identifier using the "id" attribute of the data model resources used
        in the request

        Returns:
            lookup (str) : The base lookup key that correspond to the request

        """
        return LookUpKey.get_lookup_key(self.base_boss_key).lookup_key

    def get_lookup_key_list(self):
        """
        Returns the list of lookup keys for the request when including the resolution and time sample

        The lookup key is the compound identifier using the "id" attribute of the data model resources used
        in the request

        Returns:
            lookup (list(str))) : List of Lookup keys that correspond to the request

        """
        request_lookup_keys = []
        if self.base_boss_key:
            # Get the lookup key for the bosskey
            base_lookup = LookUpKey.get_lookup_key(self.base_boss_key)

            # If not a core service, append resolution and time
            if self.service == 'meta':
                request_lookup_keys = [base_lookup.lookup_key]
            else:
                for time_step in range(self.time_start, self.time_stop):
                    request_lookup_keys.append(base_lookup.lookup_key + '&' +
                                               str(self.resolution) + '&' + str(time_step))

        return request_lookup_keys

    def set_time(self, time):
        """
        Set the time range for a request.
        Args:
            time: String representing the Time range

        Raises : Boss Error if the range is out or bounds or invalid

        """
        m = re.match("/?(?P<time_start>\d+)\:?(?P<time_stop>\d+)?/?", time)
        if m:
            [tstart, tstop] = [arg for arg in m.groups()]
            if tstart:
                self.time_start = int(tstart)
                if self.time_start > self.experiment.max_time_sample:
                    return BossHTTPError("Invalid time range {}. Start time is greater than the maximum time sample {}"
                                         .format(time, str(self.experiment.max_time_sample)), ErrorCodes.INVALID_URL)
            else:
                return BossHTTPError("Unable to parse time sample argument {}".format(time), ErrorCodes.INVALID_URL)
            if tstop:
                self.time_stop = int(tstop)
                if self.time_start > self.time_stop or self.time_stop > self.experiment.max_time_sample + 1:
                    return BossHTTPError("Invalid time range {}. End time is greater than the start time or out of "
                                         "bounds with maximum time sample {}".format
                                         (time, str(self.experiment.max_time_sample)), ErrorCodes.INVALID_URL)
            else:
                self.time_stop = self.time_start + 1


    def get_time(self):
        """
        Return the time step range
        Returns:
            Time sample range

        """
        return range(self.time_start, self.time_stop)
