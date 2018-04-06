import urllib.request
import re
from pprint import pprint

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
    
def parseWind(tokens, wind):
    if not tokens:
        return
    
    token = tokens[0]
    
    p = re.compile('([0-9VRB/]{3})([0-9/]{2})(G([0-9]{2}))?([A-Z]+)')
    m = p.match(token)

    if m:
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

        if m.group(3):
            wind['speed in gusts'] = m.group(3)[-2:]

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
        
    
def parseVisibility(tokens, visibility):

    if tokens == []:
        return False

    if len(tokens[0]) == 4 and tokens[0][-2:] == 'KM':
        visibility['distance'] = tokens[0]
        tokens.pop(0)

        return True

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
    
def parseFog(tokens, precip):
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

        precip['intensity'] = intensity
        if desc != '':
            precip['description'] = descMap[desc]
        precip['type'] = precipMap[decip]

        tokens.pop(0)
        
        return True
    return False
    
def parseClouds(tokens, clouds):
    #TODO: Add octas
    if tokens == []:
        return False
    
    token = tokens[0]
    coverage = token[0:3] #TODO: Find real METAR with VV
    height = token[3:6]

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
    
def parseTrend(tokens, trend):
    if tokens == []:
        return False

    def parseSubMetar(tokens, trend):
        wind = {}
        trend['wind'] = wind
        parseWind(tokens, wind)

        visibility = {}
        trend['visibility'] = visibility
        parseVisibility(tokens, visibility)

        precip = {}
        trend['precipitation'] = precip
        parseFog(tokens, precip)

        clouds = {}
        trend['clouds'] = clouds
        parseClouds(tokens, clouds)
    
    token = tokens[0]

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
        trend['from'] = "%s:%s" % (changeHours, changeMinutes)

        parseSubMetar(tokens, trend)

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
        trend['from'] = "%s:%s" % (fromHours, fromMinutes)
        trend['to'] = "%s:%s" % (toHours, toMinutes)

        parseSubMetar(tokens, trend)
        
    else:
        #print("Unknown trend %s" % token)
        return False

    return True
        
def parseRunway(tokens, runway):
    #http://www.flyingineurope.be/MetarRunway.htm
    #http://sto.iki.fi/metar/
    #TODO: Find real data
    if tokens == []:
        return False

    token = tokens[0]

    if len(token) != 8:
        return False

    p = re.compile("([0-9]{2})(CLRD|([0-9/]{1})([1259]{1})([0-9]{2}))([0-9/]{2})")

    m = p.match(token)

    if int(m.group(1)) < 50:
        runway['runway'] = m.group(1)
    else:
        runway['runway'] = str(int(m.group(1))-50)+'R'

    status = ""
    if m.group(1) == "CLRD":
        status = "Cleared"

    typeMap = {'0': 'clear and dry',
               '1': 'damp',
               '2': 'wet or puddles',
               '3': 'frost',
               '4': 'dry snow',
               '5': 'wet snow',
               '6': 'slush',
               '7': 'ice',
               '8': 'compacted snow',
               '9': 'frozen ridges',
               '/': 'no report'}
    runway['type'] = typeMap[m.group(3)]

    extentMap = {'1': '1-10%',
                 '2': '11-25%',
                 '5': '26-50%',
                 '9': '51-100%'}
    runway['extent'] = extentMap[m.group(4)]

    depthMap = {'00': 'less than 1mm',
                '92': '10cm',
                '93': '15cm',
                '94': '20cm',
                '95': '25cm',
                '96': '30cm',
                '97': '35cm',
                '98': '40cm',
                '99': 'rwy not in use'}

    depth = m.group(5)

    if int(depth) > 0 and int(depth) <= 90:
        runway['depth'] = depth+'mm'
    else:
        runway['depth'] = depthMap[depth]

    frictionMap = {'91': 'poor',
                   '92': 'poor/medium',
                   '93': 'medium',
                   '94': 'medium/good',
                   '95': 'good',
                   '99': 'unreliable measurement'}

    friction = m.group(6)

    if int(friction) <= 90:
        runway['friction'] = str(float(friction) * 0.01)
    elif friction in frictionMap:
        runway['friction'] = frictionMap[friction]


    #print("Runway %s: %s, friction %s" % (rwy, status, friction))

    tokens.pop(0)

    return True

def parseRemark(tokens, metar):
    if tokens == []:
        return False
    
    if tokens[0] != "RMK":
        return False
    
    #print("Remark: %s" % ' '.join(tokens[1:]))
    metar['remark'] = ' '.join(tokens[1:])

def parseString(string):
    #print("-> %s" % metar)

    tokens = string.split(' ')

    metar = {}

    parseAirportCode(tokens, metar)
    parseTime(tokens, metar)

    wind = {}
    metar['wind'] = wind
    parseWind(tokens, wind)

    visibilityList = []

    while True:
        visibility = {}
        ok = parseVisibility(tokens, visibility)
        if not ok:
            break

        visibilityList.append(visibility)

    if visibilityList:
        metar['visibility'] = visibilityList

    precip = {}
    parseFog(tokens, precip)
    if precip:
        metar['precipitation'] = precip

    cloudList = []

    while True:
        clouds = {}
        ok = parseClouds(tokens, clouds)
        if not ok:
            break

        cloudList.append(clouds)

    if cloudList:
        metar['clouds'] = cloudList

    parseTemperatures(tokens, metar)

    parseQNH(tokens, metar)

    runway = {}
    parseRunway(tokens, runway)
    if runway:
        metar['runway'] = runway

    trendList = []

    while tokens:
        trend = {}
        ok = parseTrend(tokens, trend)

        if not ok:
            break

        trendList.append(trend)

    if trendList:
        metar['trends'] = trendList

    parseRemark(tokens, metar)

    return metar

def parse(url):
    with urllib.request.urlopen(url) as response:
        message = response.read()
        
        string = message.splitlines(True)[1].decode("utf-8").strip() #Remove first line

        print(string)
        metar = parseString(string)
        pprint(metar)
            
def iterateAll():
    with urllib.request.urlopen('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/') as files:
        listing = files.read().splitlines(True)
        
        forbidden = ['A302.TXT', 'AAXX.TXT', 'AGGG.TXT', 'AGGM.TXT', 'AK15.TXT',
                     'ATAR.TXT', 'B635.TXT']

        for l in listing:
            filename = l.split()[-1].decode('ascii')

            if filename in forbidden:
                continue
            
            #if filename[0:2] != "ES":
            #    continue
            
            pprint(parse("ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/%s" % filename))
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
        wind = {}
        tokens = ['12345KT']
        parseWind(tokens, wind)

        self.assertEqual(wind['direction'], '123')
        self.assertEqual(wind['speed'], '45')
        self.assertEqual(wind['unit'], 'KT')

        wind = {}
        tokens = ['12345G67KT']
        parseWind(tokens, wind)

        self.assertEqual(wind['direction'], '123')
        self.assertEqual(wind['speed'], '45')
        self.assertEqual(wind['speed in gusts'], '67')
        self.assertEqual(wind['unit'], 'KT')

        wind = {}
        tokens = ['VRB45KT', '120V140']
        parseWind(tokens, wind)

        self.assertNotIn('direction', wind)
        self.assertTrue(wind['variable'])

        self.assertEqual(wind['speed'], '45')
        self.assertEqual(wind['varying']['from'], '120')
        self.assertEqual(wind['varying']['to'], '140')

    def testParseVisibility(self):
        visibility = {}
        tokens = ['CAVOK']

        parseVisibility(tokens, visibility)

        self.assertTrue(visibility['CAVOK'])

        visibility = {}
        tokens = ['0100']
        parseVisibility(tokens, visibility)
        self.assertEqual(visibility['distance'], '0100')

        visibility = {}
        tokens = ['25KM']
        parseVisibility(tokens, visibility)
        self.assertEqual(visibility['distance'], '25KM')

        visibility = {}
        tokens = ['R11/0550']
        parseVisibility(tokens, visibility)
        self.assertEqual(visibility['runways']['11']['distance'], '0550')

        visibility = {}
        tokens = ['R29/0300V0450N']
        parseVisibility(tokens, visibility)
        self.assertEqual(visibility['runways']['29']['varying']['from'], '0300')
        self.assertEqual(visibility['runways']['29']['varying']['to'], '0450')

    def testParseFog(self):
        precip = {}
        tokens = ['RA']
        parseFog(tokens, precip)

        self.assertEqual(precip['intensity'], 'moderate')
        self.assertNotIn('description' ,precip)
        self.assertEqual(precip['type'], 'rain')

        precip = {}
        tokens = ['+BLSN']
        parseFog(tokens, precip)

        self.assertEqual(precip['intensity'], 'heavy')
        self.assertEqual(precip['description'], 'blowing')
        self.assertEqual(precip['type'], 'snow')

    def testParseClouds(self):
        clouds = {}
        tokens = ['NSC']
        parseClouds(tokens, clouds)

        self.assertEqual(clouds['status'], 'No significant clouds')

        metar = {}
        tokens = ['VV007']
        parseClouds(tokens, clouds)

        self.assertEqual(clouds['vertical visibility'], '700')

        metar = {}
        tokens = ['BKN050CB']
        parseClouds(tokens, clouds)

        self.assertEqual(clouds['coverage'], 'broken')
        self.assertEqual(clouds['height'], '5000')
        self.assertEqual(clouds['type'], 'cumulonimbus')

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
        trend = {}
        tokens = ['NOSIG']
        parseTrend(tokens, trend)

        self.assertEqual(trend['type'], 'No significant change expected')

        trend = {}
        tokens = ['FM1325', '10044KT', '0100', 'RA', 'BKN050']
        parseTrend(tokens, trend)

        self.assertEqual(trend['type'], 'change')
        self.assertEqual(trend['from'], '13:25')
        self.assertEqual(trend['wind']['direction'], '100')
        self.assertEqual(trend['wind']['speed'], '44')
        self.assertEqual(trend['visibility']['distance'], '0100')
        self.assertEqual(trend['precipitation']['type'], 'rain')
        self.assertEqual(trend['clouds']['coverage'], 'broken')
        self.assertEqual(trend['clouds']['height'], '5000')

        trend = {}
        tokens = ['TEMPO', '1325/1415', '10044KT', '0100', 'RA', 'BKN050']
        parseTrend(tokens, trend)

        self.assertEqual(trend['type'], 'temporary')
        self.assertEqual(trend['from'], '13:25')
        self.assertEqual(trend['to'], '14:15')
        self.assertEqual(trend['wind']['direction'], '100')
        self.assertEqual(trend['wind']['speed'], '44')
        self.assertEqual(trend['visibility']['distance'], '0100')
        self.assertEqual(trend['precipitation']['type'], 'rain')
        self.assertEqual(trend['clouds']['coverage'], 'broken')
        self.assertEqual(trend['clouds']['height'], '5000')

    def testParseRunway(self):
        rwy = {}
        tokens = ['74692225']
        parseRunway(tokens, rwy)

        self.assertEqual(rwy['runway'], '24R')
        self.assertEqual(rwy['type'], 'slush')
        self.assertEqual(rwy['extent'], '51-100%')
        self.assertEqual(rwy['depth'], '22mm')
        self.assertEqual(rwy['friction'], '0.25')

        rwy = {}
        tokens = ['24119895']
        parseRunway(tokens, rwy)

        self.assertEqual(rwy['runway'], '24')
        self.assertEqual(rwy['type'], 'damp')
        self.assertEqual(rwy['extent'], '1-10%')
        self.assertEqual(rwy['depth'], '40cm')
        self.assertEqual(rwy['friction'], 'good')

    def testParseRemark(self):
        metar = {}
        tokens = ['RMK', 'FOO', 'BAR']
        parseRemark(tokens, metar)

        self.assertEqual(metar['remark'], 'FOO BAR')


def main():
    #unittest.main()

    iterateAll()
    #AGGM 020300Z 09005KT 25KM HZ FEW020 SCT300 33/25 Q1005
    #ABBN 160530Z 23004KT 9999 NSC 02/M05 Q1029 R14R/CLRD60 NOSIG RMK G/O QFE696
    #ESSL 160520Z 00000KT 0100 R11/0550 R29/0300V0450N FG VV000 01/01 Q1026
    #BGCH 271228Z 07013KT 3000 -SN BLSN DRSN VV009 M07/M09 Q1002

    #parse('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/ESSL.TXT')
    #print("---\n")
    #parse('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/YSSY.TXT')
    #print("---\n")
    #parse('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/EDDT.TXT')
    #print("---\n")


if __name__ == "__main__":
    main()
    