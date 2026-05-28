# PostgreSQL Database Setup Guide

This guide covers multiple ways to set up a PostgreSQL database for the Job Board application.

## Quick Reference

The application expects a database named `jobboard` with the following default credentials:
- **Database**: `jobboard`
- **User**: `user`
- **Password**: `password`
- **Host**: `localhost`
- **Port**: `5432`

Connection string format: `postgresql://user:password@localhost:5432/jobboard`

---

## Method 1: Using Docker (Recommended - Easiest)

Docker is the easiest way to get PostgreSQL running without installing it locally.

### Prerequisites
- Docker installed ([Download Docker](https://www.docker.com/get-started))

### Steps

1. **Run PostgreSQL container:**
   ```bash
   docker run --name jobboard-db \
     -e POSTGRES_USER=user \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=jobboard \
     -p 5432:5432 \
     -d postgres:latest
   ```

2. **Verify it's running:**
   ```bash
   docker ps
   # Should show jobboard-db container running
   ```

3. **Test connection:**
   ```bash
   docker exec -it jobboard-db psql -U user -d jobboard
   # You should see: jobboard=#
   # Type \q to exit
   ```

### Docker Commands Reference

```bash
# Start the database (if stopped)
docker start jobboard-db

# Stop the database
docker stop jobboard-db

# View logs
docker logs jobboard-db

# Remove the container (WARNING: This deletes all data!)
docker rm -f jobboard-db

# Connect to database via psql
docker exec -it jobboard-db psql -U user -d jobboard
```

### Using Docker Compose (Alternative)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:latest
    container_name: jobboard-db
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: jobboard
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Then run:
```bash
docker-compose up -d
```

---

## Method 2: Local PostgreSQL Installation

### Step 1: Install PostgreSQL

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install postgresql postgresql-server
sudo postgresql-setup --initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

**macOS (using Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Windows:**
- Download installer from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)
- Run the installer and follow the setup wizard
- Remember the password you set for the `postgres` user

### Step 2: Start PostgreSQL Service

**Linux:**
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Enable auto-start on boot
```

**macOS:**
```bash
brew services start postgresql@15
```

**Windows:**
- PostgreSQL service should start automatically after installation
- Or use Services Manager to start `postgresql-x64-15` service

### Step 3: Create Database and User

**Option A: Using psql (Command Line)**

1. **Connect as postgres superuser:**
   ```bash
   # Linux/macOS
   sudo -u postgres psql
   
   # Or if you have a postgres user account
   psql -U postgres
   
   # Windows (use psql from PostgreSQL installation)
   psql -U postgres
   ```

2. **Run SQL commands:**
   ```sql
   -- Create database
   CREATE DATABASE jobboard;
   
   -- Create user
   CREATE USER user WITH PASSWORD 'password';
   
   -- Grant privileges
   GRANT ALL PRIVILEGES ON DATABASE jobboard TO user;
   
   -- Connect to the new database and grant schema privileges
   \c jobboard
   GRANT ALL ON SCHEMA public TO user;
   
   -- Exit psql
   \q
   ```

**Option B: Using createdb command (Linux/macOS)**

```bash
# Create database
sudo -u postgres createdb jobboard

# Create user and set password
sudo -u postgres psql -c "CREATE USER user WITH PASSWORD 'password';"

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE jobboard TO user;"
```

### Step 4: Verify Setup

```bash
# Test connection with new user
psql -U user -d jobboard -h localhost

# You should be prompted for password: password
# If successful, you'll see: jobboard=>
# Type \q to exit
```

---

## Method 3: Using Cloud PostgreSQL Services

### Option A: Supabase (Free Tier Available)

1. Sign up at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings → Database
4. Copy the connection string
5. Update your `.env` file with the connection string

### Option B: Railway

1. Sign up at [railway.app](https://railway.app)
2. Create a new PostgreSQL service
3. Copy the connection string from the Variables tab
4. Update your `.env` file

### Option C: Neon (Serverless PostgreSQL)

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string
4. Update your `.env` file

---

## Configure Your Application

After setting up the database, configure your application:

1. **Create `.env` file:**
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` with your database credentials:**
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/jobboard
   ```

   For Docker:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/jobboard
   ```

   For cloud services, use the provided connection string:
   ```env
   DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require
   ```

3. **Test the connection:**
   ```bash
   # Using Python
   python -c "from job_scraper.app.database import engine; engine.connect(); print('Connection successful!')"
   
   # Or using uv
   uv run python -c "from job_scraper.app.database import engine; engine.connect(); print('Connection successful!')"
   ```

---

## Troubleshooting

### Connection Issues

**Error: `could not connect to server: Connection refused`**
- **Solution**: PostgreSQL service is not running
  - Linux: `sudo systemctl status postgresql`
  - macOS: `brew services list`
  - Docker: `docker ps` (check if container is running)

**Error: `password authentication failed`**
- **Solution**: 
  - Verify username and password in `.env` file
  - For local PostgreSQL, check `pg_hba.conf` file
  - Try resetting password: `ALTER USER user WITH PASSWORD 'password';`

**Error: `database "jobboard" does not exist`**
- **Solution**: Create the database (see Method 2, Step 3)

**Error: `permission denied for database jobboard`**
- **Solution**: Grant privileges to user:
  ```sql
  GRANT ALL PRIVILEGES ON DATABASE jobboard TO user;
  \c jobboard
  GRANT ALL ON SCHEMA public TO user;
  ```

### Port Already in Use

**Error: `port 5432 is already in use`**
- **Solution**: 
  - Check what's using the port: `lsof -i :5432` (macOS/Linux) or `netstat -ano | findstr :5432` (Windows)
  - Stop the conflicting service or use a different port
  - For Docker, change port mapping: `-p 5433:5432`

### Docker-Specific Issues

**Error: `container name already exists`**
- **Solution**: Remove existing container: `docker rm -f jobboard-db`

**Error: `port is already allocated`**
- **Solution**: 
  - Use a different port: `-p 5433:5432`
  - Or stop the service using port 5432

---

## Useful PostgreSQL Commands

```sql
-- List all databases
\l

-- Connect to a database
\c jobboard

-- List all tables
\dt

-- Describe a table
\d jobs

-- List all users
\du

-- Exit psql
\q
```

```bash
# Connect to database via command line
psql -U user -d jobboard

# Execute SQL file
psql -U user -d jobboard -f script.sql

# Backup database
pg_dump -U user jobboard > backup.sql

# Restore database
psql -U user jobboard < backup.sql
```

---

## Security Notes

⚠️ **Important for Production:**

1. **Change default passwords** - Never use `password` in production
2. **Use strong passwords** - At least 12 characters with mixed case, numbers, symbols
3. **Limit network access** - Only allow connections from trusted IPs
4. **Use SSL/TLS** - Enable SSL connections for remote databases
5. **Regular backups** - Set up automated backups
6. **Update regularly** - Keep PostgreSQL updated with security patches

---

## Next Steps

After setting up the database:

1. ✅ Database is created and running
2. ✅ `.env` file is configured with correct `DATABASE_URL`
3. ✅ Test connection (see "Configure Your Application" section)
4. ✅ Run the application - tables will be created automatically on first run
5. ✅ Check logs for "Database initialized" message

The application will automatically create the `jobs` table on startup using SQLAlchemy.
