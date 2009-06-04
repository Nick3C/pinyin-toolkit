#!/bin/sh

for file in *.py; do
    if [ $file == "__init__.py" ]; then
        continue
    fi
    
    echo ">>> Testing $file:"
    python $file || exit 1
done