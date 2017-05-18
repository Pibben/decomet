import urllib.request
import re

def parseAirportCode(tokens, metar):
    #print("Airport ICAO: %s" % tokens[0])
    metar['airport'] = tokens.pop(0)
    
def parseTime(tokens, metar):
    token = tokens[0]

    if len(token) != 7:
        raise ValueError('Time token wrong length')

    date = token[0:2]
    hours = token[2:4]
    minutes = token[4:6]
    
    if token[6] != 'Z':
        raise ValueError('Time token malformed')

    metar['date'] = date
    metar['time'] = "%s:%s" % (hours, minutes)
    
    #print("Date: %s" % date)
    #print("UTC time: %s:%s" % (hours, minutes))
    
    tokens.pop(0)
    
    if tokens and tokens[0] == "AUTO":
        metar['automatic'] = True
        tokens.pop(0)
    
def parseWind(tokens):
    if tokens == []:
        return False
    
    token = tokens[0]
    
    p = re.compile('([0-9VRB/]{3})([0-9/]{2})(G([0-9]{2}))?([A-Z]+)')
    m = p.match(token)

    if m:
        direction = m.group(1)
        speed = m.group(2)
        unit = m.group(5)
        assert(m.group(3) == None)
        
        if direction == "///":
            direction = "<unknown>"

        if speed == "//":
            speed = "<unknown>"
    
        if direction == "VRB":
            print("Variable wind, %s %s" % (speed, unit))
        else:
            print("Wind %s degrees, %s %s" % (direction, speed, unit))
    
        tokens.pop(0)
        
        #Varying
        token = tokens[0]
        if len(token) == 7 and token[3] == 'V':
            toFrom = token.split('V')
            print("Varying from %s to %s degrees\n" % (toFrom[0], toFrom[1]))
            
            tokens.pop(0)
        
    
def parseVisibility(tokens):
    #ESSL 160520Z 00000KT 0100 R11/0550 R29/0300V0450N FG VV000 01/01 Q1026
    if tokens == []:
        return False
    
    p = re.compile("([0-9]{4})(NDV)?|CAVOK|R([0-9]{2})/([0-9]{4})(V([0-9]{4}))?")
    
    m = p.match(tokens[0])
    
    if not m:
        return False
    
    if m.group(0) == "CAVOK":
        print("Ceiling and visibility OK")
    else:
    
        if m.group(1) == "9999":
            visibilityStr = "More than 10000"
        else:
            visibilityStr = m.group(1)
            
        note = ""
        if m.group(2) == "NDV":
            note = " (No directional variation)"
        
        if m.group(3):
            if m.group(5):
                print("Runway %s: %s, varying to %s" % (m.group(3), m.group(4), m.group(6)))
            else:
                print("Runway %s: %s" % (m.group(3), m.group(4)))
        else:
            print("Visibility: %s meters%s" % (visibilityStr, note))
        


    
    tokens.pop(0)
    
    return True
    
def parseFog(tokens):
    if tokens == []:
        return False
    
    token = tokens[0]
    
    intensity = "Moderate"
    if token[0] == '-':
        intensity = "Light"
        token = token[1:]
    elif token[0] == '+':
        intensity = "Heavy"
        token = token[1:]
        
    
    descMap = {'MI': 'shallow ',
               'PR': 'partial ',
               'BC': 'patches of ',
               'DR': 'low drifting',
               'BL': 'blowing',
               'SH': 'showers of',
               'FZ': 'freezing ',
               'RE': 'recent ',
               '': ''}
    
    decipMap = {'DZ': 'drizzle',
                'RA': 'rain',
                'SN': 'snow',
                'GS': 'small of soft hail',
                'GR': 'hail',
                'PE': 'ice pellets',
                'IC': 'ic crystals',
                'TS': 'thunderstorm',
                'HZ': 'haze',
                'BR': 'mist',
                'FG': 'fog',
                'FU': 'smoke',
                'SS': 'sandstorm',
                'DS': 'duststorm',
                'PO': 'dust devils',
                'DU': 'dust',
                'SQ': 'squall',
                'FC': 'funnel cloud',
                'UP': 'unknown precipitation'}
    
    
    if len(token) == 2:
        desc = ''
        decip = token
    elif len(token) == 4:
        desc = token[0:2]
        decip = token[2:4]
    else:
        return False
            
        
    
    if decip in decipMap and desc in descMap:
        print("%s %s%s" % (intensity, descMap[desc], decipMap[decip]))
        tokens.pop(0)
        
        return True
    return False
    
def parseClouds(tokens):
    if tokens == []:
        return False
    
    token = tokens[0]
    coverage = token[0:3]
    height = token[3:6]
    
    if coverage == 'NSC':
        print("No significant clouds")
        tokens.pop(0)
    elif coverage == 'SKC':
        print("Sky clear")
        tokens.pop(0)
    elif coverage == 'NCD':
        print("No clouds detected")
        tokens.pop(0)
    elif coverage[0:2] == 'VV':
        print("Vertical visibility: %s" % coverage[2:])
        tokens.pop(0)
    else:
        
        coverageMap = {'FEW': 'few clouds',
                       'SCT': 'scattered clouds',
                       'BKN': 'broken clouds',
                       'OVC': 'overcast'}

        if coverage in coverageMap:
            
            type = ""
            if token[-2:] == "CB":
                type = " (Cumulonimbus cloud)"
    
            print("Clouds: %s at %d feet%s" % (coverageMap[coverage], int(height)*100, type))
    
            tokens.pop(0)
            return True
    return False
    

    
def parseTemperatures(tokens):
    if tokens == []:
        return False
    
    def parseTemperature(string):
        if string[0] == 'M':
            return -int(string[1:])
        else:
            return int(string)
    
    token = tokens[0]
    temps = token.split('/')
    
    if len(temps) != 2:
        return False
    
    temperature = temps[0]
    dewpoint = temps[1]
    
    print("Temperature %d C, dewpoint %d C" % (parseTemperature(temperature), parseTemperature(dewpoint)))
    
    tokens.pop(0)
    
def parseQNH(tokens):
    if tokens == []:
        return False
    
    token = tokens[0]
    assert(token[0] == 'Q')
    qnh = token[1:]
    
    if qnh == "////":
        qnh = "<unknown>"
    
    print("QNH: %s hPa" % qnh)
    
    tokens.pop(0)
    
def parseTrend(tokens):
    if tokens == []:
        return False
    
    token = tokens[0]
    
    if token == "NOSIG":
        print("No significant change expected within next 2 hours")
        tokens.pop(0)

    elif token[0:2] == "FM":
        changeHours = token[2:4]
        changeMinutes = token[4:]
        tokens.pop(0)
        
        print("From %s:%s UTC:" % (changeHours, changeMinutes))
        
        parseWind(tokens)
        parseVisibility(tokens)
        parseFog(tokens)
        parseClouds(tokens)
        
    elif token == "TEMPO":
        tokens.pop(0)

        token = tokens[0]
        fromTo = token.split('/')
        
        fromHours = fromTo[0][0:2]
        fromMinutes = fromTo[0][2:]
        toHours = fromTo[1][0:2]
        toMinutes = fromTo[1][2:]

        tokens.pop(0)
        
        print("Temporary %s:%s to %s:%s:" % (fromHours, fromMinutes, toHours, toMinutes))
        
        parseWind(tokens)
        parseVisibility(tokens)
        parseFog(tokens)
        parseClouds(tokens)
        
    else:
        print("Unknown trend %s" % token)
        return False
        
def parseRunway(tokens):
    #http://www.flyingineurope.be/MetarRunway.htm
    if tokens == []:
        return False
    
    token = tokens[0]
    
    rwydata = token.split('/')
    if len(rwydata) != 2:
        return False
    
    (rwy, data) = tuple(rwydata)
    
    friction = data[-2:]
    
    status = ""
    if data[0:4] == "CLRD":
        status = "Cleared"
    
    print("Runway %s: %s, friction %s" % (rwy, status, friction))
    
    tokens.pop(0)
    
    return True

def parseRemark(tokens):
    if tokens == []:
        return False
    
    if tokens[0] != "RMK":
        return False
    
    print("Remark: %s" % ' '.join(tokens[1:]))
    tokens = []

def parseString(metar):
    print("-> %s" % metar)

    tokens = metar.split(' ')

    parseAirportCode(tokens)
    parseTime(tokens)
    parseWind(tokens)
    while parseVisibility(tokens):
        pass
    parseFog(tokens)
    while parseClouds(tokens):
        pass
    parseTemperatures(tokens)
    parseQNH(tokens)

    parseRunway(tokens)

    while tokens != [] and parseTrend(tokens):
        pass

    parseRemark(tokens)
        
def parse(url):
    with urllib.request.urlopen(url) as response:
        message = response.read()
        
        metar = message.splitlines(True)[1].decode("utf-8").strip() #Remove first line
        
        parseString(metar)
            
def iterateAll():
    with urllib.request.urlopen('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/') as files:
        listing = files.read().splitlines(True)
        
        for l in listing:
            filename = l.split()[-1].decode('ascii')
            
            forbidden = ['A302.TXT', 'AGGG.TXT', 'AK15.TXT', 'ESGL.TXT', 'ESGR.TXT', 'ATAR.TXT']
            
            if filename in forbidden:
                continue
            
            #if filename[0:2] != "ES":
            #    continue
            
            parse("ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/%s" % filename)
            print("-----")

import unittest

class DecometTest(unittest.TestCase):

    def testParseAirportCode(self):
        metar = {}
        tokens = ['ESSL']
        parseAirportCode(tokens, metar)
        self.assertEqual(metar['airport'], 'ESSL')

    def testParseTime(self):
        metar = {}
        tokens = ['170620Z', 'AUTO']
        parseTime(tokens, metar)
        self.assertEqual(metar['date'], '17')
        self.assertEqual(metar['time'], '06:20')
        self.assertEqual(metar['automatic'], True)

        with self.assertRaises(ValueError):
            tokens = ['70620Z']
            parseTime(tokens, {})

        with self.assertRaises(ValueError):
            tokens = ['170620K']
            parseTime(tokens, {})

def main():
    unittest.main()

    #iterateAll()
    #parse('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/ESSL.TXT')
#    print("---\n")
#    parse('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/ESSL.TXT')
#    print("---\n")
#    parse('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/YSSY.TXT')
#    print("---\n")
#    parse('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/EDDT.TXT')
#    print("---\n")


if __name__ == "__main__":
    main()
    