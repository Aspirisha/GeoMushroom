\c mushrooms;
DROP TABLE IF EXISTS Mushrooms;

CREATE TABLE Mushrooms (
	id SERIAL PRIMARY KEY,
	longitude VARCHAR(50),
	latitude VARCHAR(50),
	country TEXT,
	URL TEXT,
	time TIMESTAMP,
	location GEOMETRY(POINT)
);

CREATE INDEX Mushrooms_geom_idx
  ON Mushrooms
  USING GIST(geography(location));

ALTER TABLE Mushrooms ADD CONSTRAINT unique_url UNIQUE (URL);
