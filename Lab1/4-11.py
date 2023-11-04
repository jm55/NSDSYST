import Pyro4

motd_maker = Pyro4.resolve("PYRONAME:example.motd")# use name server object lookup uri shortcut

name = input("What is your name? ").strip()

msg=motd_maker.get_motd(name)
print(msg)