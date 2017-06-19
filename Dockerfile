FROM ubuntu:14.04

# install packages
RUN apt-get update && \
    apt-get -y install --fix-missing --no-install-recommends \
        python \
        vim \
        build-essential \
        python-software-properties \
        software-properties-common \
        python-pip \
        python-numpy \
        python-scipy \
        python-dev \
        swig \
        git \
        zip \
        libproj-dev \
        libgeos-dev \
        libagg-dev \
        wget \
        zlib1g-dev

ENV GDAL_VERSION=2.1.2 \
    GDAL_CONFIG=/usr/local/bin/gdal-config \
    POTRACE_VERSION=1.14

# install potrace
RUN wget http://potrace.sourceforge.net/download/$POTRACE_VERSION/potrace-$POTRACE_VERSION.tar.gz && \
    tar -xzvf potrace-$POTRACE_VERSION.tar.gz && \
    cd potrace-$POTRACE_VERSION && \
    ./configure --with-libpotrace && \
    make && make install && cd .. && \
    rm -rf potrace-$POTRACE_VERSION*

# install gdal
RUN wget http://download.osgeo.org/gdal/$GDAL_VERSION/gdal-$GDAL_VERSION.tar.gz && \
    tar -xzvf gdal-$GDAL_VERSION.tar.gz && \
    cd gdal-$GDAL_VERSION && \
    ./configure \
        --with-static-proj4 \
        --with-geotiff=yes \
        --with-python=yes \
        --with-hdf4=no \
        --with-hdf5=no \
        --with-threads \
        --with-gif=no \
        --with-pg=no \
        --with-grass=no \
        --with-libgrass=no \
        --with-cfitsio=no \
        --with-pcraster=no \
        --with-netcdf=no \
        --with-png=no \
        --with-jpeg=no \
        --with-gif=no \
        --with-ogdi=no \
        --with-fme=no \
        --with-jasper=yes \
        --with-ecw=no \
        --with-kakadu=no \
        --with-mrsid=no \
        --with-jp2mrsid=no \
        --with-bsb=no \
        --with-grib=no \
        --with-mysql=no \
        --with-ingres=no \
        --with-xerces=yes \
        --with-expat=no \
        --with-odbc=no \
        --with-curl=yes \
        --with-sqlite3=no \
        --with-dwgdirect=no \
        --with-idb=no \
        --with-sde=no \
        --with-perl=no \
        --with-php=no \
        --without-mrf \
        --with-hide-internal-symbols=yes \
        CFLAGS="-O2 -Os" CXXFLAGS="-O2 -Os" && \
        make && make install && cd .. && \
        rm -rf gdal-$GDAL_VERSION*

ENV LD_LIBRARY_PATH=/usr/local/lib

#RUN pip install --upgrade pip && \
#    pip install \
#        pytides \
#        dill

COPY requirements.txt /

# install python dependencies
RUN pip install wheel numpy && \
    pip install -r requirements.txt

# Add all scripts in bin to root directory of image
ADD ./bin /
ADD ./bftideprediction/data /opt/data
