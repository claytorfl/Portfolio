from random import *
from .models import *
from chem.models import *
from django.utils import timezone
from django.contrib.auth.models import User, Group
from re import *

#The utility.py file has various functions that are used throughout the Django app
#Currently only keyreplace is used, the rest

#Replaces a parameter key with a value
#Used with parameters
def keyreplace(strn, key, value):
    p = compile('{'+key+'}')
    newtext = p.sub(str(value), strn)
    return newtext

# Gives a random nubmer between begin and end with rounding decimals
def rand(begin, end, rounding):
    return round(random()*(end-begin)+begin, rounding)

#Returns a random number that is within the range of number-variance : number+variance
def rando(number, variance, rounding):
    return round(number + variance - random.random()*2*variance, rounding)


#Function that takes a string of numbers as input and outputs the number of significant digits
def sigfig(strnum):
        if '.' not in strnum:
            zerocount = 0
            index = -1
            while strnum[index] == "0" and abs(index) <= len(strnum):
                zerocount += 1
                index -= 1
            return len(strnum)-zerocount
        else:
            splitnum = strnum.split(".")
            decnum = splitnum[1]
            if splitnum[0] != "0":
                return len(strnum)-1
            else:
                zerocount = 0
                index = 0
                while decnum[index] == "0" and index < len(decnum):
                    zerocount += 1
                    index += 1
                return len(decnum) - zerocount



#Removes significant digits from a string number so that it has a target number of significant digits
def removesigfig(number, targetnumber):
    currentnumber = sigfig(number)
    toberemoved = currentnumber - targetnumber

    #If no sigfigs have to be removed return the number unchanged
    if toberemoved <= 0:
        return number

    #Each time through the for loop should remove one significant digit
    for x in range(toberemoved):

        #If there is a decimal you can remove significant digits by removing the last charactero of number
        if '.' in number:
            removed = eval(number[-1])
            number = number[:-2]

            #If after removing the last character the last character of number is now a decimal point remove that too
            if number[-1]=='.':
                number = number[:-2]

            #If the number being removed is the last significant digit to be removed and is above 5 round up
            if removed >= 5 and sigfig(number) == targetnumber:
                #If there is a decimal in the number round it up
                if '.' in number:
                    number = str(eval(number)+10**-(len(number)-number.index('.')-1))
                    if '.' not in number:
                        number += ".0"
                else:
                    number = str(eval(number)+1)
        else:

            #If there is no decimal then find the nonzero character closest to the right and replace it with zero
            #to get rid of a significant digit
            index = -1
            while number[index] == '0':
                index-=1
            numlist = list(number)
            removed = eval(numlist[index])
            numlist[index] = '0'
            number = ''.join(numlist)

            #If the number removed was greater than five and the last significant digit to go then round the number up
            if removed >= 5 and sigfig(number)==targetnumber:
                number = str(eval(number)+10**(abs(index)))
    return removesigfig(number, targetnumber)

#Finds the number of significant digits in a string form of scientific notation
#Like 4.07 * 10^5 would return 3 because it has 3 significant digits
def scisigfig(scistring):
    multop = '*'
    if 'x' in scistring:
        multop = "x"
    if '*' in scistring:
        multop = "*"
    number = scistring.split(multop)[0].strip()
    length = len(number)
    if '.' in number:
        length -= 1
    return length

#Evaluates scientific notation string of form 12.07 * 10^5
def scieval(scistring):
    scilist = list(scistring)
    scilist[scilist.index('^')] = "**"
    return eval(''.join(scilist))


#Returns the power of 10 associated with the metric prefix
def prefixnum(prefix):
    if prefix=='Y':
        return 24
    if prefix=='Z':
        return 21
    if prefix=='E':
        return 18
    if prefix=='P':
        return 15
    if prefix=='T':
        return 12
    if prefix=='G':
        return 9
    if prefix=='M':
        return 6
    if prefix=='k':
        return 3
    if prefix=='d':
        return -1
    if prefix=='c':
        return -2
    if prefix=='m':
        return -3
    if prefix=='u':
        return -6
    if prefix=='n':
        return -9
    if prefix=='p':
        return -12
    if prefix=='f':
        return -15
    if prefix=='a':
        return -18
    if prefix=='z':
        return -21
    if prefix=='y':
        return -24

#Function to convert the units of a number
def convert(number, unit1, unit2):
    if unit1==unit2:
        return number
    if not(unit1 and unit2):
        return False
    if unit1[-1]!=unit2[-1]:
        return False
    powerten1 = 0
    powerten2 = 0
    if len(unit1)>1:
        powerten1 = prefixnum(unit1[0])
    if len(unit2)>1:
        powerten2 = prefixnum(unit2[0])
    return round(number*10**(powerten1-powerten2), len(str(number)))