#!/bin/bash
echo "Avinstallerar Timeshift Panel Indicator..."
echo ""
echo "1. Stoppar programmet..."
pkill -f timeshift-panel-indicator.py
echo ""
echo "2. Tar bort script..."
sudo rm -f /usr/local/bin/timeshift-panel-indicator.py
echo ""
echo "3. Tar bort autostart..."
rm -f ~/.config/autostart/timeshift-panel-indicator.desktop
echo ""
echo "4. Rensar sudoers (frivilligt)..."
echo "Vill du ta bort sudoers-filen? (j/n)"
read answer
if [ "$answer" = "j" ]; then
    sudo rm -f /etc/sudoers.d/timeshift-panel-indicator
fi
echo ""
echo "Avinstallation klar!"
echo "Logga ut och in för att se alla ändringar."
