# Database

This folder stores the MySQL database schema for the EAGL system.

- `schema.sql` creates the `eagle_db` database, the `eagle_user` MySQL user, and all required tables.

## MySQL setup instructions

1. Ensure MySQL is running and you have a user with permission to create users and databases.

2. Import the schema directly:

```bash
mysql -u root -p < database/schema.sql
```

3. The schema file creates:

- `eagle_db`
- MySQL user `eagle_user`@`localhost` with password `1234`
- Tables such as `users`, `areas`, `funds`, `sub_areas`, `attendance`, `beneficiaries`, `eligible_families`, `coordinator_live_tracking`, `coordinator2_assignments`, and `livestock_delivery`

4. Configure your backend to connect to MySQL using:

- host: `localhost`
- database: `eagle_db`
- user: `eagle_user`
- password: `1234`

5. Start the backend API once the database is configured.
