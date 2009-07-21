import pinyin.utils

sandhiModifier = "Shift"

def shortcutKeyFor(i):
    if pinyin.utils.isosx():
        # Alt maps to the Windows key on my keyboard, NOT the Alt key.
        # NB: Ctrl maps to Option on OS X, and Option+Fx conflicts with
        # some special meanings given to those keys on Mac laptops.
        return "Alt+" + str(i)
    else:
        return "Ctrl+F" + str(i)