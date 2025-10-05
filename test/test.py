text = "Hello, World!"
for i in range(256):
    print(f"\n\033[38;5;{i}m{text}{i}m\033[0m")