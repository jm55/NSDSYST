import Pyro4, random

motd = ["Fortune and love favor the brave.",
        "Live as brave men; and if fortune is adverse, front its blows with brave hearts.",
        "Behind every great fortune lies a great crime."]

@Pyro4.expose
class MotdMaker(object):
    def __init__(self):
        self.msg = motd[random.randint(0,2)]
    def get_motd(self, name):
        print ("request made \n")
        return "Message of the day for {0}:\n{1}".format(name, self.msg)

def main():
    Pyro4.Daemon.serveSimple(
        {
        MotdMaker: "example.motd"
        },
        host= '192.168.162.1', #change this to the IP address of the computer
        ns = True,
    )

if __name__=="__main__":
    main()