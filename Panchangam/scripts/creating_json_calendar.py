#!/Users/user/venv/bin/python
import datetime
import swisseph as swe

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

    def get_previous_sankranti(jd_end):
        """Find the previous Sankranti (zodiac entry) before the given Julian Day and return (jd_sankranti, entered_sign)"""
        കൃത്യത = 0.0003 #ഒരു വിനാഴിക കൃത്യത 
        # Check for sankranti in the interval [jd_end - 1, jd_end]
        
        def find_crossing(jd_low, jd_high, sign_low):
            """Helper for binary search between two points"""
            low, high = jd_low, jd_high
            while high - low > കൃത്യത:
                mid = (low + high) / 2
                sun_pos = swe.calc_ut(mid, swe.SUN, flags=swe.FLG_SIDEREAL)
                sign_mid = int(sun_pos[0][0] // 30)
            
                if sign_mid == sign_low:
                    low = mid
                else:
                    high = mid
            return (low + high) / 2
        
        try:
            sun_pos_before = swe.calc_ut(jd_end - 1.0, swe.SUN, flags=swe.FLG_SIDEREAL)
            sign_before = int(sun_pos_before[0][0] // 30)
            sun_pos_after = swe.calc_ut(jd_end, swe.SUN, flags=swe.FLG_SIDEREAL)
            sign_after = int(sun_pos_after[0][0] // 30)

            if sign_before != sign_after:
                cross_jd = find_crossing(jd_end - 1.0, jd_end, sign_before)
                return cross_jd, sign_after
        except Exception as e:
            raise RuntimeError(f"Error checking for sankranti: {e}")

        # Search backward in time (up to 40 days)
        for i in range(1, 41):
            try:
                jd_start = jd_end - (i + 1)
                jd_mid = jd_end - i
            
                sun_pos_1 = swe.calc_ut(jd_start, swe.SUN, flags=swe.FLG_SIDEREAL)
                sign1 = int(sun_pos_1[0][0] // 30)
                sun_pos_2 = swe.calc_ut(jd_mid, swe.SUN, flags=swe.FLG_SIDEREAL)
                sign2 = int(sun_pos_2[0][0] // 30)

                if sign1 != sign2:
                    cross_jd = find_crossing(jd_start, jd_mid, sign1)
                    return cross_jd, sign2
            except Exception as e:
                raise RuntimeError(f"Error during backward search: {e}")

        raise RuntimeError("No sankranti found within 40 days")

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


    # Find previous Sankranti and the entered sign
    try:
        cross_jd, entered_sign = get_previous_sankranti(jd_sunset)
        sankranti_ist = jd_to_ist(cross_jd)
        sankranti_date_ist = sankranti_ist.date()
    except Exception as e:
        raise RuntimeError(f"Failed to find Sankranti: {e}")

    # Get sunrise and sunset on Sankranti's local date
    sk_dt_ist = datetime.datetime.combine(sankranti_date_ist, datetime.time(0, 0))
    sk_dt_utc = sk_dt_ist - datetime.timedelta(hours=IST_OFFSET)
    sk_jd_start = swe.julday(sk_dt_utc.year, sk_dt_utc.month, sk_dt_utc.day, sk_dt_utc.hour)

    try:
        sk_jd_sunset = get_sun_event_jd(sk_jd_start, swe.CALC_SET)
    except ValueError as e:
        raise RuntimeError(f"Sunset calculation failed: {e}")

    # Adjust first day if Sankranti occurred after sunset
    if cross_jd >= sk_jd_sunset:
        first_day = sankranti_date_ist + datetime.timedelta(days=1)
    else:
        first_day = sankranti_date_ist

    # Calculate Malayalam day number
    malayalam_day = (input_date - first_day).days + 1
    if malayalam_day < 1:
        raise RuntimeError("Day calculation error: negative day")

    # Get month name from entered_sign
    malayalam_month = മാസങ്ങൾ[entered_sign]
    
    greg_year = first_day.year
    greg_month = input_date.month
    
    # കൊല്ലവർഷം കണക്കാക്കൽ (ചിങ്ങം 1)
    if entered_sign >= 4 and entered_sign < 9:  # ചിങ്ങം(4) തൊട്ട് ധനു (7) വരെ.
        കൊല്ലവർഷം = greg_year - 824
    else:  # Medam(0) to Karkidakam(3) or Meenam(9) to Medam(11)
        കൊല്ലവർഷം = greg_year - 825
    
    # കൃഷ്ണവർഷം കണക്കാക്കൽ (മേടം 1)
    if entered_sign >= 0 and entered_sign < 9:  # മേടം(0) തൊട്ട് ധനു (7) വരെ. ധനുവിന് വേറെയായ് കൈകാര്യം ചെയ്യേണ്ട ആവശ്യമില്ല, എന്തെന്നാൽ greg_year കണക്കാകപെടുക സൗരമാസം തുടക്കാനുസൃതമാണ്. അത് Dec15 തന്നെയാണ് കാണിക്കുക, January മാസദിനമാണെങ്കിൽ പോലും.
        കൃഷ്ണവർഷം = greg_year + 3102
    else:  # മകരം(9) to മീനം(11)
        കൃഷ്ണവർഷം = greg_year + 3101

    സമ്പൂർണമലയാളദിനം = f"{കൃഷ്ണവർഷം} {malayalam_month} {malayalam_day:02d}"
    return സമ്പൂർണമലയാളദിനം



import json
from pathlib import Path

output = []
start_date = datetime.date(2025, 1, 1)
end_date = datetime.date(2026, 12, 31)
delta = datetime.timedelta(days=1)

മാസങ്ങൾ = ["മേടം", "ഇടവം", "മിഥുനം", "കർക്കിടകം", "ചിങ്ങം", "കന്നി", "തുലാം", "വൃശ്ചികം", "ധനു", "മകരം", "കുംഭം", "മീനം"]

current_date = start_date
while current_date <= end_date:
    try:
        mal_date = മലയാളദിനം(current_date)  # example: "5127 ഇടവം 01"
        parts = mal_date.split(" ")  # U+2009 thin space separator
        if len(parts) == 3:
            ml_year = int(parts[0])
            ml_month = parts[1]
            month_index = മാസങ്ങൾ.index(ml_month) + 1
            ml_day = int(parts[2])
            output.append({
                "gregorianDate": current_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                #"gregorianDate": current_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "mlYear": ml_year,
                "mlMonth": ml_month,
                "mlMonthNumber": month_index,
                "mlDay": ml_day
            })
        else:
            print(f"⚠️ Unexpected format for {current_date}: {mal_date}")
    except Exception as e:
        print(f"❌ Error on {current_date}: {e}")
    current_date += delta

# Save to JSON
output_path = Path("/Users/user/Files/codes/uom/Panchangam/Panchangam/scripts/malayalam_gregorian_2025_2026.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ Saved {len(output)} days to {output_path}")
