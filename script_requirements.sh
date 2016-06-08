#! /bin/bash

if [ -f /usr/local/bin/pip ]
  then
    sudo pip install requests pytz iso8601
  else
    echo "Please install Python with PIP..."
fi

if [ -f ./api_keys.txt ]
  then
    echo "api_keys.txt file found"
  else
    echo "*** api_keys.txt file not found ***"
    echo "Please create api_keys.txt as specified in the readme.md"
    echo "If api_keys.txt is not stored in local directory"
    echo "Please update the variable in config.py for: api_keys_path = \\Path\\to\\api_keys.txt'"
fi
