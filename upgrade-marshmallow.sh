#!/usr/bin/env bash
for path in $(rg 'marshmallow|fields' -l | grep .py); do
    echo $path
    ./marshmallow.awk $path > /tmp/$(basename $path)
    mv /tmp/$(basename $path) $path
done
black --preview $(rg marshmallow -l | grep .py)
