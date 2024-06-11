#!/bin/bash

#Convert special characters to adjust them to unix
sed -i -e 's/\r$//' 01_skrypt_tworzacy_zrodlowe_tematy_kafki.sh
sed -i -e 's/\r$//' 02_skrypt_uruchamiajacy_kafkaproducer.sh
sed -i -e 's/\r$//' 04_skrypt_uruchamiajacy_program_przetwarzania_strumieni_danych.sh
sed -i -e 's/\r$//' 05_2_skrypt_uruchamiajacy_skrypt_przygotowujacy_miejsce_docelowe.sh
sed -i -e 's/\r$//' 06_skrypt_odczytujacy_wyniki_z_miejsca_docelowego.sh

#Add executable permissions
chmod +x 01_skrypt_tworzacy_zrodlowe_tematy_kafki.sh
chmod +x 02_skrypt_uruchamiajacy_kafkaproducer.sh
chmod +x 03_program_przetwarzania_strumieni_danych.py
chmod +x 04_skrypt_uruchamiajacy_program_przetwarzania_strumieni_danych.sh
chmod +x 05_1_skrypt_przygotowujacy_miejsce_docelowe.sql
chmod +x 05_2_skrypt_uruchamiajacy_skrypt_przygotowujacy_miejsce_docelowe.sh
chmod +x 06_skrypt_odczytujacy_wyniki_z_miejsca_docelowego.sh
chmod +x KafkaProducer.jar

