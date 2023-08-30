# Setting up native development in windows for RD WATCH
1) Install python 3.10 without conda and deactivate conda environments, including base
	- https://www.python.org/downloads/release/python-3100/
2) Set the environment variables in .env.
3) Run docker compose -f ./docker-compose.yaml up -d
4) `pip install psycopg2-binary`
5) Install poetry
```pwsh
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```
6) Install/create python env with poetry
```
poetry --directory django install
```

You might have to install Visual C++ build tools 14.0+
Just follow the link in the error message and make sure you check off the build tools

7)
Make sure `.py` files are associated with python interpreter. Cannot be conda.

or

Set poetry interpreter in pycharm. This is what I am doing.

8) Set up environment variables
The intent is to just set the variables present in the `.env` and `dev/.env.docker-compose-native` files. Do it any way you see fit, including manually via the windows UI.

The following is a scripted way
```pwsh
get-content .env.docker-compose-native | foreach {
    $name, $value = $_.split('=')
    [Environment]::SetEnvironmentVariable($name, $value, 'User')
}
```

Run this `.ps1` script to set environment variables in windows powershell
```
. .\export-env.ps1  
```

You have to remove empty lines and comments from the `.env` files, or else you will get an error about 0 length variables. 

**Also make sure there are no quotation marks!!**

Also, need to install gdal via this method. Conda will not work
https://trac.osgeo.org/osgeo4w/

Select advanced installation and ensure `gdal` and the `gdal303-runtime` are selected. The dependencies should automatically be installed after.

9) 
```
poetry run --directory django .\django\src\manage.py runserver
```

or

run `manage.py` in pycharm after setting up interpreter. Make sure to restart pycharm if you are using it to update `os.environ` and environment variables.

10)
Run, in a separate terminal,
`poetry run --directory django celery --app rdwatch.celery worker --loglevel INFO --without-heartbeat`

If you get an error about finding some `gdal304.dll`, go to the location and rename it to `gdal304.dll.orig`, and do the same for any other potential environments on the PATH. For me, I found one in the base anaconda environment.

11) 
Run, in a separate terminal,
`poetry run --directory django celery --app rdwatch.celery beat --loglevel INFO`

12) 
Run, in a separate terminal,
`cd vue`
`npm run dev`

to spin up the front end

13) To use the scoring database in the frontend, make sure you are connected to the APL T&E database

```
ssh -L 8088:localhost:8088 -L 5433:localhost:5432 5-2-1-a@smart-te-dmz.outer.jhuapl.edu
```

and make sure to change the outward facing port to 5433, and change the correponding port in the docker compose, as well as commenting out the RDWatch Scoring DB in `docker-compose.yaml`:
```
  # Scoring database
#  scoredb:
#    image: postgis/postgis:latest
#    environment:
#      POSTGRES_USER: scoring
#      POSTGRES_DB: scoring
#      POSTGRES_PASSWORD: secretkey
#    volumes:
#      - postgresql-scoring-data:/var/lib/postgresql/data
#    ports:
#      - 5433:5432
```
and access this URL: `http://localhost:8080/#/scoring/`