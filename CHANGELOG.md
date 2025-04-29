# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2025-04-17
MR #7

### Added
- Extraction of next station
- Import next station data

### Changed
- Timestamp format to hour only

### Fixed
- Logger import on schedules data

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