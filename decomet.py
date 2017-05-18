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
    
def parseWind(tokens, metar):
    if not tokens:
        return
    
    token = tokens[0]
    
    p = re.compile('([0-9VRB/]{3})([0-9/]{2})(G([0-9]{2}))?([A-Z]+)')
    m = p.match(token)

    if m:
        wind = {}
        metar['wind'] = wind

        assert(m.group(3) == None)

        unit = m.group(5)
        wind['unit'] = unit

        direction = m.group(1)

        if direction == "VRB":
            wind['variable'] = True

        elif direction != "///":
            wind['direction'] = direction

        speed = m.group(2)

        if speed != "//":
            wind['speed'] = speed


        tokens.pop(0)

        #Varying
        if tokens:
            token = tokens[0]
            if len(token) == 7 and token[3] == 'V': #TODO: Regexp
                varying = {}
                wind['varying'] = varying
                toFrom = token.split('V')
                varying['from'] = toFrom[0]
                varying['to'] = toFrom[1]

                tokens.pop(0)
        
    
def parseVisibility(tokens, metar):
    #ESSL 160520Z 00000KT 0100 R11/0550 R29/0300V0450N FG VV000 01/01 Q1026
    if tokens == []:
        return False

    visibility = {}
    metar['visibility'] = visibility
    
    p = re.compile("([0-9]{4})(NDV)?|CAVOK|R([0-9]{2})/([0-9]{4})(V([0-9]{4}))?")
    
    m = p.match(tokens[0])
    
    if not m:
        return False

    if m.group(0) == "CAVOK":
        #print("Ceiling and visibility OK")
        visibility['CAVOK'] = True
    else:
    
        if m.group(1) == "9999":
            visibility['distance'] = "More than 10000"
        else:
            visibility['distance'] = m.group(1)
            
        note = ""
        if m.group(2) == "NDV":
            note = " (No directional variation)"
        
        if m.group(3):
            runways = {}
            visibility['runways'] = runways
            thisRunway = {}
            runways[m.group(3)] = thisRunway

            if m.group(5):
                #print("Runway %s: %s, varying to %s" % (m.group(3), m.group(4), m.group(6)))
                thisRunway['varying'] = {'from': m.group(4), 'to': m.group(6)}
            else:
                #print("Runway %s: %s" % (m.group(3), m.group(4)))
                thisRunway['distance'] = m.group(4)

    tokens.pop(0)
    
    return True
    
def parseFog(tokens, metar):
    if tokens == []:
        return False
    
    token = tokens[0]
    
    intensity = "moderate"
    if token[0] == '-':
        intensity = "light"
        token = token[1:]
    elif token[0] == '+':
        intensity = "heavy"
        token = token[1:]
        
    
    descMap = {'MI': 'shallow',
               'PR': 'partial',
               'BC': 'patches',
               'DR': 'low drifting',
               'BL': 'blowing',
               'SH': 'showers',
               'FZ': 'freezing',
               'RE': 'recent',
               '': ''}
    
    precipMap = {'DZ': 'drizzle',
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

    if decip in precipMap and desc in descMap:
        #print("%s %s%s" % (intensity, descMap[desc], pecipMap[decip]))
        percip = {}
        metar['precipitation'] = percip

        percip['intensity'] = intensity
        percip['description'] = descMap[desc]
        percip['type'] = precipMap[decip]

        tokens.pop(0)
        
        return True
    return False
    
def parseClouds(tokens, metar):
    #TODO: Add octas
    if tokens == []:
        return False
    
    token = tokens[0]
    coverage = token[0:3] #TODO: Find real METAR with VV
    height = token[3:6]

    clouds = {}
    metar['clouds'] = clouds
    
    if coverage == 'NSC':
        #print("No significant clouds")
        clouds['status'] = "No significant clouds"
        tokens.pop(0)
    elif coverage == 'SKC':
        #print("Sky clear")
        clouds['status'] = "Sky clear"
        tokens.pop(0)
    elif coverage == 'NCD':
        #print("No clouds detected")
        clouds['status'] = "No clouds detected"
        tokens.pop(0)
    elif coverage[0:2] == 'VV':
        #print("Vertical visibility: %s" % coverage[2:])
        height = token[2:5]
        clouds['vertical visibility'] = str(int(height)*100)
        tokens.pop(0)
    else:
        coverageMap = {'FEW': 'few',
                       'SCT': 'scattered',
                       'BKN': 'broken',
                       'OVC': 'overcast'}

        if coverage in coverageMap:
            
            type = ""
            if token[-2:] == "CB": #TODO: Add TCU (Towering Cumulus)
                #type = " (Cumulonimbus cloud)"
                clouds['type'] = 'cumulonimbus'

            #print("Clouds: %s at %d feet%s" % (coverageMap[coverage], int(height)*100, type))
            clouds['coverage'] = coverageMap[coverage]
            clouds['height'] = str(int(height)*100)
    
            tokens.pop(0)

            return True

    return False
    

def parseTemperatures(tokens, metar):
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
    
    #print("Temperature %d C, dewpoint %d C" % (parseTemperature(temperature), parseTemperature(dewpoint)))
    metar['temperature'] = str(parseTemperature(temperature))
    metar['dew point'] = str(parseTemperature(dewpoint))
    
    tokens.pop(0)

    return True
    
def parseQNH(tokens, metar):
    if tokens == []:
        return False
    
    token = tokens[0]
    assert(token[0] == 'Q')
    qnh = token[1:]
    
    if qnh == "////":
        qnh = "<unknown>"
    
    #print("QNH: %s hPa" % qnh)
    metar['QNH'] = qnh
    
    tokens.pop(0)
    
def parseTrend(tokens, metar):
    if tokens == []:
        return False
    
    token = tokens[0]

    trend = {}
    metar['trend'] = trend
    
    if token == "NOSIG":
        #print("No significant change expected within next 2 hours")
        trend['type'] = 'No significant change expected'
        tokens.pop(0)

    elif token[0:2] == "FM":
        changeHours = token[2:4]
        changeMinutes = token[4:]
        tokens.pop(0)
        
        #print("From %s:%s UTC:" % (changeHours, changeMinutes))
        trend['type'] = 'change'
        
        parseWind(tokens, metar)
        parseVisibility(tokens, metar)
        parseFog(tokens, metar)
        parseClouds(tokens, metar)
        
    elif token == "TEMPO":
        tokens.pop(0)

        token = tokens[0]
        fromTo = token.split('/')
        
        fromHours = fromTo[0][0:2]
        fromMinutes = fromTo[0][2:]
        toHours = fromTo[1][0:2]
        toMinutes = fromTo[1][2:]

        tokens.pop(0)
        
        #print("Temporary %s:%s to %s:%s:" % (fromHours, fromMinutes, toHours, toMinutes))
        trend['type'] = 'temporary'
        
        parseWind(tokens, metar)
        parseVisibility(tokens, metar)
        parseFog(tokens, metar)
        parseClouds(tokens, metar)
        
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

    def testParseWind(self):
        metar = {}
        tokens = ['12345KT']
        parseWind(tokens, metar)

        self.assertEqual(metar['wind']['direction'], '123')
        self.assertEqual(metar['wind']['speed'], '45')
        self.assertEqual(metar['wind']['unit'], 'KT')

        metar = {}
        tokens = ['VRB45KT', '120V140']
        parseWind(tokens, metar)

        self.assertNotIn('direction', metar['wind'])
        self.assertTrue(metar['wind']['variable'])

        self.assertEqual(metar['wind']['speed'], '45')
        self.assertEqual(metar['wind']['varying']['from'], '120')
        self.assertEqual(metar['wind']['varying']['to'], '140')

    def testParseVisibility(self):
        metar = {}
        tokens = ['CAVOK']

        parseVisibility(tokens, metar)

        self.assertTrue(metar['visibility']['CAVOK'])

        metar = {}
        tokens = ['0100']
        parseVisibility(tokens, metar)
        self.assertEqual(metar['visibility']['distance'], '0100')

        metar = {}
        tokens = ['R11/0550']
        parseVisibility(tokens, metar)
        self.assertEqual(metar['visibility']['runways']['11']['distance'], '0550')

        metar = {}
        tokens = ['R29/0300V0450N']
        parseVisibility(tokens, metar)
        self.assertEqual(metar['visibility']['runways']['29']['varying']['from'], '0300')
        self.assertEqual(metar['visibility']['runways']['29']['varying']['to'], '0450')

    def testParseFog(self):
        metar = {}
        tokens = ['RA']
        parseFog(tokens, metar)

        self.assertEqual(metar['precipitation']['type'], 'rain')

        metar = {}
        tokens = ['+BLSN']
        parseFog(tokens, metar)

        self.assertEqual(metar['precipitation']['intensity'], 'heavy')
        self.assertEqual(metar['precipitation']['description'], 'blowing')
        self.assertEqual(metar['precipitation']['type'], 'snow')

    def testParseClouds(self):
        metar = {}
        tokens = ['NSC']
        parseClouds(tokens, metar)

        self.assertEqual(metar['clouds']['status'], 'No significant clouds')

        metar = {}
        tokens = ['VV007']
        parseClouds(tokens, metar)

        self.assertEqual(metar['clouds']['vertical visibility'], '700')

        metar = {}
        tokens = ['BKN050CB']
        parseClouds(tokens, metar)

        self.assertEqual(metar['clouds']['coverage'], 'broken')
        self.assertEqual(metar['clouds']['height'], '5000')
        self.assertEqual(metar['clouds']['type'], 'cumulonimbus')

    def testParseTemperatures(self):
        metar = {}
        tokens = ['M05/02']
        parseTemperatures(tokens, metar)

        self.assertEqual(metar['temperature'], '-5')
        self.assertEqual(metar['dew point'], '2')

    def testParseQNH(self):
        metar = {}
        tokens = ['Q1007']
        parseQNH(tokens, metar)

        self.assertEqual(metar['QNH'], '1007')

    def testParseTrend(self):
        metar = {}
        tokens = ['NOSIG']
        parseTrend(tokens, metar)

        self.assertEqual(metar['trend']['type'], 'No significant change expected')

        metar = {}
        tokens = ['FM1325', '10044KT']
        parseTrend(tokens, metar)

        self.assertEqual(metar['trend']['type'], 'change')

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
    