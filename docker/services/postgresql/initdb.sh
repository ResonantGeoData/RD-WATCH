#!/bin/sh
set -e

psql -v ON_ERROR_STOP=1 --username rdwatch --dbname rdwatch <<-EOSQL
  ALTER DATABASE rdwatch SET CLIENT_ENCODING TO 'UTF8';
  ALTER DATABASE rdwatch SET DEFAULT_TRANSACTION_ISOLATION TO 'read committed';
  ALTER DATABASE rdwatch SET TIMEZONE TO 'UTC';
  CREATE EXTENSION postgis;
  CREATE EXTENSION postgis_raster;
  CREATE EXTENSION postgis_topology;
  CREATE EXTENSION postgis_sfcgal;
  CREATE EXTENSION fuzzystrmatch;
  CREATE EXTENSION address_standardizer;
  CREATE EXTENSION address_standardizer_data_us;
  CREATE EXTENSION postgis_tiger_geocoder;
EOSQL
