#!/bin/bash

pg_dump -Fc coop_mes -U coop_mes -h localhost > pg_dump.data

