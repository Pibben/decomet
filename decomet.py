import urllib.request

def parseAirportCode(tokens):
    print("Airport ICAO: %s" % tokens[0])
    tokens.pop(0)
    
def parseTime(tokens):
    token = tokens[0]
    date = token[0:2]
    hours = token[2:4]
    minutes = token[4:6]
    
    assert(token[6] == 'Z')
    
    print("Date: %s" % date)
    print("UTC time: %s:%s" % (hours, minutes))
    
    tokens.pop(0)
    
def parseWind(tokens):
    token = tokens[0]
    direction = token[0:3]
    speed = token[3:5]
    unit = token[5:]
    
    if unit == "KT" or unit == "MPS":
    
        print("Wind %s degrees, %s %s" % (direction, speed, unit))
    
        tokens.pop(0)
    
def parseVisibility(tokens):
    visibility = tokens[0]
    
    if visibility == "CAVOK":
        print("Ceiling and visibility OK")
    else:
    
        if visibility == "9999":
            visibility = "More than 10000"
        
        print("Visibility: %s meters" % visibility)
    
    tokens.pop(0)
    
def parseFog(tokens):
    token = tokens[0]
    
    fogMap = {'FG': 'fog',
              'MIFG': 'shallow fog',
              'BCFG': 'fog patches',
              'PRFG': 'partial fog',
              'FZFG': 'freezing fog'}
    
    if token in fogMap:
        print("Fog: %s" % fogMap[token])
        tokens.pop(0)
    
def parseClouds(tokens):
    token = tokens[0]
    coverage = token[0:3]
    height = token[3:]
    
    if coverage == 'NSC':
        print("No significant clouds")
        tokens.pop(0)
    else:
        
        coverageMap = {'FEW': 'few clouds',
                       'SCT': 'scattered clouds',
                       'BKN': 'broken clouds',
                       'OVC': 'overcast'}

        if coverage in coverageMap:
    
            print("Clouds: %s at %d feet" % (coverageMap[coverage], int(height)*100))
    
            tokens.pop(0)
    

    
def parseTemperatures(tokens):
    def parseTemperature(string):
        if string[0] == 'M':
            return -int(string[1:])
        else:
            return int(string)
    
    token = tokens[0]
    temps = token.split('/')
    temperature = temps[0]
    dewpoint = temps[1]
    
    print("Temperature %d C, dewpoint %d C" % (parseTemperature(temperature), parseTemperature(dewpoint)))
    
    tokens.pop(0)
    
def parseQNH(tokens):
    token = tokens[0]
    assert(token[0] == 'Q')
    qnh = token[1:]
    
    print("QNH: %s hPa" % qnh)
    
    tokens.pop(0)
    
def parseTrend(tokens):
    if tokens == []:
        return
    
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
        tokens.pop(0)
        
def parse(url):
    with urllib.request.urlopen(url) as response:
        message = response.read()
        
        metar = message.splitlines(True)[1].decode("utf-8").strip()
        
        print("-> %s" % metar)
        
        tokens = metar.split(' ')
        
        parseAirportCode(tokens)
        parseTime(tokens)
        parseWind(tokens)
        parseVisibility(tokens)
        parseFog(tokens)
        parseClouds(tokens)
        parseTemperatures(tokens)
        parseQNH(tokens)
        
        while tokens != []:
            parseTrend(tokens)

def main():

    parse('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/LXGB.TXT')
    print("---\n")
    parse('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/ESSL.TXT')
    print("---\n")
    parse('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/YSSY.TXT')
    print("---\n")


if __name__ == "__main__":
    main()
    