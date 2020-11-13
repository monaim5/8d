

from config import Config


value = 2
maxs = Config.durations.value[min(x for x in Config.durations.value if x > value)]


print(maxs)
