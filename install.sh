#!/bin/bash
echo "Installerar Timeshift Panel Indicator..."
echo ""
echo "1. Installerar beroenden..."
sudo apt install -y python3-gi python3-gi-cairo gir1.2-appindicator3-0.1
echo ""
echo "2. Kopierar script..."
sudo cp timeshift-panel-indicator.py /usr/local/bin/
sudo chmod +x /usr/local/bin/timeshift-panel-indicator.py
echo ""
echo "3. Skapar autostart..."
mkdir -p ~/.config/autostart
cp timeshift-panel-indicator.desktop ~/.config/autostart/
echo ""
echo "4. Startar indikatorn..."
pkill -f timeshift-panel-indicator.py 2>/dev/null || true
/usr/local/bin/timeshift-panel-indicator.py &
echo ""
echo "Klar! Ikonen visas i panelen."
echo "Högerklick för meny, varningsikon när inaktiverat."
