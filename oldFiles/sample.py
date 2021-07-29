
from sarge import Command, run, Capture
from subprocess import PIPE

p = Command("python3 gattProcess.py PSYONIC-20ABH025", stdout=Capture(buffer_size=1))
p.run(input=PIPE, async_=True)

while True:
    print(p.stdout.readline())
    q = input()
    if q[0] == "/":
        p.stdin.write(q.encode() + b"\n")
        p.stdin.flush()