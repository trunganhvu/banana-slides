#!/bin/bash

echo "===================================="
echo " (Banana Slides) "
echo "===================================="
echo ""

echo "[1/3] ..."
if [ ! -d "node_modules" ]; then
    echo ", ..."
    npm install
    if [ $? -ne 0 ]; then
        echo ", : npm install"
        exit 1
    fi
else
    echo ""
fi

echo ""
echo "[2/3] ..."
echo ""
echo "[3/3] ..."
echo " http://localhost:3011"
echo " http://localhost:5011"
echo ""
echo " Ctrl+C "
echo ""

npm run dev