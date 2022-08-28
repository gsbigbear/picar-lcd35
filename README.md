# picar-lcd35


LCD-35

kiosk

    sudo apt-get -y install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox chromium-browser

auto-start

    sudo raspi-config
    
    1  system-option
    S5 boot/autologin
    B2 Console Autologin
 
 
sudo nano /etc/xdg/openbox/autostart
    
    xset -dpms            # turn off display power management system
    xset s noblank        # turn off screen blanking
    xset s off            # turn off screen saver
    # Remove exit errors from the config files that could trigger a warning

    sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/'Local State'

    sed -i 's/"exited_cleanly":false/"exited_cleanly":true/; s/"exit_type":"[^"]\+"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences
    
    # Run Chromium in kiosk mode
    chromium-browser  --noerrdialogs --disable-infobars --kiosk $KIOSK_URL
    
    
sudo nano /etc/xdg/openbox/environment

    export KIOSK_URL=http://localhost


sudo nano ~/.bash_rc
    
    [[ -z $DISPLAY && $XDG_VTNR -eq 1 ]] && startx -- -nocursor


Fix - X launch
    
    sudo mv /usr/share/X11/xorg.conf.d/99-fbturbo.conf ~


lcd

    git clone https://github.com/goodtft/LCD-show.git
    chmod -R 755 LCD-show
    cd LCD-show/
    sudo ./LCD35-show
    
    
