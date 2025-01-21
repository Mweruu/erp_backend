'''
Created on Jan 8, 2020

@author: Zuhair Hammadi
'''
import re
import math

class CurrencyInfo():
    
    def __init__(self, currency):
        
        if isinstance(currency, dict):
            for name, value in currency.items():
                setattr(self, name, value)
            
        elif currency == 'AED' :
            self.currencyCode = currency;
            self.isCurrencyNameFeminine = False;
            self.englishCurrencyName = "UAE Dirham";
            self.englishPluralCurrencyName = "UAE Dirhams";
            self.englishCurrencyPartName = "Fils";
            self.englishPluralCurrencyPartName = "Fils";
            self.arabic1CurrencyName = "درهم إماراتي";
            self.arabic2CurrencyName = "درهمان إماراتيان";
            self.arabic310CurrencyName = "دراهم إماراتية";
            self.arabic1199CurrencyName = "درهماً إماراتياً";
            self.arabic1CurrencyPartName = "فلس";
            self.arabic2CurrencyPartName = "فلسان";
            self.arabic310CurrencyPartName = "فلوس";
            self.arabic1199CurrencyPartName = "فلساً";
            self.partPrecision = 2;
            self.isCurrencyPartNameFeminine = False;                    
    
        elif currency == 'JOD' : 
            self.currencyCode = currency;
            self.isCurrencyNameFeminine = False;
            self.englishCurrencyName = "Jordanian Dinar";
            self.englishPluralCurrencyName = "Jordanian Dinars";
            self.englishCurrencyPartName = "Fils";
            self.englishPluralCurrencyPartName = "Fils";
            self.arabic1CurrencyName = "دينار أردني";
            self.arabic2CurrencyName = "ديناران أردنيان";
            self.arabic310CurrencyName = "دنانير أردنية";
            self.arabic1199CurrencyName = "ديناراً أردنياً";
            self.arabic1CurrencyPartName = "فلس";
            self.arabic2CurrencyPartName = "فلسان";
            self.arabic310CurrencyPartName = "فلوس";
            self.arabic1199CurrencyPartName = "فلساً";
            self.partPrecision = 3;
            self.isCurrencyPartNameFeminine = False;

        elif currency == 'BHD' :
            self.currencyCode = currency
            self.isCurrencyNameFeminine = False;
            self.englishCurrencyName = "Bahraini Dinar";
            self.englishPluralCurrencyName = "Bahraini Dinars";
            self.englishCurrencyPartName = "Fils";
            self.englishPluralCurrencyPartName = "Fils";
            self.arabic1CurrencyName = "دينار بحريني";
            self.arabic2CurrencyName = "ديناران بحرينيان";
            self.arabic310CurrencyName = "دنانير بحرينية";
            self.arabic1199CurrencyName = "ديناراً بحرينياً";
            self.arabic1CurrencyPartName = "فلس";
            self.arabic2CurrencyPartName = "فلسان";
            self.arabic310CurrencyPartName = "فلوس";
            self.arabic1199CurrencyPartName = "فلساً";
            self.partPrecision = 3;
            self.isCurrencyPartNameFeminine = False;
            
        elif currency ==  'SAR' :
            self.currencyCode = currency;    
            self.isCurrencyNameFeminine = False;
            self.englishCurrencyName = "Saudi Riyal";
            self.englishPluralCurrencyName = "Saudi Riyals";
            self.englishCurrencyPartName = "Halala";
            self.englishPluralCurrencyPartName = "Halalas";
            self.arabic1CurrencyName = "ريال سعودي";
            self.arabic2CurrencyName = "ريالان سعوديان";
            self.arabic310CurrencyName = "ريالات سعودية";
            self.arabic1199CurrencyName = "ريالاً سعودياً";
            self.arabic1CurrencyPartName = "هللة";
            self.arabic2CurrencyPartName = "هللتان";
            self.arabic310CurrencyPartName = "هللات";
            self.arabic1199CurrencyPartName = "هللة";
            self.partPrecision = 2;
            self.isCurrencyPartNameFeminine = True;
            
        elif currency == 'SYP' :
            self.currencyCode = currency;
            self.isCurrencyNameFeminine = True;
            self.englishCurrencyName = "Syrian Pound";
            self.englishPluralCurrencyName = "Syrian Pounds";
            self.englishCurrencyPartName = "Piaster";
            self.englishPluralCurrencyPartName = "Piasteres";
            self.arabic1CurrencyName = "ليرة سورية";
            self.arabic2CurrencyName = "ليرتان سوريتان";
            self.arabic310CurrencyName = "ليرات سورية";
            self.arabic1199CurrencyName = "ليرة سورية";
            self.arabic1CurrencyPartName = "قرش";
            self.arabic2CurrencyPartName = "قرشان";
            self.arabic310CurrencyPartName = "قروش";
            self.arabic1199CurrencyPartName = "قرشاً";
            self.partPrecision = 2;
            self.isCurrencyPartNameFeminine = False; 

        else:
            self.currencyCode = currency;
            self.isCurrencyNameFeminine = False;
            self.englishCurrencyName = "Dinar";
            self.englishPluralCurrencyName = "Dinars";
            self.englishCurrencyPartName = "Fils";
            self.englishPluralCurrencyPartName = "Fils";
            self.arabic1CurrencyName = "دينار ";
            self.arabic2CurrencyName = "ديناران ";
            self.arabic310CurrencyName = "دنانير ";
            self.arabic1199CurrencyName = "دينارا ";
            self.arabic1CurrencyPartName = "فلس";
            self.arabic2CurrencyPartName = "فلسان";
            self.arabic310CurrencyPartName = "فلس";
            self.arabic1199CurrencyPartName = "فلسا";
            self.partPrecision = 3;
            self.isCurrencyPartNameFeminine = False;
            
    def getPartPrecision(self):
        return self.partPrecision

class NumberToArabic():
    englishPrefixText = ""
    englishSuffixText = "only."
    arabicPrefixText = ""
    arabicSuffixText = "لا غير."
        
    englishOnes =[
         "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
         "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"
    ]

    englishTens = [
         "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"
    ]
    
    englishGroup = [
         "Hundred", "Thousand", "Million", "Billion", "Trillion", "Quadrillion", "Quintillion", "Sextillian",
         "Septillion", "Octillion", "Nonillion", "Decillion", "Undecillion", "Duodecillion", "Tredecillion",
         "Quattuordecillion", "Quindecillion", "Sexdecillion", "Septendecillion", "Octodecillion", "Novemdecillion",
         "Vigintillion", "Unvigintillion", "Duovigintillion", "10^72", "10^75", "10^78", "10^81", "10^84", "10^87",
         "Vigintinonillion", "10^93", "10^96", "Duotrigintillion", "Trestrigintillion"
    ]
    
    arabicOnes =[
         "", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة",
         "عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"
    ]

    arabicFeminineOnes = [
         "", "إحدى", "اثنتان", "ثلاث", "أربع", "خمس", "ست", "سبع", "ثمان", "تسع",
         "عشر", "إحدى عشرة", "اثنتا عشرة", "ثلاث عشرة", "أربع عشرة", "خمس عشرة", "ست عشرة", "سبع عشرة", "ثماني عشرة", "تسع عشرة"
    ]

    arabicTens = [
         "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"
    ]

    arabicHundreds = [
         "", "مائة", "مئتان", "ثلاثمائة", "أربعمائة", "خمسمائة", "ستمائة", "سبعمائة", "ثمانمائة","تسعمائة"
    ]

    arabicAppendedTwos = [
         "مئتا", "ألفا", "مليونا", "مليارا", "تريليونا", "كوادريليونا", "كوينتليونا", "سكستيليونا"
    ]

    arabicTwos = [
         "مئتان", "ألفان", "مليونان", "ملياران", "تريليونان", "كوادريليونان", "كوينتليونان", "سكستيليونان"
    ]

    arabicGroup =[
         "مائة", "ألف", "مليون", "مليار", "تريليون", "كوادريليون", "كوينتليون", "سكستيليون"
    ]

    arabicAppendedGroup = [
         "", "ألفاً", "مليوناً", "ملياراً", "تريليوناً", "كوادريليوناً", "كوينتليوناً", "سكستيليوناً"
    ]

    arabicPluralGroups = [
         "", "آلاف", "ملايين", "مليارات", "تريليونات", "كوادريليونات", "كوينتليونات", "سكستيليونات"
    ]
    
     
    def numberToArabic(self, number, currency, englishPrefixText, englishSuffixText, arabicPrefixText, arabicSuffixText) : 
        self.englishPrefixText = englishPrefixText;
        self.englishSuffixText = englishSuffixText;
        self.arabicPrefixText = arabicPrefixText;
        self.arabicSuffixText = arabicSuffixText;

        self.extractIntegerAndDecimalParts()
    
    
    def extractIntegerAndDecimalParts(self) :      
        splits = re.split("\\.", str(self.number));

        self._intergerValue = int(splits[0])

        if len(splits) > 1:
            self._decimalValue = int(self.getDecimalValue(splits[1]))
        else:
            self._decimalValue = 0;

    
    def getDecimalValue(self, decimalPart):
        result = "";

        if self.currencyInfo.getPartPrecision() != len(decimalPart) :
            decimalPartLength = len(decimalPart)

            for i in range(0, self.currencyInfo.getPartPrecision()  - decimalPartLength):  # @UnusedVariable
                decimalPart += "0"; #Fix for 1 number after decimal ( 10.5 , 1442.2 , 375.4 ) 

            dec = len(decimalPart) <= self.currencyInfo.getPartPrecision() and len(decimalPart) or self.currencyInfo.getPartPrecision();
            result = decimalPart[:dec]
        
        else:
            result = decimalPart;

        for i in range(len(result), self.currencyInfo.getPartPrecision()):  # @UnusedVariable
            result += "0";

        return result;
    
    def processGroup(self, groupNumber):
        tens = groupNumber % 100;

        hundreds = groupNumber / 100;

        retVal = "";

        if (hundreds > 0):
            retVal = "%s %s" % (self.englishOnes[hundreds], self.englishGroup[0])
        
        if (tens > 0):
            if (tens < 20):
                retVal += ((retVal != "") and " " or "") + self.englishOnes[tens];
        
            else:
                ones = tens % 10;

                tens = (tens / 10) - 2; # 20's offset

                retVal += ((retVal != "") and " " or "") + self.englishTens[tens];

                if (ones > 0):
                    retVal += ((retVal != "") and " " or "") + self.englishOnes[ones];
                
            

        return retVal;
    
    
    def getDigitFeminineStatus(self, digit, groupLevel):
        if (groupLevel == -1) : # if it is in the decimal part
            if (self.currencyInfo.isCurrencyPartNameFeminine):
                return self.arabicFeminineOnes[digit] # use feminine field
            else:
                return self.arabicOnes[digit];
        
        else:
            if (groupLevel == 0) :
                if (self.currencyInfo.isCurrencyNameFeminine):
                    return self.arabicFeminineOnes[digit] # use feminine field
                else:
                    return self.arabicOnes[digit]
            else:
                return self.arabicOnes[digit]

    
    def processArabicGroup(self, groupNumber, groupLevel, remainingNumber) :
        tens = groupNumber % 100;

        hundreds = groupNumber // 100;                

        retVal = "";
        
        _intergerValue = self._intergerValue

        if (hundreds > 0):
            if (tens == 0 and hundreds == 2): #// حالة المضاف
                retVal = "%s" % self.arabicAppendedTwos[0]
            else: #  الحالة العادية
                retVal = "%s" % self.arabicHundreds[hundreds];
        
        if (tens > 0):
            if (tens < 20) : # if we are processing under 20 numbers
                if (tens == 2 and hundreds == 0 and groupLevel > 0) : #// This is special case for number 2 when it comes alone in the group
                    if (_intergerValue == 2000 or _intergerValue == 2000000 or _intergerValue == 2000000000 or _intergerValue == 2000000000000 or _intergerValue == 2000000000000000 or _intergerValue == 2000000000000000000):
                        retVal = "%s" % self.arabicAppendedTwos[groupLevel] #// في حالة الاضافة
                    else:
                        retVal = "%s" % self.arabicTwos[groupLevel]#//  في حالة الافراد
                else : #// General case
                    if (retVal != ""):
                        #//retVal += " و ";
                        retVal += " و"

                    if (tens == 1 and groupLevel > 0 and hundreds == 0):
                        retVal += " "
                    else:
                        if ((tens == 1 or tens == 2) and (groupLevel == 0 or groupLevel == -1) and hundreds == 0 and remainingNumber == 0):
                            retVal += "" #// Special case for 1 and 2 numbers like: ليرة سورية و ليرتان سوريتان
                        else:
                            retVal += self.getDigitFeminineStatus(tens, groupLevel)#// Get Feminine status for this digit
                            
            else:
                ones = tens % 10;
                tens = (tens // 10) - 2; #// 20's offset

                if (ones > 0):
                    if (retVal != ""):
                        #retVal += " و ";
                        retVal += " و";

                    #// Get Feminine status for this digit
                    retVal += self.getDigitFeminineStatus(ones, groupLevel);
                
                if (retVal != ""):
                    #//retVal += " و ";
                    retVal += " و";

                #// Get Tens text
                retVal += self.arabicTens[tens];

        return retVal;
    
    
    def convertToArabic(self, value, currencyCode = 'SAR'):
            
        currency = currencyCode;
        self.currencyInfo = CurrencyInfo(currency);
        self.number = round(value, self.currencyInfo.getPartPrecision());
        
        self.numberToArabic(self.number, self.currencyInfo, self.englishPrefixText, self.englishSuffixText, self.arabicPrefixText, self.arabicSuffixText);
        
        return self._convertToArabic();
    
    def _convertToArabic(self):
        tempNumber = self.number;

        if (tempNumber == 0):
            return "صفر";

        #// Get Text for the decimal part
        decimalString = self.processArabicGroup(self._decimalValue, -1, 0);

        retVal = ""; 
        group = 0;
        while (tempNumber > 0):
        
            #// seperate number into groups
            numberToProcess = int(tempNumber % 1000) 

            tempNumber = int(tempNumber // 1000)

            #// convert group into its text
            groupDescription = self.processArabicGroup(numberToProcess, group, math.floor(tempNumber))

            if (groupDescription != ""):
            # // here we add the new converted group to the previous concatenated text
                if (group > 0):
                
                    if (retVal != ""):
                        retVal = "%s%s" % ("و", retVal);

                    if (numberToProcess != 2):
                    
                        if (numberToProcess % 100 != 1):
                        
                            if (numberToProcess >= 3 and numberToProcess <= 10) : #// for numbers between 3 and 9 we use plural name
                                retVal = "%s %s" % (self.arabicPluralGroups[group], retVal);
                            
                            else:
                            
                                if (retVal != ""): #// use appending case
                                    retVal = "%s %s" % (self.arabicAppendedGroup[group], retVal);
                                else:
                                    retVal = "%s %s" % (self.arabicGroup[group], retVal); # // use normal case
                            
                        
                        else:
                            retVal = "%s %s" % (self.arabicGroup[group], retVal); #// use normal case
                    
                

                retVal = "%s %s" % (groupDescription, retVal);
            

            group +=1;
        

        formattedNumber = "";
        formattedNumber += (self.arabicPrefixText != "") and "%s " % self.arabicPrefixText or "";
        formattedNumber += (retVal != "") and retVal or "";
        if (self._intergerValue != 0):
        #{ // here we add currency name depending on _intergerValue : 1 ,2 , 3--->10 , 11--->99
            remaining100 = (self._intergerValue % 100);

            if (remaining100 == 0):
                formattedNumber += self.currencyInfo.arabic1CurrencyName;
            else:
                if (remaining100 == 1):
                    formattedNumber += self.currencyInfo.arabic1CurrencyName;
                else:
                    if (remaining100 == 2):
                    
                        if (self._intergerValue == 2):
                            formattedNumber += self.currencyInfo.arabic2CurrencyName;
                        else:
                            formattedNumber += self.currencyInfo.arabic1CurrencyName;
                    
                    else:
                        if (remaining100 >= 3 and remaining100 <= 10):
                            formattedNumber += self.currencyInfo.arabic310CurrencyName;
                        else:
                            if (remaining100 >= 11 and remaining100 <= 99):
                                formattedNumber += self.currencyInfo.arabic1199CurrencyName;
        
        formattedNumber += (self._decimalValue != 0) and " و" or "";
        formattedNumber += (self._decimalValue != 0) and decimalString or "";
        if (self._decimalValue != 0):
        #{ // here we add currency part name depending on _intergerValue : 1 ,2 , 3--->10 , 11--->99
            formattedNumber += " ";

            remaining100 = (self._decimalValue % 100);

            if (remaining100 == 0):
                formattedNumber += self.currencyInfo.arabic1CurrencyPartName;
            else:
                if (remaining100 == 1):
                    formattedNumber += self.currencyInfo.arabic1CurrencyPartName;
                else:
                    if (remaining100 == 2):
                        formattedNumber += self.currencyInfo.arabic2CurrencyPartName;
                    else:
                        if (remaining100 >= 3 and remaining100 <= 10):
                            formattedNumber += self.currencyInfo.arabic310CurrencyPartName;
                        else:
                            if (remaining100 >= 11 and remaining100 <= 99):
                                formattedNumber += self.currencyInfo.arabic1199CurrencyPartName;
        
        formattedNumber += (self.arabicSuffixText != "") and " %s" % self.arabicSuffixText or "";

        return formattedNumber;

def amount_to_text_ar(value, currencyCode = 'SAR'):
    a = NumberToArabic()
    return a.convertToArabic(value, currencyCode)

def en_to_ar(value):
    if not isinstance(value, str):
        value = str(value)
    if not value:
        return value
    
    digits_map = {
        "0": "٠",
        "1": "١",
        "2": "٢",
        "3": "٣",
        "4": "٤",
        "5": "٥",
        "6": "٦",
        "7": "٧",
        "8": "٨",
        "9": "٩",
    }
    
    pattern = re.compile("|".join(digits_map.keys()))
        
    return pattern.sub(lambda x: digits_map[x.group()], value)
