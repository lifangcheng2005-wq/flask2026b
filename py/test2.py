def life(y):
	Result = 0
	for t in y:
		Result += int(t)
	print(f"您的西元生日8位數相加結果為{Result}")

x = input("請輸入西元生日(年月日)：")
life(x)