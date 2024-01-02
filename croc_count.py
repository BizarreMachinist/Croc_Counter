class crocFile:
  def __init__(self, sourceFile:str):
    try:
      self.file = open(sourceFile, "r") # open file supplied
    except Exception as err:
      self.file = ""
      print(f"Unexpected {err=}, {type(err)=}")

    self.line       = ""  # current file line
    self.lineNumber = 0   # current file line number
    self.round      = 1   # stitches on current round
    self.total      = 0   # stitches in total
    self.buffer     = ""  # output buffer

  # check if the source file is open
  def is_open(self):
    if not self.file: return False
    else:             return True

  # read next file line, store it, and inc line number
  def read(self):
    self.line = self.file.readline()
    if not self.line:
      return False
    self.lineNumber += 1
    return True

  # check if the current line is a header, instruction, or comments
  def is_code(self):
    if '{' == self.line[0]:      return 2
    elif self.line[0].isalnum(): return 1
    else:                        return 0

  # add a string or array to the buffer
  def append(self, strings, *, prepend:str = "", postpend:str = "", interpend:str = ""):
    if list == type(strings):
      self.buffer += prepend
      length       = len(strings)

      for i in range(length):
        self.buffer += str(strings[i])
        if i < length-1:
          self.buffer += interpend
      self.buffer += postpend

    elif strings:
      self.buffer += prepend + strings + postpend

  # close file
  def close(self):
    if not self.file.closed:
      self.file.close()

  def __del__(self):
    if self.file:
      if not self.file.closed:
        self.file.close()

# extract the round number, instruction, and comment
def partition(line:str):
  rnd         = ""
  instruction = ""
  comment     = ""
  temp        = line.lstrip().rstrip()

  i = temp.find('#')
  if -1 != i:
    temp    = [temp[:i], temp[i:]]
    comment = temp[1]
    temp    = temp[0].replace(' ', '')
  else:
    temp = temp.replace(' ', '')

  i    = temp.find(':')
  temp = [temp[:i], temp[i+1:]]
  rnd  = temp[0]

  i = temp[1].find('(')
  if -1 != i:
    instruction = temp[1][:i]
  else:
    instruction = temp[1]

  return rnd, instruction, comment

# make the instruction simpler with substitution
def substitute(instruction):
  replace = {
    "ch"  :"A",
    "slst":"B",
    "sc"  :"C",
    "hdc" :"D",
    "dc"  :"E",
    "trc" :"F",
    "tr"  :"F",
    "inc" :"G",
    "dec" :"H",
    "turn":"I",
    "join":"J",
    "rep" :"K",
    "mr"  :"L"
  }
  for old, new in replace.items():
    instruction = instruction.replace(old, new)

  return instruction

# multiply in the scale to the pattern
def expand(instruction):
  bracketStart = instruction.find('[')
  while -1 != bracketStart:
    bracketEnd = instruction.find(']')
    scaleEnd   = instruction[bracketEnd+1:].find(',')

    if -1 == bracketEnd:
      return 0, "Found an opening bracket.... but no closing one. Put one"
    elif '*' != instruction[bracketEnd+1]:
      return 0, "Put an asterisk after the closing bracket"

    bracket = instruction[bracketStart+1:bracketEnd].split(',')
    if not bracket:
      return 0, "If you put brackets, make sure there's something inside them mate"

    if -1 == scaleEnd:
      scale     = instruction[bracketEnd+2:]
      remainder = ""
    else:
      scale     = instruction[bracketEnd+2:bracketEnd+scaleEnd+1]
      remainder = instruction[bracketEnd+scaleEnd+1:]

    if not scale:
      return 0, "You can't multiply by nothing. I need a number"
    if not scale.isnumeric():
      return 0, "The *number* after the '*' needs to be a *number*. That's where the word **number** comes in"

    if 0 != bracketStart:
      instruction = instruction[:bracketStart]
    else:
      instruction = ""

    firstTime = True
    for i in bracket:
      if 1 != len(i):
        coefficient = i[:-1]
      else:
        coefficient = "1"
      if not coefficient.isnumeric():
        return 0, "The coefficient is not a number"
      
      if firstTime:
        instruction += str(int(coefficient)*int(scale)) + i[-1]
        firstTime    = False
      else:
        instruction += "," + str(int(coefficient)*int(scale)) + i[-1]
    instruction += remainder

    bracketStart = instruction.find('[')

  if ']' in instruction:
    return 0, "Spare closing bracket found. Leave no survivors"

  return instruction

# counts the stitches in a round and in total
def count_stitches(instruction, rnd, total):
  instruction = instruction.split(',')
  width       = 0
  increase    = 0

  for i in instruction:
    if 1 == len(i):
      i = "1" + i
    if not i[:-1].isnumeric():
          return 0, "Coefficient needs to be a number please!"

    match i[-1]:
      case 'G':
        increase += int(i[:-1])
      case 'H':
        increase -= int(i[:-1])
      case 'L':
        return [int(i[:-1]), int(i[:-1])]
      case _:
        pass

    width += int(i[:-1])

  if width > rnd:
    return 0, "Too many stitches in this round. It can't matchup to the previous round"

  k       = width
  repeats = 1
  while (rnd-k) > 0:
    k       += width
    repeats += 1

  if (k-rnd) > 0:
    return 0, "Needs more crochets to complete, suggestion: {0}sc\nInstruction repeated: {1} times".format(rnd-(k-width), repeats-1)

  totals = [(width+increase)*repeats, total+(width+increase)*repeats]
  return totals

def croc_count(pattern, outFile):

  while pattern.read():
    path = pattern.is_code()

    if 2 == path:
      pattern.round = 0
      pattern.total = 0
      pattern.append(pattern.line)
      # <NOTE> this is where we can do something with the header

    elif 1 == path:
      rnd, instructionRaw, comment = partition(pattern.line)

      instruction = substitute(instructionRaw)
      instruction = expand(instruction)
      if not instruction[0]:
        print("Error at line {0}\nInstruction was: {1}\nError: {2}".format(pattern.lineNumber, pattern.line.rstrip(), instruction[1]))
        outFile.write("Error at line {0}\nInstruction was: {1}\nError: {2}".format(pattern.lineNumber, pattern.line.rstrip(), instruction[1]))
        break

      totals = count_stitches(instruction, pattern.round, pattern.total)
      if not totals[0]:
        print("Error at line {0}\nInstruction was: {1}\nError: {2}".format(pattern.lineNumber, pattern.line.rstrip(), totals[1]))
        outFile.write("Error at line {0}\nInstruction was: {1}\nError: {2}".format(pattern.lineNumber, pattern.line.rstrip(), totals[1]))
        break
      pattern.round, pattern.total = totals

      pattern.append(rnd, postpend = ": ")
      pattern.append(instructionRaw.split(','), interpend = ', ')
      pattern.append(totals, prepend = " (", interpend = ", ", postpend = ")")
      pattern.append(comment, prepend = " ")
      pattern.append("\n")
    else:
      pattern.append(pattern.line)
      continue

  else:
    print("All passed. Writing to file!")
    outFile.write(pattern.buffer)

if "__main__" == __name__:
  file = input("Drag and drop your .croc in here....")
  pattern = crocFile(file)
  if not pattern.is_open():
    print("Can't find the file to open")
    quit()
  
  patternOut = open("pattern.croc", 'w')

  croc_count(pattern, patternOut)
  patternOut.close()