import Pyro4, random

motd = ["Fortune and love favor the brave.",
        "Live as brave men; and if fortune is adverse, front its blows with brave hearts.",
        "Behind every great fortune lies a great crime."]

@Pyro4.expose
class MotdMaker(object):
    def __init__(self):
        self.msg = motd[random.randint(0,2)]
    def get_motd(self, name):
        return "Message of the daty for {0}:\n {1}".format(name, self.msg)

daemon = Pyro4.Daemon()
uri = daemon.register(MotdMaker)

print("Ready. Object uri=", uri)
daemon.requestLoop()
