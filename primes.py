#insert data user
num = int(input(“insert number: “))
if num > 1:
for i in range(2,num):
if (num % i) == 0:
print(num, “not primes”)
print(i, “kali”, num//i, “=”, num)
break
else:
print(num,”primres”)

# number<1
else:
print(num, “not primes”)
