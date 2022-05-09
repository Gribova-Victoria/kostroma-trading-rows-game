# -*- coding: utf-8 -*-
import code_analyzer

allText = ""
with open("scenery.txt", "r", encoding='utf-8') as file:
    allText = file.read()
    print(allText)
    
analyzer = code_analyzer.CodeAnalyzer()
analyzed = analyzer.get_words(allText)[0]
print(len(analyzed))
krtForParsing = analyzer.get_words_for_parsing(analyzed)
print(len(krtForParsing))
print(krtForParsing)
