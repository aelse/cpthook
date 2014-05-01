#!/bin/bash
# Rebuild hooks when cpthook configuration changes

CYAN="\e[0;36m"
YELLOW="\e[0;33m"
RED="\e[0;31m"
GREEN="\e[0;32m"
RESET="\e[0m"

function echo_colour {
    local COLOUR=$1
    shift
    echo -e ${COLOUR}$*${RESET}
}

function echo_error {
    echo_colour $RED $*
}

function echo_warning {
    echo_colour $YELLOW $*
}

function echo_success {
    echo_colour $GREEN $*
}

function echo_notice {
    echo_colour $CYAN $*
}

hookdir=""
if [ -d "hooks" ]; then
    hookdir="hooks"
elif [ -d ".git/hooks" ]; then
    hookdir=".git/hooks"
fi

if [ "$hookdir" == "" ]; then
    echo_warning Could not locate hooks.
    exit 0
fi

# Attempt to cpthook path from wrapper script in repository.
cpthook=`grep --no-filename cpthook $hookdir/* 2>/dev/null | grep -- --config | cut -d\  -f1 | head -1`

if [ "$cpthook" == "" ]; then
    echo_warning Could not locate cpthook.
    exit 0
fi

if [ ! -x "$cpthook" ]; then
    echo_warning cpthook is not executable.
    exit 0
fi

# Attempt to extract hook config file path from wrapper script in repository.
hookcfg=`grep --no-filename cpthook $hookdir/* 2>/dev/null | grep -- --config | sed -e "s/.*--config=\(\S*\).*/\1/" | head -1`

if [ "$hookcfg" == "" ]; then
    echo_warning Could not locate hook config.
    exit 0
fi

if [ ! -f "$hookcfg" ]; then
    echo_warning Hook config does not exist at $hookcfg.
    exit 0
fi

hookbase=`basename $hookcfg`

# Look for a file with the same name as the config file that
# cpthook used to run this script, then examine the file contents
# to see if hook-cfg also matches.
while read oldrev newrev refname; do
    for file in `git diff-tree --no-commit-id --name-only -r $newrev`; do
        filebase=`basename $file`
        if [ "$filebase" == "$hookbase" ]; then
            tmpdir=`mktemp -d`
            tmpfile="$tmpdir/$filebase"
            git show $newrev:$file > $tmpfile
            cfg=`grep '^\s*hook-cfg\s*=' $tmpfile | \
                sed -e "s/^\s*hook-cfg\s*=\s*//"`
            if [ "$cfg" == "$hookcfg" ]; then
                # Filename in repo and hook-cfg config item match the
                # config cpthook was invoked with.

                # Check that config file is valid. If not, refuse commit.
                $cpthook --config=$tmpfile --validate
                ret=$?
                if [ $ret -ne 0 ]; then
                    echo_notice Ran: $cpthook --config=$hookcfg --validate
                    echo_warning Invalid cpthook configuration.
                    echo_error Refusing commit.
                    rm -rf $tmpdir
                    exit 1
                fi

                # Attempt to update the active cpthook configuration.
                cat $tmpfile > $hookcfg
                ret=$?
                if [ $? -eq 1 ]; then
                    echo_warning Could not write $hookcfg. Please investigate.
                else
                    echo_notice Wrote cpthook config $hookcfg.
                    $cpthook --config=$hookcfg --init
                    ret=$?
                    if [ $ret -eq 0 ]; then
                        echo_success Successfully updated cpthook config
                    else
                        echo_notice Ran: $cpthook --config=$hookcfg --init
                        echo_error cpthook update failed. Please investigate.
                    fi
                fi
            fi
            rm -rf $tmpdir
        fi
    done
done
exit 0
