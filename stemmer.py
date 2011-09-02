#!/usr/bin/env python

import re

Vowels = ['a', 'e', 'i', 'o', 'u', 'y']

ValidLiEndings = ['c', 'd', 'e', 'g', 'h', 'k', 'm', 'n', 'r', 't']

class Suffix():
    def __init__(self, Target, Replacement, HasConditions):
        self.Target = Target    # the target suffix
        self.Replacement = Replacement  #what the replace(not always exact)
        self.HasConditions = HasConditions  #whether there are conditions
        self.Length = len(Target)

def Stem(Target):
    """removes the plural suffixes from words
    Ex: cameras -> camera
    """
    
    Target = Target.lower()
    Target = Target.strip()
    
    #check whether the word is a model number
    if not re.search("[^A-Za-z'-]", Target):
        #it's not a model number
        
        if len(Target) < 3:
            return Target
        
        #check for special ' characters cases
        if ord(Target[-1]) > 255 and Target[-2] == 's' and ord(Target[-3]) > 255:
            Target = Target[:-3] + "'s'"
        elif ord(Target[-2]) > 255 and Target[-1] == 's':
            Target = Target[:-2] + "'s"
        elif ord(Target[-1]) > 255:
            Target = Target[:-1] + "'"
            
        #remove ' at start of word if present
        if Target[0] == "'":
            Target = Target[1:]
            
        #resolve the y's as vowels or consonants
        Target = __ResolveY(Target)
        
        #carry out each step        
        Target = __Step0(Target)
        Target = __Step1a(Target)
        Target = __Step1c(Target)
        Target = __Step2(Target)
        Target = __Step5(Target)
        
        Target = Target.lower()
        Target = Target.strip()
        
    return Target
        
def __ResolveY(Target):
    if len(Target) == 0:
        return Target
    
    if Target[0] == 'y':
        Target = 'Y' + Target[1:]
            
    for i in range(len(Target) - 1):
        if Vowels.__contains__(Target[i]) and Target[i+1] == 'y':
            Target = Target[:i+1] + 'Y' + Target[i+2:]
    
    return Target

#STEPS

def __Step0(Target):
    if Target.endswith(s_0_1.Target): Target = Target[:-s_0_1.Length]
    elif Target.endswith(s_0_2.Target): Target = Target[:-s_0_2.Length]
    elif Target.endswith(s_0_3.Target): Target = Target[:-s_0_3.Length]
    
    return Target

def __Step1a(Target):
    if Target.endswith(s_1a_1.Target):Target = Target[:-2]
    elif Target.endswith(s_1a_3.Target):
        if len(Target) > 4:
            Target = Target[:-2]
        else:
            Target = Target[:-1]
    elif Target.endswith(s_1a_4.Target) or Target.endswith(s_1a_5.Target):
        pass
    elif Target.endswith(s_1a_6.Target):
        for i in range(len(Target)):
            if Vowels.__contains__(Target[i]) and i != len(Target) - 2:
                Target = Target[:-1]
                break
            
    return Target
    

def __Step1c(Target):
    if len(Target) < 3:
        return Target
    
    if Target.endswith('y') or Target.endswith('Y'):
        if not Vowels.__contains__(Target[-2]):
            Target = Target[:-1] + 'i'
            
    return Target

def __Step2(Target):
    R1 = __GetR(Target)
    
    suffixesInUse = [s_2_14, s_2_15, s_2_16, s_2_17, s_2_20, s_2_21]
    changed = False
    
    #do stuff with all the ones in the list
    for suffix in suffixesInUse:
        if Target.endswith(suffix.Target) and R1.__contains__(suffix.Target):
            Target = Target[:-suffix.Length] + suffix.Replacement
            changed = True
            break
    
    #treated different:
    if not changed and Target.endswith(s_2_23.Target) and R1.__contains__(s_2_23.Target):
        PrecedingString = Target[:-s_2_23.Length]
        if __HasValidLiEnding(PrecedingString):
            Target = Target[:-s_2_23.Length] + s_2_23.Replacement
            
    return Target

def __Step5(Target):
    R1 = __GetR(Target)
    R2 = __GetR(R1)
    
    if Target.endswith(s_5_1.Target):
        PrecedingString = Target[:-s_5_1.Length]
        if R2.__contains__(s_5_1.Target):
            Target = PrecedingString
        elif R1.__contains__(s_5_1.Target):
            if len(PrecedingString) > 2:
                PrecedingSyllable = PrecedingString[-3:]
            else:
                PrecedingSyllable = PrecedingString
                
            if not __IsShortSyllable(PrecedingSyllable):
                Target = PrecedingString
    elif Target.endswith(s_5_2.Target) and R2.__contains__(s_5_2.Target):
        PrecedingString = Target[:-s_5_2.Length]
        if PrecedingString.endswith("l"):
            Target = PrecedingString
    
    return Target

#UTILITY METHODS

def __HasValidLiEnding(Target):
    for validLiEnding in ValidLiEndings:
        if Target.endswith(validLiEnding):
            return True
    
    return False

def __GetR(Target):
    R = ''
    if len(Target) < 3:
        return R
    
    for i in range(1, len(Target)-1):
        if Vowels.__contains__(Target[i-1]) and not Vowels.__contains__(Target[i]):
            R = Target[i+1:]
            break
        
    return R

def __IsShortSyllable(Target):
    Exceptions = ['w', 'x', 'Y']
    
    if len(Target) < 2 or len(Target) > 3:
        return False
    
    if len(Target) == 2 and Vowels.__contains__(Target[0]) and not Vowels.__contains__(Target[1]):
        return True
    
    if len(Target) == 3 and not Vowels.__contains__(Target[0]) and Vowels.__contains__(Target[1]) and not Exceptions.__contains__(Target[2]) and not Vowels.__contains__(Target[2]):
        return True
    
    return False



# Step 0 strings.
s_0_1 = Suffix("'s'", "", False)
s_0_2 = Suffix("'s", "", False)
s_0_3 = Suffix("'", "", False)

        # Step 1a strings.
s_1a_1 = Suffix("sses", "ss", False)
s_1a_2 = Suffix("ied", "i/ie", True)
s_1a_3 = Suffix("ies", "i/ie", True)
s_1a_4 = Suffix("us", "us", False)
s_1a_5 = Suffix("ss", "ss", False)
s_1a_6 = Suffix("s", "", True)

        # Step 2 strings.
        # 7 characters.
s_2_1 = Suffix("ational", "ate", False)
s_2_2 = Suffix("ization", "ize", False)
s_2_3 = Suffix("fulness", "ful", False)
s_2_4 = Suffix("iveness", "ive", False)
        # 6 characters.
s_2_5 = Suffix("tional", "tion", False)
s_2_6 = Suffix("biliti", "ble", False)
s_2_7 = Suffix("lessli", "less", False)
        # 5 characters.
s_2_8 = Suffix("entli", "ent", False)
s_2_9 = Suffix("ation", "ate", False)
s_2_10 = Suffix("alism", "al", False)
s_2_11 = Suffix("aliti", "al", False)
s_2_12 = Suffix("ousli", "ous", False)
s_2_13 = Suffix("iviti", "ive", False)
s_2_14 = Suffix("fulli", "fully", False)
        # 4 characters.
s_2_15 = Suffix("enci", "ency", False)
s_2_16 = Suffix("anci", "ancy", False)
s_2_17 = Suffix("abli", "ably", False)
s_2_18 = Suffix("izer", "ize", False)
s_2_19 = Suffix("ator", "ate", False)
s_2_20 = Suffix("alli", "ally", False)
        # 3 characters.
s_2_21 = Suffix("bli", "bly", False)
s_2_22 = Suffix("ogi", "og", True)
        # 2 characters.
s_2_23 = Suffix("li", "ly", True)

        # Step 5 strings.
s_5_1 = Suffix("e", "", True)
s_5_2 = Suffix("l", "", True)
