#!/Users/user/venv/bin/python
# Change the above line to your Python environment and leave blank if you have no virtual environment

import datetime
import sys
import swisseph as swe
import os
import subprocess
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from PIL import Image, ImageDraw
import base64
from io import BytesIO
import time
import math

DEBUG_MODE = False  # Set to True to enable debug prints

def dprint(*args, **kwargs):
    if DEBUG_MODE:
        print(*args, **kwargs)
        
script_directory = os.path.dirname(os.path.realpath(__file__))

def get_user_input():
    """Prompt the user to enter date, time, and location using AppleScript."""
    script = '''
    set userInput to display dialog "Enter Date, Time, and Location (e.g., 2025-04-20 22:27:00, 76.6548, 10.7867):" default answer "" buttons {"OK"} default button "OK"
    set inputText to text returned of userInput
    return inputText
    '''
    input_text = os.popen(f"osascript -e '{script}'").read().strip()
    return input_text

def മലയാളദിനം(input_date=None, LAT=10.7867, LON=76.6548): # Constants for Palakkad, Kerala
    if input_date is None:
        input_date = datetime.date.today()
    ALT = 0  # Meters
    IST_OFFSET = 5.5  # Hours

    # Malayalam month names based on zodiac signs (0-11)
    മാസങ്ങൾ = ["മേടം", "ഇടവം","മിഥുനം", "കർക്കിടകം","ചിങ്ങം", "കന്നി", "തുലാം", "വൃശ്ചികം", "ധനു","മകരം","കുംഭം", "മീനം"]
    
    swe.set_sid_mode(swe.SIDM_LAHIRI) #Otherwise 25 days shifting

    def get_sun_event_jd(jd_start_ut, event_type):
        """Calculate sunrise/sunset Julian Day with correct API parameters"""
        geopos = (LON, LAT, ALT)
        try:
            # Call rise_trans and get the full result
            result = swe.rise_trans(
                jd_start_ut,  # Julian day UT
                swe.SUN,      # Body (Sun)
                event_type,   # CALC_RISE or CALC_SET
                geopos,       # (lon, lat, alt)
                0, 0,         # Atmospheric pressure and temperature
                swe.FLG_SIDEREAL
            )

            

            # ✅ Extract the correct values
            ret_code = result[0]  # This should be 0 for success
            jd_event = result[1][0]  # The first value inside the second tuple

            

            # ✅ Ensure function call was successful
            if ret_code != 0:
                raise ValueError(f"Event calculation failed with error code {ret_code}")

            return jd_event
        except Exception as e:
            print(f"[ERROR] Exception in `get_sun_event_jd`: {e}")
            raise ValueError(f"Error in get_sun_event_jd: {e}")


    def jd_to_ist(jd_ut):
        
        """Convert Julian Day (UT) to IST datetime"""
        

    
        try:
            dt_utc = swe.revjul(jd_ut, swe.GREG_CAL)
            

            if not isinstance(dt_utc, tuple) or len(dt_utc) < 4:
                raise ValueError(f"[ERROR] Unexpected return from `swe.revjul()`: {dt_utc}")

            year, month, day, decimal_hours = dt_utc

            # Convert decimal hours into Hour, Minute, Second
            hour = int(decimal_hours)
            minute = int((decimal_hours - hour) * 60)
            second = int((((decimal_hours - hour) * 60) - minute) * 60)

            dt_utc = datetime.datetime(year, month, day, hour, minute, second)
            dt_ist = dt_utc + datetime.timedelta(hours=5, minutes=30)

            
            return dt_ist

        except Exception as e:
            print(f"[ERROR] Exception in `jd_to_ist()`: {e}")
            raise ValueError(f"Error in jd_to_ist(): {e}")


    # Convert input_date to UTC midnight to find sunrise
    dt_ist = datetime.datetime.combine(input_date, datetime.time(0, 0))
    dt_utc = dt_ist - datetime.timedelta(hours=IST_OFFSET)
    jd_start = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60)

    try:
        # Sunrise on input_date (start of Malayalam day)
        jd_sunrise = get_sun_event_jd(jd_start, swe.CALC_RISE)
        jd_sunset =  get_sun_event_jd(jd_start, swe.CALC_SET)
    except ValueError as e:
        raise RuntimeError(f"Sunrise calculation failed: {e}")

    # Get Sun's longitude at sunrise
    sun_pos = swe.calc_ut(jd_sunrise, swe.SUN, flags=swe.FLG_SIDEREAL)
    sun_lon = sun_pos[0][0]
    current_sign = int(sun_lon // 30)
    sign_start = current_sign * 30

    # Find previous Sankranti (zodiac entry) before this sunrise
    try:
        #dprint(f"[DEBUG] Finding Sankranti for sign {sign_start} before {jd_sunset}")
        cross_jd = get_previous_sankranti(sign_start, jd_sunset)
        #dprint(f"[DEBUG] Found Sankranti at JD: {cross_jd}")
    except Exception as e:
        raise RuntimeError(f"Failed to find Sankranti: {e}")

    # Convert Sankranti time to IST
    sankranti_ist = jd_to_ist(cross_jd)
    #dprint(f"[DEBUG] sankranti_ist: {sankranti_ist}") 
    sankranti_date_ist = sankranti_ist.date()
    #dprint(f"[DEBUG] sankranti_date_ist: {sankranti_date_ist}")
    

    # Get sunrise and sunset on Sankranti's local date
    sk_dt_ist = datetime.datetime.combine(sankranti_date_ist, datetime.time(0, 0))
    sk_dt_utc = sk_dt_ist - datetime.timedelta(hours=IST_OFFSET)
    sk_jd_start = swe.julday(sk_dt_utc.year, sk_dt_utc.month, sk_dt_utc.day, sk_dt_utc.hour)

    try:
        # Calculate sunrise and sunset on Sankranti's local date
        sk_jd_sunrise = get_sun_event_jd(sk_jd_start, swe.CALC_RISE)
        sk_jd_sunset = get_sun_event_jd(sk_jd_start, swe.CALC_SET)
    except ValueError as e:
        raise RuntimeError(f"Sunrise/sunset calculation failed: {e}")

    # Determine if Sankranti occurred after sunset
    #dprint(f"[DEBUG] cross_jd & sk_jd_sunset are : {cross_jd}, {sk_jd_sunset}")
    if cross_jd >= sk_jd_sunset:
        first_day = sankranti_date_ist + datetime.timedelta(days=1)
    #elif cross_jd >= sk_jd_sunrise:
    #    first_day = sankranti_date_ist #redundant
    else:
        first_day = sankranti_date_ist
    
    #dprint(f"[DEBUG] first_day & sankranti_date_ist are : {first_day}, {sankranti_date_ist}")

    # Calculate Malayalam day number
    malayalam_day = (input_date - first_day).days + 1
    #dprint(f"[DEBUG] input_date & first_day are : {input_date}, {first_day}")
    #dprint(f"[DEBUG] malayalam_day : {malayalam_day}")
    if malayalam_day < 1:
        raise RuntimeError("Day calculation error: negative day")

    # Get month name
    malayalam_month = മാസങ്ങൾ[current_sign]
    
    greg_year = first_day.year
    greg_month = input_date.month
    
    # കൊല്ലവർഷം കണക്കാക്കൽ (ചിങ്ങം 1)
    if current_sign >= 4 and current_sign < 9:  # ചിങ്ങം(4) തൊട്ട് ധനു (7) വരെ.
        കൊല്ലവർഷം = greg_year - 824
    else:  # Medam(0) to Karkidakam(3) or Meenam(9) to Medam(11)
        കൊല്ലവർഷം = greg_year - 825
    
    # കൃഷ്ണവർഷം കണക്കാക്കൽ (മേടം 1)
    if current_sign >= 0 and current_sign < 9:  # മേടം(0) തൊട്ട് ധനു (7) വരെ. ധനുവിന് വേറെയായ് കൈകാര്യം ചെയ്യേണ്ട ആവശ്യമില്ല, എന്തെന്നാൽ greg_year കണക്കാകപെടുക സൗരമാസം തുടക്കാനുസൃതമാണ്. അത് Dec15 തന്നെയാണ് കാണിക്കുക, January മാസദിനമാണെങ്കിൽ പോലും.
        കൃഷ്ണവർഷം = greg_year + 3102
    else:  # മകരം(9) to മീനം(11)
        കൃഷ്ണവർഷം = greg_year + 3101
    
    #ചന്ദ്രനെ വരക്കുന്നു. ആദ്യം Get tithi at sunrise
    current_tithi = get_tithi(jd_sunrise)
    moon_path = generate_moon_image(current_tithi)
    #return f"{'     　 : '} {കൃഷ്ണവർഷം} {malayalam_month} {malayalam_day:02d} | image={moon_image}\n" #no space comes before year if something like ":" is not used.
    സമ്പൂർണമലയാളദിനം = f"{കൃഷ്ണവർഷം} {malayalam_month} {malayalam_day:02d}"
    return സമ്പൂർണമലയാളദിനം, moon_path


def get_previous_sankranti(sign_start, jd_sunset):
    """Find the previous Sankranti (zodiac entry) before or on the given Julian Day."""
    # Step 1: Check if Sankranti occurs on the input date (between sunset of the previous day and sunset of the input date)
    try:
        # Check if the Sun crosses the sign boundary between jd_sunset - 1 day and jd_sunset
        sun_pos_before = swe.calc_ut(jd_sunset - 1.0, swe.SUN, flags=swe.FLG_SIDEREAL)
        sun_lon_before = sun_pos_before[0][0]
        sun_pos_after = swe.calc_ut(jd_sunset, swe.SUN, flags=swe.FLG_SIDEREAL)
        sun_lon_after = sun_pos_after[0][0]

        # If the Sun crosses the sign boundary, return the exact time of crossing
        if int(sun_lon_before // 30) != int(sun_lon_after // 30):
            # Use binary search to find the exact crossing time
            low = jd_sunset - 1.0
            high = jd_sunset
            precision = 0.0001  # Stop when the step size is smaller than this

            while high - low > precision:
                mid = (low + high) / 2
                sun_pos_mid = swe.calc_ut(mid, swe.SUN, flags=swe.FLG_SIDEREAL)
                sun_lon_mid = sun_pos_mid[0][0]

                if int(sun_lon_mid // 30) == int(sun_lon_before // 30):
                    low = mid
                else:
                    high = mid

            return (low + high) / 2  # Return the approximate crossing time
    except Exception as e:
        raise RuntimeError(f"Error checking for Sankranti on input date: {e}")

    # Step 2: If no Sankranti is found on the input date, search backward in time
    step = 1.0  # Step size in days for searching backward
    max_steps = 40  # Maximum steps to avoid infinite loops
    current_jd = jd_sunset - 1.0  # Start searching from sunset of the previous day

    for _ in range(max_steps):
        try:
            # Check if the Sun is crossing the sign boundary
            sun_pos = swe.calc_ut(current_jd, swe.SUN, flags=swe.FLG_SIDEREAL)
            sun_lon = sun_pos[0][0]
            current_sign = int(sun_lon // 30)

            if current_sign == sign_start // 30:
                # We are in the target sign, so the previous Sankranti is behind us
                current_jd -= step
            else:
                # We have crossed the boundary, so the Sankranti is between current_jd and current_jd + step
                # Refine the search with smaller steps
                step /= 10.0
                if step < 0.0001:  # Stop when we have sufficient precision
                    return current_jd
        except Exception as e:
            raise RuntimeError(f"Error finding Sankranti: {e}")

    raise RuntimeError("Failed to find Sankranti within the allowed steps")




def get_tithi(jd):
    """Calculate tithi (0-29) from Julian date"""
    sun = swe.calc_ut(jd, swe.SUN, flags=swe.FLG_SIDEREAL)[0][0]
    moon = swe.calc_ut(jd, swe.MOON, flags=swe.FLG_SIDEREAL)[0][0]
    return int(((moon - sun) % 360) // 12)

def generate_moon_image(phase, size=142, output_size=18):
    """Generate moon phase image with correct shading for waxing/waning"""
    # Convert phase (0-29) to illumination fraction (0.0-1.0)
    # Full moon (14) = 1.0, new moon (29/0) = 0.0
    illumination = 1 - abs(phase - 14) / 14
    
    # Determine if waxing (ശുക്ല) or waning (കൃഷ്ണ)
    waxing = phase < 15
    
    # Create image
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = (size//2, size//2)
    radius = size//2 - 1
    
    # Draw full white circle (moon)
    draw.ellipse((center[0]-radius, center[1]-radius, 
                center[0]+radius, center[1]+radius), 
                fill='white')
    
    # Draw shadow based on illumination
    shadow_color = (51, 51, 51, 178)  # #333333 with ~70% opacity
    
    for y in range(radius):
        x = math.sqrt(radius**2 - y**2)
        x = round(x)
        
        if waxing:
            # Waxing (ശുക്ല): shadow on the LEFT
            X_left = center[0] - x
            shade_width = round(2 * x * (1 - illumination))
            X_right = X_left + shade_width
        else:
            # Waning (കൃഷ്ണ): shadow on the RIGHT
            X_right = center[0] + x
            shade_width = round(2 * x * (1 - illumination))
            X_left = X_right - shade_width
        
        Y_top = center[1] - y
        Y_bottom = center[1] + y
        
        # Draw shadow lines
        if shade_width > 0:
            draw.line((X_left, Y_top, X_right, Y_top), fill=shadow_color)
            if Y_top != Y_bottom:
                draw.line((X_left, Y_bottom, X_right, Y_bottom), fill=shadow_color)
    
    # Outline
    draw.ellipse((center[0]-radius, center[1]-radius, 
                center[0]+radius, center[1]+radius), 
                outline='white', width=1)
    
    img = img.resize((output_size, output_size), Image.LANCZOS)
    # Convert to base64
    #buffered = BytesIO()
    image_path = os.path.join(script_directory, 'moon_output.png')
    img.save(image_path, format="PNG", optimize=True, compress_level=9)
    time.sleep(1)
    #return base64.b64encode(buffered.getvalue()).decode('utf-8')
    return image_path



def തിഥി_നക്ഷത്ര_വാരം(input_date=None, LAT=25.3176, LON=82.9739):
    """
    Calculate Tithi and Nakshatra for the given date, along with their end times.
    Returns: {"tithi": "Shukla Pratipada (HH:MM വരെ)", "nakshatra": "Ashwini (HH:MM വരെ)"}
    """
    calc_date = input_date
    if input_date is None:
        # If no input_date is provided, use the current date and time
        calc_date = datetime.datetime.now()
    elif isinstance(input_date, datetime.date):
        # If input_date is a date object, convert it to a datetime object with time set to 00:00:00
        calc_date = datetime.datetime.combine(input_date, datetime.time(0, 0))
                                               
    ALT = 0  # Meters
    IST_OFFSET = 5.5  # Hours

    # Tithi names (0-29)
    തിഥികൾ = [
        "ശുക്ല പ്രതിപദ", "ശുക്ല ദ്വിതീയ", "ശുക്ല തൃതീയ", "ശുക്ല ചതുർഥി", "ശുക്ല പഞ്ചമി",
        "ശുക്ല ഷഷ്ഠി", "ശുക്ല സപ്തമി", "ശുക്ല അഷ്ടമി", "ശുക്ല നവമി", "ശുക്ല ദശമി",
        "ശുക്ല ഏകാദശി", "ശുക്ല ദ്വാദശി", "ശുക്ല ത്രയോദശി", "ശുക്ല ചതുർദശി", "പൗർണമി",
        "കൃഷ്ണ പ്രതിപദ", "കൃഷ്ണ ദ്വിതീയ", "കൃഷ്ണ തൃതീയ", "കൃഷ്ണ ചതുർഥി", "കൃഷ്ണ പഞ്ചമി",
        "കൃഷ്ണ ഷഷ്ഠി", "കൃഷ്ണ സപ്തമി", "കൃഷ്ണ അഷ്ടമി", "കൃഷ്ണ നവമി", "കൃഷ്ണ ദശമി",
        "കൃഷ്ണ ഏകാദശി", "കൃഷ്ണ ദ്വാദശി", "കൃഷ്ണ ത്രയോദശി", "കൃഷ്ണ ചതുർദശി", "അമാവാസി"
    ]

    # Nakshatra names (0-26)
    നക്ഷത്രങ്ങൾ = [
        "അശ്വതി", "ഭരണി", "കാർത്തിക", "രോഹിണി", "മകയിരം", "തിരുവാതിര",
        "പുണർതം", "പൂയം", "ആയില്യം", "മകം", "പൂരം", "ഉത്രം", "അത്തം",
        "ചിത്തിര", "ചോതി", "വിശാഖം", "അനിഴം", "തൃക്കേട്ട", "മൂലം",
        "പൂരാടം", "ഉത്രാടം", "തിരുവോണം", "അവിട്ടം", "ചതയം", "പൂരുരുട്ടാതി",
        "ഉത്രട്ടാതി", "രേവതി"
    ]
    
    വാരങ്ങൾ = {
        "Sunday": "ഞായർ",
        "Monday": "തിങ്കൾ",
        "Tuesday": "ചൊവ്വ",
        "Wednesday": "ബുധൻ",
        "Thursday": "വ്യാഴം",
        "Friday": "വെള്ളി",
        "Saturday": "ശനി"
    }

    day_of_week = calc_date.strftime("%A")  # Get English weekday name
    വാരം = വാരങ്ങൾ[day_of_week]  # Convert to Malayalam
    
    def get_sun_event_jd(jd_start_ut, event_type):
        """Calculate sunrise/sunset Julian Day."""
        geopos = (LON, LAT, ALT)
        result = swe.rise_trans(jd_start_ut, swe.SUN, event_type, geopos, 0, 0, swe.FLG_SIDEREAL)
        return result[1][0]

    def jd_to_ist(jd_ut):
        """Convert Julian Day (UT) to IST datetime."""
        # Convert JD to UTC datetime
        dt_utc = swe.revjul(jd_ut, swe.GREG_CAL)
        # Extract year, month, day, and fractional hours
        year = int(dt_utc[0])
        month = int(dt_utc[1])
        day = int(dt_utc[2])
        fractional_hours = dt_utc[3]
        # Convert fractional hours to hours, minutes, seconds
        hours = int(fractional_hours)
        fractional_minutes = (fractional_hours - hours) * 60
        minutes = int(fractional_minutes)
        seconds = int((fractional_minutes - minutes) * 60)
        # Create UTC datetime object
        dt_utc = datetime.datetime(year, month, day, hours, minutes, seconds)
        # Convert to IST (UTC + 5:30)
        dt_ist = dt_utc + datetime.timedelta(hours=5, minutes=30)
        return dt_ist

    def find_transition(start_jd, end_jd, get_value):
        """Binary search to find when a value changes between start_jd and end_jd."""
        precision = 0.00001  # ~1 second
        initial = get_value(start_jd)
        final = get_value(end_jd)

        if initial == final:
            return end_jd  # No transition

        for _ in range(20):  # Max 20 iterations (~1 microsecond precision)
            mid_jd = (start_jd + end_jd) / 2
            mid_val = get_value(mid_jd)
            if mid_val == initial:
                start_jd = mid_jd
            else:
                end_jd = mid_jd
            if (end_jd - start_jd) < precision:
                break
        return end_jd

    # Get sunrise and next day's sunrise
    dt_ist = datetime.datetime.combine(calc_date, datetime.time(0, 0))
    dt_utc = dt_ist - datetime.timedelta(hours=IST_OFFSET)
    jd_start = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60)
    jd_sunrise = get_sun_event_jd(jd_start, swe.CALC_RISE)
    jd_next_sunrise = get_sun_event_jd(jd_start + 1, swe.CALC_RISE)
    
    # Calculate Nakshatra
    def get_nakshatra(jd):
        moon = swe.calc_ut(jd, swe.MOON, flags=swe.FLG_SIDEREAL)[0][0]
        return int((moon % 360) // (360 / 27))
    
    if input_date:
        dt_ip = input_date 
        dt_utc = dt_ip - datetime.timedelta(hours=IST_OFFSET)
        jd_input = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600)
        current_tithi = get_tithi(jd_input)
        current_nakshatra = get_nakshatra(jd_input)
        return f"{വാരം}\n{തിഥികൾ[current_tithi]}\n{നക്ഷത്രങ്ങൾ[current_nakshatra]}"
    else:
        tithi_start = get_tithi(jd_sunrise)
        nakshatra_start = get_nakshatra(jd_sunrise)
        adjust_time = lambda time_str: (datetime.datetime.strptime(time_str, "%H:%M") - datetime.timedelta(hours=6, minutes=30)).strftime("%H:%M")
        tithi_adjusted_end = adjust_time(jd_to_ist(find_transition(jd_sunrise, jd_next_sunrise, get_tithi)).strftime("%H:%M"))
        nakshatra_adjusted_end = adjust_time(jd_to_ist(find_transition(jd_sunrise, jd_next_sunrise, get_nakshatra)).strftime("%H:%M"))
        #moon_image = generate_moon_image(tithi_start)
        return (
            f"{വാരം}\n"
            #f"| image={moon_image}\n"
            f"{തിഥികൾ[tithi_start]} ({tithi_adjusted_end} വരെ)\n"
            f"{നക്ഷത്രങ്ങൾ[nakshatra_start]} ({nakshatra_adjusted_end} വരെ)"
        )
            
        
  


കാണണം = 1

if കാണണം:
    import plotly.graph_objects as go
    from timezonefinder import TimezoneFinder
    import datetime
    import pytz
    import io
    import base64

    def encode_image(image_path): #only if image is being displayed.
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    
    user_input = 0 #initializing 
    
    def timezone_adjust(custom_dt, latitude, longitude):
        tf = TimezoneFinder() # Initialize TimezoneFinder
        timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
        if timezone_str is None:
            raise ValueError("Could not determine the time zone for the given coordinates.")
        timezone = pytz.timezone(timezone_str)
        local_dt = timezone.localize(custom_dt)
        #offseting hours by longitude / 15 won't work as India does not have local timezone
        dt = local_dt.astimezone(pytz.utc) #UTC conversion
        return dt
    
    # Function to get planet positions (unchanged)
    def get_planet_positions(custom_dt=None, longitude=75.7681, latitude=23.1765): # Ujjain latitude
        planets = {
            "രവി": swe.SUN,
            "ചന്ദ്ര": swe.MOON,
            "കുജ": swe.MARS,
            "ബുധ": swe.MERCURY,
            "ഗുരു": swe.JUPITER,
            "ശുക്ര": swe.VENUS,
            "മന്ദ": swe.SATURN,
        }

        if custom_dt:
            dt = timezone_adjust(custom_dt, latitude, longitude)            
        else:
            dt = datetime.datetime.now(datetime.UTC)  # Fallback to current time. Can't use system time as I use Hindu time.
            #dt = datetime.datetime.now(datetime.UTC)+ datetime.timedelta(days=66) #to offset days to check planet positions
            
    
        #print(f"UTC Time: {dt}")

        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)
        
        elevation = 0  # Sea level
        
        swe.set_sid_mode(swe.SIDM_LAHIRI)  # Lahiri ayanamsa
        swe.set_topo(longitude, latitude, elevation) #Don't understand, something like Ujjain as topocentric location for future calls.
    
        positions = {}
    
        for planet, planet_id in planets.items():
            pos, ret = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
            lon = pos[0]
            positions[planet] = {"longitude": lon}
            #if planet == "കുജ":
            #    print(f"കുജ is at {lon:.2f}°")
                

    
        rahu_pos, ret = swe.calc_ut(jd, swe.TRUE_NODE, swe.FLG_SIDEREAL)
        rahu_lon = rahu_pos[0]
        ketu_lon = (rahu_lon + 180) % 360
    
        positions["സർപ്പി"] = {"longitude": rahu_lon}
        positions["ശിഖി"] = {"longitude": ketu_lon}
        
        # Calculate Lagna (Ascendant)
        house_system = b'W'  # Whole Sign Houses. If I use G,Sripati (Bhav Chalit) system, then lagna shifts to Kumbha.
        cusp, ascmc = swe.houses(jd, latitude, longitude, house_system)
        lagna_lon = cusp[0] % 360  # Normalized 1st house cusp
        
        positions["ലഗ്നം"] = {"longitude": lagna_lon}
        #print(f"ലഗ്നം is at {lagna_lon}°")
    
        return positions

    # Updated function to generate the chart with 12 divisions
    def generate_chart(positions, user_input=None, place_name="ഉജ്ജൈനി"):
    
    
        f = "Noto Sans Malayalam"  # Font family
        r = 3  # Font size reduction as I increase or decrease the chart size

    
        fig = go.Figure()

        # Cosmic background gradient
        fig.update_layout(
            paper_bgcolor='rgb(5,10,30)',
            plot_bgcolor='rgba(5,10,30,0.8)'
        )

        # Add celestial background elements
        fig.add_shape(type="circle",
            xref="paper", yref="paper",
            x0=0.45, y0=0.45, x1=0.55, y1=0.55,
            line=dict(color="rgba(255,255,255,0.1)", width=2)
        )
    
        num_rashis = 12
        rashis = ['മേടം', 'ഇടവം', 'മിഥുനം', 'കർക്കിടകം', 'ചിങ്ങം', 'കന്നി', 
                'തുലാം', 'വൃശ്ചികം', 'ധനു', 'മകരം', 'കുംഭം', 'മീനം']
    
        nakshatras = [
            'അശ്വതി', 'ഭരണി', 'കാർത്തിക', 'രോഹിണി', 'മകയിരം', 'തിരുവാതിര',
            'പുണർത്ഥം', 'പൂയം', 'ആയില്യം', 'മകം', 'പൂരം', 'ഉത്രം',
            'അത്തം', 'ചിത്ര', 'ചോതി', 'വിശാഖം', 'അനിഴം', 'തൃക്കേട്ട',
            'മൂലം', 'പൂരാടം', 'ഉത്രാടം', 'തിരുവോണം', 'അവിട്ടം', 'ചതയം',
            'പൂരുരുട്ടാതി', 'ഉത്രട്ടാതി', 'രേവതി'
        ]

        planet_colors = {
            "രവി": "#FF6B35",       # Sunset Orange
            "ചന്ദ്ര": "#F4F4F8",     # Moon White
            "കുജ": "#D62828",       # Mars Red
            "ബുധ": "#06D6A0",       # Mercury Teal
            "ഗുരു": "#FFD166",       # Jupiter Gold
            "ശുക്ര": "#C4C4C4",      # Venus Silver
            "മന്ദ": "#2B2D42",       # Saturn Navy
            "സർപ്പി": "#2323FF",    # Rahu Cyan
            "ശിഖി": "#7B7B7C",       # Ketu Graphite
            "ലഗ്നം": "#FF007F"       # Lagna Pink
        }

        # Add Nakshatra outer ring
        # Create Nakshatra sectors with starry effect
        nakshatra_angle = 360/27
        for i in range(27):
            start_angle = i * nakshatra_angle
            end_angle = (i+1) * nakshatra_angle
        
            fig.add_trace(go.Scatterpolar(
                r=[1.3, 1.45, 1.45, 1.3],
                theta=[start_angle, start_angle, end_angle, end_angle],
                mode='lines',
                fill='toself',
                line=dict(width=0),
                fillcolor='rgba(76, 201, 240, 0.15)' if i%2 == 0 else 'rgba(255, 255, 255, 0.08)',
                showlegend=False
            ))

        # Constellation line connections
        fig.add_trace(go.Scatterpolar(
            r=[1.5]*360,
            theta=list(range(360)),
            mode='lines',
            line=dict(color="rgba(255,255,255,0.05)", width=1),
            showlegend=False
        ))

        # Enhanced Nakshatra names with glow effect
        fig.add_trace(go.Scatterpolar(
            r=[1.47]*27,
            theta=[i*nakshatra_angle + nakshatra_angle/2 for i in range(27)],
            mode='text',
            text=nakshatras,
            textfont=dict(
                family=f,
                size=13-r,
                color=['#4CC9F0' if i%2==0 else '#4DC0F0' for i in range(27)],
                weight='bold'
            ),
            showlegend=False
        ))

        # Glowing Rashi labels
        fig.add_trace(go.Scatterpolar(
            r=[1.15]*12,
            theta=[i*30 + 15 for i in range(12)],
            mode='text',
            text=rashis,
            textfont=dict(
                family=f,
                size=14-r,
                color='#cfa1a0',
                weight='bold'
            ),
            showlegend=False
        ))

        # Planetary bodies with halo effect
        for planet, data in positions.items():
            lon = data['longitude']
            rad = lon % 360
        
            # Main planet marker
            fig.add_trace(go.Scatterpolar(
                r=[0.7],
                theta=[rad],
                mode='markers+text',
                marker=dict(
                    symbol='circle',
                    size=20,
                    color=planet_colors[planet],
                    line=dict(width=2, color='rgba(255,255,255,0.5)')
                ),
                text=[planet],
                textfont=dict(
                    family=f,
                    size=15-r,
                    color=planet_colors[planet],
                    weight='bold'
                ),
                textposition='middle right',
                showlegend=False
            ))
        
            # Halo effect
            fig.add_trace(go.Scatterpolar(
                r=[0.7],
                theta=[rad],
                mode='markers',
                marker=dict(
                    symbol='circle',
                    size=28,
                    color=planet_colors[planet],
                    opacity=0.15
                ),
                showlegend=False
            ))
        
        if user_input:
            custom_dt_str, lon, lat = user_input
            custom_dt = datetime.datetime.strptime(custom_dt_str, "%Y-%m-%d %H:%M:%S")
            adjusted_dt = custom_dt - datetime.timedelta(hours=6, minutes=30)
            input_Hindu_time = adjusted_dt.strftime("%H:%M")
            input_Hindu_day = മലയാളദിനം(custom_dt.date(),lat,lon)
            display_time = f"[{input_Hindu_day}] {input_Hindu_time}"
            
        else:
            display_time = datetime.datetime.now().strftime("%H:%M")
        
        location = f"{place_name} ലഗ്നം"
        
        # Final artistic layout
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',  # Fully transparent background
            plot_bgcolor='rgba(0,0,0,0)',   # Fully transparent plotting area
            title=dict( #delete this whole title block with comma
                text=f"<sub><sub>{display_time} മണി, {location}</sub></sub>",
                font=dict(
                    family="Noto Sans Malayalam",
                    size=32,
                    color='#FFD166',
                    weight='bold'
                ),
                x=0.5,
                y=0.95
            ),
            polar=dict(
                radialaxis=dict(visible=False, range=[0, 1.5]),  # Ensure full fit
                angularaxis=dict(
                    showline=True,
                    showgrid=True,
                    rotation=120, #ഇപ്പോൾ ആണ് കേരളജ്യോത്സമാവുന്നത്. ഭൂമി 0അംശം (മുകളിൽ). അതിന്റെ ഇടത് ചൊവ്വ. അങ്ങിനെയാണല്ലൊ ആകാശത്ത്. സൂര്യന്റെ അടുത്ത് ബുധൻ, പിന്നെ, ശുക്രൻ. അത് കഴിഞ്ഞ് ചൊവ്വ വരുന്ന മുമ്പ് ഭൂമി ഉള്ളതിനാൽ ചൊവ്വയെ (മേടത്തെ) 30 അംശം ഇടത്തോട്ട് മാറ്റി.
                    direction="clockwise",
                    tickvals=list(range(0, 360, 30)),
                    gridcolor='rgba(255,255,255,0.1)',
                    linecolor='rgba(255,255,255,0.2)'
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(t=20, b=20, l=20, r=20),  # Reduce empty space
            width=500,  # Reduce image size
            height=500
        )

        image_path = os.path.join(script_directory, 'chart_output.png')
        fig.write_image(image_path)  # Save to disk
        time.sleep(1)
        #with open(image_path, "rb") as image_file:
        #    image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
        return image_path
        
        image_stream = io.BytesIO()
        fig.write_image(image_stream, format="png", width=500, height=500)
        image_base64 = base64.b64encode(image_stream.getvalue()).decode("utf-8")
        return image_base64


def get_lat_lon_from_place(place_name):
    """Convert a place name to latitude & longitude using geopy."""
    geolocator = Nominatim(user_agent="swiftbar_location_picker",timeout=3)
    location = geolocator.geocode(place_name)

    if location:
        return location.latitude, location.longitude
    else:
        raise ValueError(f"അറിയാത്ത സ്ഥലം: {place_name}")



def main():
    try:
        today_solar_date, moon_path = മലയാളദിനം()
        print(today_solar_date)
        print("IMAGE-FILE: " + moon_path)
        print("---")

        # Option to input custom date, time, and location
        '''#To activate custom date astrological chart, ഈ ഭാഗത്തെ ഉത്തേജിപിക്കൂ.
        try:
            result = subprocess.run(  # Run AppleScript (osascript) via subprocess
                [
                    "osascript", "-e",
                    'display dialog "ദിവസ-സമയ-സ്ഥല വിവരങ്ങൾ (ഉദാ; 2022-04-18 16:55, വാരണാസി):" default answer "" buttons {"OK"} default button "OK"'
                ],
                capture_output=True, text=True, timeout=30  # Timeout set to 30 seconds
            )
            output = result.stdout.strip()

        except subprocess.TimeoutExpired:
            print("സമയപരിധി കഴിഞ്ഞു! ഇപ്പോഴത്തെ ജ്യോതിഷനില കാണിക്കുന്നു.")
            output = ""  # Treat it as no input
        '''
        output = ""#text returned:2025-04-13 07:27, പാലക്കാട്"
        #"text returned:1994-02-02 07:27, പാലക്കാട്"
        #"text returned:1995-01-06 22:48, വാരണാസി"
        #"text returned:2022-04-18 16:55, വാരണാസി"
        # Extract the user input (if any)
        if "text returned:" in output:
            user_input_str = output.split("text returned:")[-1].strip()
            
            # Check if the input is empty
            if not user_input_str:
                print("ഇപ്പോഴത്തെ ജ്യോതിഷനില കാണിക്കുന്നു.")
                user_input = None
            else:
                user_input_parts = user_input_str.split(",")

                # Check if the input has the correct format
                if len(user_input_parts) != 2:
                    print("തെറ്റായ ഘടന തന്നതിനാൽ ഇപ്പോഴത്തെ ജ്യോതിഷനില കാണിക്കുന്നു")
                    user_input = None
                else:
                    custom_dt_str = user_input_parts[0].strip()
                    place_name = user_input_parts[1].strip()
                    
                    # Append ":00" if seconds are missing
                    if len(custom_dt_str.split(":")) == 2:
                        custom_dt_str += ":00"

                    try:
                        custom_dt = datetime.datetime.strptime(custom_dt_str, "%Y-%m-%d %H:%M:%S")
                        lat, lon = get_lat_lon_from_place(place_name)  # Get latitude & longitude from place name
                        user_input = (custom_dt.strftime("%Y-%m-%d %H:%M:%S"), lon, lat)
                    except ValueError as e:
                        print(f"തെറ്റായ ഇൻപുട്ട്: {e}")
                        user_input = None
        else:
            user_input = None
        
        if user_input:
            custom_dt_str, lon, lat = user_input
            custom_dt = datetime.datetime.strptime(custom_dt_str, "%Y-%m-%d %H:%M:%S")      
            selected_solar_date = മലയാളദിനം(custom_dt.date(), lat, lon)
            print(f"തിരഞ്ഞെടുത്ത ദിനം: {selected_solar_date}")
            translated_description = തിഥി_നക്ഷത്ര_വാരം(custom_dt, lat, lon)
        else:
            translated_description = തിഥി_നക്ഷത്ര_വാരം()

        print(translated_description)
        print("RIGHT: [ഹിന്ദുസമയപ്രകാരം കണക്കാക്കിയത്")
        print("RIGHT: ഹിന്ദു 00:00 = കൃസ്ത്യൻ 06:30AM]") #ഉജ്ജൈനിയുടെ സമയം, UTC +5, അപ്പോഴുള്ള 30 മിനിറ്റ്, അത് കൂടാതെ 6 മണിക്കൂർ കൂട്ടൽ.
        

        if കാണണം:
            if user_input:
                positions = get_planet_positions(custom_dt, lon, lat)
                image_path = generate_chart(positions, user_input, place_name)
            else:
                positions = get_planet_positions()
                image_path = generate_chart(positions)
                            
            #dprint("IMAGE: iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=") # 1x1 transparent pixel base64 PNG
            print("IMAGE-FILE: " + image_path)


    except Exception as e:
        print("Error: Check script")
        print("---")
        print(str(e))



if __name__ == "__main__":
    main()