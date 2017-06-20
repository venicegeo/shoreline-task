import bftideprediction.data.to_db_station as to_db_station
import os

def test_to_db_fhd():
    test_file = 'test/fixtures/stations/fdh_test2.sqlite'
    if os.path.exists(test_file):
        os.remove(test_file)
    to_db_station.to_db_station(test_file, 'test/fixtures/stations')
    assert os.path.exists(test_file)
    if os.path.exists(test_file):
        os.remove(test_file)


def test_to_db_fhd_except():
    test_file = 'test/fixtures/stations/fdh_test2.sqlite'
    if os.path.exists(test_file):
        os.remove(test_file)
    to_db_station.to_db_station(test_file, 'NOTREAL/NOTREAL/POSSIBLYREAL')
    if os.path.exists(test_file):
        os.remove(test_file)

