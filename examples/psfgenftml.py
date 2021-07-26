#!/usr/bin/env python
'generate ftml tests from glyph_data.csv and UFO'
__url__ = 'http://github.com/silnrsi/pysilfont'
__copyright__ = 'Copyright (c) 2018,2021 SIL International  (http://www.sil.org)'
__license__ = 'Released under the MIT License (http://opensource.org/licenses/MIT)'
__author__ = 'Bob Hallissy'

from silfont.core import execute
import silfont.ftml_builder as FB

argspec = [
    ('ifont', {'help': 'Input UFO'}, {'type': 'infont'}),
    ('output', {'help': 'Output file ftml in XML format', 'nargs': '?'}, {'type': 'outfile', 'def': '_out.ftml'}),
    ('-i','--input', {'help': 'Glyph info csv file'}, {'type': 'incsv', 'def': 'glyph_data.csv'}),
    ('-f','--fontcode', {'help': 'letter to filter for glyph_data'},{}),
    ('-l','--log', {'help': 'Set log file name'}, {'type': 'outfile', 'def': '_ftml.log'}),
    ('--langs', {'help':'List of bcp47 language tags', 'default': None}, {}),
    ('--rtl', {'help': 'enable right-to-left features', 'action': 'store_true'}, {}),
    ('--norendercheck', {'help': 'do not include the RenderingUnknown check', 'action': 'store_true'}, {}),
    ('-t', '--test', {'help': 'name of the test to generate', 'default': None}, {}),
    ('-s','--fontsrc', {'help': 'font source: "url()" or "local()" optionally followed by "=label"', 'action': 'append'}, {}),
    ('--scale', {'help': 'percentage to scale rendered text (default 100)'}, {}),
    ('--ap', {'help': 'regular expression describing APs to examine', 'default': '.'}, {}),
    ('-w', '--width', {'help': 'total width of all <string> column (default automatic)'}, {}),
    ('--xsl', {'help': 'XSL stylesheet to use'}, {}),

]


def doit(args):
    logger = args.logger

    # Read input csv
    builder = FB.FTMLBuilder(logger, incsv=args.input, fontcode=args.fontcode, font=args.ifont, ap=args.ap,
                             rtlenable=True, langs=args.langs)

    # Override default base (25CC) for displaying combining marks:
    builder.diacBase = 0x0628   # beh

    # Initialize FTML document:
    # Default name for test: AllChars or something based on the csvdata file:
    test = args.test or ('AllChars (NG)' if args.csvdata is None else
                         f'{os.path.splitext(os.path.basename(args.csvdata))[0]}.ftml')
    widths = None
    if args.width:
        try:
            width, units = re.match(r'(\d+)(.*)$', args.width).groups()
            if len(args.fontsrc):
                width = int(round(int(width)/len(args.fontsrc)))
            widths = {'string': f'{width}{units}'}
            logger.log(f'width: {args.width} --> {widths["string"]}', 'I')
        except:
            logger.log(f'Unable to parse width argument "{args.width}"', 'W')
    # split labels from fontsource parameter
    fontsrc = []
    labels = []
    for sl in args.fontsrc:
        try:
            s, l = sl.split('=',1)
            fontsrc.append(s)
            labels.append(l)
        except ValueError:
            fontsrc.append(sl)
            labels.append(None)
    ftml = FB.FTML(test, logger, comment=backgroundLegend, rendercheck=not args.norendercheck, fontscale=args.scale,
                   widths=widths, xslfn=args.xsl, fontsrc=fontsrc, fontlabel=labels, defaultrtl=args.rtl)

    if test.lower().startswith("allchars"):
        # all chars that should be in the font:
        ftml.startTestGroup('Encoded characters')
        for uid in sorted(builder.uids()):
            if uid < 32: continue
            c = builder.char(uid)
            # iterate over all permutations of feature settings that might affect this character:
            for featlist in builder.permuteFeatures(uids = (uid,)):
                ftml.setFeatures(featlist)
                builder.render((uid,), ftml)
                # Don't close test -- collect consecutive encoded chars in a single row
            ftml.clearFeatures()
            for langID in sorted(c.langs):
                ftml.setLang(langID)
                builder.render((uid,), ftml)
            ftml.clearLang()

        # Add unencoded specials and ligatures -- i.e., things with a sequence of USVs in the glyph_data:
        ftml.startTestGroup('Specials & ligatures from glyph_data')
        for basename in sorted(builder.specials()):
            special = builder.special(basename)
            # iterate over all permutations of feature settings that might affect this special
            for featlist in builder.permuteFeatures(uids = special.uids):
                ftml.setFeatures(featlist)
                builder.render(special.uids, ftml)
                # close test so each special is on its own row:
                ftml.closeTest()
            ftml.clearFeatures()
            if len(special.langs):
                for langID in sorted(special.langs):
                    ftml.setLang(langID)
                    builder.render(special.uids, ftml)
                    ftml.closeTest()
                ftml.clearLang()

        # Add Lam-Alef data manually
        ftml.startTestGroup('Lam-Alef')
        # generate list of lam and alef characters that should be in the font:
        lamlist = filter(lambda x: x in builder.uids(), (0x0644, 0x06B5, 0x06B6, 0x06B7, 0x06B8, 0x076A, 0x08A6))
        aleflist = filter(lambda x: x in builder.uids(), (0x0627, 0x0622, 0x0623, 0x0625, 0x0671, 0x0672, 0x0673, 0x0675, 0x0773, 0x0774))
        # iterate over all combinations:
        for lam in lamlist:
            for alef in aleflist:
                for featlist in builder.permuteFeatures(uids = (lam, alef)):
                    ftml.setFeatures(featlist)
                    builder.render((lam,alef), ftml)
                    # close test so each combination is on its own row:
                    ftml.closeTest()
                ftml.clearFeatures()

    if test.lower().startswith("diac"):
        # Diac attachment:

        # Representative base and diac chars:
        repDiac = filter(lambda x: x in builder.uids(), (0x064E, 0x0650, 0x065E, 0x0670, 0x0616, 0x06E3, 0x08F0, 0x08F2))
        repBase = filter(lambda x: x in builder.uids(), (0x0627, 0x0628, 0x062B, 0x0647, 0x064A, 0x77F, 0x08AC))

        ftml.startTestGroup('Representative diacritics on all bases that take diacritics')
        for uid in sorted(builder.uids()):
            # ignore some I don't care about:
            if uid < 32 or uid in (0xAA, 0xBA): continue
            c = builder.char(uid)
            # Always process Lo, but others only if that take marks:
            if c.general == 'Lo' or c.isBase:
                for diac in repDiac:
                    for featlist in builder.permuteFeatures(uids = (uid,diac)):
                        ftml.setFeatures(featlist)
                        # Don't automatically separate connecting or mirrored forms into separate lines:
                        builder.render((uid,diac), ftml, addBreaks = False)
                    ftml.clearFeatures()
                ftml.closeTest()

        ftml.startTestGroup('All diacritics on representative bases')
        for uid in sorted(builder.uids()):
            # ignore non-ABS marks
            if uid < 0x600 or uid in range(0xFE00, 0xFE10): continue
            c = builder.char(uid)
            if c.general == 'Mn':
                for base in repBase:
                    for featlist in builder.permuteFeatures(uids = (uid,base)):
                        ftml.setFeatures(featlist)
                        builder.render((base,uid), ftml, keyUID = uid, addBreaks = False)
                    ftml.clearFeatures()
                ftml.closeTest()

        ftml.startTestGroup('Special cases')
        builder.render((0x064A, 0x065E), ftml)   # Yeh + Fatha should keep dots
        builder.render((0x064A, 0x0654), ftml)   # Yeh + Hamza should loose dots
        ftml.closeTest()

    # Write the output ftml file
    ftml.writeFile(args.output)


def cmd() : execute("UFO",doit,argspec)
if __name__ == "__main__": cmd()
