def Split(x)
	x = x.Split(",")
	school = x[0].replace("我是", "")
	print(f"學校：{school}")
	print(f"姓名：{x[2]}")

#只有直接執行example1.py時,以下程式才會跑
if __name__ == '__main__':
	Name = "我是靜宜大學,資管二B,程莉芳"
	Split(Name)