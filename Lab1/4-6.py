import Pyro4

uri = input("What is the Pyro uri of the greeting object? ").strip()
name = input("What is your name? ").strip()

motd_maker = Pyro4.Proxy(uri)
print(motd_maker.get_motd(name))
