SELECT 'CREATE DATABASE aura_workforce_test_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'aura_workforce_test_db')\gexec
