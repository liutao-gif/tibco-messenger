#!/bin/bash
# Tibco RV SendRequest wrapper — must use x86_64 JDK (Tibco libs are x86_64)
export DYLD_LIBRARY_PATH=/opt/tibco/tibrv/8.7/lib
export LANG=en_US.UTF-8
MYDIR="$(cd "$(dirname "$0")" && pwd)"

# Use x86_64 JDK to match Tibco's x86_64 native libraries
if [ -n "$JAVA_HOME" ] && [ -x "$JAVA_HOME/bin/java" ]; then
    JAVA="$JAVA_HOME/bin/java"
elif [ -x /usr/libexec/java_home ]; then
    JAVA="$(/usr/libexec/java_home)/bin/java"
else
    JAVA=java
fi

exec "$JAVA" -cp "$MYDIR:/opt/tibco/tibrv/8.7/lib/tibrvj.jar" \
    -Djava.library.path=/opt/tibco/tibrv/8.7/lib \
    TibcoRequest "$@"
