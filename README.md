# Public Transport Optimization

## Useful Commands

### Quick Start
```bash
# Set up development environment
make dev-setup

# See all available commands
make help
```

### Development Workflow
```bash
# Install dependencies
make install          # Production dependencies
make install-dev      # Development dependencies

# Code quality
make format           # Auto-format code with ruff
make lint             # Run linting checks
make check            # Run lint + tests (quick validation)

# Clean up
make clean            # Remove build artifacts and cache
```

### Running Applications
```bash
# Start services
make run-api          # Start Flask API server (port 5001)
make run-monitoring   # Start Streamlit monitoring
make run-extractor    # Start the extracting process
make run-app          # Start the user app

# Docker services
make docker-build     # Build Docker images
make docker-up        # Start all services with docker-compose
make docker-down      # Stop all services
make logs             # View docker logs
```

### Database Management
```bash
# Database operations
make db-init          # Initialize Alembic migrations
make db-migrate       # Create new migration (prompts for message)
make db-upgrade       # Apply pending migrations
make db-downgrade     # Rollback last migration
make db-seed          # Generate seed data
make db-reset         # Reset database (with confirmation prompt)
```

### Distribution & Deployment
```bash
# Build and deploy
make build            # Build distribution packages
make dist             # Create source and wheel distributions
make upload-test      # Upload to TestPyPI
make upload-prod      # Upload to PyPI
make deploy-prep      # Full pre-deployment check (clean + lint + test + build)
```

## API Routes

### Find Optimal Path API

```
GET /api/v1/routes/optimal
```

| Header | Type | Description | Example |
|--------|------|-------------|---------|
| start_coords | String | Starting coordinates as a tuple of (latitude, longitude) | "(48.855089551123996, 2.394484471898831)" |
| end_coords | String | Ending coordinates as a tuple of (latitude, longitude) | "(48.8272425814562, 2.3787827042461736)" |

Response pattern :

```json
{
  "walking_distance": 1234.56,
  "walking_duration": 15.3,
  "network_time": 25.0,
  "total_time": 40.3,
  "optimal_path": [123, 456, 789],
  "route_info": {
    "station_names": ["Station A", "Station B", "Station C"],
    "num_stations": 3,
    "travel_time_mins": 25.0,
    "travel_time_formatted": "25min",
    "segments": [
      {
        "from_station_id": 123,
        "from_station_name": "Station A",
        "to_station_id": 456,
        "to_station_name": "Station B",
        "transport_id": "Line 1",
        "travel_time_mins": 12.5,
        "is_transfer": false
      },
      {
        "from_station_id": 456,
        "from_station_name": "Station B",
        "to_station_id": 789,
        "to_station_name": "Station C",
        "transport_id": "Line 2",
        "travel_time_mins": 12.5,
        "is_transfer": true
      }
    ],
    "num_transfers": 1
  }
}
```

## Running the API

1. Install the required dependencies:
   ```
   pip install -e .
   ```

2. Start the Flask server:
   ```
   python -m public_transport_watcher.api.app
   ```
   
   > Note: The API runs on port 5001 by default to avoid conflicts with macOS AirPlay Receiver which uses port 5000.

3. Test the API:
   ```
   python scripts/test_api.py
   ```

## Verifying Logstash Configuration

The API uses logstash to log all API requests. To verify the logstash configuration:

1. Ensure logstash is running with the provided configuration:
   ```
   logstash -f logstash.conf
   ```

2. Make API requests using the test script above.

3. Check the logs directory to verify log files are being generated:
   ```
   ls logs/api
   ```

4. Check the database to verify logs are being stored by logstash.