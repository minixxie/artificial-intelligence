#!/bin/bash

curl -sOL https://www.highcharts.com/samples/data/olympic2012.json

cat olympic2012.json| jq -r '.[] | pick(.height, .weight)' | jq -s '.' | jq -r '(map(keys) | add | unique) as $cols | map(. as $row | $cols | map($row[.])) as $rows | $cols, $rows[] | @csv' | sed 1d > olympic2012.csv

