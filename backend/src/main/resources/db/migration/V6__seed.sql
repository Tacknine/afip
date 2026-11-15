INSERT INTO roles(name) VALUES
 ('SUPER_ADMIN'),
 ('AGRICULTURAL_OFFICER'),
 ('FARMER'),
 ('RESEARCHER'),
 ('DATA_ANALYST');

INSERT INTO external_data_sources(code, base_url) VALUES
 ('NASA_APPEARS','https://appeears.earthdatacloud.nasa.gov/api/'),
 ('HARVEST_CKAN','https://data.harvestportal.org/api/3/action/'),
 ('GLAM_V4','https://glam1.gsfc.nasa.gov/api/gettbl/v4'),
 ('ISDASOIL_V2','https://api.isda-africa.com');
