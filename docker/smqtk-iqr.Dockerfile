FROM python:3.11

WORKDIR /
RUN apt update && apt install -y git gdal-bin libgdal-dev
RUN git clone https://github.com/Erotemic/SMQTK-IQR.git
RUN git clone https://github.com/Kitware/SMQTK-Descriptors.git

WORKDIR /SMQTK-IQR
RUN git checkout dev/add-tutorial-3
RUN pip install -e .
RUN pip install faiss-cpu==1.8.0 \
    "psycopg2-binary>=2.9.5,<3.0.0" \
    scriptconfig \
    ubelt \
    rich \
    kwcoco \
    opencv-python-headless \
    girder-client \
    # this version matches the one from python:3.11 apt install gdal-bin
    gdal==3.6.2 \
    geowatch \
    kwcoco \
    kwgis \
    kwutil \
    scriptconfig \
    # extra pkg for running `geowatch torch_model_stats ...`
    netharn

WORKDIR /SMQTK-Descriptors
RUN pip install -e .

WORKDIR /SMQTK-IQR
