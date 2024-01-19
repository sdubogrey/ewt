#!/bin/bash

gunicorn main:application --log-config logging.conf
