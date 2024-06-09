drop database if exists streamoutput;
create database streamoutput;

\c streamoutput;

drop table if exists taxiagg;
create table taxiagg (
	id serial primary key,
	date character(10),
	borough character(30),
	N_departures integer,
	N_arrivals integer,
	N_departing integer,
	N_arriving integer
	);