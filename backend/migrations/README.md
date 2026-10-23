# Database Migrations

Migrations are plain SQL files executed in order.

## Running migrations

```bash
# Install PostgreSQL client if needed
sudo dnf install postgresql  # Fedora/RHEL
# or: sudo apt install postgresql-client  # Debian/Ubuntu

# Create database
createdb pumpwatch

# Run migration
psql -d pumpwatch -f migrations/001_initial_schema.sql
```

## Migration naming

`XXX_description.sql` where XXX is sequential number (001, 002, etc.)
