#!/bin/sh

failures=0
for file in *.py; do
    if [ $file == "__init__.py" ]; then
        continue
    fi
    
    echo ">>> Testing $file:"
    python $file

    if [ $? -ne 0 ]; then
        failures=1
    fi
done

if [ $failures -ne 0 ]; then
    echo "==== Got some failures! Check above for details."
else
    echo "==== All tests passed!"
fi

exit $failures
