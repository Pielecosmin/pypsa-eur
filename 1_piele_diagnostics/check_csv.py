try:
    with open("results/romania-2020-december/csvs/costs.csv", "r") as f:
        print("--- csvs/costs.csv head ---")
        for i in range(5):
            print(f.readline().strip())
except Exception as e:
    print(e)
