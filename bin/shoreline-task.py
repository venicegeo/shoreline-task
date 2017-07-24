# Copyright 2017, DigitalGlobe, Inc.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.

from __future__ import print_function

from cStringIO import StringIO
from datetime import datetime
import glob2
import json
import math
import os
import sqlite3
import geojson

import dill
import numpy as np
from pytides.tide import Tide

from gbdx_task_interface import GbdxTaskInterface


def init_db(db_file, in_mem=False):
    """Get DB ready by.
    Can also load existing database into memory.
    :returns: sqlite cursor
    """
    conn = sqlite3.connect(db_file)

    if in_mem is True:
        tempfile = StringIO()
        for line in conn.iterdump():
            tempfile.write('%s\n' % line)
        conn.close()

        tempfile.seek(0)

        conn = sqlite3.connect(":memory:")
        conn.cursor().executescript(tempfile.read())
        conn.commit()
        conn.row_factory = sqlite3.Row

    return conn.cursor()


def build_tide_model(data):
    """Builds a model given tide data.
    :param data: list of tuples [(date, height),...)]
    :returns: Pytides model or None if data insufficient.
    """
    try:
        dates, heights = zip(*data)
        dates = [datetime.strptime(date, '%Y-%m-%d-%H') for date in dates]
        return Tide.decompose(heights, dates).model
    except:
        return None


def build_tide_models(tide_model_file):
    """Build models for all stations.
    :returns: Dict -- {'station_id': model, ...}
    """

    # We try to read the pre fitted tidal models if they don't exists we create
    # them this model for all the stations is very tiny, so run locally if the
    # database of station data is updated to re-fit the model.
    try:
        with open(tide_model_file, 'rb') as tm:
            tide_models = dill.load(tm)

    except IOError:
        tide_models = {}
        for station in all_stations():
            # station is like (1, )
            station = station[0]

            data = station_data(station)
            model = build_tide_model(data)

            if model is not None:
                # see below, model is pickelable
                # Tide is not.
                tide_models[station] = model

            else:
                tide_models[station] = None

        # Store data for later
        with open(tide_model_file, 'wb') as tm:
            dill.dump(tide_models,
                      tm,
                      protocol=dill.HIGHEST_PROTOCOL)

    # we are doing it like this because the instantiated Tide is apparently not
    # pickelable even using dill, also we can't build a model if v is None.
    return {k: Tide(model=v, radians=False) if v is not None else v
            for (k, v) in tide_models.iteritems()}


def predict_tides(station, dtg=None):
    """Predict the tide level at a station and date.
    :param station_id: The nearest stations id.
    :type station_id: String
    :param dtg: Date time group.
    :type dtg: String -- "Y-m-d-H-M"
    """
    if dtg is None:
        dtg = datetime.now()
        dtg = datetime.strftime(dtg, '%Y-%m-%d-%H-%M')
        prediction_t0 = datetime.strptime(dtg,
                                          '%Y-%m-%d-%H-%M')
    else:
        prediction_t0 = datetime.strptime(dtg,
                                          '%Y-%m-%d-%H-%M')

    hours = 0.1 * np.arange(1 * 24 * 10)
    times = Tide._times(prediction_t0, hours)

    # Predict the tides using the Pytides model.
    try:
        model = TIDE_MODEL[station]
        my_prediction = model.at(times)
        ctide = float(my_prediction[0]) / 1000
        mint = float(min(my_prediction)) / 1000
        maxt = float(max(my_prediction)) / 1000
    except:
        ctide = 'null'
        mint = 'null'
        maxt = 'null'

    return mint, maxt, ctide, str(times[0])


def nearest_station(lat, lon):
    """Query our db for the nearest station.
    Returns the station along with all the
    data for the station.
    :param lat: Latitude
    :type lat: float
    :param lon: Longitude
    :type lon: float
    :returns: Station id -- String
    """
    if lat is None or lon is None:
        return '-9999'

    if lat > 90 or lat < -90 or lon < -180 or lon > 180:
        return '-9999'

    cur_cos_lat = math.cos(lat * math.pi / 180.0)
    cur_sin_lat = math.sin(lat * math.pi / 180.0)
    cur_cos_lon = math.cos(lon * math.pi / 180.0)
    cur_sin_lon = math.sin(lon * math.pi / 180.0)

    t = (
        cur_sin_lat,
        cur_cos_lat,
        cur_cos_lon,
        cur_sin_lon
    )

    command = (
        """
        select station, (%f * sin_lat + \
        %f * cos_lat * \
        (cos_lon * %f + sin_lon * %f)) dist \
        from stations order by dist desc limit 1;""" % t)

    DB_CURSOR.execute(command)
    station, _ = DB_CURSOR.fetchone()

    return station


def station_data(station_id):
    """Get the historical tide data for a station
    :param station_id: The station id of interest
    :type station_id: String
    :returns: List of date, height tuples -- [(date, height),...]
    """
    DB_CURSOR.execute('select date,mm from fdh where station=? order by date',
                      (str(station_id),))

    return DB_CURSOR.fetchall()


def all_stations():
    """ Get all the stations from the DB
    Used for pre-building models predictive models
    for each station.
    """
    command = 'select station from stations;'
    DB_CURSOR.execute(command)
    return DB_CURSOR.fetchall()


def tide_coordination(lat, lon, dtg=None):
    """
    :param lat: the latitude
    :type lat: float
    :param lon: the longitude
    :type lon: float
    :returns: the tide data -- json
    """
    out = {
        'minimumTide24Hours': 'null',
        'maximumTide24Hours': 'null',
        'currentTide': 'null'
    }

    station_id = nearest_station(lat, lon)

    if station_id == '-9999':
        return out

    mint, maxt, ctide, ctime = predict_tides(station_id, dtg)

    out['minimumTide24Hours'] = mint
    out['maximumTide24Hours'] = maxt
    out['currentTide'] = ctide

    return out


# Initialize the db, change in_mem=True for production if enough memory exists
# for each worker to load the database (~250MB)
db_file = '/opt/data/fdh.sqlite'
DB_CURSOR = init_db(db_file, in_mem=False)

# build the tide model
tide_model = '/opt/data/tidemodel.pkl'
TIDE_MODEL = build_tide_models(tide_model)


class ShorelineTask(GbdxTaskInterface):

    def invoke(self):

        # Get inputs
        lat = self.get_input_string_port('lat')
        lon = self.get_input_string_port('lon')
        dtg = self.get_input_string_port('dtg')
        meta = self.get_input_string_port('meta')
        minsize = self.get_input_string_port('minsize', default='1000.0')
        smooth = self.get_input_string_port('smooth', default='1.0')
        img = self.get_input_data_port('image')

        vector_dir = self.get_output_data_port('vector')
        os.makedirs(vector_dir)

        raster_dir = self.get_output_data_port('raster')
        os.makedirs(raster_dir)

        tide = tide_coordination(float(lat), float(lon), dtg)

        result = {
            'metadata': json.loads(meta),
            'tides': tide
        }

        # with open(os.path.join(output_dir, 'tides.json'), 'w') as f:
        #     json.dump(result, f)

        all_lower = glob2.glob('%s/**/*.tif' % img)
        all_upper = glob2.glob('%s/**/*.TIF' % img)
        all_files = all_lower + all_upper

        for img_file in all_files:
            os.system('bfalg-ndwi -i %s -b 1 8 --outdir %s --basename bf --minsize %s --smooth %s' %
                      (img_file, vector_dir, minsize, smooth))

        os.rename(os.path.join(vector_dir, 'bf_ndwi.tif'),
                  os.path.join(raster_dir, 'bf_ndwi.tif'))

        # Okay, so we need to open the output bf.geojson here, and iterate
        # through the features, added result to properties for each and every
        # one.

        with open(os.path.join(vector_dir, 'bf.geojson')) as f:
            data = geojson.load(f)

        feature_collection = data['features']
        valid_feats = []

        for feat in feature_collection:
            feat['properties'] = result
            valid_feats.append(feat)

        data['features'] = valid_feats

        with open(os.path.join(vector_dir, 'bf.geojson'), 'wb') as f:
            geojson.dump(data, f)


if __name__ == "__main__":
    with ShorelineTask() as task:
        task.invoke()
