wget --no-clobber --directory-prefix ./data/icesat_aux -i ./data/icesat_aux/download.txt

gdalwarp -of GTiff \
  -co BIGTIFF=YES -co COMPRESS=DEFLATE -co TILED=YES \
  'NETCDF:./data/icesat_aux/ATL14_A1_0329_100m_005_02.nc:h' \
  'NETCDF:./data/icesat_aux/ATL14_A2_0329_100m_005_02.nc:h' \
  'NETCDF:./data/icesat_aux/ATL14_A3_0329_100m_005_02.nc:h' \
  'NETCDF:./data/icesat_aux/ATL14_A4_0329_100m_005_02.nc:h' \
  ./data/icesat_aux/icesat_h.tif

gdal_calc -A ./data/icesat_aux/icesat_h.tif --A_band=1 \
  --calc="A*1027.0/917.0" \
  --outfile=./data/icesat_aux/icesat_thickness.tif \
  --format=GTiff \
  --co BIGTIFF=YES --co COMPRESS=DEFLATE --co TILED=YES \
  --NoDataValue=3.4028234663852886e+38 --type=Float32

gdalbuildvrt -separate ./data/icesat_aux/stacked.vrt \
  ./data/icesat_aux/icesat_h.tif ./data/icesat_aux/icesat_thickness.tif

gdal_translate -of netCDF \
  -co FORMAT=NC4 -co COMPRESS=DEFLATE -co ZLEVEL=6 \
  ./data/icesat_aux/stacked.vrt ./data/icesat.nc

ncrename -v Band1,surface -v Band2,thickness ./data/icesat.ncz