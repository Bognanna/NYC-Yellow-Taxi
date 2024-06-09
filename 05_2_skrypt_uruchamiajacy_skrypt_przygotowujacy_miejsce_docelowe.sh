#!/bin/bash
export PGPASSWORD='mysecretpassword'

wget https://jdbc.postgresql.org/download/postgresql-42.6.0.jar

docker run --name postgresdb \
	-p 8432:5432\
	-e POSTGRES_PASSWORD="${PGPASSWORD}"\
	-v "$(pwd)/05_1_skrypt_przygotowujacy_miejsce_docelowe.sql:/docker-entrypoint-initdb.d/05_1_skrypt_przygotowujacy_miejsce_docelowe.sql"\
	-d postgres
