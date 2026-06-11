import json, re
s = json.load(open('settings.json'))
c = open('auto_forza_skill_points.py').read()
replacement = f"DEFAULT_PRESETS = {json.dumps(s['presets'], indent=4)}\n\n"
c = re.sub(r'DEFAULT_PRESETS = \{.*?\n\}\n', replacement, c, flags=re.DOTALL)
open('auto_forza_skill_points.py', 'w').write(c)
