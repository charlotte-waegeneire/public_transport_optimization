# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-17
MR #31

### Added
- Unitary tests

### Modified
- `makefile` to alias the use of tests

### Fixed
- User creation on the monitoring interface

## [0.27.1] - 2025-06-01
MR #30

### Added
- `pre-commit` and `streamlit_searchbox` to dependencies

### Changed
- Transport colors are the same used by RATP/SNCF

### Fixed
- Weighting processing for congestion awareness in the graph model
- Display for transfers
- Do not show the "weighted" path if it doesn't differ from the basic one

## [0.27.0] - 2025-06-01
MR #29

### Added
- Alerts API route
- Alerts API visualisations
- Cache for all API routes
- Mapping for transport lines icons

### Changed
- Traffic API route to use the new cache

## [0.26.0] - 2025-06-01
MR #27

### Added
- Dashboard for data quality visualisations
- Queries for the data quality dashboard

### Modified
- Update for template function `display_data_quality_dashboard`

## [0.25.0] - 2025-05-31
MR #28

### Added
- Makefile for easier dev commands
- Makefile main instructions in the README
- Seeds for API logs by calling the API
- Map to the path infos

### Modified
- Ruff formatted the missing files
- Route info display in a dropdown for a lighter UI
- JSON returning the path info's to include transfer time
- French instead of english UI

## [0.24.0] - 2025-05-30
MR #26

### Removed
- Comparison between arrivals and starts graph

## [0.23.0] - 2025-05-30
MR #25

### Added
- Validations map visualisation

## [0.22.0] - 2025-05-28
MR #24

### Added
- Dashboard API visualisations
- Queries for the dashboard API

## [0.21.0] - 2025-05-28
MR #23

### Added
- GitHub workflow to check VERSION.txt

## [0.20.0] - 2025-05-27
MR #22

### Modified
- Moved the response value in the `log` table
- Modified the logger json result accordingly
- Modified the logstash configuration accordingly

## [0.19.0] - 2025-05-24
MR #21

### Added
- Load and save weighted network
- Weight parameters in the API route to get the optimal path
- Created the application interface to search for path
- `APP_API_ENDPOINT` variable in `.env.example`

### Fixed
- `is_transfer` boolean not to count arrival and departure as boolean

### Removed
- Debug output in Logstash configuration

## [0.18.0] - 2025-05-22
MR #20

### Added
- Alembic migration for the new field `name` in transport table
- Extraction and insertion of `name` for transport table
- Dashboard visualisations
- Queries for the dashboard

## [0.17.0] - 2025-05-18
MR #19

### Added
- Logstash configuration
- API logging file suite for Logstash needs
- Test route
- API readme part
- Heathcheck for database docker compose config


## [0.16.0] - 2025-05-15
MR #17

### Added
- `predict_for_all_stations` method in the arima class
- `adjust_station_weights` method in the graph class
- `predictor` object to bring everything together
- Forgotten type hints in arima/graph functions
- `matplotlib` and `networkx` in requirements

### Modified
- `console_handler` in the logging config to only show WARNING and above

## [0.14.0] - 2025-05-11
**/!\ Wrong version number, should've been 0.15.0**
MR #15

### Added
- Adaptative predictions using ARIMA model, with custom parameter for each station by finding the optimimal ones
- Combined time-weighted historical data, recent observations, and ARIMA models

## [0.14.0] - 2025-05-09
MR #14

### Added
- Calculation of the walking trip to reach the nearest station using the graph

### Changed
- `graph_builder.find_optimal_route` to use this new function to calculate the whole journey
- Transfers duration from 5 minutes to 3

## [0.13.0] - 2025-05-13
MR #16

### Added
- Streamlit core interface with user authentication
- Simple and quick schema for the user CRUD
- Streamlit to `setup.py` requirements
- Dashboard example page

### Changed
- `get_sql_query` from `extractor` to utils folder for global use
- Moved all queries to utils folder for easier use of queries through the whole project

## [0.12.0] - 2025-05-06
MR #13

### Added
- Traffic predictions with ARIMA

## [0.11.0] - 2025-05-05
MR #12

### Added
- Graph builder, saver, and loader for the public transport network
- Visualizer for the network
- `networkx` in the dependencies
- `NETWORK_PATH` in the `.env.example` file

## [0.10.0] - 2025-04-30
MR #11

### Changed
- Bulk insertion to optimize navigo validations extraction

## [0.9.0] - 2025-04-17
MR #10

### Added
- Extraction and insertion of `journey_id` for schedules

## [0.8.0] - 2025-04-17
MR #9

### Added
- Extraction of next station

### Changed
- Schedule timestamp format to hour only

### Fixed
- Logger import on schedule data insertion

## [0.7.1] - 2025-04-26
MR #8

### Fixed
- `TimedRotatingFileHandler` instead of `RotatingFileHandler` for logging configuration
- Extraction of `latin-1` encoded files
- Handling holidays for navigo validations extraction
- Uppercase station names

## [0.7.0] - 2025-04-17
MR #7

### Added
- Extraction of transport's categories
- Extraciton of the transport's lines
- Extraction of schedules data

### Changed
- Import all stations instead of only metro ones

### Fixed
- Ruff config & format

## [0.6.0] - 2025-04-16
MR #6

### Added
- Extraction of weather data with `Infoclimat.fr` API
- API variable in `.env`
- Ruff config
- `beautifulsoup4` and `requests` dependancy

## [0.5.0] - 2025-04-13
MR #5

### Added
- Extraction of the air quality data to find when the air quality is bad
- Real time extraction of the file
- Utils function to get an environnement variable

### Fixed
- Import for the utils submodule

## [0.4.0] - 2025-04-07
MR #3

### Added
- Functions to fetch data from an API
- Import traffic data

## [0.3.0] - 2025-04-02
MR #4

### Added
- Stations extraction
- Utility function to execute a `SELECT` query and return the result

### Changed
- The datalake file retriever function to accept only one folder in the path
- Extraction configuration setup

## [0.2.0] - 2025-03-29
MR #2

### Added
- Navigo validations data ingestion
- Utils function to get the credentials, datalake files and engine
- Logging configuration

### Changed
- Time bin table to include the type of day for transport data
- Station base table to remove the "wording" column

## [0.1.0] - 2025-03-23
MR #1

### Added
- `docker-compose` configuration for development
- Alembic configuration with initial migration and manager

## [0.0.0] - 2025-03-23

### Added
- Init repo