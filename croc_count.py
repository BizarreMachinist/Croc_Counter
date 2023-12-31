def expand_instruction(instruct):
  while -1 != instruct.find('['):
    start = instruct.find('[')
    end = instruct.find(']')
    timesStart = instruct.find('*')
    timesEnd = instruct[timesStart:].find(',')

    if -1 == timesEnd:
      times = instruct[timesStart+1:]
      rest = ""
    else:
      times = instruct[timesStart+1:timesStart+timesEnd]
      rest = instruct[timesStart+timesEnd:]
    
    copy = (instruct[start+1:end]+",")*int(times)
    instruct = instruct[0:start] + copy[0:-1] + rest

  return instruct

def read_instruction(instruct, totalRound, totalOverall, lineNumber):
  instruct = instruct.replace("tr", "trc")

  instruct = instruct.replace("ch", "A")
  instruct = instruct.replace("slst", "B")
  instruct = instruct.replace("sc", "C")
  instruct = instruct.replace("hdc", "D")
  instruct = instruct.replace("dc", "E")
  instruct = instruct.replace("trc", "F")
  instruct = instruct.replace("inc", "G")
  instruct = instruct.replace("dec", "H")
  instruct = instruct.replace("turn", "I")
  instruct = instruct.replace("join", "J")
  instruct = instruct.replace("rep", "K")
  instruct = instruct.replace("mr", "L")

  instruct = expand_instruction(instruct)
  if -1 != instruct.find(']'):
    print("Spare ']' found at line %s" % lineNumber)
    return -1, -1

  instruct = instruct[::-1]
  bleh = instruct
  instruct = instruct.split(',')
  instructSize = len(instruct)
  totalRoundOld = totalRound
  i = 0
  k = 0
  while i < totalRoundOld:
    j = instruct[k%instructSize]
    match j[0]:
      case "L":
        totalRound += int(j[:0:-1])-1
      case "G":
        try:
          totalRound += int(j[:0:-1])-1
        except:
          totalRound += 1
      case "H":
        try:
          totalRound -= int(j[:0:-1])-1
        except:
          totalRound -= 1
      case "C":
        try:
          i += int(j[:0:-1])-1
        except:
          pass
      case _:
        pass
    i += 1
    k += 1

  # print("instruct " + bleh +" total round " + str(totalRound) + " total total " + str(totalOverall))

  return totalRound, totalOverall

def croc_count(inFile, outFile):
  buffer = ""               #entire output file
  lineNumber = 0            #current file line number
  totalRound = 1            #crochet number for this round
  totalOverall = 0          #total crochet number
  lineArray = ["", "", ""]  #parsed line [<round number>,<instruction>,<comment>]

  for lineRaw in inFile:
    lineStripped = lineRaw.lstrip(' ').rstrip(' ')
    lineNumber += 1
    
    if lineStripped[0] == '{': #if a new header started
      temp = lineStripped.split('#')[0].find('}')
      if -1 == temp:           #if there is no closing bracket, raise error
        print("Missing closing bracket at line %s" % lineNumber)
        break

      totalRound = 1   #reset round total
      totalOverall = 0 #reset overall total
      # <NOTE> This is where we can do something with the block name lineStripped[1:temp]
      buffer += lineRaw

    elif lineStripped[0].isalnum():
      temp = lineStripped.find('#')
      if -1 != temp:
        lineArray[2] = " " + lineStripped[temp:]
        lineStripped = lineStripped[0:temp].rstrip(' ')
      else:
        lineArray[2] = "\n"

      lineStripped = lineStripped.replace(' ', '')
      posColon = lineStripped.find(':')
      if -1 == posColon:
        print("Colon not found after round number at line %s" % lineNumber)
        break
      lineArray[0] = lineStripped[0:posColon]
      if not lineArray[0].isalnum():
        print("Round number is not alpha numeric at line %s" % lineNumber)
        break

      lineArray[1] = lineStripped.split('(')[0][posColon+1:].rstrip()

      totalRound, totalOverall = read_instruction(lineArray[1], totalRound, totalOverall, lineNumber)
      if -1 == totalRound:
        break

      totalOverall += totalRound

      buffer += lineArray[0] +": "+ lineArray[1].replace(",", ", ") +" ("+ str(totalRound) +", "+ str(totalOverall) +")"+ lineArray[2]

    else:               #it's either a comment or blank line
      buffer += lineRaw #just append it

  else:
    outFile.write(buffer)

ptn = open("raw.croc", 'r')
file = open("pattern.croc", 'w')
croc_count(ptn, file)
ptn.close()
file.close()