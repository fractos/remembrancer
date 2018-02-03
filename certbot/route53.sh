#!/bin/sh

certbot certonly -a "certbot-route53:auth" --non-interactive --text --agree-tos \
    -d $DOMAIN \
    --email $EMAIL \
