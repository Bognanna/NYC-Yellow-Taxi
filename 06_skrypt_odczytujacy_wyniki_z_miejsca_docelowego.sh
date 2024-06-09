#!/bin/bash
export PGPASSWORD='mysecretpassword'

psql -h localhost -p 8432 -U postgres -d streamoutput -c "SELECT * FROM taxiagg"
