#!/usr/bin/env python3
"""
Timeshift Panel Indicator - Helts separat från befintlig lösning
Visar status i systempanelen med varningsikon när inaktiverat
"""

import os
import sys
import signal
import subprocess
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, AppIndicator3, GObject, Notify
from threading import Thread
import time
import dbus
from dbus.mainloop.glib import DBusGMainLoop

class TimeshiftPanelIndicator:
    def __init__(self):
        self.app_id = 'timeshift_panel_indicator_v2'
        self.indicator = AppIndicator3.Indicator.new(
            self.app_id,
            "system-run",  # Temporär standardikon
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        
        # Initial statuskontroll
        self.current_status = self.get_timeshift_status()
        self.update_indicator_icon()
        
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title("Timeshift Panel v2")
        
        # Bygg menyn
        self.build_menu()
        
        # Initiera notifieringar
        Notify.init(self.app_id)
        
        # Starta bakgrundstråd för statusuppdatering
        self.update_thread = Thread(target=self.background_updater)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        print(f"Timeshift Panel Indicator v2 startad (PID: {os.getpid()})")
        print("Denna version körs parallellt med befintlig lösning")
    
    def get_timeshift_status(self):
        """Läs Timeshift-status direkt från konfigurationsfilen"""
        try:
            with open('/etc/timeshift/timeshift.json', 'r') as f:
                content = f.read()
            
            # Extrahera status
            import re
            daily = re.search(r'"schedule_daily"\s*:\s*"(true|false)"', content)
            weekly = re.search(r'"schedule_weekly"\s*:\s*"(true|false)"', content)
            boot = re.search(r'"schedule_boot"\s*:\s*"(true|false)"', content)
            
            status = {
                'daily': daily.group(1) if daily else 'unknown',
                'weekly': weekly.group(1) if weekly else 'unknown',
                'boot': boot.group(1) if boot else 'unknown'
            }
            
            # Bestäm övergripande status
            if status['daily'] == 'true' or status['weekly'] == 'true' or status['boot'] == 'true':
                return 'enabled'
            else:
                return 'disabled'
                
        except Exception as e:
            print(f"Fel vid statusläsning: {e}")
            return 'unknown'
    
    def update_indicator_icon(self):
        """Uppdatera panelikonen baserat på status"""
        if self.current_status == 'disabled':
            # Inaktiverad - visa varningsikon
            self.indicator.set_icon_full("dialog-warning", "Timeshift INAKTIVERAD")
            self.indicator.set_title("Timeshift: INAKTIVERAD")
        elif self.current_status == 'enabled':
            # Aktiverad - visa normal ikon
            self.indicator.set_icon_full("system-run", "Timeshift Aktiverad")
            self.indicator.set_title("Timeshift: Aktiverad")
        else:
            # Okänd status
            self.indicator.set_icon_full("dialog-question", "Timeshift Status okänd")
            self.indicator.set_title("Timeshift: Status okänd")
    
    def build_menu(self):
        """Bygg kontextmenyn"""
        self.menu = Gtk.Menu()
        
        # Titel/status
        self.status_item = Gtk.MenuItem(label="Laddar status...")
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)
        
        self.menu.append(Gtk.SeparatorMenuItem())
        
        # Snabbkontroller
        enable_item = Gtk.MenuItem(label="🚀 Aktivera Timeshift")
        enable_item.connect("activate", self.on_enable_clicked)
        self.menu.append(enable_item)
        
        disable_item = Gtk.MenuItem(label="⛔ Inaktivera Timeshift")
        disable_item.connect("activate", self.on_disable_clicked)
        self.menu.append(disable_item)
        
        self.menu.append(Gtk.SeparatorMenuItem())
        
        # Öppna Timeshift GUI
        gui_item = Gtk.MenuItem(label="📊 Öppna Timeshift GUI")
        gui_item.connect("activate", self.open_timeshift_gui)
        self.menu.append(gui_item)
        
        # Öppna befintlig skrivbordsikon
        desktop_item = Gtk.MenuItem(label="🖱️ Öppna befintlig kontroll")
        desktop_item.connect("activate", self.open_desktop_app)
        self.menu.append(desktop_item)
        
        self.menu.append(Gtk.SeparatorMenuItem())
        
        # Avsluta
        quit_item = Gtk.MenuItem(label="❌ Avsluta panelindikator")
        quit_item.connect("activate", self.quit_indicator)
        self.menu.append(quit_item)
        
        self.menu.show_all()
        self.indicator.set_menu(self.menu)
        
        # Uppdatera status i menyn
        self.update_menu_status()
    
    def update_menu_status(self):
        """Uppdatera status i menyn"""
        if self.current_status == 'enabled':
            status_text = "✅ Timeshift: AKTIVERAD"
            details = "(Automatiska backup körs)"
        elif self.current_status == 'disabled':
            status_text = "⚠️ Timeshift: INAKTIVERAD"
            details = "(Inga automatiska backup)"
        else:
            status_text = "❓ Timeshift: STATUS OKÄND"
            details = "(Kunde inte läsa konfiguration)"
        
        self.status_item.set_label(f"{status_text}\n{details}")
    
    def background_updater(self):
        """Uppdatera status i bakgrunden"""
        while True:
            time.sleep(60)  # Uppdatera varje minut
            
            # Uppdatera status
            old_status = self.current_status
            self.current_status = self.get_timeshift_status()
            
            # Uppdatera GUI om status ändrats
            if self.current_status != old_status:
                GObject.idle_add(self.update_indicator_icon)
                GObject.idle_add(self.update_menu_status)
                
                # Visa notifikation vid statusändring
                if old_status != 'unknown' and self.current_status != 'unknown':
                    if self.current_status == 'disabled' and old_status == 'enabled':
                        GObject.idle_add(
                            self.show_notification,
                            "Timeshift Inaktiverad",
                            "Automatiska backup är avstängda\nKommer återaktiveras vid omstart",
                            "dialog-warning"
                        )
                    elif self.current_status == 'enabled' and old_status == 'disabled':
                        GObject.idle_add(
                            self.show_notification,
                            "Timeshift Aktiverad",
                            "Automatiska backup är nu påslagna",
                            "system-run"
                        )
    
    def on_enable_clicked(self, widget):
        """Aktivera Timeshift direkt via konfigurationsfil"""
        self.modify_timeshift_config(enable=True)
        self.current_status = 'enabled'
        self.update_indicator_icon()
        self.update_menu_status()
        self.show_notification("Timeshift Aktiverad", 
                             "Automatiska backup är nu aktiverade", 
                             "system-run")
    
    def on_disable_clicked(self, widget):
        """Inaktivera Timeshift direkt via konfigurationsfil"""
        self.modify_timeshift_config(enable=False)
        self.current_status = 'disabled'
        self.update_indicator_icon()
        self.update_menu_status()
        self.show_notification("Timeshift Inaktiverad", 
                             "Automatiska backup är avstängda\nÅteraktiveras vid omstart", 
                             "dialog-warning")
    
    def modify_timeshift_config(self, enable=True):
        """Modifiera Timeshift-konfigurationen direkt"""
        try:
            with open('/etc/timeshift/timeshift.json', 'r') as f:
                content = f.read()
            
            # Ersätt alla schedule-inställningar
            if enable:
                # Aktivera alla
                content = content.replace('"schedule_daily" : "false"', '"schedule_daily" : "true"')
                content = content.replace('"schedule_weekly" : "false"', '"schedule_weekly" : "true"')
                content = content.replace('"schedule_monthly" : "false"', '"schedule_monthly" : "true"')
                content = content.replace('"schedule_boot" : "false"', '"schedule_boot" : "true"')
            else:
                # Inaktivera alla
                content = content.replace('"schedule_daily" : "true"', '"schedule_daily" : "false"')
                content = content.replace('"schedule_weekly" : "true"', '"schedule_weekly" : "false"')
                content = content.replace('"schedule_monthly" : "true"', '"schedule_monthly" : "false"')
                content = content.replace('"schedule_boot" : "true"', '"schedule_boot" : "false"')
            
            # Spara tillbaka
            with open('/etc/timeshift/timeshift.json', 'w') as f:
                f.write(content)
            
            print(f"Timeshift konfiguration {'aktiverad' if enable else 'inaktiverad'}")
            return True
            
        except Exception as e:
            print(f"Fel vid konfigurationsändring: {e}")
            # Fallback: använd befintligt script
            try:
                cmd = 'on' if enable else 'off'
                subprocess.run(['sudo', '/usr/local/bin/toggle-timeshift.sh', cmd], 
                             check=True, timeout=5)
                return True
            except:
                return False
    
    def open_timeshift_gui(self, widget):
        """Öppna det officiella Timeshift GUI:t"""
        try:
            subprocess.Popen(['timeshift-gtk'])
        except:
            self.show_notification("Fel", "Kunde inte öppna Timeshift GUI", "dialog-error")
    
    def open_desktop_app(self, widget):
        """Öppna den befintliga skrivbordsappen"""
        try:
            subprocess.Popen(['/usr/local/bin/timeshift-toggle-gui.sh'])
        except:
            self.show_notification("Fel", "Kunde inte öppna kontrollappen", "dialog-error")
    
    def show_notification(self, title, message, icon="dialog-information"):
        """Visa desktop-notification"""
        notification = Notify.Notification.new(title, message, icon)
        notification.set_urgency(Notify.Urgency.NORMAL)
        notification.show()
    
    def quit_indicator(self, widget):
        """Stäng av panelindikatorn"""
        print("Stänger av Timeshift Panel Indicator v2...")
        Notify.uninit()
        Gtk.main_quit()

def main():
    # Kontrollera att vi kan läsa Timeshift-konfigurationen
    if not os.path.exists('/etc/timeshift/timeshift.json'):
        print("Fel: Timeshift konfigurationsfil finns inte!")
        sys.exit(1)
    
    # Signalhantering
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Starta indikatorn
    indicator = TimeshiftPanelIndicator()
    
    # Starta GTK main loop
    Gtk.main()

if __name__ == "__main__":
    main()
