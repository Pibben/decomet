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
    
    print("Wind %s degrees, %s %s" % (direction, speed, unit))
    
    tokens.pop(0)
    
def parseVisibility(tokens):
    visibility = tokens[0]
    
    if visibility == "9999":
        visibility = "More than 10000"
    
    print("Visibility: %s meters" % visibility)
    
    tokens.pop(0)
    
def parseClouds(tokens):
    token = tokens[0]
    coverage = token[0:3]
    height = token[3:]
    
    coverageMap = {'FEW': 'few clouds',
                   'SCT': 'scattered clouds',
                   'BRN': 'broken clouds',
                   'OVC': 'overcast'}
    
    print("Clouds: %s at %d feet" % (coverageMap[coverage], int(height)*100))
    
    tokens.pop(0)
    
def parseTemperature(tokens):
    token = tokens[0]
    temps = token.split('/')
    temperature = temps[0]
    dewpoint = temps[1]
    
    print("Temperature %s C, dewpoint %s C" % (temperature, dewpoint))
    
    tokens.pop(0)
    
def parseQNH(tokens):
    token = tokens[0]
    assert(token[0] == 'Q')
    qnh = token[1:]
    
    print("QNH: %s hPa" % qnh)
    
    tokens.pop(0)
    
def parseTrend(tokens):
    token = tokens[0]
    
    if token == "NOSIG":
        print("No significant change expected within next 2 hours")
    else:
        print("Unknown trend %s" % token)
        
    tokens.pop(0)

def parse(tokens):
    parseAirportCode(tokens)
    parseTime(tokens)
    parseWind(tokens)
    parseVisibility(tokens)
    parseClouds(tokens)
    parseTemperature(tokens)
    parseQNH(tokens)
    parseTrend(tokens)

def main():

    with urllib.request.urlopen('ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/LXGB.TXT') as response:
        message = response.read()
        
        metar = message.splitlines(True)[1].decode("utf-8").strip()
        
        print("-> %s" % metar)
        
        tokens = metar.split(' ')
        
        parse(tokens)


if __name__ == "__main__":
    main()
    