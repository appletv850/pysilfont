#!/usr/bin/env python 
'''Demo script for UFOlib to add a gylph to a UFO font'''
__url__ = 'http://github.com/silnrsi/pysilfont'
__copyright__ = 'Copyright (c) 2015, SIL International  (http://www.sil.org)'
__license__ = 'Released under the MIT License (http://opensource.org/licenses/MIT)'
__author__ = 'David Raymond'
__version__ = '0.0.1'

from silfont.genlib import *
from silfont.UFOlib import *

argspec = [
    ('ifont',{'help': 'Input font file'}, {'type': 'infont'}),
    ('ofont',{'help': 'Output font file','nargs': '?' }, {'type': 'outfont', 'def': '_addGylph'}),
    ('-l','--log',{'help': 'Log file'}, {'type': 'outfile', 'def': '_UFOconvert.log'}),
    ('-v','--version',{'help': 'UFO version to output'},{}),
    ('-p','--params',{'help': 'Font output parameters','action': 'append'}, {'type': 'optiondict'})]

def doit(args) :
    ''' This will add the following glyph to the font

    <?xml version="1.0" encoding="UTF-8"?>
    <glyph name="Test" format="1">
    <unicode hex="007D"/>
    <outline>
    <contour>
      <point x="275" y="1582" type="line"/>
      <point x="275" y="-493" type="line"/>
    </contour>
    </outline>
    </glyph>
    '''

    font = args.ifont
 
    # Create basic glyph
    newglyph = Uglif(layer=font.deflayer)
    newglyph.inxmlstr = '<glyph name="Test" format="2">\n<unicode hex="007D"/>/n</glyph>'
    newglyph.etree = ET.fromstring(newglyph.inxmlstr) # Could also be done with ET.Element("glyph") etc
    newglyph.process_etree()

    # Add an outline
    newglyph.add("outline")
    # Create a contour and add to outline
    contour = Ucontour(newglyph["outline"],ET.fromstring('<contour><point x="275" y="1582" type="line"/><point x="275" y="-493" type="line"/></contour>'))
    newglyph["outline"].appendobject(contour,"contour")
   
    font.deflayer.addGlyph(newglyph)
    
    return args.ifont
    
execute("PSFU",doit, argspec)