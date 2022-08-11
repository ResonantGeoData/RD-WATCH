#!/bin/sh
set -e

rm -f /etc/redis.acl
touch /etc/redis.acl
chmod 400 /etc/redis.acl
chown redis:redis /etc/redis.acl
echo "user default reset" >> /etc/redis.acl

# change password of default user
SHA256_SECRET_KEY_HEX=$(echo -n "${RDWATCH_SECRET_KEY}" | sha256sum | awk '{ print $1 }')
unset RDWATCH_SECRET_KEY
echo "user rdwatch on allchannels allkeys allcommands #${SHA256_SECRET_KEY_HEX}" >> /etc/redis.acl
unset SHA256_SECRET_KEY_HEX
umask 0077
exec gosu redis:redis "$@"
